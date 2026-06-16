"""
Modelos do app payroll (TENANT_APPS).

Vivem dentro do schema de cada municipio. Sem FK explicita para Municipio.
DSL de calculo (campo formula) e implementada no Bloco 2.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db import models

from apps.core.models import TimeStampedModel
from apps.people.models import Regime, Servidor, VinculoFuncional


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
    LICENCA_PREMIO = "licenca_premio", "Licença-prêmio (indenização)"
    COMPLEMENTAR = "complementar", "Complementar"


class StatusFolha(models.TextChoices):
    ABERTA = "aberta", "Aberta"
    CALCULADA = "calculada", "Calculada"
    CONFERIDA = "conferida", "Conferida"
    FECHADA = "fechada", "Fechada"


def _default_tipos_folha() -> list[str]:
    """Por padrão, a rubrica vale apenas para a folha mensal (Onda 3.1)."""
    return [TipoFolha.MENSAL]


class Rubrica(TimeStampedModel):
    """Rubrica da folha (provento ou desconto). DSL no campo `formula` (Bloco 2)."""

    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=15, choices=TipoRubrica.choices)
    tipos_folha = models.JSONField(
        "Tipos de folha",
        default=_default_tipos_folha,
        help_text=(
            "Tipos de folha em que esta rubrica é aplicada (valores de TipoFolha). "
            "Ex.: ['mensal'] ou ['13_segunda']. — Onda 3.1."
        ),
    )
    incide_inss = models.BooleanField("Incide INSS", default=False)
    incide_irrf = models.BooleanField("Incide IRRF", default=False)
    incide_fgts = models.BooleanField("Incide FGTS", default=False)
    incide_rpps = models.BooleanField(
        "Incide RPPS",
        default=False,
        help_text="Compõe a base da previdência municipal própria (Onda 2.4).",
    )
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
    folha_origem = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complementares",
        help_text=(
            "Folha mensal de origem (apenas para folhas complementares). "
            "Rastreabilidade hoje; base do modo acumulado no futuro — ADR-0019."
        ),
    )

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


class FeriasItem(TimeStampedModel):
    """
    Programação de férias de um vínculo numa folha de férias (Onda 3.3).

    O operador adiciona um item por servidor que sai de férias, com os dias de
    gozo e os dias vendidos (abono pecuniário). O engine calcula a folha de
    férias a partir destes itens (ver ADR-0017).
    """

    folha = models.ForeignKey(Folha, on_delete=models.CASCADE, related_name="ferias_itens")
    vinculo = models.ForeignKey(
        VinculoFuncional, on_delete=models.PROTECT, related_name="ferias_itens"
    )
    dias_gozo = models.PositiveSmallIntegerField(
        default=30, help_text="Dias de férias gozados (salário de férias + 1/3)."
    )
    dias_abono = models.PositiveSmallIntegerField(
        default=0, help_text="Dias vendidos (abono pecuniário) — até 10."
    )
    data_inicio = models.DateField(null=True, blank=True, help_text="Início do gozo (opcional).")

    class Meta:
        ordering = ["vinculo__servidor__nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["folha", "vinculo"], name="ferias_item_unico_por_folha_vinculo"
            ),
        ]
        verbose_name = "item de férias"
        verbose_name_plural = "itens de férias"

    def __str__(self) -> str:
        return f"{self.vinculo.servidor.nome}: {self.dias_gozo}d gozo + {self.dias_abono}d abono"


class LicencaPremioItem(TimeStampedModel):
    """
    Programação de indenização de licença-prêmio de um vínculo numa folha
    de licença-prêmio (Onda 3.4 — ADR-0018). Verba indenizatória.
    """

    folha = models.ForeignKey(Folha, on_delete=models.CASCADE, related_name="lp_itens")
    vinculo = models.ForeignKey(
        VinculoFuncional, on_delete=models.PROTECT, related_name="lp_itens"
    )
    meses = models.PositiveSmallIntegerField(default=0, help_text="Meses de licença-prêmio indenizados.")
    dias = models.PositiveSmallIntegerField(default=0, help_text="Dias adicionais indenizados (0-29).")

    class Meta:
        ordering = ["vinculo__servidor__nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["folha", "vinculo"], name="lp_item_unico_por_folha_vinculo"
            ),
        ]
        verbose_name = "item de licença-prêmio"
        verbose_name_plural = "itens de licença-prêmio"

    def __str__(self) -> str:
        return f"{self.vinculo.servidor.nome}: {self.meses}m + {self.dias}d"


class ComplementarItem(TimeStampedModel):
    """
    Lançamento explícito de uma folha complementar (Onda 3.5 — ADR-0019).

    O operador escolhe o servidor, a rubrica (provento ou desconto) e informa
    o valor à mão. O engine materializa cada item como `Lancamento` sem rodar
    fórmulas e sem incidência automática (ver ADR-0019).
    """

    folha = models.ForeignKey(
        Folha, on_delete=models.CASCADE, related_name="complementar_itens"
    )
    vinculo = models.ForeignKey(
        VinculoFuncional, on_delete=models.PROTECT, related_name="complementar_itens"
    )
    rubrica = models.ForeignKey(
        Rubrica, on_delete=models.PROTECT, related_name="complementar_itens"
    )
    valor = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Valor explícito do lançamento (> 0)."
    )

    class Meta:
        ordering = ["vinculo__servidor__nome", "rubrica__codigo"]
        constraints = [
            models.UniqueConstraint(
                fields=["folha", "vinculo", "rubrica"],
                name="complementar_item_unico_por_folha_vinculo_rubrica",
            ),
        ]
        verbose_name = "item complementar"
        verbose_name_plural = "itens complementares"

    def __str__(self) -> str:
        return f"{self.vinculo.servidor.nome} | {self.rubrica.codigo}: R$ {self.valor}"


class ModoContribuicaoRPPS(models.TextChoices):
    FLAT = "flat", "Alíquota única"
    PROGRESSIVO = "progressivo", "Tabela progressiva (EC 103)"


# Regimes de vínculo que, por padrão, contribuem ao regime próprio (RPPS).
# Municípios podem ajustar via `RegimePrevidenciario.regimes_aplicaveis`.
REGIMES_RPPS_PADRAO = [Regime.ESTATUTARIO]


class RegimePrevidenciario(TimeStampedModel):
    """
    Configuração do regime próprio de previdência (RPPS/IPM) do município
    — Onda 2.4 (ADR-0013).

    Vive no schema do tenant (TENANT_APP): as alíquotas são municipais e
    não podem vazar entre municípios. Versionado por competência igual à
    `TabelaLegal` federal: resolve-se a config com `vigencia_inicio <=
    competencia` e (`vigencia_fim is null` ou `vigencia_fim >= competencia`).

    A contribuição do servidor pode ser:
    - `flat`: percentual único (`aliquota_servidor`) sobre a base (com teto).
    - `progressivo`: faixas (`faixas`) com alíquota efetiva por faixa, estilo
      INSS pós-EC 103/2019.

    A contribuição patronal é exposta às fórmulas via `ALIQ_RPPS_PATRONAL`.
    """

    nome = models.CharField(
        max_length=200,
        help_text="Nome do regime/instituto (ex.: 'IPM - Instituto de Previdência Municipal').",
    )
    orgao_emissor = models.ForeignKey(
        "people.OrgaoEmissor",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="regimes_previdenciarios",
        help_text="Entidade (CNPJ) gestora do RPPS, quando aplicável.",
    )
    modo_contribuicao = models.CharField(
        max_length=15,
        choices=ModoContribuicaoRPPS.choices,
        default=ModoContribuicaoRPPS.FLAT,
    )
    aliquota_servidor = models.DecimalField(
        "Alíquota do servidor",
        max_digits=6,
        decimal_places=4,
        default=Decimal("0.14"),
        help_text="Usada no modo 'flat' (ex.: 0.14 = 14%). Ignorada no progressivo.",
    )
    aliquota_patronal = models.DecimalField(
        "Alíquota patronal",
        max_digits=6,
        decimal_places=4,
        default=Decimal("0.22"),
        help_text="Contribuição do ente (ex.: 0.22 = 22%). Exposta como ALIQ_RPPS_PATRONAL.",
    )
    teto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Teto da base de contribuição (null = sem teto).",
    )
    faixas = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "Faixas progressivas (modo 'progressivo'): "
            '[{"ate": "1518.00", "aliquota": "0.075"}, {"ate": null, "aliquota": "0.14"}]'
        ),
    )
    regimes_aplicaveis = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "Regimes de vínculo cobertos pelo RPPS (valores de people.Regime). "
            "Vazio = usa o padrão (apenas efetivos/estatutários)."
        ),
    )
    vigencia_inicio = models.DateField(help_text="Primeiro dia em que esta config vigora.")
    vigencia_fim = models.DateField(
        null=True,
        blank=True,
        help_text="Último dia de vigência (null = continua valendo).",
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["-vigencia_inicio"]
        constraints = [
            models.UniqueConstraint(
                fields=["vigencia_inicio"],
                name="rpps_unico_por_vigencia_inicio",
            ),
        ]
        verbose_name = "regime previdenciário (RPPS)"
        verbose_name_plural = "regimes previdenciários (RPPS)"

    def __str__(self) -> str:
        return f"{self.nome} (desde {self.vigencia_inicio:%m/%Y})"

    @property
    def regimes_efetivos(self) -> list[str]:
        """Regimes cobertos — cai no padrão quando não configurado."""
        return list(self.regimes_aplicaveis) if self.regimes_aplicaveis else list(REGIMES_RPPS_PADRAO)

    def como_config(self) -> dict[str, Any]:
        """Serializa a config para o dicionário consumido por FAIXA_RPPS
        (ver `apps.calculo.previdencia.contribuicao_rpps`)."""
        return {
            "modo": self.modo_contribuicao,
            "aliquota_servidor": self.aliquota_servidor,
            "aliquota_patronal": self.aliquota_patronal,
            "teto": self.teto,
            "faixas": list(self.faixas or []),
        }
