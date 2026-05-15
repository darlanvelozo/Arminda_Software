"""
Testes do avaliador completo (Bloco 2.1).

Cobertura end-to-end: parse → transform → eval → resultado.
Inclui caminho feliz, erros de cada `code` e propriedades de Decimal.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.calculo.formula.avaliador import avaliar
from apps.calculo.formula.contexto import ContextoFolha
from apps.calculo.formula.errors import (
    FormulaDivisaoPorZeroError,
    FormulaFuncaoDesconhecidaError,
    FormulaRubricaInexistenteError,
    FormulaTipoInvalidoError,
    FormulaVariavelAusenteError,
)
from apps.calculo.formula.parser import limpar_cache


@pytest.fixture(autouse=True)
def _limpar_cache():
    limpar_cache()
    yield
    limpar_cache()


@pytest.fixture
def ctx_padrao():
    return ContextoFolha(
        variaveis={
            "SALARIO_BASE": Decimal("1320.00"),
            "IDADE": Decimal("35"),
            "DEPENDENTES": Decimal("2"),
            "CARGA_HORARIA": Decimal("40"),
        }
    )


class TestAritmeticaBasica:
    def test_soma(self, ctx_padrao):
        assert avaliar("1 + 2", ctx_padrao) == Decimal("3")

    def test_subtracao(self, ctx_padrao):
        assert avaliar("10 - 3", ctx_padrao) == Decimal("7")

    def test_multiplicacao(self, ctx_padrao):
        assert avaliar("SALARIO_BASE * 0.10", ctx_padrao) == Decimal("132.000")

    def test_divisao(self, ctx_padrao):
        assert avaliar("SALARIO_BASE / 2", ctx_padrao) == Decimal("660.00")

    def test_modulo(self, ctx_padrao):
        assert avaliar("10 % 3", ctx_padrao) == Decimal("1")

    def test_decimal_preserva_precisao(self, ctx_padrao):
        # 0.1 + 0.2 em float == 0.30000000000000004; em Decimal == 0.3
        resultado = avaliar("0.1 + 0.2", ctx_padrao)
        assert resultado == Decimal("0.3")

    def test_unario_negativo(self, ctx_padrao):
        assert avaliar("-SALARIO_BASE", ctx_padrao) == Decimal("-1320.00")


class TestComparacoes:
    """Comparações retornam Decimal(1)/Decimal(0) — engine sempre devolve Decimal."""

    def test_maior_que(self, ctx_padrao):
        assert avaliar("IDADE > 30", ctx_padrao) == Decimal("1")
        assert avaliar("IDADE > 40", ctx_padrao) == Decimal("0")

    def test_igualdade(self, ctx_padrao):
        assert avaliar("IDADE == 35", ctx_padrao) == Decimal("1")

    def test_comparacao_em_cadeia(self, ctx_padrao):
        # Python permite `18 < IDADE < 65`
        assert avaliar("18 < IDADE < 65", ctx_padrao) == Decimal("1")


class TestLogicos:
    """Lógicos com Decimal retornam o último operando avaliado (semântica Python)."""

    def test_and_ambos_verdadeiros_retorna_segundo(self, ctx_padrao):
        # IDADE > 18 → True; IDADE < 65 → True. Python `and` retorna o último.
        # No nosso engine, comparação retorna Decimal(1), então and de dois 1s = 1.
        assert avaliar("IDADE > 18 and IDADE < 65", ctx_padrao) == Decimal("1")

    def test_or_segundo_verdadeiro(self, ctx_padrao):
        assert avaliar("IDADE > 100 or DEPENDENTES > 0", ctx_padrao) == Decimal("1")

    def test_not(self, ctx_padrao):
        assert avaliar("not (IDADE > 100)", ctx_padrao) == Decimal("1")


class TestCondicionais:
    def test_se_verdadeiro(self, ctx_padrao):
        assert avaliar("SE(IDADE > 18, 100, 200)", ctx_padrao) == Decimal("100")

    def test_se_falso(self, ctx_padrao):
        assert avaliar("SE(IDADE > 100, 100, 200)", ctx_padrao) == Decimal("200")

    def test_se_com_calculo_no_corpo(self, ctx_padrao):
        formula = "SE(DEPENDENTES > 0, SALARIO_BASE * 0.10, 0)"
        assert avaliar(formula, ctx_padrao) == Decimal("132.000")

    def test_se_aninhado(self, ctx_padrao):
        formula = "SE(IDADE < 18, 1, SE(IDADE < 65, 2, 3))"
        assert avaliar(formula, ctx_padrao) == Decimal("2")


class TestRubricaCalculada:
    def test_acessa_rubrica(self):
        ctx = ContextoFolha(
            variaveis={},
            rubricas_calculadas={"SAL_BASE": Decimal("1320.00")},
        )
        assert avaliar("RUBRICA('SAL_BASE') * 0.10", ctx) == Decimal("132.000")

    def test_rubrica_inexistente_levanta_erro(self):
        ctx = ContextoFolha(variaveis={}, rubricas_calculadas={})
        with pytest.raises(FormulaRubricaInexistenteError):
            avaliar("RUBRICA('X')", ctx)


class TestErrosDeContexto:
    def test_variavel_inexistente(self, ctx_padrao):
        with pytest.raises(FormulaVariavelAusenteError, match="NAO_EXISTE"):
            avaliar("NAO_EXISTE + 1", ctx_padrao)

    def test_funcao_desconhecida_em_maiusculas(self, ctx_padrao):
        with pytest.raises(FormulaFuncaoDesconhecidaError, match="MINHA_FUNCAO"):
            avaliar("MINHA_FUNCAO(1, 2)", ctx_padrao)


class TestErrosDeRuntime:
    def test_divisao_por_zero(self, ctx_padrao):
        with pytest.raises(FormulaDivisaoPorZeroError):
            avaliar("SALARIO_BASE / 0", ctx_padrao)

    def test_tipo_invalido(self, ctx_padrao):
        # MAX com string não convertível
        with pytest.raises(FormulaTipoInvalidoError):
            avaliar("MAX('abc', 1)", ctx_padrao)


class TestCalculosRealistas:
    """Casos baseados em rubricas reais que vão precisar funcionar no Bloco 2.2."""

    def test_proporcionalidade_por_horas(self, ctx_padrao):
        ctx_padrao.variaveis["HORAS_TRABALHADAS"] = Decimal("160")
        ctx_padrao.variaveis["HORAS_PADRAO"] = Decimal("220")
        resultado = avaliar(
            "SALARIO_BASE * (HORAS_TRABALHADAS / HORAS_PADRAO)", ctx_padrao
        )
        # 1320 * 160/220 = 960
        assert resultado == Decimal("960.000000000000000000000000000000")
        # Arredondamento via ARRED
        resultado_arred = avaliar(
            "ARRED(SALARIO_BASE * (HORAS_TRABALHADAS / HORAS_PADRAO), 2)",
            ctx_padrao,
        )
        assert resultado_arred == Decimal("960.00")

    def test_piso_salarial(self, ctx_padrao):
        ctx_padrao.variaveis["SALARIO_MINIMO"] = Decimal("1518")
        ctx_padrao.variaveis["SALARIO_BASE"] = Decimal("1200")  # abaixo do mínimo
        resultado = avaliar(
            "MAX(SALARIO_BASE, SALARIO_MINIMO)", ctx_padrao
        )
        assert resultado == Decimal("1518")

    def test_irrf_simplificado_com_dependentes(self, ctx_padrao):
        # Simulação simplificada: 10% sobre salário menos R$ 189,59 por dependente
        formula = "ARRED(SE(DEPENDENTES > 0, SALARIO_BASE * 0.10 - DEPENDENTES * 189.59, SALARIO_BASE * 0.10), 2)"
        resultado = avaliar(formula, ctx_padrao)
        # 1320 * 0.10 - 2 * 189.59 = 132 - 379.18 = -247.18
        assert resultado == Decimal("-247.18")
