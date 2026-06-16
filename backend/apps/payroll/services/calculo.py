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
from typing import TYPE_CHECKING

from django.db import transaction
from django.db.models import Q

from apps.calculo.dependencias import RubricaParaOrdenar, ordenar_topologicamente
from apps.calculo.formula.avaliador import avaliar
from apps.calculo.formula.contexto import ContextoFolha
from apps.calculo.formula.errors import FormulaError
from apps.payroll.models import Folha, Lancamento, Rubrica, TipoFolha, TipoRubrica
from apps.payroll.services.decimo import avos_no_ano
from apps.payroll.services.ferias import vars_ferias
from apps.payroll.services.licenca_premio import vars_licenca_premio
from apps.payroll.services.previdencia import (
    regime_vigente,
    resolver_previdencia,
    rpps_config_para,
)
from apps.payroll.services.rescisao import vars_rescisao
from apps.people.models import Dependente, VinculoFuncional

if TYPE_CHECKING:
    from apps.payroll.models import RegimePrevidenciario

# Fallback do salário-mínimo caso a TabelaLegal não tenha sido seedada.
# A partir da Onda 2.3, o valor real vem de `apps.calculo.tabelas.salario_minimo`
# resolvido pela competência da folha.
SALARIO_MINIMO_FALLBACK = Decimal("1518.00")

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
    variaveis_extra: dict[str, Decimal] | None = None,
    rpps_config: dict | None = None,
) -> ContextoFolha:
    """
    Monta `ContextoFolha` com todas as variáveis padrão a partir de um
    vínculo. Esta é a fonte da verdade dos nomes de variáveis disponíveis.

    `variaveis_extra` injeta variáveis calculadas pelo engine (bases de
    incidência BASE_*, flags de regime EH_*, alíquotas ALIQ_* — Onda 2.4).
    `rpps_config` é a config do regime próprio resolvida pela competência
    (consumida por FAIXA_RPPS).

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

    # SALARIO_MINIMO dinâmico via TabelaLegal (Onda 2.3). Se não houver
    # tabela cadastrada para a competência, cai para o fallback de 2025.
    from apps.calculo.tabelas import TabelaLegalAusenteError
    from apps.calculo.tabelas import salario_minimo as _sal_min

    try:
        sal_min = _sal_min(competencia)
    except TabelaLegalAusenteError:
        sal_min = SALARIO_MINIMO_FALLBACK

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
        "SALARIO_MINIMO": sal_min,
        "COMPETENCIA_ANO": competencia.year,
        "COMPETENCIA_MES": competencia.month,
    }

    if variaveis_extra:
        variaveis.update(variaveis_extra)

    return ContextoFolha(
        variaveis=variaveis,
        rubricas_calculadas=rubricas_calculadas or {},
        competencia=competencia,
        rpps_config=rpps_config,
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


def _vinculos_rescisao(competencia: date):
    """
    Vínculos desligados no mês da competência (Onda 3.2): `data_demissao`
    entre o 1º e o último dia do mês — independente de `ativo`, pois o
    desligado deixa de ser ativo.
    """
    import calendar

    ultimo_dia = competencia.replace(day=calendar.monthrange(competencia.year, competencia.month)[1])
    return (
        VinculoFuncional.objects.filter(
            data_demissao__gte=competencia,
            data_demissao__lte=ultimo_dia,
        )
        .select_related("servidor", "cargo", "lotacao", "unidade_orcamentaria")
        .order_by("servidor__nome", "id")
    )


def _vinculos_por_itens(folha: Folha, manager_name: str, attr: str):
    """Vínculos vindos de itens da folha (férias / licença-prêmio).
    Anexa o item ao vínculo em `attr` para evitar N queries."""
    itens = (
        getattr(folha, manager_name)
        .select_related(
            "vinculo__servidor", "vinculo__cargo", "vinculo__lotacao",
            "vinculo__unidade_orcamentaria",
        )
        .order_by("vinculo__servidor__nome", "vinculo_id")
    )
    vinculos = []
    for item in itens:
        v = item.vinculo
        setattr(v, attr, item)
        vinculos.append(v)
    return vinculos


def _vinculos_da_folha(folha: Folha):
    """Seleciona os vínculos conforme o tipo de folha."""
    if folha.tipo == TipoFolha.RESCISAO:
        return _vinculos_rescisao(folha.competencia)
    if folha.tipo == TipoFolha.FERIAS:
        return _vinculos_por_itens(folha, "ferias_itens", "_ferias_item")
    if folha.tipo == TipoFolha.LICENCA_PREMIO:
        return _vinculos_por_itens(folha, "lp_itens", "_lp_item")
    return _vinculos_da_competencia(folha.competencia)


def _vinculos_complementar(folha: Folha):
    """Vínculos com itens complementares (Onda 3.5 — ADR-0019). Agrupa os
    itens por vínculo e anexa a lista em `_complementar_itens` (evita N
    queries na materialização)."""
    itens = folha.complementar_itens.select_related(
        "vinculo__servidor", "vinculo__cargo", "vinculo__lotacao",
        "vinculo__unidade_orcamentaria", "rubrica",
    ).order_by("vinculo__servidor__nome", "vinculo_id", "rubrica__codigo")
    por_vinculo: dict[int, tuple[VinculoFuncional, list]] = {}
    for item in itens:
        if item.vinculo_id not in por_vinculo:
            por_vinculo[item.vinculo_id] = (item.vinculo, [])
        por_vinculo[item.vinculo_id][1].append(item)
    vinculos = []
    for vinculo, lista in por_vinculo.values():
        vinculo._complementar_itens = lista
        vinculos.append(vinculo)
    return vinculos


def _calcular_complementar(folha: Folha, relatorio: RelatorioCalculo) -> RelatorioCalculo:
    """Folha complementar (Onda 3.5 — ADR-0019): lançamentos explícitos por
    servidor, sem fórmulas e sem incidência automática. Cada item vira um
    `Lancamento` com o valor informado; proventos/descontos somam pelo tipo
    da rubrica. Idempotente: re-rodar produz o mesmo estado."""
    vinculos = _vinculos_complementar(folha)
    relatorio.vinculos_processados = len(vinculos)
    pares_processados: set[tuple[int, int]] = set()
    total_proventos = Decimal("0")
    total_descontos = Decimal("0")

    with transaction.atomic():
        for vinculo in vinculos:
            for item in vinculo._complementar_itens:
                _, criado = Lancamento.objects.update_or_create(
                    folha=folha,
                    vinculo=vinculo,
                    rubrica=item.rubrica,
                    defaults={
                        "servidor": vinculo.servidor,
                        "referencia": Decimal(0),
                        "valor": item.valor,
                    },
                )
                if criado:
                    relatorio.lancamentos_criados += 1
                else:
                    relatorio.lancamentos_atualizados += 1
                pares_processados.add((vinculo.id, item.rubrica_id))
                if item.rubrica.tipo == TipoRubrica.PROVENTO:
                    total_proventos += item.valor
                elif item.rubrica.tipo == TipoRubrica.DESCONTO:
                    total_descontos += item.valor

        _limpar_orfaos_e_fechar(
            folha, pares_processados, total_proventos, total_descontos, relatorio
        )
    return relatorio


def _rubricas_ativas_ordenadas(tipo_folha: str) -> tuple[list[Rubrica], list[str]]:
    """
    Carrega rubricas ativas **do tipo de folha**, ordena topologicamente pela
    dependência declarada nas fórmulas (`RUBRICA('X')`).

    O filtro por `tipos_folha` (Onda 3.1) garante que a folha mensal não rode
    rubricas de 13º e vice-versa.

    Returns:
        (lista de Rubrica em ordem de cálculo, lista de códigos na ordem)
    """
    rubricas = [
        r
        for r in Rubrica.objects.filter(ativo=True).order_by("codigo")
        if tipo_folha in (r.tipos_folha or [])
    ]
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
    variaveis_extra: dict[str, Decimal] | None = None,
    rpps_config: dict | None = None,
) -> Decimal | None:
    """
    Avalia uma rubrica para um vínculo, persiste idempotentemente.
    Devolve o valor calculado (ou `None` se erro de fórmula — já registrado
    no relatório). Cache `rubricas_calc` é atualizado quando sucesso.
    """
    ctx = construir_contexto(
        vinculo,
        folha.competencia,
        rubricas_calculadas=rubricas_calc,
        variaveis_extra=variaveis_extra,
        rpps_config=rpps_config,
    )
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


# Flags `incide_*` → nome da base que a rubrica alimenta na fase 1.
_FLAG_PARA_BASE = (
    ("incide_inss", "BASE_INSS"),
    ("incide_irrf", "BASE_IRRF"),
    ("incide_fgts", "BASE_FGTS"),
    ("incide_rpps", "BASE_RPPS"),
)


def _fase_proventos(
    *,
    folha: Folha,
    vinculo: VinculoFuncional,
    proventos: list[Rubrica],
    rubricas_calc: dict[str, Decimal],
    vars_regime: dict[str, Decimal],
    rpps_config: dict | None,
    relatorio: RelatorioCalculo,
    pares_processados: set[tuple[int, int]],
) -> tuple[Decimal, dict[str, Decimal]]:
    """Fase 1 — calcula proventos e acumula as bases de incidência por flag.
    Devolve `(total_proventos, bases)`."""
    bases: dict[str, Decimal] = {
        "BASE_INSS": Decimal(0),
        "BASE_IRRF": Decimal(0),
        "BASE_FGTS": Decimal(0),
        "BASE_RPPS": Decimal(0),
    }
    total = Decimal(0)
    for rubrica in proventos:
        if not rubrica.formula or not rubrica.formula.strip():
            continue
        valor = _processar_rubrica(
            folha=folha,
            vinculo=vinculo,
            rubrica=rubrica,
            rubricas_calc=rubricas_calc,
            relatorio=relatorio,
            variaveis_extra={**vars_regime, **bases},
            rpps_config=rpps_config,
        )
        if valor is None:
            continue
        pares_processados.add((vinculo.id, rubrica.id))
        total += valor
        for flag, base in _FLAG_PARA_BASE:
            if getattr(rubrica, flag):
                bases[base] += valor
    return total, bases


def _fase_descontos(
    *,
    folha: Folha,
    vinculo: VinculoFuncional,
    pos_proventos: list[Rubrica],
    rubricas_calc: dict[str, Decimal],
    variaveis_extra: dict[str, Decimal],
    rpps_config: dict | None,
    relatorio: RelatorioCalculo,
    pares_processados: set[tuple[int, int]],
) -> Decimal:
    """Fase 2 — calcula descontos e informativas. Devolve `total_descontos`
    (informativas não entram nos totais)."""
    total = Decimal(0)
    for rubrica in pos_proventos:
        if not rubrica.formula or not rubrica.formula.strip():
            continue
        valor = _processar_rubrica(
            folha=folha,
            vinculo=vinculo,
            rubrica=rubrica,
            rubricas_calc=rubricas_calc,
            relatorio=relatorio,
            variaveis_extra=variaveis_extra,
            rpps_config=rpps_config,
        )
        if valor is None:
            continue
        pares_processados.add((vinculo.id, rubrica.id))
        if rubrica.tipo == TipoRubrica.DESCONTO:
            total += valor
    return total


_PARCELA_POR_TIPO = {
    TipoFolha.DECIMO_PRIMEIRO: 1,
    TipoFolha.DECIMO_SEGUNDO: 2,
}


def _vars_decimo(folha: Folha, vinculo: VinculoFuncional) -> dict[str, Decimal]:
    """Variáveis de 13º expostas às fórmulas (Onda 3.1): avos, base e parcela."""
    avos = avos_no_ano(vinculo.data_admissao, vinculo.data_demissao, folha.competencia.year)
    return {
        "AVOS_13": Decimal(avos),
        "BASE_13": Decimal(vinculo.salario_base or 0),
        "PARCELA_13": Decimal(_PARCELA_POR_TIPO.get(folha.tipo, 0)),
    }


def _processar_vinculo(
    *,
    folha: Folha,
    vinculo: VinculoFuncional,
    proventos: list[Rubrica],
    pos_proventos: list[Rubrica],
    regime: RegimePrevidenciario | None,
    rpps_config: dict | None,
    relatorio: RelatorioCalculo,
    pares_processados: set[tuple[int, int]],
) -> tuple[Decimal, Decimal]:
    """
    Processa um vínculo nas duas fases (proventos → bases → descontos).
    Devolve `(total_proventos, total_descontos)` deste vínculo.
    """
    rubricas_calc: dict[str, Decimal] = {}
    # Regime (RGPS/RPPS/FGTS) + 13º (avos/base/parcela) + rescisão (saldo/avos/motivo).
    vars_regime = {
        **resolver_previdencia(vinculo, regime).como_variaveis(),
        **_vars_decimo(folha, vinculo),
        **vars_rescisao(vinculo),
        **vars_ferias(vinculo),
        **vars_licenca_premio(vinculo),
    }

    total_proventos, bases = _fase_proventos(
        folha=folha,
        vinculo=vinculo,
        proventos=proventos,
        rubricas_calc=rubricas_calc,
        vars_regime=vars_regime,
        rpps_config=rpps_config,
        relatorio=relatorio,
        pares_processados=pares_processados,
    )
    total_descontos = _fase_descontos(
        folha=folha,
        vinculo=vinculo,
        pos_proventos=pos_proventos,
        rubricas_calc=rubricas_calc,
        variaveis_extra={**vars_regime, **bases},
        rpps_config=rpps_config,
        relatorio=relatorio,
        pares_processados=pares_processados,
    )
    return total_proventos, total_descontos


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

    # Folha complementar (Onda 3.5 — ADR-0019): caminho próprio, sem fórmulas
    # — os valores vêm dos itens lançados à mão.
    if folha.tipo == TipoFolha.COMPLEMENTAR:
        return _calcular_complementar(folha, relatorio)

    rubricas_ordenadas, ordem = _rubricas_ativas_ordenadas(folha.tipo)
    relatorio.ordem_rubricas = ordem

    if not rubricas_ordenadas:
        # Folha sem rubricas — não há nada a calcular, mas isso é estado
        # legítimo (município que ainda não cadastrou rubricas).
        return relatorio

    vinculos = list(_vinculos_da_folha(folha))
    relatorio.vinculos_processados = len(vinculos)
    relatorio.rubricas_processadas = len(rubricas_ordenadas)

    # Cálculo em duas fases (Onda 2.4 — ADR-0013): proventos primeiro,
    # acumulando as bases de incidência por flag; depois descontos e
    # informativas, que consomem BASE_*/EH_*/ALIQ_*.
    proventos = [r for r in rubricas_ordenadas if r.tipo == TipoRubrica.PROVENTO]
    pos_proventos = [r for r in rubricas_ordenadas if r.tipo != TipoRubrica.PROVENTO]

    # Previdência do município resolvida uma vez por folha.
    regime = regime_vigente(folha.competencia)
    rpps_config = rpps_config_para(regime)

    # Pares (vinculo_id, rubrica_id) que foram tocados nesta execução
    # — ao final, deletamos os lançamentos que sobraram (rubrica antiga).
    pares_processados: set[tuple[int, int]] = set()

    total_proventos = Decimal("0")
    total_descontos = Decimal("0")

    with transaction.atomic():
        for vinculo in vinculos:
            prov, desc = _processar_vinculo(
                folha=folha,
                vinculo=vinculo,
                proventos=proventos,
                pos_proventos=pos_proventos,
                regime=regime,
                rpps_config=rpps_config,
                relatorio=relatorio,
                pares_processados=pares_processados,
            )
            total_proventos += prov
            total_descontos += desc

        _limpar_orfaos_e_fechar(
            folha, pares_processados, total_proventos, total_descontos, relatorio
        )

    return relatorio
