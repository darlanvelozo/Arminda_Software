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
        fields = ["codigo", "nome", "natureza", "lotacao_pai", "ativo"]


class ServidorFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr="icontains")
    matricula = django_filters.CharFilter(lookup_expr="iexact")
    cargo = django_filters.NumberFilter(field_name="vinculos__cargo", distinct=True)
    lotacao = django_filters.NumberFilter(field_name="vinculos__lotacao", distinct=True)
    regime = django_filters.CharFilter(field_name="vinculos__regime", distinct=True)
    # Filtra servidores por natureza da lotação em pelo menos um vínculo ativo
    natureza = django_filters.CharFilter(
        field_name="vinculos__lotacao__natureza", distinct=True
    )
    # Onda 1.4-bis: filtra por natureza da unidade orçamentária (do empenho)
    natureza_unidade = django_filters.CharFilter(
        field_name="vinculos__unidade_orcamentaria__natureza", distinct=True
    )
    # Onda 1.6b: cadastro incompleto pra eSocial (qualquer campo obrigatório vazio)
    cadastro_incompleto = django_filters.BooleanFilter(method="_filtrar_cadastro_incompleto")

    class Meta:
        model = Servidor
        fields = ["matricula", "nome", "ativo", "sexo"]

    def _filtrar_cadastro_incompleto(self, queryset, name, value):
        # Import local pra evitar ciclo com services importando models.
        from apps.people.services.qualidade import filtrar_incompletos

        if value is True:
            return filtrar_incompletos(queryset)
        if value is False:
            ids_incompletos = list(
                filtrar_incompletos(queryset).values_list("id", flat=True)
            )
            return queryset.exclude(id__in=ids_incompletos)
        return queryset


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
