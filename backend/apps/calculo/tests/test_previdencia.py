"""
Testes da contribuição RPPS pura (Onda 2.4 — ADR-0013).

`contribuicao_rpps` não toca o banco: recebe a config como dict. Cobre
modo flat, progressivo, teto e config ausente.
"""

from __future__ import annotations

from decimal import Decimal

from apps.calculo.previdencia import contribuicao_rpps


def test_config_none_retorna_zero():
    assert contribuicao_rpps(Decimal("5000"), None) == Decimal(0)


def test_base_zero_ou_negativa_retorna_zero():
    cfg = {"modo": "flat", "aliquota_servidor": Decimal("0.14")}
    assert contribuicao_rpps(Decimal(0), cfg) == Decimal(0)
    assert contribuicao_rpps(Decimal("-100"), cfg) == Decimal(0)


def test_flat_simples():
    cfg = {"modo": "flat", "aliquota_servidor": Decimal("0.14"), "teto": None}
    # 4000 * 0.14 = 560.00
    assert contribuicao_rpps(Decimal("4000"), cfg) == Decimal("560.00")


def test_flat_respeita_teto():
    cfg = {"modo": "flat", "aliquota_servidor": Decimal("0.14"), "teto": Decimal("3000")}
    # base 5000 limitada a 3000 → 3000 * 0.14 = 420.00
    assert contribuicao_rpps(Decimal("5000"), cfg) == Decimal("420.00")


def test_progressivo_aliquota_efetiva_por_faixa():
    # Faixas estilo EC 103: cada faixa incide só sobre a parte da base nela.
    cfg = {
        "modo": "progressivo",
        "faixas": [
            {"ate": Decimal("1000"), "aliquota": Decimal("0.10")},
            {"ate": Decimal("2000"), "aliquota": Decimal("0.20")},
            {"ate": None, "aliquota": Decimal("0.30")},
        ],
        "teto": None,
    }
    # base 2500: 1000*0.10 + 1000*0.20 + 500*0.30 = 100 + 200 + 150 = 450.00
    assert contribuicao_rpps(Decimal("2500"), cfg) == Decimal("450.00")


def test_progressivo_respeita_teto():
    cfg = {
        "modo": "progressivo",
        "faixas": [
            {"ate": Decimal("1000"), "aliquota": Decimal("0.10")},
            {"ate": None, "aliquota": Decimal("0.20")},
        ],
        "teto": Decimal("1500"),
    }
    # base 5000 limitada a 1500: 1000*0.10 + 500*0.20 = 100 + 100 = 200.00
    assert contribuicao_rpps(Decimal("5000"), cfg) == Decimal("200.00")


def test_modo_desconhecido_retorna_zero():
    cfg = {"modo": "exotico", "aliquota_servidor": Decimal("0.14")}
    assert contribuicao_rpps(Decimal("4000"), cfg) == Decimal(0)


def test_faixa_rpps_builtin_via_avaliador():
    """FAIXA_RPPS deve usar a config injetada no ContextoFolha."""
    from apps.calculo.formula.avaliador import avaliar
    from apps.calculo.formula.contexto import ContextoFolha

    ctx = ContextoFolha(
        variaveis={"BASE_RPPS": Decimal("4000")},
        rpps_config={"modo": "flat", "aliquota_servidor": Decimal("0.14"), "teto": None},
    )
    assert avaliar("FAIXA_RPPS(BASE_RPPS)", ctx) == Decimal("560.00")


def test_faixa_rpps_sem_config_retorna_zero():
    from apps.calculo.formula.avaliador import avaliar
    from apps.calculo.formula.contexto import ContextoFolha

    ctx = ContextoFolha(variaveis={"BASE_RPPS": Decimal("4000")}, rpps_config=None)
    assert avaliar("FAIXA_RPPS(BASE_RPPS)", ctx) == Decimal(0)
