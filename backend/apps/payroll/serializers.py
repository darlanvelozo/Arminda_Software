"""
Serializers do app payroll.

- Rubrica (Bloco 1.2) — esqueleto.
- Folha + Lancamento (Bloco 2.2) — cálculo mensal.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.payroll.models import (
    FeriasItem,
    Folha,
    Lancamento,
    LicencaPremioItem,
    ModoContribuicaoRPPS,
    RegimePrevidenciario,
    Rubrica,
)
from apps.people.models import Regime


class RubricaListSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = Rubrica
        fields = ["id", "codigo", "nome", "tipo", "tipo_display", "ativo"]
        read_only_fields = fields


class RubricaDetailSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = Rubrica
        fields = [
            "id",
            "codigo",
            "nome",
            "tipo",
            "tipo_display",
            "tipos_folha",
            "incide_inss",
            "incide_irrf",
            "incide_fgts",
            "incide_rpps",
            "formula",
            "ativo",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["id", "criado_em", "atualizado_em", "tipo_display"]


class RubricaWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rubrica
        fields = [
            "id",
            "codigo",
            "nome",
            "tipo",
            "tipos_folha",
            "incide_inss",
            "incide_irrf",
            "incide_fgts",
            "incide_rpps",
            "formula",
            "ativo",
        ]
        read_only_fields = ["id"]

    def validate_codigo(self, value: str) -> str:
        valor = (value or "").strip().upper()
        if not valor:
            raise serializers.ValidationError("Codigo nao pode ser vazio.")
        return valor


# ============================================================
# Folha + Lancamento (Bloco 2.2)
# ============================================================


class FolhaListSerializer(serializers.ModelSerializer):
    """Listagem enxuta de folhas."""

    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    lancamentos_count = serializers.SerializerMethodField()

    class Meta:
        model = Folha
        fields = [
            "id",
            "competencia",
            "tipo",
            "tipo_display",
            "status",
            "status_display",
            "total_proventos",
            "total_descontos",
            "total_liquido",
            "lancamentos_count",
            "atualizado_em",
        ]
        read_only_fields = fields

    def get_lancamentos_count(self, obj: Folha) -> int:
        return obj.lancamentos.count()


class FolhaDetailSerializer(FolhaListSerializer):
    """Detalhe completo. Lançamentos consultados em endpoint separado para
    permitir paginação e filtros."""

    class Meta(FolhaListSerializer.Meta):
        fields = FolhaListSerializer.Meta.fields + ["observacoes", "criado_em"]
        read_only_fields = fields


class FolhaWriteSerializer(serializers.ModelSerializer):
    """Criar/editar folha (não calcula — `calcular` é action separada)."""

    class Meta:
        model = Folha
        fields = ["id", "competencia", "tipo", "observacoes"]
        read_only_fields = ["id"]


class RegimePrevidenciarioSerializer(serializers.ModelSerializer):
    """CRUD do regime próprio (RPPS) do município — Onda 2.4."""

    modo_contribuicao_display = serializers.CharField(
        source="get_modo_contribuicao_display", read_only=True
    )

    class Meta:
        model = RegimePrevidenciario
        fields = [
            "id",
            "nome",
            "orgao_emissor",
            "modo_contribuicao",
            "modo_contribuicao_display",
            "aliquota_servidor",
            "aliquota_patronal",
            "teto",
            "faixas",
            "regimes_aplicaveis",
            "vigencia_inicio",
            "vigencia_fim",
            "ativo",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["id", "criado_em", "atualizado_em", "modo_contribuicao_display"]

    def validate_regimes_aplicaveis(self, value: list) -> list:
        validos = set(Regime.values)
        invalidos = [v for v in (value or []) if v not in validos]
        if invalidos:
            raise serializers.ValidationError(
                f"Regimes inválidos: {', '.join(invalidos)}. "
                f"Use valores de people.Regime."
            )
        return value

    def validate_faixas(self, value: list) -> list:
        if not value:
            return value
        for i, f in enumerate(value):
            if not isinstance(f, dict) or "aliquota" not in f:
                raise serializers.ValidationError(
                    f"Faixa #{i + 1} precisa de 'aliquota' (e 'ate' ou null na última)."
                )
        if value[-1].get("ate") is not None:
            raise serializers.ValidationError(
                "A última faixa precisa ter 'ate': null (faixa aberta)."
            )
        return value

    def validate(self, attrs: dict) -> dict:
        modo = attrs.get("modo_contribuicao") or getattr(
            self.instance, "modo_contribuicao", None
        )
        faixas = attrs.get("faixas", getattr(self.instance, "faixas", None))
        if modo == ModoContribuicaoRPPS.PROGRESSIVO and not faixas:
            raise serializers.ValidationError(
                {"faixas": "Modo progressivo exige ao menos uma faixa."}
            )
        vig_inicio = attrs.get("vigencia_inicio") or getattr(
            self.instance, "vigencia_inicio", None
        )
        vig_fim = attrs.get("vigencia_fim", getattr(self.instance, "vigencia_fim", None))
        if vig_fim and vig_inicio and vig_fim < vig_inicio:
            raise serializers.ValidationError(
                {"vigencia_fim": "Fim da vigência não pode ser antes do início."}
            )
        return attrs


class FeriasItemSerializer(serializers.ModelSerializer):
    """Programação de férias de um vínculo numa folha (Onda 3.3)."""

    servidor_nome = serializers.CharField(source="vinculo.servidor.nome", read_only=True)
    servidor_matricula = serializers.CharField(
        source="vinculo.servidor.matricula", read_only=True
    )
    cargo = serializers.CharField(source="vinculo.cargo.nome", read_only=True)

    class Meta:
        model = FeriasItem
        fields = [
            "id",
            "folha",
            "vinculo",
            "servidor_nome",
            "servidor_matricula",
            "cargo",
            "dias_gozo",
            "dias_abono",
            "data_inicio",
        ]
        read_only_fields = ["id", "servidor_nome", "servidor_matricula", "cargo"]

    def validate_dias_abono(self, value: int) -> int:
        if value > 10:
            raise serializers.ValidationError("Abono pecuniário é de no máximo 10 dias.")
        return value


class LicencaPremioItemSerializer(serializers.ModelSerializer):
    """Programação de indenização de licença-prêmio numa folha (Onda 3.4)."""

    servidor_nome = serializers.CharField(source="vinculo.servidor.nome", read_only=True)
    servidor_matricula = serializers.CharField(
        source="vinculo.servidor.matricula", read_only=True
    )
    cargo = serializers.CharField(source="vinculo.cargo.nome", read_only=True)

    class Meta:
        model = LicencaPremioItem
        fields = [
            "id", "folha", "vinculo", "servidor_nome", "servidor_matricula",
            "cargo", "meses", "dias",
        ]
        read_only_fields = ["id", "servidor_nome", "servidor_matricula", "cargo"]

    def validate_dias(self, value: int) -> int:
        if value > 29:
            raise serializers.ValidationError("Dias adicionais é de no máximo 29 (use meses).")
        return value


class LancamentoSerializer(serializers.ModelSerializer):
    """Lançamento individual + dados básicos do servidor/rubrica."""

    servidor_matricula = serializers.CharField(
        source="servidor.matricula", read_only=True
    )
    servidor_nome = serializers.CharField(source="servidor.nome", read_only=True)
    rubrica_codigo = serializers.CharField(source="rubrica.codigo", read_only=True)
    rubrica_nome = serializers.CharField(source="rubrica.nome", read_only=True)
    rubrica_tipo = serializers.CharField(source="rubrica.tipo", read_only=True)

    class Meta:
        model = Lancamento
        fields = [
            "id",
            "folha",
            "servidor",
            "servidor_matricula",
            "servidor_nome",
            "vinculo",
            "rubrica",
            "rubrica_codigo",
            "rubrica_nome",
            "rubrica_tipo",
            "referencia",
            "valor",
        ]
        read_only_fields = fields
