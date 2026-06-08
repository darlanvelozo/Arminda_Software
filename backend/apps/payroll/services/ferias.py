"""
Variáveis de férias para o engine — Onda 3.3 (ADR-0017).

A folha de férias é dirigida por `FeriasItem` (um por vínculo). O seletor de
vínculos anexa o item ao vínculo (`_ferias_item`) para evitar N queries; aqui
só lemos esse atributo e expomos DIAS_FERIAS / DIAS_ABONO ao contexto.
"""

from __future__ import annotations

from decimal import Decimal

from apps.people.models import VinculoFuncional


def vars_ferias(vinculo: VinculoFuncional) -> dict[str, Decimal]:
    """DIAS_FERIAS (gozo) e DIAS_ABONO (venda) do item de férias do vínculo."""
    item = getattr(vinculo, "_ferias_item", None)
    dias_gozo = item.dias_gozo if item is not None else 0
    dias_abono = item.dias_abono if item is not None else 0
    return {
        "DIAS_FERIAS": Decimal(dias_gozo),
        "DIAS_ABONO": Decimal(dias_abono),
    }
