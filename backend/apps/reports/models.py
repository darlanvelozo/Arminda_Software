"""
Modelos do app reports (TENANT_APPS).

Vivem dentro do schema de cada municipio. Sem FK explicita para Municipio.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models


class TipoRelatorio(models.TextChoices):
    HOLERITE = "holerite", "Holerite"
    RESUMO_FOLHA = "resumo_folha", "Resumo da folha"
    FICHA_FINANCEIRA = "ficha_financeira", "Ficha financeira"
    INFORME_RENDIMENTOS = "informe_rendimentos", "Informe de rendimentos"
    ESOCIAL = "esocial", "eSocial"
    SEFIP = "sefip", "SEFIP"
    IMPORT_FIORILLI = "import_fiorilli", "Importacao Fiorilli"
    OUTRO = "outro", "Outro"


class RelatorioGerado(models.Model):
    """Registro de relatorio gerado pelo sistema."""

    tipo = models.CharField(max_length=30, choices=TipoRelatorio.choices)
    titulo = models.CharField(max_length=200)
    competencia = models.DateField(null=True, blank=True)
    arquivo = models.FileField(upload_to="relatorios/%Y/%m/", null=True, blank=True)
    gerado_em = models.DateTimeField(auto_now_add=True)
    gerado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-gerado_em"]
        verbose_name = "relatorio gerado"
        verbose_name_plural = "relatorios gerados"

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} - {self.titulo}"
