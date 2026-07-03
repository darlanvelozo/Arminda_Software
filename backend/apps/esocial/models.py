"""
Modelos do eSocial (Onda 4.1 — ADR-0020).

`EventoESocial` é genérico: uma linha por evento gerado, discriminado por
`tipo`. O serviço (`apps.esocial.services`) sabe montar o XML de cada tipo.
Eventos são gerados por órgão emissor (CNPJ próprio), não por município.
"""

from __future__ import annotations

from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import TimeStampedModel
from apps.people.models import OrgaoEmissor


class TipoEvento(models.TextChoices):
    S_1000 = "S-1000", "S-1000 — Informações do empregador"
    S_1005 = "S-1005", "S-1005 — Tabela de estabelecimentos"
    S_1010 = "S-1010", "S-1010 — Tabela de rubricas"


class StatusEvento(models.TextChoices):
    GERADO = "gerado", "Gerado"
    VALIDADO = "validado", "Validado (XSD)"
    ASSINADO = "assinado", "Assinado"
    ENVIADO = "enviado", "Enviado"
    PROCESSADO = "processado", "Processado"
    REJEITADO = "rejeitado", "Rejeitado"


class EventoESocial(TimeStampedModel):
    """Evento do eSocial gerado para um órgão emissor."""

    tipo = models.CharField(max_length=10, choices=TipoEvento.choices)
    orgao_emissor = models.ForeignKey(
        OrgaoEmissor, on_delete=models.PROTECT, related_name="eventos_esocial"
    )
    # Sujeito do evento quando aplicável (ex.: S-1010 é por rubrica). Eventos de
    # tabela do empregador (S-1000/S-1005) não usam. Vínculo/folha entram nos
    # eventos periódicos (ondas seguintes).
    rubrica = models.ForeignKey(
        "payroll.Rubrica", on_delete=models.PROTECT, null=True, blank=True,
        related_name="eventos_esocial",
    )
    id_evento = models.CharField(
        "ID do evento", max_length=36, unique=True,
        help_text="ID único do eSocial (ID + inscrição + timestamp + sequencial).",
    )
    versao_layout = models.CharField(max_length=20, default="S_01_03_00")
    xml = models.TextField(blank=True)
    status = models.CharField(
        max_length=15, choices=StatusEvento.choices, default=StatusEvento.GERADO
    )
    lote = models.CharField(max_length=40, blank=True)
    retorno = models.JSONField(null=True, blank=True)

    history = HistoricalRecords(excluded_fields=["atualizado_em"])

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "evento eSocial"
        verbose_name_plural = "eventos eSocial"

    def __str__(self) -> str:
        return f"{self.tipo} · {self.orgao_emissor.cnpj} · {self.get_status_display()}"
