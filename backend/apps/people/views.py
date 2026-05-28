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
    OrgaoEmissor,
    Servidor,
    Sindicato,
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
    OrgaoEmissorDetailSerializer,
    OrgaoEmissorListSerializer,
    OrgaoEmissorWriteSerializer,
    ServidorDetailSerializer,
    ServidorListSerializer,
    ServidorWriteSerializer,
    SindicatoDetailSerializer,
    SindicatoListSerializer,
    SindicatoWriteSerializer,
    TransferenciaInputSerializer,
    VinculoDetailSerializer,
    VinculoListSerializer,
    VinculoWriteSerializer,
)
from apps.people.services.admissao import DadosAdmissao, admitir_servidor
from apps.people.services.bulk import (
    aplicar_bulk_update_servidores,
    aplicar_bulk_update_vinculos,
)
from apps.people.services.desligamento import (
    DadosDesligamento,
    desligar_servidor,
)
from apps.people.services.exceptions import DomainError
from apps.people.services.qualidade import (
    LABELS as QUALIDADE_LABELS,
)
from apps.people.services.qualidade import (
    avaliar_servidor,
    resumir,
)
from apps.people.services.sugestao_area import sugerir_natureza
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

    READ_ACTIONS = _PapelPorAcaoMixin.READ_ACTIONS | {"sugestao_natureza"}

    def get_serializer_class(self):
        if self.action == "list":
            return CargoListSerializer
        if self.action in ("create", "update", "partial_update"):
            return CargoWriteSerializer
        return CargoDetailSerializer

    @action(detail=True, methods=["get"], url_path="sugestao-natureza")
    def sugestao_natureza(self, request, pk=None):
        """GET /api/people/cargos/<id>/sugestao-natureza/ — heurística (Onda 1.6b)."""
        cargo = self.get_object()
        sugestao = sugerir_natureza(cargo.nome)
        if sugestao is None:
            return Response({"natureza_sugerida": None, "confianca": 0, "motivo": ""})
        return Response(
            {
                "natureza_sugerida": sugestao.natureza_sugerida,
                "natureza_label": sugestao.label,
                "confianca": sugestao.confianca,
                "motivo": sugestao.motivo,
            }
        )


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

    READ_ACTIONS = _PapelPorAcaoMixin.READ_ACTIONS | {"historico", "qualidade", "qualidade_resumo"}

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

    @action(detail=True, methods=["get"], url_path="qualidade")
    def qualidade(self, request, pk=None):
        """GET /api/people/servidores/<id>/qualidade/ — score do servidor."""
        servidor = self.get_object()
        avaliacao = avaliar_servidor(servidor)
        return Response(
            {
                "servidor_id": avaliacao.servidor_id,
                "matricula": avaliacao.matricula,
                "nome": avaliacao.nome,
                "total_campos": avaliacao.total_campos,
                "campos_preenchidos": avaliacao.campos_preenchidos,
                "campos_faltantes": [
                    {"campo": c, "label": QUALIDADE_LABELS.get(c, c)}
                    for c in avaliacao.campos_faltantes
                ],
                "score": avaliacao.score,
                "completo": avaliacao.completo,
            }
        )

    @action(detail=False, methods=["get"], url_path="qualidade-resumo")
    def qualidade_resumo(self, request):
        """GET /api/people/servidores/qualidade-resumo/ — dashboard agregado."""
        qs = self.filter_queryset(self.get_queryset())
        resumo = resumir(qs)
        return Response(
            {
                "total_servidores": resumo.total_servidores,
                "completos": resumo.completos,
                "incompletos": resumo.incompletos,
                "score_medio": resumo.score_medio,
                "breakdown_campos_faltantes": [
                    {
                        "campo": campo,
                        "label": QUALIDADE_LABELS.get(campo, campo),
                        "servidores_pendentes": count,
                    }
                    for campo, count in resumo.breakdown_campos_faltantes.items()
                ],
            }
        )

    @action(detail=False, methods=["post"], url_path="bulk-update")
    def bulk_update(self, request):
        """POST /api/people/servidores/bulk-update/.

        Body:
            {
                "servidor_ids": [1,2,3],
                "updates": {"tipo_logradouro": "avenida", "cidade": "Aracaju", "uf": "SE"}
            }

        Aplica `updates` em cada `Servidor` cujo id está em `servidor_ids`.
        Campos não listados em `updates` ficam intactos.
        """
        servidor_ids = request.data.get("servidor_ids") or []
        updates = request.data.get("updates") or {}
        if not isinstance(servidor_ids, list) or not servidor_ids:
            raise ValidationError({"servidor_ids": "Forneça uma lista de ids."})
        if not isinstance(updates, dict) or not updates:
            raise ValidationError({"updates": "Forneça um dict com campos a atualizar."})
        try:
            resultado = aplicar_bulk_update_servidores(
                ids=[int(i) for i in servidor_ids],
                updates=updates,
            )
        except DomainError as exc:
            raise _domain_error_to_validation_error(exc) from exc
        return Response(resultado)


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

    @action(detail=False, methods=["post"], url_path="bulk-update")
    def bulk_update(self, request):
        """POST /api/people/vinculos/bulk-update/ — aplica updates em lote.

        Body:
            {
                "vinculo_ids": [10, 11, 12],
                "updates": {"orgao_emissor": 3, "sindicato": 7}
            }
        """
        vinculo_ids = request.data.get("vinculo_ids") or []
        updates = request.data.get("updates") or {}
        if not isinstance(vinculo_ids, list) or not vinculo_ids:
            raise ValidationError({"vinculo_ids": "Forneça uma lista de ids."})
        if not isinstance(updates, dict) or not updates:
            raise ValidationError({"updates": "Forneça um dict com campos a atualizar."})
        try:
            resultado = aplicar_bulk_update_vinculos(
                ids=[int(i) for i in vinculo_ids],
                updates=updates,
            )
        except DomainError as exc:
            raise _domain_error_to_validation_error(exc) from exc
        return Response(resultado)


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


# ============================================================
# OrgaoEmissor — pré-eSocial S-1005 (Onda 1.6a)
# ============================================================


class OrgaoEmissorViewSet(_PapelPorAcaoMixin, viewsets.ModelViewSet):
    """CRUD de órgãos emissores (entidades fiscais com CNPJ próprio).

    Tipicamente Prefeitura matriz, Câmara, Fundo Municipal de Saúde,
    FMAS, IPM. Cada um com CNPJ distinto, base do envio do S-1005 no
    eSocial.
    """

    queryset = OrgaoEmissor.objects.all()
    search_fields = ["nome", "sigla", "cnpj"]
    ordering_fields = ["nome", "sigla", "criado_em"]

    def get_serializer_class(self):
        if self.action == "list":
            return OrgaoEmissorListSerializer
        if self.action in ("create", "update", "partial_update"):
            return OrgaoEmissorWriteSerializer
        return OrgaoEmissorDetailSerializer


# ============================================================
# Sindicato — pré-eSocial S-2200 (Onda 1.6a)
# ============================================================


class SindicatoViewSet(_PapelPorAcaoMixin, viewsets.ModelViewSet):
    """CRUD de sindicatos representantes de categoria."""

    queryset = Sindicato.objects.all()
    search_fields = ["nome", "cnpj", "categoria", "codigo_sindical"]
    ordering_fields = ["nome", "criado_em"]

    def get_serializer_class(self):
        if self.action == "list":
            return SindicatoListSerializer
        if self.action in ("create", "update", "partial_update"):
            return SindicatoWriteSerializer
        return SindicatoDetailSerializer
