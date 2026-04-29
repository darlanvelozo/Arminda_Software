"""
Fixtures globais para os testes do Arminda.

Estrutura:
- session: 2 tenants (tenant_a, tenant_b) criados uma unica vez
- function: usuarios e API clients (criados a cada teste para isolamento)

Como django-tenants altera o engine de banco, usamos o `django_db_setup`
do pytest-django como ponto de entrada e setamos os tenants logo na sequencia.
"""

from __future__ import annotations

import pytest
from django.contrib.auth.models import Group
from django.db import connection
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

# ============================================================
# Setup do banco e tenants (session-scoped)
# ============================================================


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Roda apos o pytest-django criar o banco. Cria os 2 tenants de teste."""
    from apps.core.models import Domain, Municipio

    with django_db_blocker.unblock():
        # Garante que estamos no public para criar Municipios
        connection.set_schema_to_public()

        if not Municipio.objects.filter(schema_name="test_tenant_a").exists():
            tenant_a = Municipio(
                schema_name="test_tenant_a",
                nome="Test Tenant A",
                uf="MA",
                codigo_ibge="9999991",
            )
            tenant_a.save()
            Domain.objects.create(
                domain="tenant-a.test.localhost", tenant=tenant_a, is_primary=True
            )

        if not Municipio.objects.filter(schema_name="test_tenant_b").exists():
            tenant_b = Municipio(
                schema_name="test_tenant_b",
                nome="Test Tenant B",
                uf="PI",
                codigo_ibge="9999992",
            )
            tenant_b.save()
            Domain.objects.create(
                domain="tenant-b.test.localhost", tenant=tenant_b, is_primary=True
            )

        # Garante seed dos Groups (a migration 0002 ja faz, mas idempotente)
        for nome in (
            "staff_arminda",
            "admin_municipio",
            "rh_municipio",
            "financeiro_municipio",
            "leitura_municipio",
        ):
            Group.objects.get_or_create(name=nome)


# ============================================================
# Tenants
# ============================================================


@pytest.fixture
def tenant_a(db):
    from apps.core.models import Municipio

    return Municipio.objects.get(schema_name="test_tenant_a")


@pytest.fixture
def tenant_b(db):
    from apps.core.models import Municipio

    return Municipio.objects.get(schema_name="test_tenant_b")


# ============================================================
# Usuarios
# ============================================================


@pytest.fixture
def usuario_factory(db):
    """Factory que cria usuarios. Use:
    user = usuario_factory(email="x@x.com", papeis=[(tenant_a, "rh_municipio")])
    """
    from django.contrib.auth import get_user_model

    from apps.core.models import UsuarioMunicipioPapel

    User = get_user_model()

    def _criar(
        email: str = "user@arminda.test",
        password: str = "senha-segura-123",
        nome_completo: str = "",
        papeis: list[tuple] | None = None,
        is_staff: bool = False,
        is_superuser: bool = False,
        precisa_trocar_senha: bool = False,
    ):
        user = User.objects.create_user(
            email=email,
            password=password,
            nome_completo=nome_completo,
            is_staff=is_staff,
            is_superuser=is_superuser,
            precisa_trocar_senha=precisa_trocar_senha,
        )
        for tenant, grupo_nome in papeis or []:
            grupo = Group.objects.get(name=grupo_nome)
            UsuarioMunicipioPapel.objects.create(usuario=user, municipio=tenant, grupo=grupo)
        return user

    return _criar


@pytest.fixture
def usuario_admin_a(usuario_factory, tenant_a):
    return usuario_factory(
        email="admin-a@arminda.test",
        papeis=[(tenant_a, "admin_municipio")],
    )


@pytest.fixture
def usuario_rh_a(usuario_factory, tenant_a):
    return usuario_factory(
        email="rh-a@arminda.test",
        papeis=[(tenant_a, "rh_municipio")],
    )


@pytest.fixture
def usuario_leitura_a(usuario_factory, tenant_a):
    return usuario_factory(
        email="leitura-a@arminda.test",
        papeis=[(tenant_a, "leitura_municipio")],
    )


@pytest.fixture
def usuario_admin_b(usuario_factory, tenant_b):
    return usuario_factory(
        email="admin-b@arminda.test",
        papeis=[(tenant_b, "admin_municipio")],
    )


@pytest.fixture
def usuario_staff_arminda(usuario_factory):
    """Membro da equipe Arminda (cross-tenant)."""
    from django.contrib.auth.models import Group

    user = usuario_factory(email="staff@arminda.test", is_staff=True)
    user.groups.add(Group.objects.get(name="staff_arminda"))
    return user


# ============================================================
# API Clients
# ============================================================


@pytest.fixture
def api_client():
    """Cliente DRF cru, sem auth nem tenant."""
    return APIClient()


@pytest.fixture
def api_client_factory():
    """Factory que monta um APIClient autenticado e com tenant.

    Uso:
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
    """

    def _criar(*, user=None, tenant=None):
        client = APIClient()
        if user is not None:
            refresh = RefreshToken.for_user(user)
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        if tenant is not None:
            schema = tenant.schema_name if hasattr(tenant, "schema_name") else tenant
            client.defaults["HTTP_X_TENANT"] = schema
        return client

    return _criar


# ============================================================
# Tenant context helper
# ============================================================


@pytest.fixture
def in_tenant():
    """Context manager para rodar codigo no contexto de um tenant.

    Uso:
        with in_tenant(tenant_a):
            Servidor.objects.create(...)
    """
    from contextlib import contextmanager

    @contextmanager
    def _ctx(tenant):
        connection.set_tenant(tenant)
        try:
            yield
        finally:
            connection.set_schema_to_public()

    return _ctx
