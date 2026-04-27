"""
Modelos do app reports.

Relatorios consolidados e exportacoes.
"""

from django.conf import settings
from django.db import models

from apps.core.models import Municipio


class RelatorioGerado(models.Model):
    """Registro de relatorio gerado pelo sistema."""

    municipio = models.ForeignKey(
        Municipio, on_delete=models.CASCADE, related_name="relatorios"
    )
    tipo = models.CharField(
        max_length=30,
        choices=[
            ("holerite", "Holerite"),
            ("resumo_folha", "Resumo da folha"),
            ("ficha_financeira", "Ficha financeira"),
            ("informe_rendimentos", "Informe de rendimentos"),
            ("esocial", "eSocial"),
            ("sefip", "SEFIP"),
            ("outro", "Outro"),
        ],
    )
    titulo = models.CharField(max_length=200)
    competencia = models.DateField(null=True, blank=True)
    arquivo = models.FileField(upload_to="relatorios/%Y/%m/", null=True, blank=True)
    gerado_em = models.DateTimeField(auto_now_add=True)
    gerado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )

    class Meta:
        ordering = ["-gerado_em"]
        verbose_name = "relatorio gerado"
        verbose_name_plural = "relatorios gerados"

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.titulo}"
