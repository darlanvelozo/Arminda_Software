"""
Testes do serviço de paridade Fiorilli (Onda 2.7).

Exercitam `comparar_competencia` com linhas de BASES sintéticas (sem PII,
sem Firebird) e valores conferidos à mão contra as tabelas legais 2025
(seed da migration 0004). Garantem que:
- o casamento à-vista (≤1¢) é contado como exato;
- a divergência real cai na faixa de magnitude correta;
- a semântica de IRRF é `tabela(base − dedução publicada)`;
- FGTS é 8% linear.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from apps.imports.services.paridade import comparar_competencia

COMP = date(2025, 7, 1)


def _base(registro: str, **kwargs) -> dict:
    """Linha de BASES com zeros por padrão (só os campos do teste importam)."""
    linha = {
        "registro": registro,
        "baseprevidenciames": "0",
        "valorprevidenciames": "0",
        "baseirrfmes": "0",
        "valorirrfmes": "0",
        "deduirrfmes": "0",
        "basefgtsmes": "0",
        "valorfgtsmes": "0",
    }
    linha.update(kwargs)
    return linha


@pytest.mark.django_db
class TestParidadeIRRF:
    def test_irrf_casa_a_vista(self):
        # base 3000, dedução 0 → faixa 15% (mai/2025): 3000×0,15 − 394,16 = 55,84
        bases = [_base("1", baseirrfmes="3000.00", deduirrfmes="0", valorirrfmes="55.84")]
        rel = comparar_competencia(competencia=COMP, bases=bases)
        t = rel.tributos["IRRF"]
        assert t.comparados == 1
        assert t.exatos == 1
        assert t.divergentes == 0

    def test_irrf_usa_deducao_publicada(self):
        # base 3189,59 − dedução 189,59 = 3000 → 55,84 (mesma faixa)
        bases = [
            _base("1", baseirrfmes="3189.59", deduirrfmes="189.59", valorirrfmes="55.84")
        ]
        rel = comparar_competencia(competencia=COMP, bases=bases)
        assert rel.tributos["IRRF"].exatos == 1

    def test_irrf_divergencia_cai_na_faixa(self):
        # nosso cálculo dá 55,84; SIP publicou 45,84 → divergência de R$10 (faixa R$1–10 é <=10)
        bases = [_base("1", baseirrfmes="3000.00", valorirrfmes="45.84")]
        rel = comparar_competencia(competencia=COMP, bases=bases)
        t = rel.tributos["IRRF"]
        assert t.exatos == 0
        assert t.divergentes == 1
        assert t.maior_divergencia == Decimal("10.00")

    def test_irrf_isento_nao_diverge(self):
        # base − dedução na faixa de isenção → 0,00, igual ao SIP
        bases = [_base("1", baseirrfmes="2000.00", valorirrfmes="0")]
        rel = comparar_competencia(competencia=COMP, bases=bases)
        assert rel.tributos["IRRF"].exatos == 1


@pytest.mark.django_db
class TestParidadePrevidencia:
    def test_previdencia_primeira_faixa(self):
        # base 1518 (1º piso 2025) → INSS 7,5% = 113,85
        bases = [_base("1", baseprevidenciames="1518.00", valorprevidenciames="113.85")]
        rel = comparar_competencia(competencia=COMP, bases=bases)
        assert rel.tributos["Previdência (trunc. por faixa)"].exatos == 1

    def test_aliquota_efetiva_registrada(self):
        bases = [_base("1", baseprevidenciames="1518.00", valorprevidenciames="113.85")]
        rel = comparar_competencia(competencia=COMP, bases=bases)
        # 113,85 / 1518 = 0,075 → registrada no histograma
        assert rel.rpps_aliquotas.get("0.0750") == 1

    def test_residuo_aposentado_imune(self):
        # Base > 0, valor = 0 → aposentado/imune; entra no resíduo RPPS.
        bases = [_base("1", baseprevidenciames="3000.00", valorprevidenciames="0")]
        rel = comparar_competencia(competencia=COMP, bases=bases)
        assert rel.residuo_rpps.get("aposentado/imune (base>0, valor=0)") == 1

    def test_residuo_rpps_teto(self):
        # Valor que não bate nem por truncamento e ≠ 0 → RPPS com regra própria.
        bases = [_base("1", baseprevidenciames="5000.00", valorprevidenciames="992.21")]
        rel = comparar_competencia(competencia=COMP, bases=bases)
        assert rel.residuo_rpps.get("RPPS c/ teto ou regra própria") == 1


@pytest.mark.django_db
class TestParidadeFGTS:
    def test_fgts_oito_por_cento(self):
        bases = [_base("1", basefgtsmes="1000.00", valorfgtsmes="80.00")]
        rel = comparar_competencia(competencia=COMP, bases=bases)
        assert rel.tributos["FGTS"].exatos == 1

    def test_fgts_divergente(self):
        bases = [_base("1", basefgtsmes="1000.00", valorfgtsmes="75.00")]
        rel = comparar_competencia(competencia=COMP, bases=bases)
        assert rel.tributos["FGTS"].divergentes == 1


@pytest.mark.django_db
def test_relatorio_agrega_multiplos_servidores():
    bases = [
        _base("1", baseirrfmes="3000.00", valorirrfmes="55.84"),  # exato
        _base("2", baseirrfmes="3000.00", valorirrfmes="45.84"),  # diverge
        _base("3", baseprevidenciames="1518.00", valorprevidenciames="113.85"),  # exato
    ]
    rel = comparar_competencia(competencia=COMP, bases=bases)
    assert rel.total_servidores == 3
    assert rel.tributos["IRRF"].comparados == 2
    assert rel.tributos["IRRF"].taxa_acerto == 50.0
    assert rel.tributos["Previdência (trunc. por faixa)"].exatos == 1
