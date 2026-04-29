"""
FilterSets para os viewsets do app people (Bloco 1.2).

Permitem ?codigo=...&nivel_escolaridade=...&ativo=true e busca em campos textuais.
"""

from __future__ import annotations

import django_filters

from apps.people.models import (
    Cargo,
    Dependente,
    Documento,
    Lotacao,
    Servidor,
    VinculoFuncional,
)


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


class ServidorFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr="icontains")
    matricula = django_filters.CharFilter(lookup_expr="iexact")
    cargo = django_filters.NumberFilter(field_name="vinculos__cargo")
    lotacao = django_filters.NumberFilter(field_name="vinculos__lotacao")
    regime = django_filters.CharFilter(field_name="vinculos__regime")

    class Meta:
        model = Servidor
        fields = ["matricula", "nome", "ativo", "sexo"]


class VinculoFilter(django_filters.FilterSet):
    admitido_apos = django_filters.DateFilter(field_name="data_admissao", lookup_expr="gte")
    admitido_ate = django_filters.DateFilter(field_name="data_admissao", lookup_expr="lte")

    class Meta:
        model = VinculoFuncional
        fields = ["servidor", "cargo", "lotacao", "regime", "ativo"]


class DependenteFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Dependente
        fields = ["servidor", "parentesco", "ir", "salario_familia"]


class DocumentoFilter(django_filters.FilterSet):
    class Meta:
        model = Documento
        fields = ["servidor", "tipo"]
