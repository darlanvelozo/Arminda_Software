"""
App: payroll

Rubricas, folha de pagamento, lançamentos, engine de cálculo e holerites.
"""

from django.apps import AppConfig


class PayrollConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.payroll"
    verbose_name = "Folha"
