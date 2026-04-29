"""
ViewSets do app people (Bloco 1.2).

Padrao: ModelViewSet com permissions por papel (RBAC do ADR-0007).
- Leitura: IsLeituraMunicipio (qualquer papel >= leitura)
- Escrita: IsRHMunicipio (rh, admin ou staff_arminda)

Documento aceita upload (MultiPartParser).
Servidor expoe @action /historico/ consultando simple-history.
"""

from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.core.permissions import IsLeituraMunicipio, IsRHMunicipio
from apps.people.filters import (
    CargoFilter,
    DependenteFilter,
    DocumentoFilter,
    LotacaoFilter,
    ServidorFilter,
    VinculoFilter,
)
from apps.people.models import (
    Cargo,
    Dependente,
    Documento,
    Lotacao,
    Servidor,
    VinculoFuncional,
)
from apps.people.serializers import (
    CargoDetailSerializer,
    CargoListSerializer,
    CargoWriteSerializer,
    DependenteDetailSerializer,
    DependenteListSerializer,
    DependenteWriteSerializer,
    DocumentoDetailSerializer,
    DocumentoListSerializer,
    DocumentoWriteSerializer,
    HistoricoServidorSerializer,
    LotacaoDetailSerializer,
    LotacaoListSerializer,
    LotacaoWriteSerializer,
    ServidorDetailSerializer,
    ServidorListSerializer,
    ServidorWriteSerializer,
    VinculoDetailSerializer,
    VinculoListSerializer,
    VinculoWriteSerializer,
)

# ============================================================
# Mixin: leitura vs escrita (RBAC)
# ============================================================


class _PapelPorAcaoMixin:
    """Permissions diferentes por tipo de acao (read vs write).

    Convencao deste app:
    - actions de leitura -> IsLeituraMunicipio
    - actions de escrita -> IsRHMunicipio
    Subclasses podem sobrescrever READ_ACTIONS para incluir @action customizadas.
    """

    READ_ACTIONS: set[str] = {"list", "retrieve"}

    def get_permissions(self):
        if self.action in self.READ_ACTIONS:
            return [IsLeituraMunicipio()]
        return [IsRHMunicipio()]


# ============================================================
# Cargo
# ============================================================


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


# ============================================================
# Lotacao
# ============================================================


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


# ============================================================
# Servidor
# ============================================================


class ServidorViewSet(_PapelPorAcaoMixin, viewsets.ModelViewSet):
    """CRUD de servidores do municipio + endpoint de historico."""

    queryset = Servidor.objects.prefetch_related(
        "dependentes",
        "vinculos__cargo",
        "vinculos__lotacao",
    ).all()
    filterset_class = ServidorFilter
    search_fields = ["matricula", "nome", "cpf"]
    ordering_fields = ["nome", "matricula", "criado_em"]

    READ_ACTIONS = _PapelPorAcaoMixin.READ_ACTIONS | {"historico"}

    def get_serializer_class(self):
        if self.action == "list":
            return ServidorListSerializer
        if self.action in ("create", "update", "partial_update"):
            return ServidorWriteSerializer
        return ServidorDetailSerializer

    @action(detail=True, methods=["get"], url_path="historico")
    def historico(self, request, pk=None):
        """GET /api/people/servidores/{id}/historico/ — versoes simple-history."""
        servidor = self.get_object()
        history = servidor.history.all().order_by("-history_date")
        page = self.paginate_queryset(history)
        if page is not None:
            ser = HistoricoServidorSerializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = HistoricoServidorSerializer(history, many=True)
        return Response(ser.data)


# ============================================================
# VinculoFuncional
# ============================================================


class VinculoFuncionalViewSet(_PapelPorAcaoMixin, viewsets.ModelViewSet):
    """CRUD de vinculos funcionais (servidor x cargo x lotacao)."""

    queryset = VinculoFuncional.objects.select_related("servidor", "cargo", "lotacao").all()
    filterset_class = VinculoFilter
    search_fields = ["servidor__matricula", "servidor__nome"]
    ordering_fields = ["data_admissao", "salario_base"]

    def get_serializer_class(self):
        if self.action == "list":
            return VinculoListSerializer
        if self.action in ("create", "update", "partial_update"):
            return VinculoWriteSerializer
        return VinculoDetailSerializer


# ============================================================
# Dependente
# ============================================================


class DependenteViewSet(_PapelPorAcaoMixin, viewsets.ModelViewSet):
    """CRUD de dependentes (filtrar por ?servidor=<id>)."""

    queryset = Dependente.objects.select_related("servidor").all()
    filterset_class = DependenteFilter
    search_fields = ["nome", "cpf"]
    ordering_fields = ["nome", "data_nascimento"]

    def get_serializer_class(self):
        if self.action == "list":
            return DependenteListSerializer
        if self.action in ("create", "update", "partial_update"):
            return DependenteWriteSerializer
        return DependenteDetailSerializer


# ============================================================
# Documento
# ============================================================


class DocumentoViewSet(_PapelPorAcaoMixin, viewsets.ModelViewSet):
    """CRUD de documentos digitalizados (upload via multipart)."""

    queryset = Documento.objects.select_related("servidor").all()
    filterset_class = DocumentoFilter
    search_fields = ["descricao", "servidor__nome"]
    ordering_fields = ["data_upload"]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.action == "list":
            return DocumentoListSerializer
        if self.action in ("create", "update", "partial_update"):
            return DocumentoWriteSerializer
        return DocumentoDetailSerializer
