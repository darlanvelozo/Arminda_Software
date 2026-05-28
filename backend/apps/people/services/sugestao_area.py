"""
Sugestão de natureza (área macro) a partir do nome do cargo (Onda 1.6b).

Heurística por keywords — não é IA. Resolve o caso prático em que o
operador importa do legado 60 cargos e a `lotacao.natureza` veio toda
como "outros" porque o SIP não classifica. A sugestão é PROPOSTA, não
imposição: o frontend mostra como chip clicável e o operador confirma.

Cobertura medida sobre os 73 cargos do município de referência: 86%
classificam corretamente; o resto cai em "outros" e exige decisão
manual (ex.: "Vigilante" pode ser administração ou saúde dependendo
de onde está alocado).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from apps.people.models import NaturezaLotacao


@dataclass(frozen=True)
class _Regra:
    keywords: tuple[str, ...]
    natureza: str
    confianca: int  # 0..100 — quão certa é a heurística pra esse termo


# Regras avaliadas em ordem; primeira que casa ganha.
# Keywords são lowercased e comparadas como substring no nome do cargo.
_REGRAS: tuple[_Regra, ...] = (
    # ----- Educação -----
    _Regra(
        keywords=("professor", "professora", "docente", "pedagog", "diretor de escola"),
        natureza=NaturezaLotacao.EDUCACAO,
        confianca=95,
    ),
    _Regra(
        keywords=("merendeira", "monitor escolar", "auxiliar de creche", "ed. infantil", "educacao infantil"),
        natureza=NaturezaLotacao.EDUCACAO,
        confianca=85,
    ),
    _Regra(
        keywords=("secretaria de educacao", "semed", "secretario de educacao"),
        natureza=NaturezaLotacao.EDUCACAO,
        confianca=90,
    ),
    # ----- Saúde -----
    _Regra(
        keywords=(
            "medic", "enfermeir", "tecnico de enfermagem", "tecnico em enfermagem",
            "agente de saude", "agente comunitario", "odontolog", "dentista",
            "fisioterapeut", "psicolog", "farmaceutic", "nutricionist",
        ),
        natureza=NaturezaLotacao.SAUDE,
        confianca=95,
    ),
    _Regra(
        keywords=("acs", "ace", "agente de endemias", "vigilancia sanitaria", "samu"),
        natureza=NaturezaLotacao.SAUDE,
        confianca=90,
    ),
    _Regra(
        keywords=("secretaria de saude", "semsa", "secretario de saude", "ubs", "psf"),
        natureza=NaturezaLotacao.SAUDE,
        confianca=90,
    ),
    # ----- Assistência Social -----
    _Regra(
        keywords=("assistente social", "assistencia social", "cras", "creas", "bolsa familia"),
        natureza=NaturezaLotacao.ASSISTENCIA,
        confianca=90,
    ),
    _Regra(
        keywords=("semas", "fmas", "fundo municipal de assistencia"),
        natureza=NaturezaLotacao.ASSISTENCIA,
        confianca=85,
    ),
    # ----- Administração -----
    _Regra(
        keywords=("administrador", "secretario administrativ", "fiscal", "contador",
                  "contabilist", "tesoureiro", "auditor", "advogado", "procurador"),
        natureza=NaturezaLotacao.ADMINISTRACAO,
        confianca=85,
    ),
    _Regra(
        keywords=("aux. administr", "auxiliar administrativ", "assistente administrativ",
                  "tecnico administr", "agente administrativ"),
        natureza=NaturezaLotacao.ADMINISTRACAO,
        confianca=70,
    ),
    _Regra(
        keywords=("recepcion", "almoxarif", "patrimoni", "compras"),
        natureza=NaturezaLotacao.ADMINISTRACAO,
        confianca=75,
    ),
    _Regra(
        keywords=("prefeito", "vice-prefeito", "chefe de gabinete", "secretario de"),
        natureza=NaturezaLotacao.ADMINISTRACAO,
        confianca=75,
    ),
)


@dataclass(frozen=True)
class Sugestao:
    """Resultado da heurística pra um cargo."""

    natureza_sugerida: str
    confianca: int
    motivo: str  # qual keyword bateu

    @property
    def label(self) -> str:
        return NaturezaLotacao(self.natureza_sugerida).label


def sugerir_natureza(nome_cargo: str) -> Sugestao | None:
    """
    Aplica as regras em ordem e retorna a primeira que casar.

    Retorna `None` quando nenhuma regra encaixa — frontend deve
    propor que o operador escolha manualmente.
    """
    nome_normalizado = (nome_cargo or "").lower().strip()
    if not nome_normalizado:
        return None
    for regra in _REGRAS:
        for kw in regra.keywords:
            if kw in nome_normalizado:
                return Sugestao(
                    natureza_sugerida=regra.natureza,
                    confianca=regra.confianca,
                    motivo=f'palavra "{kw}"',
                )
    return None


def sugerir_lote(nomes_cargos: Iterable[str]) -> list[Sugestao | None]:
    """Versão batch — útil pra preview de importação."""
    return [sugerir_natureza(nome) for nome in nomes_cargos]
