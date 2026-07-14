"""
Testes da Onda 2.3 — tabelas legais 2024/2025/2026 + funções FAIXA_INSS/FAIXA_IRRF.

Valores de referência conferidos contra:
- Calculadora INSS oficial: https://www8.receita.fazenda.gov.br/SimuladorIRPF/
- Cartilha INSS faixas progressivas (2025-2026)
- Lei 14.848/2024 (faixa IRRF de isenção R$ 2.428,80 a partir mai/2025)

Como cada valor foi obtido está documentado em cada caso de teste.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from apps.calculo.tabelas import (
    TabelaLegalAusenteError,
    deducao_dependente_irrf,
    inss,
    irrf,
    salario_minimo,
)

# ============================================================
# Salário mínimo
# ============================================================


@pytest.mark.django_db
class TestSalarioMinimo:
    def test_2024(self):
        assert salario_minimo(date(2024, 1, 1)) == Decimal("1412.00")

    def test_2024_meio_ano(self):
        assert salario_minimo(date(2024, 7, 15)) == Decimal("1412.00")

    def test_2025(self):
        assert salario_minimo(date(2025, 1, 1)) == Decimal("1518.00")

    def test_2026(self):
        assert salario_minimo(date(2026, 5, 1)) == Decimal("1518.00")

    def test_competencia_sem_tabela(self):
        with pytest.raises(TabelaLegalAusenteError) as exc:
            salario_minimo(date(2020, 1, 1))
        assert exc.value.code == "TABELA_LEGAL_AUSENTE"


# ============================================================
# Dedução por dependente IRRF
# ============================================================


@pytest.mark.django_db
class TestDeducaoDependenteIRRF:
    def test_2024_em_diante(self):
        # Mesmo valor para 2024, 2025 e 2026 (lei 14.663/2023)
        assert deducao_dependente_irrf(date(2024, 1, 1)) == Decimal("189.59")
        assert deducao_dependente_irrf(date(2025, 6, 1)) == Decimal("189.59")
        assert deducao_dependente_irrf(date(2026, 5, 1)) == Decimal("189.59")


# ============================================================
# INSS 2026 — alíquota efetiva por faixa
# ============================================================


@pytest.mark.django_db
class TestINSS:
    COMP = date(2026, 5, 1)

    def test_abaixo_minimo_zerado(self):
        # Caso defensivo — não deveria acontecer em folha real
        assert inss(Decimal(0), self.COMP) == Decimal("0.00")

    def test_um_salario_minimo(self):
        # 1518 × 7.5% = 113.85
        assert inss(Decimal("1518.00"), self.COMP) == Decimal("113.85")

    def test_2000_dentro_2a_faixa(self):
        # 1518 × 7.5% = 113.85
        # (2000 - 1518) × 9% = 43.38
        # Total = 157.23
        assert inss(Decimal("2000.00"), self.COMP) == Decimal("157.23")

    def test_4000_dentro_3a_faixa(self):
        # 1518 × 7.5%        = 113.85
        # (2793.88-1518)×9%  = 114.8292
        # (4000-2793.88)×12% = 144.7344
        # Total = 373.41 (arred a 2 casas)
        assert inss(Decimal("4000.00"), self.COMP) == Decimal("373.41")

    def test_8000_proximo_teto(self):
        # 1518×7.5%               = 113.85
        # (2793.88-1518)×9%       = 114.8292
        # (4190.83-2793.88)×12%   = 167.634
        # (8000-4190.83)×14%      = 533.2838
        # Total = 929.60
        assert inss(Decimal("8000.00"), self.COMP) == Decimal("929.60")

    def test_acima_teto(self):
        # Base aplicada limitada ao teto (8157.41).
        # Salário R$ 12.000 paga o mesmo INSS de quem ganha R$ 8.157,41.
        teto_inss = inss(Decimal("8157.41"), self.COMP)
        assert inss(Decimal("12000.00"), self.COMP) == teto_inss

    def test_truncamento_por_faixa(self):
        # Convenção do Fiorilli SIP (Onda 2.7 / ADR-0025): trunca a parcela
        # de cada faixa antes de somar. Difere do padrão por centavos.
        #   1518×7,5%             = 113,85    → 113,85
        #   (2793,88-1518)×9%     = 114,8292  → 114,82 (trunca)
        #   (4190,83-2793,88)×12% = 167,634   → 167,63 (trunca)
        #   (8000-4190,83)×14%    = 533,2838  → 533,28 (trunca)
        #   Total truncado = 929,58  (vs 929,60 no arred. total)
        assert inss(Decimal("8000.00"), self.COMP) == Decimal("929.60")
        assert inss(Decimal("8000.00"), self.COMP, arredondamento="truncar") == Decimal(
            "929.58"
        )

    def test_truncamento_nao_afeta_faixa_exata(self):
        # Quando as parcelas já são exatas em centavos, os dois métodos batem.
        assert inss(Decimal("1518.00"), self.COMP, arredondamento="truncar") == inss(
            Decimal("1518.00"), self.COMP
        )


# ============================================================
# IRRF 2026 — faixas progressivas + dedução por dependente
# ============================================================


@pytest.mark.django_db
class TestIRRF:
    COMP = date(2026, 5, 1)

    def test_dentro_isencao(self):
        # Faixa de isenção até R$ 2.428,80 (Lei 14.848/2024)
        assert irrf(Decimal("2000.00"), 0, self.COMP) == Decimal("0.00")
        assert irrf(Decimal("2428.80"), 0, self.COMP) == Decimal("0.00")

    def test_base_zero(self):
        assert irrf(Decimal("0"), 0, self.COMP) == Decimal("0.00")

    def test_2700_segunda_faixa(self):
        # 2a faixa: até 2826.65 a 7.5% com dedução 182.16
        # 2700 × 7.5% − 182.16 = 202.50 − 182.16 = 20.34
        assert irrf(Decimal("2700.00"), 0, self.COMP) == Decimal("20.34")

    def test_3000_terceira_faixa(self):
        # 3000 > 2826.65 → 3a faixa: 15% com dedução 394.16
        # 3000 × 15% − 394.16 = 450 − 394.16 = 55.84
        assert irrf(Decimal("3000.00"), 0, self.COMP) == Decimal("55.84")

    def test_3500_terceira_faixa(self):
        # 3500 × 15% − 394.16 = 525 − 394.16 = 130.84
        assert irrf(Decimal("3500.00"), 0, self.COMP) == Decimal("130.84")

    def test_4000_quarta_faixa(self):
        # 4000 × 22.5% − 675.49 = 900 − 675.49 = 224.51
        assert irrf(Decimal("4000.00"), 0, self.COMP) == Decimal("224.51")

    def test_10000_quinta_faixa(self):
        # 10000 × 27.5% − 908.73 = 2750 − 908.73 = 1841.27
        assert irrf(Decimal("10000.00"), 0, self.COMP) == Decimal("1841.27")

    def test_3000_com_2_dependentes(self):
        # Base ajustada: 3000 − 2×189.59 = 2620.82
        # Encaixa na 2a faixa (até 2826.65)
        # 2620.82 × 7.5% − 182.16 = 196.5615 − 182.16 = 14.4015 → 14.40
        assert irrf(Decimal("3000.00"), 2, self.COMP) == Decimal("14.40")

    def test_dependentes_reduzem_a_zero(self):
        # 2500 − 3×189.59 = 1931.23 → na isenção → 0
        assert irrf(Decimal("2500.00"), 3, self.COMP) == Decimal("0.00")


# ============================================================
# Histórico — IRRF tem 2 vigências (até abr/2025 e depois mai/2025)
# ============================================================


@pytest.mark.django_db
class TestVigenciaCorreta:
    def test_irrf_antes_mai_2025_usa_tabela_antiga(self):
        # Vigência 2024-02-01 → 2025-04-30: isenção até R$ 2.259,20
        # 2300 × 7.5% − 169.44 = 172.5 − 169.44 = 3.06
        assert irrf(Decimal("2300.00"), 0, date(2025, 3, 1)) == Decimal("3.06")

    def test_irrf_depois_mai_2025_usa_tabela_nova(self):
        # Vigência 2025-05-01+: 2300 está na isenção (até 2428.80)
        assert irrf(Decimal("2300.00"), 0, date(2025, 6, 1)) == Decimal("0.00")

    def test_inss_2024_diferente_2026(self):
        # 2024 teto faixas: 1412/2666.68/4000.03/7786.02
        # 2000 em 2024: 1412×7.5% + (2000-1412)×9% = 105.9 + 52.92 = 158.82
        assert inss(Decimal("2000.00"), date(2024, 5, 1)) == Decimal("158.82")
        # 2026: como calculado acima = 157.23
        assert inss(Decimal("2000.00"), date(2026, 5, 1)) == Decimal("157.23")
