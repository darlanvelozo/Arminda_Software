"""
Erros de fórmula com códigos estáveis (Bloco 2.1 — ADR-0012).

Cada `FormulaError` carrega um `code` que é traduzido para HTTP 400
quando a fórmula é avaliada via endpoint. Os códigos são parte do
contrato externo e não mudam ao longo das versões.
"""

from __future__ import annotations


class FormulaError(Exception):
    """Erro durante compilação ou avaliação de uma fórmula DSL."""

    code: str = "FORMULA_ERRO"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code:
            self.code = code

    def __str__(self) -> str:
        return f"[{self.code}] {self.args[0] if self.args else 'Erro de fórmula'}"


class FormulaSintaxeError(FormulaError):
    """ast.parse falhou: fórmula com sintaxe inválida."""

    code = "FORMULA_SINTAXE"


class FormulaNaoPermitidaError(FormulaError):
    """AST contém nó/operador fora da whitelist (segurança)."""

    code = "FORMULA_NAO_PERMITIDA"


class FormulaFuncaoDesconhecidaError(FormulaError):
    """Chamada de função que não está na lista de builtins permitidos."""

    code = "FORMULA_FUNCAO_DESCONHECIDA"


class FormulaVariavelAusenteError(FormulaError):
    """Identificador referencia variável que não existe no contexto."""

    code = "FORMULA_VARIAVEL_AUSENTE"


class FormulaRubricaInexistenteError(FormulaError):
    """RUBRICA('X') chamada com X que não foi calculada nesta competência."""

    code = "FORMULA_RUBRICA_NAO_EXISTE"


class FormulaDivisaoPorZeroError(FormulaError):
    """Divisão por zero durante avaliação."""

    code = "FORMULA_DIV_POR_ZERO"


class FormulaTipoInvalidoError(FormulaError):
    """Operação entre tipos incompatíveis (ex.: soma de string + Decimal)."""

    code = "FORMULA_TIPO_INVALIDO"
