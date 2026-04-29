"""
Testes dos management commands de tenant (apps.core.management.commands).
"""

from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.django_db
class TestCriarMunicipio:
    def test_cria_tenant_basico(self):
        from apps.core.models import Domain, Municipio

        out = StringIO()
        call_command(
            "criar_municipio",
            "--nome=Imperatriz",
            "--uf=MA",
            "--codigo-ibge=2105302",
            "--schema=test_mun_imperatriz",
            "--domain=imperatriz.test.localhost",
            stdout=out,
        )
        output = out.getvalue()
        assert "criado" in output.lower()
        assert Municipio.objects.filter(schema_name="test_mun_imperatriz").exists()
        assert Domain.objects.filter(domain="imperatriz.test.localhost").exists()

    def test_cria_sem_domain(self):
        from apps.core.models import Domain, Municipio

        out = StringIO()
        call_command(
            "criar_municipio",
            "--nome=Caxias",
            "--uf=MA",
            "--codigo-ibge=2103000",
            "--schema=test_mun_caxias",
            stdout=out,
        )
        municipio = Municipio.objects.get(schema_name="test_mun_caxias")
        assert municipio.uf == "MA"
        assert not Domain.objects.filter(tenant=municipio).exists()

    def test_falha_em_schema_duplicado(self, tenant_a):
        with pytest.raises(CommandError, match="Schema"):
            call_command(
                "criar_municipio",
                "--nome=Outro",
                "--uf=MA",
                "--codigo-ibge=1234567",
                f"--schema={tenant_a.schema_name}",
            )

    def test_falha_em_codigo_ibge_duplicado(self, tenant_a):
        with pytest.raises(CommandError, match="IBGE"):
            call_command(
                "criar_municipio",
                "--nome=Outro",
                "--uf=PI",
                f"--codigo-ibge={tenant_a.codigo_ibge}",
                "--schema=test_mun_outro",
            )


@pytest.mark.django_db
class TestListarTenants:
    def test_lista_inclui_tenants_de_teste(self, tenant_a, tenant_b):
        out = StringIO()
        call_command("listar_tenants", stdout=out)
        output = out.getvalue()
        assert tenant_a.schema_name in output
        assert tenant_b.schema_name in output
        assert "Total: " in output
