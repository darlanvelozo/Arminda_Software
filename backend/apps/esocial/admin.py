"""Admin do app esocial (schema do tenant)."""

from __future__ import annotations

from django.contrib import admin

from .models import CertificadoDigital, EventoESocial, LoteESocial


@admin.register(EventoESocial)
class EventoESocialAdmin(admin.ModelAdmin):
    list_display = ("tipo", "orgao_emissor", "rubrica", "id_evento", "status", "criado_em")
    list_filter = ("tipo", "status", "versao_layout")
    search_fields = ("id_evento", "orgao_emissor__nome", "orgao_emissor__cnpj")
    raw_id_fields = ("orgao_emissor", "rubrica")
    readonly_fields = ("id_evento", "xml", "versao_layout")
    date_hierarchy = "criado_em"


@admin.register(LoteESocial)
class LoteESocialAdmin(admin.ModelAdmin):
    list_display = ("id", "orgao_emissor", "grupo", "status", "protocolo_envio", "criado_em")
    list_filter = ("grupo", "status")
    raw_id_fields = ("orgao_emissor",)
    readonly_fields = ("xml_envio", "xml_retorno", "protocolo_envio")


@admin.register(CertificadoDigital)
class CertificadoDigitalAdmin(admin.ModelAdmin):
    """Só metadados. O PFX/senha cifrados nunca aparecem no admin."""

    list_display = ("orgao_emissor", "titular", "cnpj", "validade_fim")
    search_fields = ("titular", "cnpj", "orgao_emissor__nome")
    raw_id_fields = ("orgao_emissor",)
    # Campos cifrados fora do formulário — nunca exibir/editar aqui.
    fields = (
        "orgao_emissor", "titular", "cnpj", "emissor",
        "validade_inicio", "validade_fim", "thumbprint",
    )
    readonly_fields = fields
