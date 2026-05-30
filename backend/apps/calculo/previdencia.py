"""
Cálculo puro da contribuição previdenciária do servidor ao RPPS (Onda 2.4).

Função pura, sem acesso ao banco: recebe a `config` do regime próprio
como um dicionário simples (resolvido por `apps.payroll.services.previdencia`
e injetado no `ContextoFolha.rpps_config`). Mantém `apps.calculo` livre de
dependência de `apps.payroll` — ver ADR-0013.

Formato esperado de `config`:

    {
        "modo": "flat" | "progressivo",
        "aliquota_servidor": Decimal,   # usado quando modo == "flat"
        "teto": Decimal | None,         # teto da base (parcela RGPS, p.ex.)
        "faixas": [                     # usado quando modo == "progressivo"
            {"ate": Decimal | None, "aliquota": Decimal},
            ...
        ],
    }

`None` (município sem RPPS) → contribuição 0.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

CENTAVOS = Decimal("0.01")


def _d(v: Any) -> Decimal:
    return v if isinstance(v, Decimal) else Decimal(str(v))


def contribuicao_rpps(base: Any, config: dict[str, Any] | None) -> Decimal:
    """
    Contribuição do servidor ao RPPS sobre `base`, conforme `config`.

    - `config is None` → 0 (município sem regime próprio).
    - modo "flat": `min(base, teto) * aliquota_servidor`.
    - modo "progressivo": alíquota efetiva por faixa (cada faixa incide
      só sobre a parte da base que cai nela), respeitando o teto — mesma
      mecânica do INSS pós-EC 103.

    Sempre arredonda para centavos (ROUND_HALF_EVEN do Decimal padrão é
    suficiente aqui; folha usa `quantize` em 2 casas).
    """
    if config is None:
        return Decimal(0)

    base_d = _d(base)
    if base_d <= 0:
        return Decimal(0)

    teto_raw = config.get("teto")
    teto = _d(teto_raw) if teto_raw is not None else None
    base_aplicada = min(base_d, teto) if teto is not None else base_d

    modo = config.get("modo", "flat")

    if modo == "flat":
        aliquota = _d(config.get("aliquota_servidor", 0))
        return (base_aplicada * aliquota).quantize(CENTAVOS)

    if modo == "progressivo":
        faixas = config.get("faixas") or []
        contribuicao = Decimal(0)
        limite_inferior = Decimal(0)
        for f in faixas:
            ate_raw = f.get("ate")
            teto_faixa = _d(ate_raw) if ate_raw is not None else base_aplicada
            if base_aplicada <= limite_inferior:
                break
            parte = min(base_aplicada, teto_faixa) - limite_inferior
            if parte > 0:
                contribuicao += parte * _d(f.get("aliquota", 0))
            limite_inferior = teto_faixa
        return contribuicao.quantize(CENTAVOS)

    # Modo desconhecido — tratado como sem contribuição (defensivo;
    # o modelo valida o domínio antes de chegar aqui).
    return Decimal(0)
