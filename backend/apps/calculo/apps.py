from django.apps import AppConfig


class CalculoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.calculo"
    label = "calculo"
    verbose_name = "Engine de cálculo de folha"
