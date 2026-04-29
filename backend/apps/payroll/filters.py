"""FilterSets do app payroll (Bloco 1.2 — Onda 3)."""

from __future__ import annotations

import django_filters

from apps.payroll.models import Rubrica


class RubricaFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr="icontains")
    codigo = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = Rubrica
        fields = [
            "codigo",
            "nome",
            "tipo",
            "incide_inss",
            "incide_irrf",
            "incide_fgts",
            "ativo",
        ]
