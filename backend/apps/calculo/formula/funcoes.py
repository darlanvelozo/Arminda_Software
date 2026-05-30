"""
Funções builtin disponíveis dentro de uma fórmula DSL (Bloco 2.1 + Onda 2.3).

Cada função recebe argumentos posicionais (não aceita kwargs) e retorna
um Decimal (exceto onde explicitamente diferente).

FAIXA_INSS e FAIXA_IRRF entraram na Onda 2.3 — leem `apps.core.TabelaLegal`
via `apps.calculo.tabelas`, resolvendo pela competência da folha.

Toda função nova exige:
1. Implementação aqui.
2. Adição em `BUILTINS` (dict abaixo).
3. Teste explícito em `apps/calculo/tests/test_funcoes.py`.

Adicionar função SEM teste explícito é violação do CONTEXT.md.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from apps.calculo.formula.errors import (
    FormulaRubricaInexistenteError,
    FormulaTipoInvalidoError,
)


def _to_decimal(v: Any, *, nome_arg: str = "argumento") -> Decimal:
    """Converte int/Decimal/str-numérico para Decimal. Falha amigável caso contrário."""
    if isinstance(v, Decimal):
        return v
    if isinstance(v, bool):
        # bool é subclasse de int — tratar explicitamente como erro p/ evitar ambiguidade
        return Decimal(int(v))
    if isinstance(v, int):
        return Decimal(v)
    if isinstance(v, str):
        try:
            return Decimal(v)
        except Exception as exc:
            raise FormulaTipoInvalidoError(
                f"'{nome_arg}' = {v!r} não pode ser convertido para número."
            ) from exc
    raise FormulaTipoInvalidoError(
        f"'{nome_arg}' = {v!r} tem tipo incompatível ({type(v).__name__})."
    )


def fn_se(condicao: Any, valor_se_verdadeiro: Any, valor_se_falso: Any) -> Any:
    """SE(cond, sim, nao) — condicional ternário."""
    return valor_se_verdadeiro if bool(condicao) else valor_se_falso


def fn_max(*args: Any) -> Decimal:
    """MAX(a, b, c, ...) — maior valor."""
    if not args:
        raise FormulaTipoInvalidoError("MAX() exige pelo menos 1 argumento.")
    decimais = [_to_decimal(a, nome_arg=f"MAX arg {i+1}") for i, a in enumerate(args)]
    return max(decimais)


def fn_min(*args: Any) -> Decimal:
    """MIN(a, b, c, ...) — menor valor."""
    if not args:
        raise FormulaTipoInvalidoError("MIN() exige pelo menos 1 argumento.")
    decimais = [_to_decimal(a, nome_arg=f"MIN arg {i+1}") for i, a in enumerate(args)]
    return min(decimais)


def fn_abs(v: Any) -> Decimal:
    """ABS(x) — valor absoluto."""
    return abs(_to_decimal(v, nome_arg="ABS"))


def fn_arred(valor: Any, casas: Any = 2) -> Decimal:
    """
    ARRED(valor, casas=2) — arredonda para N casas decimais usando
    half-up (regra contábil padrão: .5 sempre vai pra cima).
    """
    valor_d = _to_decimal(valor, nome_arg="ARRED valor")
    casas_int = int(_to_decimal(casas, nome_arg="ARRED casas"))
    if casas_int < 0:
        raise FormulaTipoInvalidoError(
            f"ARRED não aceita casas negativas ({casas_int})."
        )
    quantize = Decimal(10) ** -casas_int
    return valor_d.quantize(quantize, rounding=ROUND_HALF_UP)


def make_fn_rubrica(rubricas_calculadas: dict[str, Decimal]) -> Callable[[str], Decimal]:
    """
    Cria a função RUBRICA(codigo) bound ao dict de rubricas já calculadas
    nesta competência. Permite uma rubrica referenciar outra:

        formula  = "RUBRICA('SAL_BASE') * 0.10"
    """

    def fn_rubrica(codigo: Any) -> Decimal:
        if not isinstance(codigo, str):
            raise FormulaTipoInvalidoError(
                f"RUBRICA() exige um código de texto, recebeu {type(codigo).__name__}."
            )
        if codigo not in rubricas_calculadas:
            raise FormulaRubricaInexistenteError(
                f"Rubrica '{codigo}' não foi calculada ainda nesta competência. "
                f"Verifique a ordem de cálculo das rubricas."
            )
        return rubricas_calculadas[codigo]

    return fn_rubrica


# Funções de tabela legal — Onda 2.3.
# Vivem em `apps.calculo.tabelas` e leem `apps.core.TabelaLegal`.
# Recebem a competência via factory (igual RUBRICA recebe rubricas_calculadas).


def make_fn_faixa_inss(competencia: date) -> Callable[..., Decimal]:
    """Cria FAIXA_INSS(base) bound à competência da folha."""
    from apps.calculo import tabelas

    def fn_faixa_inss(base: Any) -> Decimal:
        base_d = _to_decimal(base, nome_arg="FAIXA_INSS base")
        return tabelas.inss(base_d, competencia)

    return fn_faixa_inss


def make_fn_faixa_irrf(competencia: date) -> Callable[..., Decimal]:
    """Cria FAIXA_IRRF(base, dependentes) bound à competência."""
    from apps.calculo import tabelas

    def fn_faixa_irrf(base: Any, dependentes: Any = 0) -> Decimal:
        base_d = _to_decimal(base, nome_arg="FAIXA_IRRF base")
        deps_int = int(_to_decimal(dependentes, nome_arg="FAIXA_IRRF dependentes"))
        return tabelas.irrf(base_d, deps_int, competencia)

    return fn_faixa_irrf


def make_fn_faixa_rpps(rpps_config: dict[str, Any] | None) -> Callable[..., Decimal]:
    """
    Cria FAIXA_RPPS(base) bound à config do regime próprio do município
    (Onda 2.4). A config flui como dado (ContextoFolha.rpps_config) para
    manter o engine puro — ver ADR-0013. `None` → contribuição 0.
    """
    from apps.calculo.previdencia import contribuicao_rpps

    def fn_faixa_rpps(base: Any) -> Decimal:
        base_d = _to_decimal(base, nome_arg="FAIXA_RPPS base")
        return contribuicao_rpps(base_d, rpps_config)

    return fn_faixa_rpps


# ============================================================
# Whitelist de builtins
# ============================================================
# A chave é o nome usado dentro da fórmula. O valor é o callable.
#
# Importante: RUBRICA é diferente porque depende do dict de rubricas
# calculadas da competência atual; o avaliador injeta a versão bound
# em runtime via `make_fn_rubrica`.

BUILTINS_STATIC: dict[str, Callable[..., Any]] = {
    "SE": fn_se,
    "MAX": fn_max,
    "MIN": fn_min,
    "ABS": fn_abs,
    "ARRED": fn_arred,
}

# Nomes reservados que são injetados dinamicamente (dependem do contexto
# da competência sendo calculada).
BUILTINS_DINAMICAS: frozenset[str] = frozenset(
    {"RUBRICA", "FAIXA_INSS", "FAIXA_IRRF", "FAIXA_RPPS"}
)

NOMES_PERMITIDOS: frozenset[str] = frozenset(BUILTINS_STATIC) | BUILTINS_DINAMICAS
