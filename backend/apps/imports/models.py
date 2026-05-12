"""
Modelo de auditoria das importações de sistemas legados (Bloco 1.4).

Vive em TENANT_APPS — cada município tem seu próprio histórico.
"""

from __future__ import annotations

from django.db import models


class TipoEntidadeSip(models.TextChoices):
    CARGO = "cargo", "Cargo"
    LOTACAO = "lotacao", "Lotação"
    UNIDADE_ORCAMENTARIA = "unidade_orcamentaria", "Unidade orçamentária"
    SERVIDOR = "servidor", "Servidor"
    VINCULO = "vinculo", "Vínculo Funcional"
    DEPENDENTE = "dependente", "Dependente"
    RUBRICA = "rubrica", "Rubrica (evento)"


class StatusImportacao(models.TextChoices):
    OK = "ok", "OK"
    ERRO = "erro", "Erro"


class SipImportRecord(models.Model):
    """
    Rastreia uma linha SIP importada para Arminda.

    Chave única: (tipo, chave_sip). Re-importação atualiza o registro
    com novo `payload_sip_hash` se o conteúdo na origem mudou.
    """

    tipo = models.CharField(max_length=20, choices=TipoEntidadeSip.choices)
    chave_sip = models.CharField(
        max_length=120,
        help_text="Identificador estável na origem (ex.: '001-PROFE' para Cargo).",
    )
    arminda_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="PK do registro criado no Arminda. Null se status=erro.",
    )
    payload_sip_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="sha256 do dict bruto vindo do SIP — detecta drift na origem.",
    )
    status = models.CharField(
        max_length=10, choices=StatusImportacao.choices, default=StatusImportacao.OK
    )
    erro_mensagem = models.TextField(blank=True)

    importado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tipo", "chave_sip"],
                name="sip_import_unico_por_tipo_e_chave",
            ),
        ]
        indexes = [
            models.Index(fields=["tipo", "status"]),
        ]
        ordering = ["-importado_em"]
        verbose_name = "registro de importação SIP"
        verbose_name_plural = "registros de importação SIP"

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} · {self.chave_sip} · {self.get_status_display()}"
