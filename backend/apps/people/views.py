"""
ViewSets do app people (Bloco 1.2).

Padrao: ModelViewSet com permissions por papel (RBAC do ADR-0007).
- Leitura: IsLeituraMunicipio (qualquer papel >= leitura)
- Escrita: IsRHMunicipio (rh, admin ou staff_arminda)
"""

from __future__ import annotations

from rest_framework import viewsets

from apps.core.permissions import IsLeituraMunicipio, IsRHMunicipio
from apps.people.filters import CargoFilter, LotacaoFilter
from apps.people.models import Cargo, Lotacao
from apps.people.serializers import (
    CargoDetailSerializer,
    CargoListSerializer,
    CargoWriteSerializer,
    LotacaoDetailSerializer,
    LotacaoListSerializer,
    LotacaoWriteSerializer,
)


class _PapelPorAcaoMixin:
    """Permissions diferentes por tipo de acao (read vs write).

    Convencao:
    - list/retrieve  -> IsLeituraMunicipio
    - tudo o resto   -> IsRHMunicipio (escopo deste app)
    """

    READ_ACTIONS = {"list", "retrieve"}

    def get_permissions(self):
        if self.action in self.READ_ACTIONS:
            return [IsLeituraMunicipio()]
        return [IsRHMunicipio()]


class CargoViewSet(_PapelPorAcaoMixin, viewsets.ModelViewSet):
    """CRUD de cargos do municipio (tenant atual)."""

    queryset = Cargo.objects.all()
    filterset_class = CargoFilter
    search_fields = ["codigo", "nome", "cbo"]
    ordering_fields = ["nome", "codigo", "criado_em"]

    def get_serializer_class(self):
        if self.action == "list":
            return CargoListSerializer
        if self.action in ("create", "update", "partial_update"):
            return CargoWriteSerializer
        return CargoDetailSerializer


class LotacaoViewSet(_PapelPorAcaoMixin, viewsets.ModelViewSet):
    """CRUD de lotacoes (secretarias) do municipio."""

    queryset = Lotacao.objects.select_related("lotacao_pai").all()
    filterset_class = LotacaoFilter
    search_fields = ["codigo", "nome", "sigla"]
    ordering_fields = ["nome", "codigo", "criado_em"]

    def get_serializer_class(self):
        if self.action == "list":
            return LotacaoListSerializer
        if self.action in ("create", "update", "partial_update"):
            return LotacaoWriteSerializer
        return LotacaoDetailSerializer
