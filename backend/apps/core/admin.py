"""Admin do app core (schema public)."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import ConfiguracaoGlobal, Domain, Municipio, User, UsuarioMunicipioPapel

admin.site.site_header = "Arminda — Administracao"
admin.site.site_title = "Arminda Admin"
admin.site.index_title = "Painel de administracao"


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Admin do User customizado (login por e-mail)."""

    ordering = ("email",)
    list_display = (
        "email",
        "nome_completo",
        "is_active",
        "is_staff",
        "is_superuser",
        "precisa_trocar_senha",
        "last_login",
    )
    list_filter = ("is_active", "is_staff", "is_superuser", "groups")
    search_fields = ("email", "nome_completo", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Dados pessoais",
            {"fields": ("nome_completo", "first_name", "last_name")},
        ),
        (
            "Permissoes",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Seguranca",
            {"fields": ("precisa_trocar_senha", "last_login", "date_joined")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_superuser"),
            },
        ),
    )
    readonly_fields = ("last_login", "date_joined")


@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ("nome", "uf", "codigo_ibge", "schema_name", "ativo", "data_adesao")
    list_filter = ("uf", "ativo")
    search_fields = ("nome", "codigo_ibge", "schema_name")
    list_editable = ("ativo",)
    readonly_fields = ("criado_em", "atualizado_em")


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("domain", "tenant", "is_primary")
    list_filter = ("is_primary",)
    search_fields = ("domain",)


@admin.register(UsuarioMunicipioPapel)
class UsuarioMunicipioPapelAdmin(admin.ModelAdmin):
    list_display = ("usuario", "municipio", "grupo", "criado_em")
    list_filter = ("grupo", "municipio")
    search_fields = ("usuario__email", "municipio__nome")
    raw_id_fields = ("usuario", "municipio")
    autocomplete_fields = ("grupo",)


@admin.register(ConfiguracaoGlobal)
class ConfiguracaoGlobalAdmin(admin.ModelAdmin):
    list_display = ("chave", "descricao")
    search_fields = ("chave", "descricao")
