"""
Avaliador de fórmulas DSL (Bloco 2.1 — ADR-0012).

Orquestra compile + monta namespace (variáveis do contexto +
builtins) + executa via `eval`. Tudo Decimal. Erros viram
`FormulaError` com `code` estável.
"""

from __future__ import annotations

import re
from decimal import Decimal, DivisionByZero, InvalidOperation
from typing import Any

from apps.calculo.formula.contexto import ContextoFolha
from apps.calculo.formula.errors import (
    FormulaDivisaoPorZeroError,
    FormulaError,
    FormulaFuncaoDesconhecidaError,
    FormulaTipoInvalidoError,
    FormulaVariavelAusenteError,
)
from apps.calculo.formula.funcoes import (
    BUILTINS_DINAMICAS,
    BUILTINS_STATIC,
    NOMES_PERMITIDOS,
    make_fn_rubrica,
)
from apps.calculo.formula.parser import compilar


def _construir_namespace(ctx: ContextoFolha) -> dict[str, Any]:
    """
    Monta o namespace que será passado para `eval()`.

    Inclui:
    - `_D = Decimal` — função interna que converte literais do parser
      (todo `Constant` numérico vira `_D("0.10")` durante o transform).
    - Builtins estáticos (SE, MAX, MIN, ABS, ARRED, FAIXA_*).
    - `RUBRICA` injetado dinamicamente com o dict da competência atual.
    - Variáveis do contexto (SALARIO_BASE, IDADE, etc.).
    """
    namespace: dict[str, Any] = {"_D": Decimal}
    namespace.update(BUILTINS_STATIC)
    namespace["RUBRICA"] = make_fn_rubrica(ctx.rubricas_calculadas)
    namespace.update(ctx.como_namespace())
    return namespace


class _BuiltinsNoGlobals(dict):
    """
    Dict que dá NameError ao acessar nomes não permitidos — usado como
    `globals` do `eval` para garantir que nada de fora do namespace
    seja resolvido (em particular, evita acesso aos builtins do Python).
    """

    def __getitem__(self, key: str) -> Any:  # pragma: no cover (defensivo)
        if key == "__builtins__":
            # Python passa isso implicitamente; devolve dict vazio pra não vazar nada
            return {}
        raise KeyError(key)


def avaliar(formula: str, contexto: ContextoFolha) -> Decimal:
    """
    Avalia uma fórmula DSL com o contexto fornecido.

    Args:
        formula: expressão DSL como string. Ex.: "SALARIO_BASE * 0.10".
        contexto: ContextoFolha com variáveis e rubricas já calculadas.

    Returns:
        Decimal com o resultado.

    Raises:
        FormulaSintaxeError: sintaxe inválida.
        FormulaNaoPermitidaError: AST contém nó proibido.
        FormulaFuncaoDesconhecidaError: chamada para função fora da whitelist.
        FormulaVariavelAusenteError: variável não existe no contexto.
        FormulaRubricaInexistenteError: RUBRICA("X") com X inexistente.
        FormulaDivisaoPorZeroError: divisão por zero.
        FormulaTipoInvalidoError: tipos incompatíveis em operação.
    """
    code = compilar(formula)
    namespace = _construir_namespace(contexto)

    # Pré-validação: nomes de função invocados (ast.walk não dá pra fazer
    # em runtime sem re-parse — vamos confiar no NameError e re-mapear).
    try:
        resultado = eval(  # noqa: S307 — eval intencional, com namespace controlado
            code,
            _BuiltinsNoGlobals(),
            namespace,
        )
    except NameError as exc:
        # NameError pode vir de variável ausente OU função não permitida.
        # Distingue olhando o source: se aparecer "NOME(" na fórmula, é função.
        nome = str(exc).split("'")[1] if "'" in str(exc) else "desconhecido"
        if nome in NOMES_PERMITIDOS:
            raise FormulaError(f"Erro interno ao resolver '{nome}'.") from exc
        if re.search(rf"\b{re.escape(nome)}\s*\(", formula):
            raise FormulaFuncaoDesconhecidaError(
                f"Função '{nome}' não é permitida em fórmulas. "
                f"Funções disponíveis: {', '.join(sorted(NOMES_PERMITIDOS))}."
            ) from exc
        raise FormulaVariavelAusenteError(
            f"Variável '{nome}' não está disponível no contexto da fórmula."
        ) from exc
    except (DivisionByZero, ZeroDivisionError) as exc:
        raise FormulaDivisaoPorZeroError("Divisão por zero na fórmula.") from exc
    except InvalidOperation as exc:
        raise FormulaTipoInvalidoError(
            f"Operação Decimal inválida: {exc}"
        ) from exc
    except TypeError as exc:
        raise FormulaTipoInvalidoError(
            f"Tipo incompatível em operação: {exc}"
        ) from exc
    except FormulaError:
        # Erros já tipados (vindos de funcoes.py) sobem direto
        raise

    # Garante saída sempre Decimal
    if isinstance(resultado, bool):
        return Decimal(int(resultado))
    if isinstance(resultado, int):
        return Decimal(resultado)
    if isinstance(resultado, Decimal):
        return resultado
    if isinstance(resultado, float):
        # Não devia acontecer (constantes viram Decimal no parser), mas defensivo
        return Decimal(str(resultado))
    raise FormulaTipoInvalidoError(
        f"Fórmula retornou tipo inesperado: {type(resultado).__name__}"
    )
