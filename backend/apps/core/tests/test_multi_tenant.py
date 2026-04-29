"""
Testes de multi-tenant (ADR-0006): isolamento real por schema.
"""

from __future__ import annotations

import pytest
from django.db import connection


@pytest.mark.django_db
class TestTenants:
    def test_tenants_de_teste_existem(self, tenant_a, tenant_b):
        assert tenant_a.schema_name == "test_tenant_a"
        assert tenant_b.schema_name == "test_tenant_b"
        assert tenant_a.codigo_ibge != tenant_b.codigo_ibge

    def test_schema_de_tenant_foi_criado_no_postgres(self, tenant_a):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT schema_name FROM information_schema.schemata " "WHERE schema_name = %s",
                [tenant_a.schema_name],
            )
            assert cursor.fetchone() is not None


@pytest.mark.django_db
class TestIsolamentoEntreSchemas:
    """O dado criado em tenant_a NAO pode aparecer em tenant_b."""

    def test_servidor_criado_em_a_nao_aparece_em_b(self, tenant_a, tenant_b, in_tenant):
        from apps.people.models import Servidor

        with in_tenant(tenant_a):
            Servidor.objects.create(
                matricula="001",
                nome="Joao da Silva",
                cpf="111.111.111-11",
                data_nascimento="1990-01-01",
                sexo="M",
            )
            servidores_em_a = list(Servidor.objects.values_list("nome", flat=True))

        with in_tenant(tenant_b):
            servidores_em_b = list(Servidor.objects.values_list("nome", flat=True))

        assert "Joao da Silva" in servidores_em_a
        assert "Joao da Silva" not in servidores_em_b
        assert servidores_em_b == []

    def test_codigo_unique_por_schema_nao_global(self, tenant_a, tenant_b, in_tenant):
        """Mesmo `codigo` pode existir em tenants diferentes (cargo)."""
        from apps.people.models import Cargo

        with in_tenant(tenant_a):
            Cargo.objects.create(codigo="PROF", nome="Professor I")

        # Mesmo codigo em outro tenant: deve passar
        with in_tenant(tenant_b):
            Cargo.objects.create(codigo="PROF", nome="Professor I (B)")

        with in_tenant(tenant_a):
            assert Cargo.objects.filter(codigo="PROF").count() == 1

        with in_tenant(tenant_b):
            assert Cargo.objects.filter(codigo="PROF").count() == 1
