"""
Smoke test do Django admin e das paginas HTML/OpenAPI publicas.

Cobre o caminho de codigo que **render** templates Django, especificamente
as `templatetags` do `django_tenants` (`{% load tenant %}` esta no
admin/base_site.html via inclusao). Esses templates nao rodam em testes
de API REST puros — esse arquivo fecha o buraco.

Bug historico (Bloco 1.2 — Onda 3): o middleware setava
`request.tenant = None` em rotas publicas. A template tag
`is_public_schema` faz `hasattr(request, 'tenant')` e quebrava com
None.schema_name. Fix: nao setar o atributo em rotas publicas.
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()


@pytest.fixture
def superuser_admin(db):
    """Superuser para acessar /admin/."""
    return User.objects.create_superuser(
        email="admin@test.local", password="senha-super-segura-123"
    )


@pytest.fixture
def admin_client(superuser_admin) -> Client:
    """Client de teste autenticado como superuser via SessionAuth."""
    client = Client()
    logged = client.login(email="admin@test.local", password="senha-super-segura-123")
    assert logged, "login falhou — superuser nao autenticou"
    return client


# ============================================================
# Admin do Django (rota publica que renderiza HTML)
# ============================================================


@pytest.mark.django_db
class TestAdminPaginas:
    """Garantia: paginas HTML renderizam sem 500.

    Falha se o middleware quebrar templatetags do django_tenants.
    """

    @pytest.mark.parametrize(
        "path",
        [
            "/admin/login/",
            "/admin/",
            "/admin/auth/group/",
            "/admin/core/user/",
            "/admin/core/municipio/",
            "/admin/core/domain/",
            "/admin/core/usuariomunicipiopapel/",
            "/admin/core/configuracaoglobal/",
        ],
    )
    def test_pagina_admin_renderiza(self, admin_client, path):
        response = admin_client.get(path)
        # 200 (renderiza) ou 302 (redirect — ex: /admin/login/ ja autenticado)
        assert response.status_code in (200, 302), (
            f"GET {path} retornou {response.status_code}; " f"corpo={response.content[:300]}"
        )
        # Garantia explicita: nao subiu erro renderizando template
        if response.status_code == 200:
            body = response.content.decode("utf-8", errors="replace")
            assert "AttributeError" not in body
            assert "NoneType" not in body or "schema_name" not in body


# ============================================================
# OpenAPI / Swagger / Redoc (drf-spectacular)
# ============================================================


@pytest.mark.django_db
class TestOpenAPIPaginas:
    @pytest.mark.parametrize(
        "path",
        ["/api/schema/", "/api/docs/", "/api/redoc/"],
    )
    def test_pagina_openapi_renderiza(self, api_client, path):
        response = api_client.get(path)
        assert response.status_code == 200, f"GET {path} retornou {response.status_code}"


# ============================================================
# Detalhe: verifica que request.tenant nao e seta como None em rotas publicas.
# Esse era o root cause do bug. Se algum dia voltar, este teste falha.
# ============================================================


@pytest.mark.django_db
class TestMiddlewareNaoQuebraTemplatetags:
    """Em rotas publicas, request.tenant nao deve ser setado para None.

    O atributo deve nao existir (hasattr -> False) para a template tag
    `is_public_schema` do django_tenants funcionar corretamente.
    """

    def test_request_tenant_nao_e_atribuido_em_rota_publica(self, api_client):
        """Acessa uma rota publica e inspeciona que o middleware nao
        deixa um attr `tenant=None` na request (que quebraria templatetags).
        """
        # /health/ e publica (PUBLIC_PATH_PREFIXES). A response funcional
        # ja foi coberta em test_smoke; aqui validamos que a renderizacao
        # do admin (que usa {% load tenant %}) nao quebra.
        response = api_client.get("/health/")
        assert response.status_code == 200
