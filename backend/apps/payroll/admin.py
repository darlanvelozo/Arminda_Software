"""
Admin do app payroll.
"""

from django.contrib import admin

from .models import Folha, Lancamento, Rubrica


class LancamentoInline(admin.TabularInline):
    model = Lancamento
    extra = 0
    fields = ("servidor", "vinculo", "rubrica", "referencia", "valor")
    raw_id_fields = ("servidor", "vinculo", "rubrica")


@admin.register(Rubrica)
class RubricaAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nome",
        "tipo",
        "incide_inss",
        "incide_irrf",
        "incide_fgts",
        "municipio",
        "ativo",
    )
    list_filter = ("tipo", "incide_inss", "incide_irrf", "incide_fgts", "municipio", "ativo")
    search_fields = ("codigo", "nome")
    list_editable = ("ativo",)
    list_per_page = 50

    fieldsets = (
        (None, {"fields": ("municipio", "codigo", "nome", "tipo", "ativo")}),
        (
            "Incidencias",
            {"fields": ("incide_inss", "incide_irrf", "incide_fgts")},
        ),
        (
            "Formula",
            {
                "classes": ("collapse",),
                "fields": ("formula",),
            },
        ),
    )


@admin.register(Folha)
class FolhaAdmin(admin.ModelAdmin):
    list_display = (
        "competencia",
        "tipo",
        "status",
        "municipio",
        "total_proventos",
        "total_descontos",
        "total_liquido",
    )
    list_filter = ("status", "tipo", "municipio")
    date_hierarchy = "competencia"
    inlines = [LancamentoInline]
    readonly_fields = ("total_proventos", "total_descontos", "total_liquido")

    fieldsets = (
        (None, {"fields": ("municipio", "competencia", "tipo", "status")}),
        (
            "Totais",
            {
                "fields": (
                    "total_proventos",
                    "total_descontos",
                    "total_liquido",
                ),
            },
        ),
        ("Observacoes", {"fields": ("observacoes",)}),
    )


@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = ("servidor", "rubrica", "referencia", "valor", "folha")
    list_filter = ("folha__competencia", "rubrica__tipo")
    search_fields = ("servidor__nome", "rubrica__nome")
    raw_id_fields = ("folha", "servidor", "vinculo", "rubrica")
    list_per_page = 50
