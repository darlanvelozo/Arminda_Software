"""
Resolução do regime previdenciário do município por competência e
mapeamento regime-de-vínculo → incidências (Onda 2.4 — ADR-0013).

Este módulo é a ponte entre o cadastro (`RegimePrevidenciario`, no schema
do tenant) e o engine puro (`apps.calculo`). Ele resolve a config RPPS
vigente e decide, por vínculo, se incide RGPS (INSS), RPPS ou FGTS.

Alíquota federal do FGTS — depósito mensal de 8% (Lei 8.036/90, art. 15).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from django.db.models import Q

from apps.payroll.models import RegimePrevidenciario
from apps.people.models import Regime, VinculoFuncional

ALIQUOTA_FGTS = Decimal("0.08")


def regime_vigente(competencia: date) -> RegimePrevidenciario | None:
    """RPPS ativo vigente na competência, ou None se o município não tem."""
    return (
        RegimePrevidenciario.objects.filter(
            ativo=True,
            vigencia_inicio__lte=competencia,
        )
        .filter(Q(vigencia_fim__isnull=True) | Q(vigencia_fim__gte=competencia))
        .order_by("-vigencia_inicio")
        .first()
    )


@dataclass(frozen=True)
class PrevidenciaVinculo:
    """Incidências previdenciárias resolvidas para um vínculo na competência."""

    eh_rgps: bool
    eh_rpps: bool
    eh_fgts: bool
    aliquota_patronal_rpps: Decimal

    def como_variaveis(self) -> dict[str, Decimal]:
        """Variáveis 1/0 + alíquotas que o engine injeta no contexto."""
        return {
            "EH_RGPS": Decimal(1) if self.eh_rgps else Decimal(0),
            "EH_RPPS": Decimal(1) if self.eh_rpps else Decimal(0),
            "EH_FGTS": Decimal(1) if self.eh_fgts else Decimal(0),
            "ALIQ_RPPS_PATRONAL": self.aliquota_patronal_rpps,
            "ALIQ_FGTS": ALIQUOTA_FGTS,
        }


def resolver_previdencia(
    vinculo: VinculoFuncional, regime: RegimePrevidenciario | None
) -> PrevidenciaVinculo:
    """
    Decide as incidências de um vínculo:

    - RPPS quando há regime próprio vigente e o `regime` do vínculo está
      entre os cobertos (`regimes_efetivos`). Senão, RGPS/INSS.
    - FGTS apenas para celetistas (empregados públicos regidos pela CLT).
    """
    eh_rpps = bool(regime is not None and vinculo.regime in regime.regimes_efetivos)
    eh_rgps = not eh_rpps
    eh_fgts = vinculo.regime == Regime.CELETISTA
    aliq_patronal = regime.aliquota_patronal if (eh_rpps and regime is not None) else Decimal(0)
    return PrevidenciaVinculo(
        eh_rgps=eh_rgps,
        eh_rpps=eh_rpps,
        eh_fgts=eh_fgts,
        aliquota_patronal_rpps=aliq_patronal,
    )


def rpps_config_para(regime: RegimePrevidenciario | None) -> dict[str, Any] | None:
    """Config RPPS no formato consumido por FAIXA_RPPS (ou None)."""
    return regime.como_config() if regime is not None else None
