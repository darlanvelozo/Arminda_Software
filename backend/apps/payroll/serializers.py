"""
Serializers do app payroll (Bloco 1.2 — Onda 3).

Apenas Rubrica esqueleto neste momento. DSL de calculo (campo `formula`)
sera implementada no Bloco 2.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.payroll.models import Rubrica


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
