"""
ViewSets do app payroll (Bloco 1.2 — Onda 3).

Apenas Rubrica esqueleto. Folha e Lancamento entram nos Blocos 2-3.
RBAC: leitura para qualquer papel, escrita exige financeiro/admin/staff.
"""

from __future__ import annotations

from rest_framework import viewsets

from apps.core.permissions import IsFinanceiroMunicipio, IsLeituraMunicipio
from apps.payroll.filters import RubricaFilter
from apps.payroll.models import Rubrica
from apps.payroll.serializers import (
    RubricaDetailSerializer,
    RubricaListSerializer,
    RubricaWriteSerializer,
)


class RubricaViewSet(viewsets.ModelViewSet):
    """CRUD de rubricas (provento, desconto, informativa) do tenant atual.

    DSL de calculo (campo `formula`) sera implementada no Bloco 2;
    aqui aceitamos como TextField sem interpretacao.
    """

    queryset = Rubrica.objects.all()
    filterset_class = RubricaFilter
    search_fields = ["codigo", "nome"]
    ordering_fields = ["codigo", "nome", "criado_em"]

    READ_ACTIONS = {"list", "retrieve"}

    def get_permissions(self):
        if self.action in self.READ_ACTIONS:
            return [IsLeituraMunicipio()]
        return [IsFinanceiroMunicipio()]

    def get_serializer_class(self):
        if self.action == "list":
            return RubricaListSerializer
        if self.action in ("create", "update", "partial_update"):
            return RubricaWriteSerializer
        return RubricaDetailSerializer
