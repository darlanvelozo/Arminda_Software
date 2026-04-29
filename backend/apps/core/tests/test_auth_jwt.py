"""
Testes dos endpoints JWT (ADR-0007).

Cobre:
- POST /api/auth/login/    (sucesso e falha)
- POST /api/auth/refresh/  (rotacao)
- POST /api/auth/logout/   (blacklist do refresh)
- GET  /api/auth/me/       (usuario autenticado + papeis)
- Claims customizadas no access token
"""

from __future__ import annotations

import pytest


@pytest.mark.django_db
class TestLogin:
    def test_login_com_credenciais_validas_retorna_tokens(
        self, api_client, usuario_factory, tenant_a
    ):
        usuario_factory(
            email="ana@arminda.test",
            password="senha-segura-123",
            papeis=[(tenant_a, "rh_municipio")],
        )
        response = api_client.post(
            "/api/auth/login/",
            {"email": "ana@arminda.test", "password": "senha-segura-123"},
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert "access" in data
        assert "refresh" in data
        assert data["user"]["email"] == "ana@arminda.test"
        # Papeis vem na resposta
        municipios = data["user"]["municipios"]
        assert len(municipios) == 1
        assert municipios[0]["schema"] == tenant_a.schema_name
        assert municipios[0]["papel"] == "rh_municipio"

    def test_login_com_senha_errada_retorna_401(self, api_client, usuario_factory):
        usuario_factory(email="x@x.test", password="certa")
        response = api_client.post(
            "/api/auth/login/",
            {"email": "x@x.test", "password": "errada"},
            format="json",
        )
        assert response.status_code == 401

    def test_login_com_email_inexistente_retorna_401(self, api_client):
        response = api_client.post(
            "/api/auth/login/",
            {"email": "ninguem@x.test", "password": "x"},
            format="json",
        )
        assert response.status_code == 401


@pytest.mark.django_db
class TestRefresh:
    def test_refresh_gera_novo_access(self, api_client, usuario_factory):
        usuario_factory(email="r@x.test", password="senha-segura-123")
        login = api_client.post(
            "/api/auth/login/",
            {"email": "r@x.test", "password": "senha-segura-123"},
            format="json",
        ).json()

        response = api_client.post(
            "/api/auth/refresh/",
            {"refresh": login["refresh"]},
            format="json",
        )
        assert response.status_code == 200
        assert "access" in response.json()


@pytest.mark.django_db
class TestLogout:
    def test_logout_blacklisteia_refresh(self, api_client, usuario_factory):
        usuario_factory(email="l@x.test", password="senha-segura-123")
        login = api_client.post(
            "/api/auth/login/",
            {"email": "l@x.test", "password": "senha-segura-123"},
            format="json",
        ).json()

        access = login["access"]
        refresh = login["refresh"]

        # logout
        response = api_client.post(
            "/api/auth/logout/",
            {"refresh": refresh},
            HTTP_AUTHORIZATION=f"Bearer {access}",
            format="json",
        )
        assert response.status_code == 204

        # tentar refresh com o token blacklistado deve falhar
        retry = api_client.post("/api/auth/refresh/", {"refresh": refresh}, format="json")
        assert retry.status_code == 401


@pytest.mark.django_db
class TestMe:
    def test_me_sem_token_retorna_401(self, api_client):
        response = api_client.get("/api/auth/me/")
        assert response.status_code == 401

    def test_me_com_token_retorna_usuario_e_papeis(
        self, api_client, usuario_factory, tenant_a, tenant_b
    ):
        user = usuario_factory(
            email="m@x.test",
            password="senha-segura-123",
            papeis=[
                (tenant_a, "rh_municipio"),
                (tenant_b, "leitura_municipio"),
            ],
        )
        login = api_client.post(
            "/api/auth/login/",
            {"email": "m@x.test", "password": "senha-segura-123"},
            format="json",
        ).json()

        response = api_client.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Bearer {login['access']}")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "m@x.test"
        assert data["id"] == user.id
        assert len(data["municipios"]) == 2
        papeis = {m["schema"]: m["papel"] for m in data["municipios"]}
        assert papeis[tenant_a.schema_name] == "rh_municipio"
        assert papeis[tenant_b.schema_name] == "leitura_municipio"


@pytest.mark.django_db
class TestClaimsCustomizadas:
    def test_access_token_carrega_email_e_papeis(self, api_client, usuario_factory, tenant_a):
        import jwt
        from django.conf import settings

        usuario_factory(
            email="claim@x.test",
            password="senha-segura-123",
            papeis=[(tenant_a, "admin_municipio")],
        )
        login = api_client.post(
            "/api/auth/login/",
            {"email": "claim@x.test", "password": "senha-segura-123"},
            format="json",
        ).json()

        # Decodifica o access token e checa as claims
        payload = jwt.decode(
            login["access"],
            settings.SIMPLE_JWT["SIGNING_KEY"],
            algorithms=[settings.SIMPLE_JWT["ALGORITHM"]],
        )
        assert payload["email"] == "claim@x.test"
        assert payload["is_staff_arminda"] is False
        assert any(
            m["schema"] == tenant_a.schema_name and m["papel"] == "admin_municipio"
            for m in payload["municipios"]
        )
