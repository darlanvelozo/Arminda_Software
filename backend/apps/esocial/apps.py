"""
App: esocial

Geração e validação de eventos do eSocial (Bloco 4). Onda 4.1 cobre a
camada de geração de XML + validação contra XSD oficial (S-1.3); assinatura
e transmissão entram em ondas seguintes (ADR-0020).
"""

from django.apps import AppConfig


class EsocialConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.esocial"
    verbose_name = "eSocial"
