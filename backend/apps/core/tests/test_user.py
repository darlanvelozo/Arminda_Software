"""
Testes do User customizado (ADR-0005).
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_cria_usuario_com_email(self):
        user = User.objects.create_user(email="ana@arminda.test", password="senha-123")
        assert user.email == "ana@arminda.test"
        assert user.check_password("senha-123")
        assert not user.is_staff
        assert not user.is_superuser

    def test_email_e_obrigatorio(self):
        with pytest.raises(ValueError, match="E-mail"):
            User.objects.create_user(email="", password="x")

    def test_cria_superuser(self):
        user = User.objects.create_superuser(email="root@arminda.test", password="senha-segura")
        assert user.is_staff is True
        assert user.is_superuser is True

    def test_email_e_unique(self):
        from django.db import IntegrityError

        User.objects.create_user(email="dup@arminda.test", password="x")
        with pytest.raises(IntegrityError):
            User.objects.create_user(email="dup@arminda.test", password="y")

    def test_normaliza_email(self):
        user = User.objects.create_user(email="ANA@ARMINDA.TEST", password="x")
        # parte local preservada (caso pode ser sensivel); dominio em lower
        assert user.email.endswith("@arminda.test")

    def test_username_field_e_email(self):
        assert User.USERNAME_FIELD == "email"

    def test_str_retorna_email(self):
        user = User(email="x@y.test")
        assert str(user) == "x@y.test"

    def test_precisa_trocar_senha_default_false(self):
        user = User.objects.create_user(email="z@y.test", password="x")
        assert user.precisa_trocar_senha is False
