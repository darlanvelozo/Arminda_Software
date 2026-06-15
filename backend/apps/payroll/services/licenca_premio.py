"""
Variáveis de licença-prêmio para o engine — Onda 3.4 (ADR-0018).

A folha de licença-prêmio é dirigida por `LicencaPremioItem` (um por vínculo).
O seletor anexa o item ao vínculo (`_lp_item`); aqui só lemos e expomos
MESES_LP / DIAS_LP ao contexto.
"""

from __future__ import annotations

from decimal import Decimal

from apps.people.models import VinculoFuncional


def vars_licenca_premio(vinculo: VinculoFuncional) -> dict[str, Decimal]:
    """MESES_LP e DIAS_LP do item de licença-prêmio do vínculo."""
    item = getattr(vinculo, "_lp_item", None)
    meses = item.meses if item is not None else 0
    dias = item.dias if item is not None else 0
    return {"MESES_LP": Decimal(meses), "DIAS_LP": Decimal(dias)}
