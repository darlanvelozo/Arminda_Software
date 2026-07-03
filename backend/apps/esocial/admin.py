"""Admin do app esocial (schema do tenant)."""

from __future__ import annotations

from django.contrib import admin

from .models import EventoESocial


@admin.register(EventoESocial)
class EventoESocialAdmin(admin.ModelAdmin):
    list_display = ("tipo", "orgao_emissor", "rubrica", "id_evento", "status", "criado_em")
    list_filter = ("tipo", "status", "versao_layout")
    search_fields = ("id_evento", "orgao_emissor__nome", "orgao_emissor__cnpj")
    raw_id_fields = ("orgao_emissor", "rubrica")
    readonly_fields = ("id_evento", "xml", "versao_layout")
    date_hierarchy = "criado_em"
