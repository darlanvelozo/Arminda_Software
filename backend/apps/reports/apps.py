"""
App: reports

Relatórios consolidados, dashboards, indicadores e BI.
"""

from django.apps import AppConfig


class ReportsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reports"
    verbose_name = "Relatórios"
