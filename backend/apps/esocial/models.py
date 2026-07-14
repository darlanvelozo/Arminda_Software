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
    S_1200 = "S-1200", "S-1200 — Remuneração (RGPS)"
    S_1202 = "S-1202", "S-1202 — Remuneração de servidor (RPPS)"
    S_1210 = "S-1210", "S-1210 — Pagamentos"


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
    # Eventos periódicos (S-1200/S-1202/S-1210 — Onda 4.5): folha + vínculo.
    folha = models.ForeignKey(
        "payroll.Folha", on_delete=models.PROTECT, null=True, blank=True,
        related_name="eventos_esocial",
    )
    vinculo = models.ForeignKey(
        "people.VinculoFuncional", on_delete=models.PROTECT, null=True, blank=True,
        related_name="eventos_esocial",
    )
    lote_envio = models.ForeignKey(
        "LoteESocial", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="eventos",
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


class GrupoLote(models.IntegerChoices):
    TABELAS = 1, "Eventos de tabela"
    NAO_PERIODICOS = 2, "Eventos não periódicos"
    PERIODICOS = 3, "Eventos periódicos"


class StatusLote(models.TextChoices):
    MONTADO = "montado", "Montado (validado)"
    ENVIADO = "enviado", "Enviado"
    PROCESSADO = "processado", "Processado"
    ERRO = "erro", "Erro"


class LoteESocial(TimeStampedModel):
    """Lote de envio ao webservice do eSocial (Onda 4.6 — ADR-0024)."""

    orgao_emissor = models.ForeignKey(
        OrgaoEmissor, on_delete=models.PROTECT, related_name="lotes_esocial"
    )
    grupo = models.IntegerField(choices=GrupoLote.choices)
    status = models.CharField(
        max_length=12, choices=StatusLote.choices, default=StatusLote.MONTADO
    )
    protocolo_envio = models.CharField(max_length=60, blank=True)
    xml_envio = models.TextField(blank=True)
    xml_retorno = models.TextField(blank=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "lote eSocial"
        verbose_name_plural = "lotes eSocial"

    def __str__(self) -> str:
        return f"Lote #{self.pk} · {self.get_grupo_display()} · {self.get_status_display()}"


class CertificadoDigital(TimeStampedModel):
    """
    Cofre do certificado e-CNPJ (A1) de um órgão emissor (Onda 4.2 — ADR-0022).

    O `.pfx` e a senha ficam **cifrados** (Fernet). Metadados em claro só para
    operação (validade, titular). Nunca expor `arquivo_cifrado`/`senha_cifrada`
    por API nem em log.
    """

    orgao_emissor = models.OneToOneField(
        OrgaoEmissor, on_delete=models.CASCADE, related_name="certificado"
    )
    arquivo_cifrado = models.TextField(help_text="PFX cifrado (Fernet). Nunca expor.")
    senha_cifrada = models.TextField(help_text="Senha do PFX cifrada (Fernet). Nunca expor.")
    titular = models.CharField(max_length=200, blank=True)
    cnpj = models.CharField("CNPJ do titular", max_length=18, blank=True)
    emissor = models.CharField("Autoridade certificadora", max_length=200, blank=True)
    validade_inicio = models.DateTimeField(null=True, blank=True)
    validade_fim = models.DateTimeField(null=True, blank=True)
    thumbprint = models.CharField("Impressão digital (SHA-1)", max_length=64, blank=True)

    class Meta:
        verbose_name = "certificado digital"
        verbose_name_plural = "certificados digitais"

    def __str__(self) -> str:
        return f"Certificado {self.titular or self.cnpj} (até {self.validade_fim:%d/%m/%Y})"
