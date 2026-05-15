"""FilterSets do app payroll."""

from __future__ import annotations

import django_filters

from apps.payroll.models import Folha, Lancamento, Rubrica


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


class FolhaFilter(django_filters.FilterSet):
    competencia_de = django_filters.DateFilter(
        field_name="competencia", lookup_expr="gte"
    )
    competencia_ate = django_filters.DateFilter(
        field_name="competencia", lookup_expr="lte"
    )
    ano = django_filters.NumberFilter(field_name="competencia", lookup_expr="year")
    mes = django_filters.NumberFilter(field_name="competencia", lookup_expr="month")

    class Meta:
        model = Folha
        fields = ["competencia", "tipo", "status"]


class LancamentoFilter(django_filters.FilterSet):
    servidor_nome = django_filters.CharFilter(
        field_name="servidor__nome", lookup_expr="icontains"
    )
    rubrica_codigo = django_filters.CharFilter(field_name="rubrica__codigo")

    class Meta:
        model = Lancamento
        fields = ["folha", "servidor", "vinculo", "rubrica"]
