"""
Parser e validador da DSL de fórmulas (Bloco 2.1 — ADR-0012).

Compila uma string de fórmula em bytecode Python via `ast.parse` em
modo `eval`, mas só depois de **validar** que o AST contém apenas
nós da whitelist. Constantes numéricas viram `Decimal` em
pré-processamento para evitar surpresas de float.

Compilação é cacheada via `functools.lru_cache` — fórmula nova compila
uma vez; subsequentes apenas executam.
"""

from __future__ import annotations

import ast
from functools import lru_cache
from typing import Any

from apps.calculo.formula.errors import (
    FormulaNaoPermitidaError,
    FormulaSintaxeError,
)

# ============================================================
# Whitelist de nós AST permitidos
# ============================================================
#
# Toda outra construção de Python é bloqueada — em particular:
#   Attribute (a.b)         — bloqueia introspecção/escape
#   Subscript (a[b])        — bloqueia acesso a dict/list externos
#   Lambda, FunctionDef     — bloqueia definição de funções
#   Import, ImportFrom      — bloqueia import
#   For, While, Try, With   — bloqueia controle de fluxo
#   ListComp, SetComp, ...  — bloqueia compreensões
#   Pow (**)                — bloqueia ataques DoS (10**10**10)
#   FloorDiv (//), MatMult  — fora do escopo da DSL
ALLOWED_NODES: set[type[ast.AST]] = {
    ast.Expression,
    ast.Constant,
    ast.Name,
    ast.Load,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.BoolOp,
    ast.IfExp,
    ast.Call,
    # Operadores binários
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    # Operadores unários
    ast.USub,
    ast.UAdd,
    ast.Not,
    # Comparações
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    # Booleanos
    ast.And,
    ast.Or,
}


def _validar_no(node: ast.AST) -> None:
    """Percorre a árvore e levanta erro no primeiro nó proibido."""
    for child in ast.walk(node):
        if type(child) not in ALLOWED_NODES:
            raise FormulaNaoPermitidaError(
                f"Construção '{type(child).__name__}' não é permitida em fórmulas. "
                f"Use apenas operações aritméticas, comparações, funções builtin e variáveis do contexto."
            )
        # Bloqueia chamadas com keyword arguments (assinatura simples)
        if isinstance(child, ast.Call) and child.keywords:
            raise FormulaNaoPermitidaError(
                "Funções em fórmulas não aceitam argumentos nomeados. Use só posicionais."
            )
        # Bloqueia chamada onde o callable não é um Name simples
        if isinstance(child, ast.Call) and not isinstance(child.func, ast.Name):
            raise FormulaNaoPermitidaError(
                "Apenas funções builtin podem ser chamadas (ex.: SE(...), MAX(...))."
            )


class _NumericToDecimalTransformer(ast.NodeTransformer):
    """
    Substitui Constant(numeric) por Call(_D, ["valor"]) em runtime.

    Motivo: `compile()` do Python rejeita Decimal em Constant — bytecode
    só aceita tipos built-in. A solução é converter cada literal
    numérico em chamada a `_D(string)`, onde `_D` é injetado no namespace
    do avaliador apontando para `Decimal`.

    Importante: usamos `repr(float)` para preservar a representação
    digitada pelo usuário (0.1 → "0.1", não a expansão binária).
    """

    def visit_Constant(self, node: ast.Constant) -> ast.AST:  # noqa: N802
        if isinstance(node.value, bool):
            # bool é subclasse de int — preservar como Constant nativo
            return node
        if isinstance(node.value, int):
            literal = str(node.value)
        elif isinstance(node.value, float):
            literal = repr(node.value)
        else:
            # Strings, None passam direto — usados como argumentos (ex.: RUBRICA("X"))
            return node

        new_node = ast.Call(
            func=ast.Name(id="_D", ctx=ast.Load()),
            args=[ast.Constant(value=literal)],
            keywords=[],
        )
        return ast.copy_location(new_node, node)


@lru_cache(maxsize=1024)
def compilar(formula: str) -> Any:  # retorna code object
    """
    Compila uma fórmula string em bytecode Python validado.

    Args:
        formula: expressão DSL como string (ex.: "SALARIO_BASE * 0.10").

    Returns:
        Code object pronto para `eval()`.

    Raises:
        FormulaSintaxeError: se `ast.parse` falhar.
        FormulaNaoPermitidaError: se a AST contiver nó proibido.
    """
    if not formula or not formula.strip():
        raise FormulaSintaxeError("Fórmula vazia.")

    try:
        tree = ast.parse(formula, mode="eval")
    except SyntaxError as exc:
        raise FormulaSintaxeError(
            f"Sintaxe inválida na fórmula: {exc.msg}"
        ) from exc

    _validar_no(tree)

    # Transforma constantes numéricas em Decimal antes de compilar
    tree = _NumericToDecimalTransformer().visit(tree)
    ast.fix_missing_locations(tree)

    return compile(tree, filename="<formula>", mode="eval")


def limpar_cache() -> None:
    """Limpa o cache LRU — útil em testes ou após atualização em produção."""
    compilar.cache_clear()
