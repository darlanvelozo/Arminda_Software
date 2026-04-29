"""
Testes do TenantHeaderOrHostMiddleware (ADR-0006).

Cobre:
- Rota publica passa sem tenant
- Header X-Tenant valido resolve tenant
- Header X-Tenant invalido retorna 400
- Falta de header em rota tenant cai no fallback (subdominio) ou erro
"""

from __future__ import annotations

import pytest


@pytest.mark.django_db
class TestRotasPublicas:
    """Rotas em PUBLIC_PATH_PREFIXES rodam sem tenant resolvido."""

    def test_health_passa_sem_tenant(self, api_client):
        response = api_client.get("/health/")
        assert response.status_code == 200

    def test_status_passa_sem_tenant(self, api_client):
        response = api_client.get("/status/")
        assert response.status_code == 200

    def test_login_passa_sem_tenant(self, api_client):
        response = api_client.post(
            "/api/auth/login/",
            {"email": "fake@x.com", "password": "x"},
            format="json",
        )
        # 401 ou 400 sao validos (login falhou) — o que NAO pode e 400
        # com codigo TENANT_NAO_RESOLVIDO
        assert response.status_code in (400, 401)
        body = response.json()
        assert body.get("code") != "TENANT_NAO_RESOLVIDO"
        assert body.get("code") != "TENANT_NAO_ENCONTRADO"


@pytest.mark.django_db
class TestResolucaoPorHeader:
    def test_x_tenant_com_schema_name_resolve(self, api_client, tenant_a, usuario_admin_a):
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(usuario_admin_a).access_token
        response = api_client.get(
            "/api/auth/me/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_TENANT=tenant_a.schema_name,
        )
        assert response.status_code == 200

    def test_x_tenant_com_codigo_ibge_resolve(self, api_client, tenant_a, usuario_admin_a):
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(usuario_admin_a).access_token
        # Como ainda nao temos rota tenant funcional, validamos so a resolucao
        # via "/api/people/": 404 = tenant resolveu (404 do url dispatcher);
        # 400 com TENANT_NAO_ENCONTRADO = falhou no middleware.
        response = api_client.get(
            "/api/people/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_TENANT=tenant_a.codigo_ibge,
        )
        assert response.status_code == 404, (
            f"Esperava 404 (sem rota), recebeu {response.status_code}: " f"{response.content[:200]}"
        )

    def test_x_tenant_inexistente_retorna_400(self, api_client, usuario_admin_a):
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(usuario_admin_a).access_token
        response = api_client.get(
            "/api/people/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_TENANT="nao-existe",
        )
        assert response.status_code == 400
        body = response.json()
        assert body["code"] == "TENANT_NAO_ENCONTRADO"
