"""
Serializers customizados para autenticacao JWT (ADR-0007).

Adiciona claims `municipios` e `is_staff_arminda` no payload do access token,
e enriquece a resposta de login com dados do usuario.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.core.models import User, UsuarioMunicipioPapel


class UserMeSerializer(serializers.ModelSerializer):
    """Representacao do usuario autenticado, com seus papeis nos municipios."""

    municipios = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "nome_completo",
            "first_name",
            "last_name",
            "is_staff",
            "is_superuser",
            "precisa_trocar_senha",
            "municipios",
        ]
        read_only_fields = fields

    def get_municipios(self, user: User) -> list[dict[str, Any]]:
        papeis = (
            UsuarioMunicipioPapel.objects.filter(usuario=user)
            .select_related("municipio", "grupo")
            .order_by("municipio__nome", "grupo__name")
        )
        return [
            {
                "schema": p.municipio.schema_name,
                "codigo_ibge": p.municipio.codigo_ibge,
                "nome": p.municipio.nome,
                "uf": p.municipio.uf,
                "papel": p.grupo.name,
            }
            for p in papeis
        ]


class ArmindaTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Login: gera tokens com claims customizadas e retorna dados do usuario."""

    username_field = User.USERNAME_FIELD  # email

    @classmethod
    def get_token(cls, user: User):
        token = super().get_token(user)
        token["email"] = user.email
        token["is_staff_arminda"] = user.groups.filter(name="staff_arminda").exists()
        token["municipios"] = [
            {"schema": p.municipio.schema_name, "papel": p.grupo.name}
            for p in UsuarioMunicipioPapel.objects.filter(usuario=user).select_related(
                "municipio", "grupo"
            )
        ]
        return token

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        data = super().validate(attrs)
        data["user"] = UserMeSerializer(self.user).data
        return data


# ============================================================
# Edição do próprio perfil (Onda 1.5)
# ============================================================


class UserMeUpdateSerializer(serializers.ModelSerializer):
    """PATCH /api/auth/me/ — campos editáveis pelo próprio usuário."""

    class Meta:
        model = User
        fields = ["nome_completo"]

    def validate_nome_completo(self, value: str) -> str:
        valor = (value or "").strip()
        if len(valor) < 2:
            raise serializers.ValidationError("Nome muito curto.")
        return valor[:200]


class ChangePasswordSerializer(serializers.Serializer):
    """POST /api/auth/change-password/ — troca de senha do próprio usuário."""

    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    new_password_confirm = serializers.CharField(write_only=True, required=True)

    def validate_current_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                "Senha atual incorreta.",
                code="SENHA_ATUAL_INCORRETA",
            )
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "As senhas não conferem."},
                code="SENHAS_NAO_CONFEREM",
            )
        if attrs["new_password"] == attrs["current_password"]:
            raise serializers.ValidationError(
                {"new_password": "Nova senha deve ser diferente da atual."},
                code="NOVA_SENHA_IGUAL_ATUAL",
            )
        # Validators do Django (mínimo, similaridade, etc.)
        user = self.context["request"].user
        try:
            validate_password(attrs["new_password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {"new_password": exc.messages},
                code="SENHA_FRACA",
            ) from exc
        return attrs

    def save(self) -> User:
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.precisa_trocar_senha = False
        user.save(update_fields=["password", "precisa_trocar_senha"])
        return user
