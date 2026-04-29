"""
Serializers do app people (Bloco 1.2).

Padrao adotado: 3 serializers por modelo (List/Detail/Write).
- List   — campos enxutos para listagem.
- Detail — completo, para `retrieve`.
- Write  — para `create`/`update`, com validacao e normalizacao.

Validators de dominio brasileiro vivem em `apps.core.validators` e sao
chamados a partir dos `validate_<campo>` deste arquivo (HTTP boundary).
"""

from __future__ import annotations

from rest_framework import serializers

from apps.people.models import Cargo, Lotacao

# ============================================================
# Cargo
# ============================================================


class CargoListSerializer(serializers.ModelSerializer):
    """Versao enxuta para listagem."""

    nivel_escolaridade_display = serializers.CharField(
        source="get_nivel_escolaridade_display", read_only=True
    )

    class Meta:
        model = Cargo
        fields = [
            "id",
            "codigo",
            "nome",
            "nivel_escolaridade",
            "nivel_escolaridade_display",
            "ativo",
        ]
        read_only_fields = fields


class CargoDetailSerializer(serializers.ModelSerializer):
    """Versao completa para retrieve."""

    nivel_escolaridade_display = serializers.CharField(
        source="get_nivel_escolaridade_display", read_only=True
    )

    class Meta:
        model = Cargo
        fields = [
            "id",
            "codigo",
            "nome",
            "cbo",
            "nivel_escolaridade",
            "nivel_escolaridade_display",
            "ativo",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["id", "criado_em", "atualizado_em", "nivel_escolaridade_display"]


class CargoWriteSerializer(serializers.ModelSerializer):
    """Versao para create/update."""

    class Meta:
        model = Cargo
        fields = ["id", "codigo", "nome", "cbo", "nivel_escolaridade", "ativo"]
        read_only_fields = ["id"]

    def validate_codigo(self, value: str) -> str:
        valor = value.strip().upper()
        if not valor:
            raise serializers.ValidationError("Codigo nao pode ser vazio.")
        return valor

    def validate_cbo(self, value: str) -> str:
        # CBO e opcional no Bloco 1.2; validacao contra tabela so no Bloco 4
        return (value or "").strip()


# ============================================================
# Lotacao
# ============================================================


class LotacaoListSerializer(serializers.ModelSerializer):
    """Versao enxuta para listagem."""

    class Meta:
        model = Lotacao
        fields = ["id", "codigo", "nome", "sigla", "ativo"]
        read_only_fields = fields


class LotacaoDetailSerializer(serializers.ModelSerializer):
    """Versao completa com resumo do pai."""

    lotacao_pai_nome = serializers.CharField(
        source="lotacao_pai.nome", read_only=True, default=None
    )

    class Meta:
        model = Lotacao
        fields = [
            "id",
            "codigo",
            "nome",
            "sigla",
            "lotacao_pai",
            "lotacao_pai_nome",
            "ativo",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["id", "criado_em", "atualizado_em", "lotacao_pai_nome"]


class LotacaoWriteSerializer(serializers.ModelSerializer):
    """Versao para create/update."""

    class Meta:
        model = Lotacao
        fields = ["id", "codigo", "nome", "sigla", "lotacao_pai", "ativo"]
        read_only_fields = ["id"]

    def validate_codigo(self, value: str) -> str:
        valor = value.strip().upper()
        if not valor:
            raise serializers.ValidationError("Codigo nao pode ser vazio.")
        return valor

    def validate(self, attrs: dict) -> dict:
        # Impede ciclo: lotacao_pai != self
        instance = getattr(self, "instance", None)
        pai = attrs.get("lotacao_pai")
        if instance and pai and pai.pk == instance.pk:
            raise serializers.ValidationError(
                {"lotacao_pai": "Uma lotacao nao pode ser pai de si mesma."}
            )
        return attrs
