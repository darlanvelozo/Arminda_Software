"""Serializers do eSocial (Onda 4.1)."""

from __future__ import annotations

from rest_framework import serializers

from apps.esocial.models import EventoESocial


class EventoESocialSerializer(serializers.ModelSerializer):
    """Lista/detalhe de evento. O XML completo vem no endpoint `baixar`."""

    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    orgao_nome = serializers.CharField(source="orgao_emissor.nome", read_only=True)
    orgao_cnpj = serializers.CharField(source="orgao_emissor.cnpj", read_only=True)

    class Meta:
        model = EventoESocial
        fields = [
            "id", "tipo", "tipo_display", "orgao_emissor", "orgao_nome",
            "orgao_cnpj", "id_evento", "versao_layout", "status",
            "status_display", "lote", "criado_em",
        ]
        read_only_fields = fields


class GerarEventoSerializer(serializers.Serializer):
    """Entrada para gerar um evento."""

    tipo = serializers.ChoiceField(choices=EventoESocial._meta.get_field("tipo").choices)
    orgao_emissor = serializers.IntegerField()
    competencia = serializers.DateField(required=False)
    class_trib = serializers.CharField(required=False, default="60", max_length=2)
