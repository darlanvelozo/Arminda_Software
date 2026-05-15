"""
Testes do parser de fórmulas DSL (Bloco 2.1).

Todos os testes são puros (sem DB). Cobre:
- Compilação de fórmulas válidas
- Rejeição de sintaxe inválida
- Rejeição de nós AST proibidos (segurança)
- Comportamento de cache
"""

from __future__ import annotations

import pytest

from apps.calculo.formula.errors import (
    FormulaNaoPermitidaError,
    FormulaSintaxeError,
)
from apps.calculo.formula.parser import compilar, limpar_cache


class TestCompilacaoValida:
    def setup_method(self):
        limpar_cache()

    def test_expressao_aritmetica_simples(self):
        code = compilar("1 + 2 * 3")
        assert code is not None

    def test_expressao_com_variaveis(self):
        code = compilar("SALARIO_BASE * 0.10")
        assert code is not None

    def test_chamada_de_funcao_builtin(self):
        code = compilar("MAX(1, 2, 3)")
        assert code is not None

    def test_condicional_if(self):
        code = compilar("SE(IDADE > 18, 1, 0)")
        assert code is not None

    def test_python_ternario_funciona_tambem(self):
        # `x if cond else y` deve passar — usamos `IfExp` interno
        code = compilar("1 if True else 0")
        assert code is not None


class TestSintaxeInvalida:
    def setup_method(self):
        limpar_cache()

    def test_formula_vazia(self):
        with pytest.raises(FormulaSintaxeError, match="vazia"):
            compilar("")

    def test_formula_so_espacos(self):
        with pytest.raises(FormulaSintaxeError):
            compilar("   ")

    def test_parenteses_desbalanceados(self):
        with pytest.raises(FormulaSintaxeError):
            compilar("(1 + 2")

    def test_operador_solto(self):
        with pytest.raises(FormulaSintaxeError):
            compilar("* 5")


class TestSeguranca:
    """Garante que construções perigosas do Python sejam rejeitadas."""

    def setup_method(self):
        limpar_cache()

    def test_attribute_access_bloqueado(self):
        # a.b → AttributeError de runtime seria possível; bloquear na AST
        with pytest.raises(FormulaNaoPermitidaError, match="Attribute"):
            compilar("SALARIO.real")

    def test_subscript_bloqueado(self):
        with pytest.raises(FormulaNaoPermitidaError, match="Subscript"):
            compilar("SALARIO[0]")

    def test_lambda_bloqueado(self):
        # Lambda é rejeitado — pode ser pelo nó Lambda ou pelo Call não-Name; basta levantar
        with pytest.raises(FormulaNaoPermitidaError):
            compilar("(lambda: 1)()")

    def test_list_comp_bloqueado(self):
        with pytest.raises(FormulaNaoPermitidaError, match="ListComp"):
            compilar("[x for x in [1,2,3]]")

    def test_pow_operator_bloqueado(self):
        # ** poderia ser DoS via 10**10**10
        with pytest.raises(FormulaNaoPermitidaError, match="Pow"):
            compilar("2 ** 10")

    def test_floor_div_bloqueado(self):
        with pytest.raises(FormulaNaoPermitidaError, match="FloorDiv"):
            compilar("5 // 2")

    def test_kwargs_em_funcao_bloqueado(self):
        with pytest.raises(FormulaNaoPermitidaError, match="nomeados"):
            compilar("MAX(a=1, b=2)")

    def test_call_em_expressao_bloqueado(self):
        # `(SALARIO + 1)(2)` — chamada onde callable não é Name simples
        with pytest.raises(FormulaNaoPermitidaError):
            compilar("(SALARIO + 1)(2)")


class TestCache:
    def setup_method(self):
        limpar_cache()

    def test_mesma_formula_retorna_mesmo_code(self):
        c1 = compilar("SALARIO * 2")
        c2 = compilar("SALARIO * 2")
        assert c1 is c2  # mesmo objeto, do cache

    def test_formulas_diferentes_codes_diferentes(self):
        c1 = compilar("SALARIO * 2")
        c2 = compilar("SALARIO * 3")
        assert c1 is not c2

    def test_limpar_cache_funciona(self):
        c1 = compilar("SALARIO * 2")
        limpar_cache()
        c2 = compilar("SALARIO * 2")
        assert c1 is not c2  # objetos diferentes após limpar
