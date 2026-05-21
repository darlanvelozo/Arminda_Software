"""
App: core

Tenant, autenticação, RBAC, configurações globais. Compartilhado entre todos os módulos.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"

    def ready(self) -> None:
        # Registra signals (invalidação de cache de tabelas legais)
        from . import signals  # noqa: F401
