"""
Resolução de tabelas legais por competência (Onda 2.3).

As tabelas vivem em `apps.core.models.TabelaLegal` (schema public, SHARED
entre tenants — INSS/IRRF/salário mínimo são federais).

A função `tabela_vigente()` busca a versão correta para uma competência
e fica cacheada por `lru_cache` enquanto o processo viver. O cache é
invalidado por `_invalidar_cache()` (chamado por sinais do TabelaLegal).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_DOWN, Decimal
from functools import lru_cache
from typing import Any

from apps.calculo.formula.errors import FormulaError


class TabelaLegalAusenteError(FormulaError):
    """Não existe tabela vigente para a competência consultada."""

    code = "TABELA_LEGAL_AUSENTE"


class TabelaLegalInvalidaError(FormulaError):
    """Estrutura do JSON da tabela está inconsistente com o tipo declarado."""

    code = "TABELA_LEGAL_INVALIDA"


@dataclass(frozen=True)
class FaixaProgressiva:
    """Uma faixa de tabela progressiva (INSS ou IRRF)."""

    ate: Decimal | None  # None = faixa aberta (sem teto)
    aliquota: Decimal
    deducao: Decimal = Decimal(0)  # só IRRF usa


def _resolver_competencia(competencia: date | str) -> date:
    """Aceita date ou string YYYY-MM-DD."""
    if isinstance(competencia, date):
        return competencia
    return date.fromisoformat(str(competencia))


@lru_cache(maxsize=256)
def _buscar_tabela(tipo: str, competencia_iso: str) -> dict[str, Any]:
    """
    Busca cacheada (chave: tipo + ISO date). Devolve só o dict `valores`.

    Cache invalidado por `_invalidar_cache()` quando alguma TabelaLegal é
    salva/deletada — ver `apps.core.signals` (registrado em apps.py).
    """
    from apps.core.models import TabelaLegal  # import tardio para evitar ciclo

    competencia = date.fromisoformat(competencia_iso)
    qs = (
        TabelaLegal.objects.filter(tipo=tipo, vigencia_inicio__lte=competencia)
        .filter(
            # vigencia_fim IS NULL OR vigencia_fim >= competencia
            models_Q(vigencia_fim__isnull=True) | models_Q(vigencia_fim__gte=competencia)
        )
        .order_by("-vigencia_inicio")
    )
    obj = qs.first()
    if obj is None:
        raise TabelaLegalAusenteError(
            f"Não existe tabela '{tipo}' vigente em {competencia_iso}. "
            "Cadastre via admin (/admin/core/tabelalegal/) antes de calcular."
        )
    return dict(obj.valores)


# Q vem como import lazy pra não importar Django no topo
def models_Q(*args, **kwargs):
    from django.db.models import Q

    return Q(*args, **kwargs)


def _invalidar_cache() -> None:
    """Chamado por signal pós-save/delete de TabelaLegal."""
    _buscar_tabela.cache_clear()


# ============================================================
# Acessores públicos
# ============================================================


def salario_minimo(competencia: date | str) -> Decimal:
    """Salário mínimo nacional vigente na competência."""
    comp = _resolver_competencia(competencia)
    valores = _buscar_tabela("salario_minimo", comp.isoformat())
    try:
        return Decimal(str(valores["valor"]))
    except (KeyError, TypeError) as exc:
        raise TabelaLegalInvalidaError(
            f"Tabela salario_minimo em {comp} sem chave 'valor'."
        ) from exc


def deducao_dependente_irrf(competencia: date | str) -> Decimal:
    """Dedução mensal por dependente para IRRF (federal)."""
    comp = _resolver_competencia(competencia)
    valores = _buscar_tabela("deducao_dependente_irrf", comp.isoformat())
    try:
        return Decimal(str(valores["valor"]))
    except (KeyError, TypeError) as exc:
        raise TabelaLegalInvalidaError(
            f"Tabela deducao_dependente_irrf em {comp} sem chave 'valor'."
        ) from exc


def _parse_faixas(
    raw_faixas: list[dict[str, Any]], *, tem_deducao: bool, tipo: str, competencia: date
) -> list[FaixaProgressiva]:
    if not isinstance(raw_faixas, list) or not raw_faixas:
        raise TabelaLegalInvalidaError(
            f"Tabela {tipo} em {competencia} sem lista 'faixas'."
        )
    faixas: list[FaixaProgressiva] = []
    for i, f in enumerate(raw_faixas):
        try:
            ate_raw = f.get("ate")
            ate = Decimal(str(ate_raw)) if ate_raw is not None else None
            aliquota = Decimal(str(f["aliquota"]))
            deducao = Decimal(str(f.get("deducao", "0"))) if tem_deducao else Decimal(0)
        except (KeyError, TypeError, ValueError) as exc:
            raise TabelaLegalInvalidaError(
                f"Tabela {tipo} em {competencia}, faixa #{i + 1}: estrutura inválida."
            ) from exc
        faixas.append(FaixaProgressiva(ate=ate, aliquota=aliquota, deducao=deducao))
    # Garante que a última faixa é aberta (sem teto) — convenção
    if faixas[-1].ate is not None:
        raise TabelaLegalInvalidaError(
            f"Tabela {tipo} em {competencia}: última faixa precisa ter 'ate': null."
        )
    return faixas


def inss(
    base: Decimal, competencia: date | str, *, arredondamento: str = "round"
) -> Decimal:
    """
    Calcula contribuição INSS progressiva sobre `base` na competência.

    Aplica alíquota efetiva em cada faixa (regra brasileira: a alíquota
    de uma faixa só incide sobre a parte da base que cai naquela faixa,
    NÃO sobre toda a base). Respeita o teto previdenciário.

    `arredondamento` controla a convenção de centavos:
    - `"round"` (padrão): soma exata das faixas e arredonda o total ao fim
      (meio-a-cima). É o método alinhado à calculadora oficial.
    - `"truncar"`: trunca a parcela de CADA faixa para centavos antes de
      somar. É a convenção do Fiorilli SIP (e de vários sistemas legados);
      difere do padrão por 1–2 centavos em algumas bases. Ver ADR-0025 e a
      paridade da Onda 2.7.
    """
    comp = _resolver_competencia(competencia)
    base_d = Decimal(str(base))
    if base_d <= 0:
        return Decimal(0)

    valores = _buscar_tabela("inss", comp.isoformat())
    faixas = _parse_faixas(
        list(valores.get("faixas", [])), tem_deducao=False, tipo="inss", competencia=comp
    )
    teto_raw = valores.get("teto")
    teto = Decimal(str(teto_raw)) if teto_raw is not None else None

    truncar_faixa = arredondamento == "truncar"
    base_aplicada = min(base_d, teto) if teto is not None else base_d
    contribuicao = Decimal(0)
    limite_inferior = Decimal(0)
    for f in faixas:
        teto_faixa = f.ate if f.ate is not None else base_aplicada
        if base_aplicada <= limite_inferior:
            break
        parte = min(base_aplicada, teto_faixa) - limite_inferior
        if parte > 0:
            valor_faixa = parte * f.aliquota
            if truncar_faixa:
                valor_faixa = valor_faixa.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
            contribuicao += valor_faixa
        limite_inferior = teto_faixa
    # Arredonda o total para 2 casas (centavos)
    return contribuicao.quantize(Decimal("0.01"))


def irrf(base: Decimal, dependentes: int | Decimal, competencia: date | str) -> Decimal:
    """
    Calcula IRRF na competência (regra simplificada: aplica dedução por
    dependente sobre a base ANTES de procurar a faixa).

    A base de cálculo é `base - deducao_dependente * dependentes`. Pega
    a faixa onde a base se encaixa e devolve `base × aliquota − deducao`.
    """
    comp = _resolver_competencia(competencia)
    base_d = Decimal(str(base))
    if base_d <= 0:
        return Decimal(0)

    dep = int(dependentes)
    valor_deducao_dep = deducao_dependente_irrf(comp) * dep
    base_ajustada = base_d - valor_deducao_dep
    if base_ajustada <= 0:
        return Decimal(0)

    valores = _buscar_tabela("irrf", comp.isoformat())
    faixas = _parse_faixas(
        list(valores.get("faixas", [])), tem_deducao=True, tipo="irrf", competencia=comp
    )
    for f in faixas:
        if f.ate is None or base_ajustada <= f.ate:
            imposto = base_ajustada * f.aliquota - f.deducao
            return max(imposto, Decimal(0)).quantize(Decimal("0.01"))
    # Não deveria chegar aqui (última faixa é aberta)
    return Decimal(0)
