"""
ViewSets do app people (Bloco 1.2).

Padrao: ModelViewSet com permissions por papel (RBAC do ADR-0007).
- Leitura: IsLeituraMunicipio (qualquer papel >= leitura)
- Escrita: IsRHMunicipio (rh, admin ou staff_arminda)

Documento aceita upload (MultiPartParser).
Servidor expoe @action /historico/ consultando simple-history.
"""

from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
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
    AdmissaoInputSerializer,
    CargoDetailSerializer,
    CargoListSerializer,
    CargoWriteSerializer,
    DependenteDetailSerializer,
    DependenteListSerializer,
    DependenteWriteSerializer,
    DesligamentoInputSerializer,
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
    TransferenciaInputSerializer,
    VinculoDetailSerializer,
    VinculoListSerializer,
    VinculoWriteSerializer,
)
from apps.people.services.admissao import DadosAdmissao, admitir_servidor
from apps.people.services.desligamento import (
    DadosDesligamento,
    desligar_servidor,
)
from apps.people.services.exceptions import DomainError
from apps.people.services.transferencia import (
    DadosTransferencia,
    transferir_lotacao,
)


def _domain_error_to_validation_error(exc: DomainError) -> ValidationError:
    """Traduz erro de dominio para resposta HTTP 400 com `code` estavel."""
    return ValidationError({"detail": str(exc), "code": exc.code})


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
        if self.action == "admitir":
            return AdmissaoInputSerializer
        if self.action == "desligar":
            return DesligamentoInputSerializer
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

    @action(detail=False, methods=["post"], url_path="admitir")
    def admitir(self, request):
        """POST /api/people/servidores/admitir/ — cria Servidor + Vinculo (atomico)."""
        ser = AdmissaoInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            servidor = admitir_servidor(DadosAdmissao(**ser.validated_data))
        except DomainError as exc:
            raise _domain_error_to_validation_error(exc) from exc
        return Response(
            ServidorDetailSerializer(servidor).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="desligar")
    def desligar(self, request, pk=None):
        """POST /api/people/servidores/<id>/desligar/ — encerra vinculos + inativa."""
        ser = DesligamentoInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            servidor = desligar_servidor(
                DadosDesligamento(servidor_id=int(pk), **ser.validated_data)
            )
        except DomainError as exc:
            raise _domain_error_to_validation_error(exc) from exc
        return Response(ServidorDetailSerializer(servidor).data)


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
        if self.action == "transferir":
            return TransferenciaInputSerializer
        return VinculoDetailSerializer

    @action(detail=True, methods=["post"], url_path="transferir")
    def transferir(self, request, pk=None):
        """POST /api/people/vinculos/<id>/transferir/ — encerra atual + cria novo."""
        ser = TransferenciaInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            novo = transferir_lotacao(DadosTransferencia(vinculo_id=int(pk), **ser.validated_data))
        except DomainError as exc:
            raise _domain_error_to_validation_error(exc) from exc
        return Response(VinculoDetailSerializer(novo).data, status=status.HTTP_201_CREATED)


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
