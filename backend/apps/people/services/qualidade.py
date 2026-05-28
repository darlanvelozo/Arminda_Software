"""
Qualidade cadastral (Onda 1.6b).

Calcula health score por servidor com base em campos exigidos pelo eSocial
(S-1005 + S-2200). Devolve campos faltantes pra o frontend renderizar
chips e o operador entender o que falta antes de gerar a primeira remessa.

Política: "completo" significa pronto pra gerar S-2200 sem rejeição
estrutural. Pode haver mais validações específicas no adapter eSocial,
mas o que aqui faz já bate >95% das rejeições básicas observadas no
backup do município de referência.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from django.db.models import QuerySet

from apps.people.models import Servidor, VinculoFuncional

# Campos do Servidor exigidos pelo S-2200 — todos texto que ficaria em branco
# se vier zerado do legado.
CAMPOS_SERVIDOR_OBRIGATORIOS: tuple[str, ...] = (
    "tipo_logradouro",
    "logradouro",
    "numero",
    "bairro",
    "cidade",
    "uf",
    "cep",
    "nome_mae",
    "nacionalidade",
    "raca",
    "estado_civil",
    "instrucao",
    "pis_pasep",
)

# Campos do VinculoFuncional ativo exigidos pelo S-2200.
CAMPOS_VINCULO_OBRIGATORIOS: tuple[str, ...] = (
    "orgao_emissor",
    "sindicato",
)


LABELS = {
    "tipo_logradouro": "Tipo de logradouro",
    "logradouro": "Logradouro",
    "numero": "Número",
    "bairro": "Bairro",
    "cidade": "Cidade",
    "uf": "UF",
    "cep": "CEP",
    "nome_mae": "Nome da mãe",
    "nacionalidade": "Nacionalidade",
    "raca": "Raça/cor",
    "estado_civil": "Estado civil",
    "instrucao": "Grau de instrução",
    "pis_pasep": "PIS/PASEP",
    "orgao_emissor": "Órgão emissor (CNPJ do vínculo)",
    "sindicato": "Sindicato",
}


@dataclass(frozen=True)
class QualidadeCadastral:
    """Avaliação de um servidor — quantos campos faltam pra ele estar pronto."""

    servidor_id: int
    matricula: str
    nome: str
    total_campos: int
    campos_preenchidos: int
    campos_faltantes: list[str]

    @property
    def score(self) -> int:
        """0..100. 100 = pronto pra S-2200."""
        if self.total_campos == 0:
            return 100
        return round(100 * self.campos_preenchidos / self.total_campos)

    @property
    def completo(self) -> bool:
        return self.campos_preenchidos == self.total_campos


def _faltantes_servidor(servidor: Servidor) -> list[str]:
    """Lista campos do Servidor que estão em branco."""
    return [
        campo
        for campo in CAMPOS_SERVIDOR_OBRIGATORIOS
        if not (getattr(servidor, campo, "") or "").strip()
    ]


def _faltantes_vinculo(vinculo: VinculoFuncional | None) -> list[str]:
    """Lista campos do vínculo ativo que estão em branco (FK = NULL)."""
    if vinculo is None:
        # Sem vínculo ativo, ambos contam como faltantes
        return list(CAMPOS_VINCULO_OBRIGATORIOS)
    return [campo for campo in CAMPOS_VINCULO_OBRIGATORIOS if getattr(vinculo, f"{campo}_id") is None]


def _vinculo_principal(servidor: Servidor) -> VinculoFuncional | None:
    """
    Vínculo de referência pra qualidade cadastral.

    Critério: vínculo ativo mais antigo (data_admissao). Em geral o
    servidor só tem um ativo; quando tem mais de um (acúmulo legal),
    o eSocial trata cada matrícula/vínculo separadamente, então a
    avaliação aqui é representativa do "principal".
    """
    return (
        servidor.vinculos.filter(ativo=True)
        .order_by("data_admissao")
        .first()
    )


def avaliar_servidor(servidor: Servidor) -> QualidadeCadastral:
    """Health score de UM servidor."""
    vinculo = _vinculo_principal(servidor)
    faltantes = _faltantes_servidor(servidor) + _faltantes_vinculo(vinculo)
    total = len(CAMPOS_SERVIDOR_OBRIGATORIOS) + len(CAMPOS_VINCULO_OBRIGATORIOS)
    return QualidadeCadastral(
        servidor_id=servidor.id,
        matricula=servidor.matricula,
        nome=servidor.nome,
        total_campos=total,
        campos_preenchidos=total - len(faltantes),
        campos_faltantes=faltantes,
    )


def avaliar_lote(servidores: Iterable[Servidor]) -> list[QualidadeCadastral]:
    """Avalia uma coleção de servidores — usado em /qualidade-cadastral/."""
    return [avaliar_servidor(s) for s in servidores]


@dataclass(frozen=True)
class ResumoQualidade:
    """Agregado pra dashboard /qualidade-cadastral."""

    total_servidores: int
    completos: int
    incompletos: int
    score_medio: int
    breakdown_campos_faltantes: dict[str, int]  # campo -> N servidores que faltam


def resumir(servidores_qs: QuerySet[Servidor]) -> ResumoQualidade:
    """
    Resume a qualidade cadastral de um queryset (já filtrado por tenant).

    Itera em memória — para 5-10k servidores é OK. Acima disso vale
    refazer com Subquery + Case/When (não é prioridade nesta onda).
    """
    avaliacoes = avaliar_lote(
        servidores_qs.prefetch_related("vinculos").all()
    )
    total = len(avaliacoes)
    if total == 0:
        return ResumoQualidade(
            total_servidores=0,
            completos=0,
            incompletos=0,
            score_medio=100,
            breakdown_campos_faltantes={},
        )
    completos = sum(1 for a in avaliacoes if a.completo)
    score_medio = round(sum(a.score for a in avaliacoes) / total)
    breakdown: dict[str, int] = {}
    for a in avaliacoes:
        for campo in a.campos_faltantes:
            breakdown[campo] = breakdown.get(campo, 0) + 1
    breakdown_ordenado = dict(sorted(breakdown.items(), key=lambda kv: -kv[1]))
    return ResumoQualidade(
        total_servidores=total,
        completos=completos,
        incompletos=total - completos,
        score_medio=score_medio,
        breakdown_campos_faltantes=breakdown_ordenado,
    )


def filtrar_incompletos(qs: QuerySet[Servidor]) -> QuerySet[Servidor]:
    """
    Retorna apenas servidores com pelo menos 1 campo faltando.

    Implementação: avalia em Python e retorna `qs.filter(id__in=...)`.
    Para volumes baixos (<10k) é eficiente o suficiente; o filter final
    garante que o caller pode continuar paginando/ordenando normalmente.
    """
    avaliacoes = avaliar_lote(qs.prefetch_related("vinculos").all())
    ids_incompletos = [a.servidor_id for a in avaliacoes if not a.completo]
    return qs.filter(id__in=ids_incompletos)
