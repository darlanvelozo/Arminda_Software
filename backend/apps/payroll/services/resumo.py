"""
Resumos agregados de uma folha — refinos operacionais (v0.13.0).

- `resumo_por_servidor(folha)`: uma linha por vínculo com proventos,
  descontos e líquido (agregação dos lançamentos por tipo).
- `resumo_por_area(folha)`: totais agrupados por lotação e por órgão
  emissor, mais o total geral da folha.

Tudo via agregação no banco (não itera lançamentos em Python). Valores
devolvidos como string (Decimal exato, consistente com o resto da API).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db.models import DecimalField, Q, Sum
from django.db.models.functions import Coalesce

from apps.payroll.models import Folha, Lancamento, TipoRubrica

CENTAVOS = Decimal("0.01")


def _somas():
    """Anotações de soma de proventos e descontos (zero quando ausente)."""
    dec = DecimalField(max_digits=14, decimal_places=2)
    return {
        "proventos": Coalesce(
            Sum("valor", filter=Q(rubrica__tipo=TipoRubrica.PROVENTO)),
            Decimal(0),
            output_field=dec,
        ),
        "descontos": Coalesce(
            Sum("valor", filter=Q(rubrica__tipo=TipoRubrica.DESCONTO)),
            Decimal(0),
            output_field=dec,
        ),
    }


def _linha(proventos: Decimal, descontos: Decimal, extra: dict[str, Any]) -> dict[str, Any]:
    liquido = (proventos - descontos).quantize(CENTAVOS)
    return {
        **extra,
        "proventos": str(proventos.quantize(CENTAVOS)),
        "descontos": str(descontos.quantize(CENTAVOS)),
        "liquido": str(liquido),
    }


def resumo_por_servidor(folha: Folha) -> list[dict[str, Any]]:
    """Uma linha por vínculo: servidor, cargo, lotação e totais."""
    qs = (
        Lancamento.objects.filter(folha=folha)
        .values(
            "vinculo",
            "vinculo__servidor__nome",
            "vinculo__servidor__matricula",
            "vinculo__cargo__nome",
            "vinculo__lotacao__nome",
        )
        .annotate(**_somas())
        .order_by("vinculo__servidor__nome", "vinculo")
    )
    return [
        _linha(
            row["proventos"],
            row["descontos"],
            {
                "vinculo_id": row["vinculo"],
                "servidor_nome": row["vinculo__servidor__nome"],
                "servidor_matricula": row["vinculo__servidor__matricula"],
                "cargo": row["vinculo__cargo__nome"],
                "lotacao": row["vinculo__lotacao__nome"],
            },
        )
        for row in qs
    ]


def _agrupar(folha: Folha, group_id: str, group_label: str, sem_label: str) -> list[dict[str, Any]]:
    qs = (
        Lancamento.objects.filter(folha=folha)
        .values(group_id, group_label)
        .annotate(**_somas())
        .order_by(group_label)
    )
    linhas = []
    for row in qs:
        linhas.append(
            _linha(
                row["proventos"],
                row["descontos"],
                {
                    "id": row[group_id],
                    "nome": row[group_label] or sem_label,
                },
            )
        )
    return linhas


def resumo_por_area(folha: Folha) -> dict[str, Any]:
    """Totais por lotação e por órgão emissor + total geral da folha."""
    por_lotacao = _agrupar(
        folha, "vinculo__lotacao", "vinculo__lotacao__nome", "(sem lotação)"
    )
    por_orgao = _agrupar(
        folha, "vinculo__orgao_emissor", "vinculo__orgao_emissor__nome", "(sem órgão)"
    )
    geral = Lancamento.objects.filter(folha=folha).aggregate(**_somas())
    return {
        "por_lotacao": por_lotacao,
        "por_orgao": por_orgao,
        "geral": _linha(geral["proventos"], geral["descontos"], {}),
    }
