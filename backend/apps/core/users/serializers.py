"""
Serializers para gestão de usuários do município (Onda 1.5).

O recurso exposto é `UsuarioMunicipioPapel` — uma associação User × Município ×
Group. Cada item da listagem representa "um usuário com seu papel no município
ativo" — abordagem que evita expor o modelo User diretamente.
"""

from __future__ import annotations

import secrets
from typing import Any

from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from apps.core.models import User, UsuarioMunicipioPapel
from apps.core.permissions import GRUPOS_BASE


class _UsuarioEmbutidoSerializer(serializers.ModelSerializer):
    """Read-only — exibe dados públicos do User dentro de cada papel."""

    class Meta:
        model = User
        fields = ["id", "email", "nome_completo", "is_active", "precisa_trocar_senha"]
        read_only_fields = fields


class UsuarioMunicipioPapelListSerializer(serializers.ModelSerializer):
    """GET /api/core/usuarios/ — lista de papéis no tenant ativo."""

    usuario = _UsuarioEmbutidoSerializer(read_only=True)
    papel = serializers.CharField(source="grupo.name", read_only=True)

    class Meta:
        model = UsuarioMunicipioPapel
        fields = ["id", "usuario", "papel", "criado_em"]
        read_only_fields = fields


class UsuarioMunicipioPapelCreateSerializer(serializers.Serializer):
    """
    POST /api/core/usuarios/ — cria User + atribui papel no tenant ativo.

    Idempotência: se o e-mail já existe como User no public, reaproveita e
    apenas cria/atualiza o papel no tenant. Senha temporária só é setada
    quando o User é novo.
    """

    email = serializers.EmailField()
    nome_completo = serializers.CharField(max_length=200)
    papel = serializers.ChoiceField(choices=[(g, g) for g in GRUPOS_BASE])
    senha_temporaria = serializers.CharField(write_only=True, required=False)

    def validate_papel(self, value: str) -> str:
        # staff_arminda não pode ser atribuído via UI do município
        if value == "staff_arminda":
            raise serializers.ValidationError(
                "staff_arminda só pode ser atribuído via comando administrativo.",
                code="PAPEL_PROIBIDO",
            )
        return value

    def validate_senha_temporaria(self, value: str) -> str:
        if value:
            try:
                validate_password(value)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(exc.messages, code="SENHA_FRACA") from exc
        return value

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> UsuarioMunicipioPapel:
        from django_tenants.utils import schema_context

        request = self.context["request"]
        municipio = request.tenant
        if municipio is None or getattr(municipio, "schema_name", None) == "public":
            raise serializers.ValidationError(
                "Município ativo não foi resolvido. Envie o cabeçalho X-Tenant.",
                code="TENANT_AUSENTE",
            )

        email = validated_data["email"].lower().strip()
        nome_completo = validated_data["nome_completo"].strip()
        papel_nome = validated_data["papel"]
        senha = validated_data.get("senha_temporaria") or secrets.token_urlsafe(12)

        # User e Group vivem no schema public (SHARED_APPS)
        with schema_context("public"):
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "nome_completo": nome_completo,
                    "is_active": True,
                    "precisa_trocar_senha": True,
                },
            )
            if created:
                user.set_password(senha)
                user.save(update_fields=["password"])
            else:
                # User já existia; só atualiza o nome se vier preenchido e
                # não mexe em senha (não é admissão de novo usuário, é
                # extensão de papel para outro município)
                if nome_completo and not user.nome_completo:
                    user.nome_completo = nome_completo
                    user.save(update_fields=["nome_completo"])

            grupo = Group.objects.get(name=papel_nome)

            papel, _ = UsuarioMunicipioPapel.objects.update_or_create(
                usuario=user,
                municipio=municipio,
                defaults={"grupo": grupo},
            )

        return papel


class UsuarioMunicipioPapelUpdateSerializer(serializers.Serializer):
    """PATCH /api/core/usuarios/{id}/ — troca o papel do usuário no tenant."""

    papel = serializers.ChoiceField(choices=[(g, g) for g in GRUPOS_BASE])

    def validate_papel(self, value: str) -> str:
        if value == "staff_arminda":
            raise serializers.ValidationError(
                "staff_arminda só pode ser atribuído via comando administrativo.",
                code="PAPEL_PROIBIDO",
            )
        return value

    def update(
        self, instance: UsuarioMunicipioPapel, validated_data: dict[str, Any]
    ) -> UsuarioMunicipioPapel:
        from django_tenants.utils import schema_context

        with schema_context("public"):
            grupo = Group.objects.get(name=validated_data["papel"])
            instance.grupo = grupo
            instance.save(update_fields=["grupo"])
        return instance
