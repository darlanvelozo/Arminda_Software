"""
Testes das funções builtin da DSL (Bloco 2.1).

Cada função em `apps.calculo.formula.funcoes.BUILTINS_STATIC` deve ter
pelo menos 1 caso de sucesso + 1 caso de erro de tipo aqui. Sem isso, a
função não pode ser adicionada à whitelist (CONTEXT.md).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.calculo.formula.errors import (
    FormulaRubricaInexistenteError,
    FormulaTipoInvalidoError,
)
from apps.calculo.formula.funcoes import (
    fn_abs,
    fn_arred,
    fn_faixa_inss,
    fn_faixa_irrf,
    fn_max,
    fn_min,
    fn_se,
    make_fn_rubrica,
)


class TestFnSe:
    def test_condicao_verdadeira(self):
        assert fn_se(True, "sim", "nao") == "sim"

    def test_condicao_falsa(self):
        assert fn_se(False, "sim", "nao") == "nao"

    def test_decimal_zero_e_falsy(self):
        assert fn_se(Decimal("0"), "sim", "nao") == "nao"

    def test_decimal_diferente_de_zero_e_truthy(self):
        assert fn_se(Decimal("0.01"), "sim", "nao") == "sim"


class TestFnMax:
    def test_dois_decimais(self):
        assert fn_max(Decimal("10"), Decimal("20")) == Decimal("20")

    def test_misturando_int_e_decimal(self):
        assert fn_max(5, Decimal("3.5")) == Decimal("5")

    def test_negativos(self):
        assert fn_max(Decimal("-10"), Decimal("-5")) == Decimal("-5")

    def test_varios_argumentos(self):
        assert fn_max(1, 5, 3, 2) == Decimal("5")

    def test_string_nao_numerica_falha(self):
        with pytest.raises(FormulaTipoInvalidoError):
            fn_max("abc", 1)

    def test_zero_argumentos_falha(self):
        with pytest.raises(FormulaTipoInvalidoError, match="pelo menos 1"):
            fn_max()


class TestFnMin:
    def test_dois_decimais(self):
        assert fn_min(Decimal("10"), Decimal("20")) == Decimal("10")

    def test_string_nao_numerica_falha(self):
        with pytest.raises(FormulaTipoInvalidoError):
            fn_min("xyz", 5)


class TestFnAbs:
    def test_negativo_vira_positivo(self):
        assert fn_abs(Decimal("-42.5")) == Decimal("42.5")

    def test_positivo_inalterado(self):
        assert fn_abs(Decimal("10")) == Decimal("10")

    def test_zero(self):
        assert fn_abs(Decimal("0")) == Decimal("0")


class TestFnArred:
    def test_arredonda_para_cima(self):
        assert fn_arred(Decimal("10.555"), 2) == Decimal("10.56")

    def test_meio_arredonda_para_cima_half_up(self):
        # ROUND_HALF_UP: .5 sempre vai pra cima (não banker's rounding)
        assert fn_arred(Decimal("10.5"), 0) == Decimal("11")
        assert fn_arred(Decimal("11.5"), 0) == Decimal("12")

    def test_casa_padrao_eh_dois(self):
        assert fn_arred(Decimal("10.999")) == Decimal("11.00")

    def test_casas_negativas_falha(self):
        with pytest.raises(FormulaTipoInvalidoError, match="negativas"):
            fn_arred(Decimal("100"), -1)


class TestFnRubrica:
    def test_acessa_rubrica_existente(self):
        rubricas = {"SAL_BASE": Decimal("1320.00")}
        fn = make_fn_rubrica(rubricas)
        assert fn("SAL_BASE") == Decimal("1320.00")

    def test_rubrica_inexistente_levanta_erro(self):
        fn = make_fn_rubrica({})
        with pytest.raises(FormulaRubricaInexistenteError, match="SAL_BASE"):
            fn("SAL_BASE")

    def test_argumento_nao_string_falha(self):
        fn = make_fn_rubrica({})
        with pytest.raises(FormulaTipoInvalidoError, match="texto"):
            fn(123)


class TestPlaceholdersOnda23:
    """Funções FAIXA_* são placeholders até a Onda 2.3."""

    def test_faixa_irrf_levanta_not_implemented(self):
        with pytest.raises(NotImplementedError, match="2.3"):
            fn_faixa_irrf(Decimal("1000"), "2026")

    def test_faixa_inss_levanta_not_implemented(self):
        with pytest.raises(NotImplementedError, match="2.3"):
            fn_faixa_inss(Decimal("1000"), "2026")
