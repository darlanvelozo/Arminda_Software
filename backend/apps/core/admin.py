"""
Admin do app core.
"""

from django.contrib import admin

from .models import ConfiguracaoGlobal, Municipio

admin.site.site_header = "Arminda — Administracao"
admin.site.site_title = "Arminda Admin"
admin.site.index_title = "Painel de administracao"


@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ("nome", "uf", "codigo_ibge", "ativo", "data_adesao")
    list_filter = ("uf", "ativo")
    search_fields = ("nome", "codigo_ibge")
    list_editable = ("ativo",)
    readonly_fields = ("criado_em", "atualizado_em", "criado_por", "atualizado_por")

    fieldsets = (
        (None, {"fields": ("nome", "codigo_ibge", "uf", "ativo", "data_adesao")}),
        (
            "Auditoria",
            {
                "classes": ("collapse",),
                "fields": (
                    "criado_em",
                    "atualizado_em",
                    "criado_por",
                    "atualizado_por",
                ),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.criado_por = request.user
        obj.atualizado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(ConfiguracaoGlobal)
class ConfiguracaoGlobalAdmin(admin.ModelAdmin):
    list_display = ("chave", "valor", "descricao")
    search_fields = ("chave", "descricao")
