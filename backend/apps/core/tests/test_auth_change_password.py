"""
Testes do POST /api/auth/change-password/ e PATCH /api/auth/me/ (Onda 1.5).
"""

from __future__ import annotations

import pytest


@pytest.mark.django_db
class TestChangePassword:
    def test_troca_senha_com_credenciais_corretas(
        self, api_client_factory, usuario_factory
    ):
        user = usuario_factory(email="rh@arminda.test", password="senha-atual-1")
        client = api_client_factory(user=user)
        response = client.post(
            "/api/auth/change-password/",
            {
                "current_password": "senha-atual-1",
                "new_password": "nova-senha-456",
                "new_password_confirm": "nova-senha-456",
            },
            format="json",
        )
        assert response.status_code == 204

        user.refresh_from_db()
        assert user.check_password("nova-senha-456")
        assert user.precisa_trocar_senha is False

    def test_troca_falha_se_senha_atual_incorreta(
        self, api_client_factory, usuario_factory
    ):
        user = usuario_factory(email="rh@arminda.test", password="senha-atual-1")
        client = api_client_factory(user=user)
        response = client.post(
            "/api/auth/change-password/",
            {
                "current_password": "ERRADA",
                "new_password": "nova-senha-456",
                "new_password_confirm": "nova-senha-456",
            },
            format="json",
        )
        assert response.status_code == 400
        body = response.json()
        assert "current_password" in body or "Senha atual" in str(body)

    def test_troca_falha_se_confirmacao_nao_bate(
        self, api_client_factory, usuario_factory
    ):
        user = usuario_factory(email="rh@arminda.test", password="senha-atual-1")
        client = api_client_factory(user=user)
        response = client.post(
            "/api/auth/change-password/",
            {
                "current_password": "senha-atual-1",
                "new_password": "nova-senha-456",
                "new_password_confirm": "outra-coisa",
            },
            format="json",
        )
        assert response.status_code == 400

    def test_troca_falha_se_nova_igual_atual(
        self, api_client_factory, usuario_factory
    ):
        user = usuario_factory(email="rh@arminda.test", password="igual-igual-1")
        client = api_client_factory(user=user)
        response = client.post(
            "/api/auth/change-password/",
            {
                "current_password": "igual-igual-1",
                "new_password": "igual-igual-1",
                "new_password_confirm": "igual-igual-1",
            },
            format="json",
        )
        assert response.status_code == 400

    def test_troca_falha_se_senha_muito_curta(
        self, api_client_factory, usuario_factory
    ):
        user = usuario_factory(email="rh@arminda.test", password="senha-atual-1")
        client = api_client_factory(user=user)
        response = client.post(
            "/api/auth/change-password/",
            {
                "current_password": "senha-atual-1",
                "new_password": "abc",
                "new_password_confirm": "abc",
            },
            format="json",
        )
        assert response.status_code == 400

    def test_endpoint_exige_autenticacao(self, api_client):
        response = api_client.post(
            "/api/auth/change-password/",
            {"current_password": "x", "new_password": "y", "new_password_confirm": "y"},
            format="json",
        )
        assert response.status_code == 401


@pytest.mark.django_db
class TestPatchMe:
    def test_atualiza_nome_completo(self, api_client_factory, usuario_factory):
        user = usuario_factory(email="ana@arminda.test", nome_completo="Ana Velha")
        client = api_client_factory(user=user)
        response = client.patch(
            "/api/auth/me/",
            {"nome_completo": "Ana Maria da Silva"},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["nome_completo"] == "Ana Maria da Silva"

        user.refresh_from_db()
        assert user.nome_completo == "Ana Maria da Silva"

    def test_nao_permite_mudar_email(self, api_client_factory, usuario_factory):
        user = usuario_factory(email="ana@arminda.test")
        client = api_client_factory(user=user)
        client.patch(
            "/api/auth/me/",
            {"email": "outro@arminda.test"},
            format="json",
        )
        user.refresh_from_db()
        assert user.email == "ana@arminda.test"  # email não foi alterado

    def test_nome_muito_curto_falha(self, api_client_factory, usuario_factory):
        user = usuario_factory(email="ana@arminda.test", nome_completo="Ana")
        client = api_client_factory(user=user)
        response = client.patch(
            "/api/auth/me/",
            {"nome_completo": "A"},
            format="json",
        )
        assert response.status_code == 400
