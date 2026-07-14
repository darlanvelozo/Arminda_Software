"""Serializers do eSocial (Onda 4.1)."""

from __future__ import annotations

from rest_framework import serializers

from apps.esocial.models import CertificadoDigital, EventoESocial


class EventoESocialSerializer(serializers.ModelSerializer):
    """Lista/detalhe de evento. O XML completo vem no endpoint `baixar`."""

    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    orgao_nome = serializers.CharField(source="orgao_emissor.nome", read_only=True)
    orgao_cnpj = serializers.CharField(source="orgao_emissor.cnpj", read_only=True)
    rubrica_codigo = serializers.CharField(source="rubrica.codigo", read_only=True, default=None)

    class Meta:
        model = EventoESocial
        fields = [
            "id", "tipo", "tipo_display", "orgao_emissor", "orgao_nome",
            "orgao_cnpj", "rubrica", "rubrica_codigo", "id_evento",
            "versao_layout", "status", "status_display", "lote", "criado_em",
        ]
        read_only_fields = fields


class GerarEventoSerializer(serializers.Serializer):
    """Entrada para gerar um evento."""

    tipo = serializers.ChoiceField(choices=EventoESocial._meta.get_field("tipo").choices)
    orgao_emissor = serializers.IntegerField()
    rubrica = serializers.IntegerField(required=False)
    competencia = serializers.DateField(required=False)
    class_trib = serializers.CharField(required=False, default="60", max_length=2)


class GerarEventosFolhaSerializer(serializers.Serializer):
    """Entrada da geração em lote dos eventos de remuneração de uma folha."""

    orgao_emissor = serializers.IntegerField()
    folha = serializers.IntegerField()
    incluir_pagamentos = serializers.BooleanField(required=False, default=False)


class CertificadoDigitalSerializer(serializers.ModelSerializer):
    """Metadados do certificado no cofre. NUNCA expõe o PFX/senha cifrados."""

    orgao_nome = serializers.CharField(source="orgao_emissor.nome", read_only=True)
    dias_para_vencer = serializers.SerializerMethodField()

    class Meta:
        model = CertificadoDigital
        fields = [
            "id", "orgao_emissor", "orgao_nome", "titular", "cnpj", "emissor",
            "validade_inicio", "validade_fim", "dias_para_vencer", "thumbprint",
            "criado_em",
        ]
        read_only_fields = fields

    def get_dias_para_vencer(self, obj) -> int | None:
        if not obj.validade_fim:
            return None
        from django.utils import timezone
        return (obj.validade_fim - timezone.now()).days


class UploadCertificadoSerializer(serializers.Serializer):
    """Upload do .pfx + senha para o cofre de um órgão."""

    orgao_emissor = serializers.IntegerField()
    arquivo = serializers.FileField()
    senha = serializers.CharField(max_length=200, write_only=True, style={"input_type": "password"})
