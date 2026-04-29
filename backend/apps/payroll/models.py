"""
Modelos do app payroll (TENANT_APPS).

Vivem dentro do schema de cada municipio. Sem FK explicita para Municipio.
DSL de calculo (campo formula) e implementada no Bloco 2.
"""

from __future__ import annotations

from django.db import models

from apps.core.models import TimeStampedModel
from apps.people.models import Servidor, VinculoFuncional


class TipoRubrica(models.TextChoices):
    PROVENTO = "provento", "Provento"
    DESCONTO = "desconto", "Desconto"
    INFORMATIVA = "informativa", "Informativa"


class TipoFolha(models.TextChoices):
    MENSAL = "mensal", "Mensal"
    DECIMO_PRIMEIRO = "13_primeira", "13o - 1a parcela"
    DECIMO_SEGUNDO = "13_segunda", "13o - 2a parcela"
    FERIAS = "ferias", "Ferias"
    RESCISAO = "rescisao", "Rescisao"
    COMPLEMENTAR = "complementar", "Complementar"


class StatusFolha(models.TextChoices):
    ABERTA = "aberta", "Aberta"
    CALCULADA = "calculada", "Calculada"
    CONFERIDA = "conferida", "Conferida"
    FECHADA = "fechada", "Fechada"


class Rubrica(TimeStampedModel):
    """Rubrica da folha (provento ou desconto). DSL no campo `formula` (Bloco 2)."""

    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=15, choices=TipoRubrica.choices)
    incide_inss = models.BooleanField("Incide INSS", default=False)
    incide_irrf = models.BooleanField("Incide IRRF", default=False)
    incide_fgts = models.BooleanField("Incide FGTS", default=False)
    formula = models.TextField(
        "Formula de calculo",
        blank=True,
        help_text="DSL de calculo (sera implementada no Bloco 2)",
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["codigo"]
        verbose_name = "rubrica"
        verbose_name_plural = "rubricas"

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nome} ({self.get_tipo_display()})"


class Folha(TimeStampedModel):
    """Folha de pagamento mensal."""

    competencia = models.DateField(help_text="Primeiro dia do mes de referencia")
    tipo = models.CharField(max_length=20, choices=TipoFolha.choices, default=TipoFolha.MENSAL)
    status = models.CharField(
        max_length=20, choices=StatusFolha.choices, default=StatusFolha.ABERTA
    )
    total_proventos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_descontos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_liquido = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ["-competencia"]
        constraints = [
            models.UniqueConstraint(
                fields=["competencia", "tipo"],
                name="folha_unica_por_competencia_tipo",
            ),
        ]
        verbose_name = "folha"
        verbose_name_plural = "folhas"

    def __str__(self) -> str:
        return (
            f"{self.get_tipo_display()} - {self.competencia:%m/%Y} "
            f"({self.get_status_display()})"
        )


class Lancamento(TimeStampedModel):
    """Lancamento individual de um servidor numa folha."""

    folha = models.ForeignKey(Folha, on_delete=models.CASCADE, related_name="lancamentos")
    servidor = models.ForeignKey(Servidor, on_delete=models.PROTECT, related_name="lancamentos")
    vinculo = models.ForeignKey(
        VinculoFuncional, on_delete=models.PROTECT, related_name="lancamentos"
    )
    rubrica = models.ForeignKey(Rubrica, on_delete=models.PROTECT, related_name="lancamentos")
    referencia = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0,
        help_text="Quantidade, percentual ou dias",
    )
    valor = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["rubrica__codigo"]
        verbose_name = "lancamento"
        verbose_name_plural = "lancamentos"

    def __str__(self) -> str:
        return f"{self.servidor.nome} | {self.rubrica.nome}: R$ {self.valor}"
