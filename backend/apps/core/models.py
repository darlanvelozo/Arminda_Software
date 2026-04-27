"""
Modelos do app core.

Tenant, configuracoes globais e modelo base auditado.
"""

from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """Modelo abstrato com campos de auditoria."""

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_criados",
    )
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_atualizados",
    )

    class Meta:
        abstract = True


class Municipio(TimeStampedModel):
    """Municipio/Tenant — cada prefeitura e um municipio isolado."""

    nome = models.CharField(max_length=200)
    codigo_ibge = models.CharField(max_length=7, unique=True)
    uf = models.CharField(max_length=2)
    ativo = models.BooleanField(default=True)
    data_adesao = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "municipio"
        verbose_name_plural = "municipios"

    def __str__(self):
        return f"{self.nome}/{self.uf}"


class ConfiguracaoGlobal(models.Model):
    """Configuracoes do sistema por chave-valor."""

    chave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    descricao = models.TextField(blank=True)

    class Meta:
        ordering = ["chave"]
        verbose_name = "configuracao global"
        verbose_name_plural = "configuracoes globais"

    def __str__(self):
        return self.chave
