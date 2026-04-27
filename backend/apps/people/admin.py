"""
Admin do app people.
"""

from django.contrib import admin

from .models import Cargo, Dependente, Documento, Lotacao, Servidor, VinculoFuncional


class VinculoInline(admin.TabularInline):
    model = VinculoFuncional
    extra = 0
    fields = (
        "cargo",
        "lotacao",
        "regime",
        "data_admissao",
        "data_demissao",
        "carga_horaria",
        "salario_base",
        "ativo",
    )


class DependenteInline(admin.TabularInline):
    model = Dependente
    extra = 0
    fields = ("nome", "cpf", "data_nascimento", "parentesco", "ir", "salario_familia")


class DocumentoInline(admin.TabularInline):
    model = Documento
    extra = 0
    fields = ("tipo", "descricao", "arquivo")
    readonly_fields = ("data_upload",)


@admin.register(Servidor)
class ServidorAdmin(admin.ModelAdmin):
    list_display = ("matricula", "nome", "cpf", "municipio", "ativo")
    list_filter = ("municipio", "ativo", "sexo")
    search_fields = ("matricula", "nome", "cpf")
    list_per_page = 25
    inlines = [VinculoInline, DependenteInline, DocumentoInline]

    fieldsets = (
        (
            "Dados pessoais",
            {
                "fields": (
                    "municipio",
                    "matricula",
                    "nome",
                    "cpf",
                    "data_nascimento",
                    "sexo",
                    "estado_civil",
                    "pis_pasep",
                )
            },
        ),
        ("Contato", {"fields": ("email", "telefone")}),
        (
            "Endereco",
            {
                "classes": ("collapse",),
                "fields": (
                    "logradouro",
                    "numero",
                    "complemento",
                    "bairro",
                    "cidade",
                    "uf",
                    "cep",
                ),
            },
        ),
        ("Status", {"fields": ("ativo",)}),
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
    readonly_fields = ("criado_em", "atualizado_em", "criado_por", "atualizado_por")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.criado_por = request.user
        obj.atualizado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "nivel_escolaridade", "municipio", "ativo")
    list_filter = ("municipio", "nivel_escolaridade", "ativo")
    search_fields = ("codigo", "nome", "cbo")
    list_editable = ("ativo",)


@admin.register(Lotacao)
class LotacaoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "sigla", "municipio", "ativo")
    list_filter = ("municipio", "ativo")
    search_fields = ("codigo", "nome", "sigla")
    list_editable = ("ativo",)


@admin.register(VinculoFuncional)
class VinculoFuncionalAdmin(admin.ModelAdmin):
    list_display = (
        "servidor",
        "cargo",
        "lotacao",
        "regime",
        "data_admissao",
        "salario_base",
        "ativo",
    )
    list_filter = ("regime", "ativo", "cargo__municipio")
    search_fields = ("servidor__nome", "servidor__matricula")
    raw_id_fields = ("servidor", "cargo", "lotacao")
    list_per_page = 25


@admin.register(Dependente)
class DependenteAdmin(admin.ModelAdmin):
    list_display = ("nome", "servidor", "parentesco", "ir", "salario_familia")
    list_filter = ("parentesco", "ir", "salario_familia")
    search_fields = ("nome", "servidor__nome")
    raw_id_fields = ("servidor",)


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ("tipo", "servidor", "descricao", "data_upload")
    list_filter = ("tipo",)
    search_fields = ("servidor__nome", "descricao")
    raw_id_fields = ("servidor",)
