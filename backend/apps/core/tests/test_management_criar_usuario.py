"""Testes do management command `criar_usuario` (Bloco 1.2 — Onda 3)."""

from __future__ import annotations

from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

User = get_user_model()


@pytest.mark.django_db
class TestCriarUsuarioBasico:
    def test_cria_usuario_simples(self):
        out = StringIO()
        call_command(
            "criar_usuario",
            "--email=joao@arminda.test",
            "--password=senha-segura-123",
            "--nome=Joao",
            stdout=out,
        )
        user = User.objects.get(email="joao@arminda.test")
        assert user.nome_completo == "Joao"
        assert user.check_password("senha-segura-123")
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.precisa_trocar_senha is False

    def test_cria_superuser(self):
        out = StringIO()
        call_command(
            "criar_usuario",
            "--email=root@arminda.test",
            "--password=senha-segura-123",
            "--superuser",
            stdout=out,
        )
        user = User.objects.get(email="root@arminda.test")
        assert user.is_superuser is True
        assert user.is_staff is True

    def test_email_duplicado_falha(self, usuario_factory):
        usuario_factory(email="dup@arminda.test", password="senha-segura-123")
        with pytest.raises(CommandError, match=r"(?i)ja existe"):
            call_command(
                "criar_usuario",
                "--email=dup@arminda.test",
                "--password=senha-segura-123",
            )

    def test_senha_curta_falha(self):
        with pytest.raises(CommandError, match="ao menos 8"):
            call_command(
                "criar_usuario",
                "--email=x@x.test",
                "--password=curta",
            )

    def test_precisa_trocar_senha_flag(self):
        call_command(
            "criar_usuario",
            "--email=trocar@arminda.test",
            "--password=senha-segura-123",
            "--precisa-trocar-senha",
            stdout=StringIO(),
        )
        user = User.objects.get(email="trocar@arminda.test")
        assert user.precisa_trocar_senha is True


@pytest.mark.django_db
class TestCriarUsuarioComPapel:
    def test_cria_usuario_com_papel_em_municipio(self, tenant_a):
        from apps.core.models import UsuarioMunicipioPapel

        out = StringIO()
        call_command(
            "criar_usuario",
            "--email=rh@x.test",
            "--password=senha-segura-123",
            f"--tenant={tenant_a.schema_name}",
            "--papel=rh_municipio",
            stdout=out,
        )
        user = User.objects.get(email="rh@x.test")
        papel = UsuarioMunicipioPapel.objects.get(usuario=user)
        assert papel.municipio_id == tenant_a.id
        assert papel.grupo.name == "rh_municipio"

    def test_papel_sem_tenant_falha(self):
        with pytest.raises(CommandError, match="tenant"):
            call_command(
                "criar_usuario",
                "--email=p@x.test",
                "--password=senha-segura-123",
                "--papel=rh_municipio",
            )

    def test_tenant_sem_papel_falha(self, tenant_a):
        with pytest.raises(CommandError, match="papel"):
            call_command(
                "criar_usuario",
                "--email=p@x.test",
                "--password=senha-segura-123",
                f"--tenant={tenant_a.schema_name}",
            )

    def test_tenant_inexistente_falha(self):
        with pytest.raises(CommandError, match="nao encontrado"):
            call_command(
                "criar_usuario",
                "--email=p@x.test",
                "--password=senha-segura-123",
                "--tenant=inexistente",
                "--papel=rh_municipio",
            )


@pytest.mark.django_db
class TestStaffArminda:
    def test_marca_staff_arminda(self):
        from django.contrib.auth.models import Group

        out = StringIO()
        call_command(
            "criar_usuario",
            "--email=staff@arminda.test",
            "--password=senha-segura-123",
            "--staff-arminda",
            stdout=out,
        )
        user = User.objects.get(email="staff@arminda.test")
        assert user.groups.filter(name="staff_arminda").exists()
        assert "staff Arminda" in out.getvalue()

        # Sanity: o grupo existe (foi seedado pelo Bloco 1.1)
        assert Group.objects.filter(name="staff_arminda").exists()
