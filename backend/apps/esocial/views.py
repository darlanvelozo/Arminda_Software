"""
Views do eSocial (Onda 4.1).

CRUD de leitura dos eventos + action `gerar` (gera/valida/persiste) e
`baixar` (devolve o XML). Geração exige papel financeiro; leitura, leitura.
"""

from __future__ import annotations

from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.core.permissions import IsFinanceiroMunicipio, IsLeituraMunicipio
from apps.esocial.models import CertificadoDigital, EventoESocial
from apps.esocial.serializers import (
    CertificadoDigitalSerializer,
    EventoESocialSerializer,
    GerarEventoSerializer,
    GerarEventosFolhaSerializer,
    UploadCertificadoSerializer,
)
from apps.esocial.services.assinatura import SemCertificado, assinar_evento
from apps.esocial.services.cofre import CertificadoInvalido, guardar_certificado
from apps.esocial.services.geracao import gerar_evento, gerar_remuneracoes_da_folha
from apps.esocial.services.validacao import ErroValidacaoXSD
from apps.payroll.models import Folha, Rubrica
from apps.people.models import OrgaoEmissor


class EventoESocialViewSet(viewsets.ReadOnlyModelViewSet):
    """Eventos eSocial gerados. Filtra por ?orgao_emissor= e ?tipo=."""

    queryset = EventoESocial.objects.select_related("orgao_emissor").all()
    serializer_class = EventoESocialSerializer
    filterset_fields = ["orgao_emissor", "tipo", "status"]
    ordering_fields = ["criado_em"]
    ordering = ["-criado_em"]

    READ_ACTIONS = {"list", "retrieve", "baixar"}

    def get_permissions(self):
        if self.action in self.READ_ACTIONS:
            return [IsLeituraMunicipio()]
        return [IsFinanceiroMunicipio()]

    @action(detail=False, methods=["post"], url_path="gerar")
    def gerar(self, request):
        entrada = GerarEventoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        dados = entrada.validated_data
        try:
            orgao = OrgaoEmissor.objects.get(pk=dados["orgao_emissor"])
        except OrgaoEmissor.DoesNotExist:
            return Response(
                {"detail": "Órgão emissor não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        rubrica = None
        if dados.get("rubrica"):
            try:
                rubrica = Rubrica.objects.get(pk=dados["rubrica"])
            except Rubrica.DoesNotExist:
                return Response(
                    {"detail": "Rubrica não encontrada."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        try:
            evento = gerar_evento(
                orgao,
                dados["tipo"],
                rubrica=rubrica,
                competencia=dados.get("competencia"),
                class_trib=dados.get("class_trib", "60"),
            )
        except ErroValidacaoXSD as exc:
            return Response(
                {"detail": "XML gerado não passou na validação XSD.", "erros": exc.erros},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(evento)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="gerar-folha")
    def gerar_folha(self, request):
        """POST /esocial/eventos/gerar-folha/ — gera os eventos de remuneração
        (S-1200/S-1202 conforme o regime; opcionalmente S-1210) de todos os
        vínculos de uma folha calculada."""
        entrada = GerarEventosFolhaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        dados = entrada.validated_data
        try:
            orgao = OrgaoEmissor.objects.get(pk=dados["orgao_emissor"])
            folha = Folha.objects.get(pk=dados["folha"])
        except OrgaoEmissor.DoesNotExist:
            return Response({"detail": "Órgão emissor não encontrado."},
                            status=status.HTTP_404_NOT_FOUND)
        except Folha.DoesNotExist:
            return Response({"detail": "Folha não encontrada."},
                            status=status.HTTP_404_NOT_FOUND)
        try:
            resultado = gerar_remuneracoes_da_folha(
                orgao, folha, incluir_pagamentos=dados["incluir_pagamentos"])
        except ErroValidacaoXSD as exc:
            return Response(
                {"detail": "XML gerado não passou na validação XSD.", "erros": exc.erros},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        return Response(resultado, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="baixar")
    def baixar(self, request, pk=None):
        evento = self.get_object()
        resp = HttpResponse(evento.xml, content_type="application/xml; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{evento.id_evento}.xml"'
        return resp

    @action(detail=True, methods=["post"], url_path="assinar")
    def assinar(self, request, pk=None):
        evento = self.get_object()
        try:
            assinar_evento(evento)
        except SemCertificado as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ErroValidacaoXSD as exc:
            return Response(
                {"detail": "XML assinado não passou na validação XSD.", "erros": exc.erros},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return Response(self.get_serializer(evento).data)


class CertificadoDigitalViewSet(viewsets.ReadOnlyModelViewSet):
    """Cofre de certificados (metadados). Upload via /upload. Dados sensíveis
    (PFX/senha) nunca são expostos. Requer papel financeiro."""

    queryset = CertificadoDigital.objects.select_related("orgao_emissor").all()
    serializer_class = CertificadoDigitalSerializer
    permission_classes = [IsFinanceiroMunicipio]
    filterset_fields = ["orgao_emissor"]
    parser_classes = [MultiPartParser, FormParser]

    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        entrada = UploadCertificadoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        dados = entrada.validated_data
        try:
            orgao = OrgaoEmissor.objects.get(pk=dados["orgao_emissor"])
        except OrgaoEmissor.DoesNotExist:
            return Response(
                {"detail": "Órgão emissor não encontrado."}, status=status.HTTP_404_NOT_FOUND
            )
        try:
            cert = guardar_certificado(orgao, dados["arquivo"].read(), dados["senha"])
        except CertificadoInvalido as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            CertificadoDigitalSerializer(cert).data, status=status.HTTP_201_CREATED
        )
