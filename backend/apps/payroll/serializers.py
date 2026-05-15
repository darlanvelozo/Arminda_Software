"""
Serializers do app payroll.

- Rubrica (Bloco 1.2) — esqueleto.
- Folha + Lancamento (Bloco 2.2) — cálculo mensal.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.payroll.models import Folha, Lancamento, Rubrica


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
            "incide_inss",
            "incide_irrf",
            "incide_fgts",
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
            "incide_inss",
            "incide_irrf",
            "incide_fgts",
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
