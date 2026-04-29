"""Admin do app people (schema do tenant)."""

from __future__ import annotations

from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

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
class ServidorAdmin(SimpleHistoryAdmin):
    list_display = ("matricula", "nome", "cpf", "ativo")
    list_filter = ("ativo", "sexo")
    search_fields = ("matricula", "nome", "cpf")
    list_per_page = 25
    inlines = [VinculoInline, DependenteInline, DocumentoInline]
    readonly_fields = ("criado_em", "atualizado_em", "criado_por", "atualizado_por")


@admin.register(Cargo)
class CargoAdmin(SimpleHistoryAdmin):
    list_display = ("codigo", "nome", "nivel_escolaridade", "ativo")
    list_filter = ("nivel_escolaridade", "ativo")
    search_fields = ("codigo", "nome", "cbo")
    list_editable = ("ativo",)


@admin.register(Lotacao)
class LotacaoAdmin(SimpleHistoryAdmin):
    list_display = ("codigo", "nome", "sigla", "ativo")
    list_filter = ("ativo",)
    search_fields = ("codigo", "nome", "sigla")
    list_editable = ("ativo",)


@admin.register(VinculoFuncional)
class VinculoFuncionalAdmin(SimpleHistoryAdmin):
    list_display = (
        "servidor",
        "cargo",
        "lotacao",
        "regime",
        "data_admissao",
        "salario_base",
        "ativo",
    )
    list_filter = ("regime", "ativo")
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
