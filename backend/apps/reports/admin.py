"""Admin do app reports (schema do tenant)."""

from __future__ import annotations

from django.contrib import admin

from .models import RelatorioGerado


@admin.register(RelatorioGerado)
class RelatorioGeradoAdmin(admin.ModelAdmin):
    list_display = ("tipo", "titulo", "competencia", "gerado_em", "gerado_por")
    list_filter = ("tipo",)
    search_fields = ("titulo",)
    date_hierarchy = "gerado_em"
    readonly_fields = ("gerado_em",)
    raw_id_fields = ("gerado_por",)
