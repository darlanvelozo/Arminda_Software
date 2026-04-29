"""
Testes de integracao HTTP do RubricaViewSet (Bloco 1.2 — Onda 3).

Cobre CRUD basico, RBAC (financeiro vs leitura) e isolamento.
DSL de calculo (campo formula) NAO eh validada aqui — Bloco 2.
"""

from __future__ import annotations

import pytest

PAYLOAD_VALIDO = {
    "codigo": "INSS",
    "nome": "INSS",
    "tipo": "desconto",
    "incide_inss": False,
    "incide_irrf": False,
    "incide_fgts": False,
    "ativo": True,
}


def _criar_rubrica(client, payload=None):
    return client.post("/api/payroll/rubricas/", payload or PAYLOAD_VALIDO, format="json")


@pytest.fixture
def usuario_financeiro_a(usuario_factory, tenant_a):
    return usuario_factory(
        email="fin-a@arminda.test",
        papeis=[(tenant_a, "financeiro_municipio")],
    )


@pytest.mark.django_db
class TestRubricaCRUD:
    def test_financeiro_cria_rubrica(self, api_client_factory, usuario_financeiro_a, tenant_a):
        client = api_client_factory(user=usuario_financeiro_a, tenant=tenant_a)
        response = _criar_rubrica(client)
        assert response.status_code == 201, response.json()
        assert response.json()["codigo"] == "INSS"

    def test_leitura_lista_apos_criar(
        self,
        api_client_factory,
        usuario_financeiro_a,
        usuario_leitura_a,
        tenant_a,
    ):
        fin = api_client_factory(user=usuario_financeiro_a, tenant=tenant_a)
        _criar_rubrica(fin)
        leitura = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        response = leitura.get("/api/payroll/rubricas/")
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_leitura_nao_cria(self, api_client_factory, usuario_leitura_a, tenant_a):
        client = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        response = _criar_rubrica(client)
        assert response.status_code == 403

    def test_rh_nao_cria_rubrica(self, api_client_factory, usuario_rh_a, tenant_a):
        """RH gerencia pessoas, nao rubricas (regra de financeiro)."""
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        response = _criar_rubrica(client)
        assert response.status_code == 403

    def test_codigo_normalizado_para_upper(
        self, api_client_factory, usuario_financeiro_a, tenant_a
    ):
        client = api_client_factory(user=usuario_financeiro_a, tenant=tenant_a)
        response = _criar_rubrica(client, {**PAYLOAD_VALIDO, "codigo": "  inss "})
        assert response.status_code == 201
        assert response.json()["codigo"] == "INSS"


@pytest.mark.django_db
class TestRubricaIsolamento:
    def test_rubrica_em_a_nao_aparece_em_b(
        self,
        api_client_factory,
        usuario_financeiro_a,
        usuario_admin_b,
        tenant_a,
        tenant_b,
    ):
        fin = api_client_factory(user=usuario_financeiro_a, tenant=tenant_a)
        _criar_rubrica(fin)
        admin_b = api_client_factory(user=usuario_admin_b, tenant=tenant_b)
        response = admin_b.get("/api/payroll/rubricas/")
        assert response.status_code == 200
        assert response.json()["count"] == 0
