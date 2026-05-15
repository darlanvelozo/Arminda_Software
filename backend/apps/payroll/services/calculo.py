"""
Serviço de cálculo de folha mensal ordinária (Bloco 2.2).

Orquestra a chamada do engine `apps.calculo` para todos os vínculos
ativos numa competência × todas as rubricas ativas, produzindo
`Lancamento` e atualizando os totais da `Folha`.

Princípios:
- **Idempotente**: rodar `calcular_folha(f)` 2 vezes produz o mesmo
  estado final. Lançamentos são atualizados via `update_or_create`
  por `(folha, vinculo, rubrica)`. Sobras (rubricas removidas entre
  runs) são apagadas.
- **Coleta erros sem parar batch**: cada par (vínculo, rubrica) tenta
  isoladamente; erros são reportados ao final no `RelatorioCalculo`.
- **Atômico**: tudo dentro de `transaction.atomic`. Se algo crítico
  falhar (não um erro de fórmula isolada), tudo é desfeito.
- **Tudo em `Decimal`**: nada de `float`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Q

from apps.calculo.dependencias import RubricaParaOrdenar, ordenar_topologicamente
from apps.calculo.formula.avaliador import avaliar
from apps.calculo.formula.contexto import ContextoFolha
from apps.calculo.formula.errors import FormulaError
from apps.payroll.models import Folha, Lancamento, Rubrica, TipoRubrica
from apps.people.models import Dependente, VinculoFuncional

# Salário mínimo nacional 2026 (referência inicial; vai virar
# `ConfiguracaoGlobal` ou tabela legal sobrescrevível na Onda 2.3).
SALARIO_MINIMO_2026 = Decimal("1518.00")

# Horas-mês padrão de jornada 40h/semana (4.345 semanas × 40h).
# Para jornadas diferentes (20h, 30h, 44h), proporcional.
HORAS_MES_44H = Decimal("220.00")


@dataclass
class ErroLancamento:
    """Um erro específico ao calcular uma rubrica para um vínculo."""

    vinculo_id: int
    matricula: str
    rubrica_codigo: str
    code: str
    mensagem: str


@dataclass
class RelatorioCalculo:
    """Resultado da execução de `calcular_folha`."""

    folha_id: int
    competencia: date
    vinculos_processados: int = 0
    rubricas_processadas: int = 0
    lancamentos_criados: int = 0
    lancamentos_atualizados: int = 0
    lancamentos_removidos: int = 0  # rubricas que sumiram entre runs
    erros: list[ErroLancamento] = field(default_factory=list)
    ordem_rubricas: list[str] = field(default_factory=list)

    @property
    def total_lancamentos(self) -> int:
        return self.lancamentos_criados + self.lancamentos_atualizados


# ============================================================
# Construção do contexto a partir de Vínculo + Competência
# ============================================================


def _idade_em(data_nascimento: date, competencia: date) -> int:
    """Idade do servidor no primeiro dia da competência."""
    return (
        competencia.year
        - data_nascimento.year
        - ((competencia.month, competencia.day) < (data_nascimento.month, data_nascimento.day))
    )


def _tempo_servico_anos(data_admissao: date, competencia: date) -> int:
    """Anos completos de serviço na competência (rounded down)."""
    return (
        competencia.year
        - data_admissao.year
        - ((competencia.month, competencia.day) < (data_admissao.month, data_admissao.day))
    )


def construir_contexto(
    vinculo: VinculoFuncional,
    competencia: date,
    *,
    rubricas_calculadas: dict[str, Decimal] | None = None,
) -> ContextoFolha:
    """
    Monta `ContextoFolha` com todas as variáveis padrão a partir de um
    vínculo. Esta é a fonte da verdade dos nomes de variáveis disponíveis.

    Variáveis derivadas (Dependente, Tempo Serviço, etc.) consultam o
    banco — caller deve ter `select_related`/`prefetch_related` se
    estiver iterando muito.
    """
    servidor = vinculo.servidor
    idade = _idade_em(servidor.data_nascimento, competencia)

    # Contagens de dependentes — cada um sob seu critério próprio
    deps_ir = Dependente.objects.filter(servidor=servidor, ir=True).count()
    deps_salfam = Dependente.objects.filter(
        servidor=servidor, salario_familia=True
    ).count()

    salario_base = Decimal(vinculo.salario_base or 0)

    variaveis: dict[str, Decimal | int] = {
        "SALARIO_BASE": salario_base,
        "CARGA_HORARIA": Decimal(vinculo.carga_horaria or 0),
        "HORAS_PADRAO": HORAS_MES_44H,
        # Por enquanto assumimos mês completo — `falta` e `dias` reais
        # entram via integração com folha-ponto na Onda 2.6+.
        "HORAS_TRABALHADAS": HORAS_MES_44H,
        "DIAS_TRABALHADOS": Decimal(30),
        "FALTAS": Decimal(0),
        "IDADE": Decimal(idade),
        "DEPENDENTES": Decimal(deps_ir),
        "DEPENDENTES_SALFAM": Decimal(deps_salfam),
        "TEMPO_SERVICO_ANOS": Decimal(_tempo_servico_anos(vinculo.data_admissao, competencia)),
        "SALARIO_MINIMO": SALARIO_MINIMO_2026,
        "COMPETENCIA_ANO": competencia.year,
        "COMPETENCIA_MES": competencia.month,
    }

    return ContextoFolha(
        variaveis=variaveis,
        rubricas_calculadas=rubricas_calculadas or {},
    )


# ============================================================
# Cálculo da folha
# ============================================================


def _vinculos_da_competencia(competencia: date):
    """
    Vínculos ativos no primeiro dia da competência:
    - admitidos até a competência
    - não desligados antes da competência
    """
    return (
        VinculoFuncional.objects.filter(
            ativo=True,
            data_admissao__lte=competencia,
        )
        .filter(Q(data_demissao__isnull=True) | Q(data_demissao__gte=competencia))
        .select_related("servidor", "cargo", "lotacao", "unidade_orcamentaria")
        .order_by("servidor__nome", "id")
    )


def _rubricas_ativas_ordenadas() -> tuple[list[Rubrica], list[str]]:
    """
    Carrega rubricas ativas, ordena topologicamente pela dependência
    declarada nas fórmulas (`RUBRICA('X')`).

    Returns:
        (lista de Rubrica em ordem de cálculo, lista de códigos na ordem)
    """
    rubricas = list(Rubrica.objects.filter(ativo=True).order_by("codigo"))
    if not rubricas:
        return [], []

    entrada = [RubricaParaOrdenar(codigo=r.codigo, formula=r.formula or "") for r in rubricas]
    ordem_codigos = ordenar_topologicamente(entrada)
    por_codigo = {r.codigo: r for r in rubricas}
    return [por_codigo[c] for c in ordem_codigos], ordem_codigos


def _processar_rubrica(
    *,
    folha: Folha,
    vinculo: VinculoFuncional,
    rubrica: Rubrica,
    rubricas_calc: dict[str, Decimal],
    relatorio: RelatorioCalculo,
) -> Decimal | None:
    """
    Avalia uma rubrica para um vínculo, persiste idempotentemente.
    Devolve o valor calculado (ou `None` se erro de fórmula — já registrado
    no relatório). Cache `rubricas_calc` é atualizado quando sucesso.
    """
    ctx = construir_contexto(vinculo, folha.competencia, rubricas_calculadas=rubricas_calc)
    try:
        valor = avaliar(rubrica.formula, ctx)
    except FormulaError as exc:
        relatorio.erros.append(
            ErroLancamento(
                vinculo_id=vinculo.id,
                matricula=vinculo.servidor.matricula,
                rubrica_codigo=rubrica.codigo,
                code=exc.code,
                mensagem=str(exc.args[0]) if exc.args else str(exc),
            )
        )
        return None

    rubricas_calc[rubrica.codigo] = valor
    _, criado = Lancamento.objects.update_or_create(
        folha=folha,
        vinculo=vinculo,
        rubrica=rubrica,
        defaults={
            "servidor": vinculo.servidor,
            "referencia": Decimal(0),
            "valor": valor,
        },
    )
    if criado:
        relatorio.lancamentos_criados += 1
    else:
        relatorio.lancamentos_atualizados += 1
    return valor


def _limpar_orfaos_e_fechar(
    folha: Folha,
    pares_processados: set[tuple[int, int]],
    total_proventos: Decimal,
    total_descontos: Decimal,
    relatorio: RelatorioCalculo,
) -> None:
    """Remove lançamentos cujo par (vínculo, rubrica) não foi tocado nesta
    execução, atualiza totais e fecha a folha (aberta → calculada)."""
    existentes = Lancamento.objects.filter(folha=folha)
    for lanc in existentes:
        chave = (lanc.vinculo_id, lanc.rubrica_id)
        if chave not in pares_processados:
            lanc.delete()
            relatorio.lancamentos_removidos += 1

    folha.total_proventos = total_proventos
    folha.total_descontos = total_descontos
    folha.total_liquido = total_proventos - total_descontos
    if folha.status == "aberta":
        folha.status = "calculada"
    folha.save(
        update_fields=[
            "total_proventos",
            "total_descontos",
            "total_liquido",
            "status",
            "atualizado_em",
        ]
    )


def calcular_folha(folha: Folha) -> RelatorioCalculo:
    """
    Calcula uma folha mensal completa.

    Para cada vínculo ativo na competência × rubrica ativa (em ordem
    topológica), avalia a fórmula e produz/atualiza um `Lancamento`.

    Idempotente: re-chamar com a mesma folha produz o mesmo estado.

    Args:
        folha: Folha já criada (em status `aberta` ou `calculada`).

    Returns:
        RelatorioCalculo com contadores e lista de erros.

    Raises:
        DependenciaCiclicaError, DependenciaInexistenteError: se as
            rubricas tiverem dependências mal configuradas. Erro de
            estrutura — não há como calcular nada, transação inteira é
            abortada.
    """
    relatorio = RelatorioCalculo(folha_id=folha.id, competencia=folha.competencia)
    rubricas_ordenadas, ordem = _rubricas_ativas_ordenadas()
    relatorio.ordem_rubricas = ordem

    if not rubricas_ordenadas:
        # Folha sem rubricas — não há nada a calcular, mas isso é estado
        # legítimo (município que ainda não cadastrou rubricas).
        return relatorio

    vinculos = list(_vinculos_da_competencia(folha.competencia))
    relatorio.vinculos_processados = len(vinculos)
    relatorio.rubricas_processadas = len(rubricas_ordenadas)

    # Pares (vinculo_id, rubrica_id) que foram tocados nesta execução
    # — ao final, deletamos os lançamentos que sobraram (rubrica antiga).
    pares_processados: set[tuple[int, int]] = set()

    total_proventos = Decimal("0")
    total_descontos = Decimal("0")

    with transaction.atomic():
        for vinculo in vinculos:
            # Cache de rubricas calculadas para este vínculo —
            # acessada por RUBRICA('X') nas fórmulas seguintes.
            rubricas_calc: dict[str, Decimal] = {}

            for rubrica in rubricas_ordenadas:
                if not rubrica.formula or not rubrica.formula.strip():
                    # Rubrica sem fórmula = não calcula (provavelmente
                    # placeholder, preenchida manualmente)
                    continue

                valor = _processar_rubrica(
                    folha=folha,
                    vinculo=vinculo,
                    rubrica=rubrica,
                    rubricas_calc=rubricas_calc,
                    relatorio=relatorio,
                )
                if valor is None:
                    continue

                pares_processados.add((vinculo.id, rubrica.id))

                # Totais (rubrica informativa não conta)
                if rubrica.tipo == TipoRubrica.PROVENTO:
                    total_proventos += valor
                elif rubrica.tipo == TipoRubrica.DESCONTO:
                    total_descontos += valor

        _limpar_orfaos_e_fechar(
            folha, pares_processados, total_proventos, total_descontos, relatorio
        )

    return relatorio
