"""
FilterSets para os viewsets do app people (Bloco 1.2).

Permitem ?codigo=...&nivel_escolaridade=...&ativo=true e busca em campos textuais.
"""

from __future__ import annotations

import django_filters

from apps.people.models import Cargo, Lotacao


class CargoFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr="icontains")
    codigo = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = Cargo
        fields = ["codigo", "nome", "nivel_escolaridade", "ativo"]


class LotacaoFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr="icontains")
    codigo = django_filters.CharFilter(lookup_expr="iexact")
    raiz = django_filters.BooleanFilter(field_name="lotacao_pai", lookup_expr="isnull")

    class Meta:
        model = Lotacao
        fields = ["codigo", "nome", "lotacao_pai", "ativo"]
