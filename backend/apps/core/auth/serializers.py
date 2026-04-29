"""
Serializers customizados para autenticacao JWT (ADR-0007).

Adiciona claims `municipios` e `is_staff_arminda` no payload do access token,
e enriquece a resposta de login com dados do usuario.
"""

from __future__ import annotations

from typing import Any

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
