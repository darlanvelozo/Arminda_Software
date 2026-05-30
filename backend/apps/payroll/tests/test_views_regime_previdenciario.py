"""
Testes HTTP do RegimePrevidenciarioViewSet (Onda 2.4).

Cobre CRUD, RBAC (financeiro escreve, leitura só lê), validação
(progressivo exige faixas; regimes válidos) e isolamento entre tenants.
"""

from __future__ import annotations

import pytest

URL = "/api/payroll/regimes-previdenciarios/"

PAYLOAD_FLAT = {
    "nome": "IPM",
    "modo_contribuicao": "flat",
    "aliquota_servidor": "0.14",
    "aliquota_patronal": "0.22",
    "regimes_aplicaveis": ["estatutario"],
    "vigencia_inicio": "2026-01-01",
    "ativo": True,
}


@pytest.fixture
def usuario_financeiro_a(usuario_factory, tenant_a):
    return usuario_factory(
        email="fin-a@arminda.test", papeis=[(tenant_a, "financeiro_municipio")]
    )


@pytest.mark.django_db
class TestRegimePrevidenciarioCRUD:
    def test_financeiro_cria(self, api_client_factory, usuario_financeiro_a, tenant_a):
        client = api_client_factory(user=usuario_financeiro_a, tenant=tenant_a)
        r = client.post(URL, PAYLOAD_FLAT, format="json")
        assert r.status_code == 201, r.json()
        assert r.json()["modo_contribuicao_display"] == "Alíquota única"

    def test_leitura_nao_cria(self, api_client_factory, usuario_leitura_a, tenant_a):
        client = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        r = client.post(URL, PAYLOAD_FLAT, format="json")
        assert r.status_code == 403

    def test_leitura_lista(
        self, api_client_factory, usuario_financeiro_a, usuario_leitura_a, tenant_a
    ):
        fin = api_client_factory(user=usuario_financeiro_a, tenant=tenant_a)
        fin.post(URL, PAYLOAD_FLAT, format="json")
        leitura = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        r = leitura.get(URL)
        assert r.status_code == 200
        assert r.json()["count"] == 1

    def test_progressivo_sem_faixas_eh_400(
        self, api_client_factory, usuario_financeiro_a, tenant_a
    ):
        client = api_client_factory(user=usuario_financeiro_a, tenant=tenant_a)
        payload = {**PAYLOAD_FLAT, "modo_contribuicao": "progressivo", "faixas": []}
        r = client.post(URL, payload, format="json")
        assert r.status_code == 400
        assert "faixas" in r.json()

    def test_progressivo_ultima_faixa_precisa_ser_aberta(
        self, api_client_factory, usuario_financeiro_a, tenant_a
    ):
        client = api_client_factory(user=usuario_financeiro_a, tenant=tenant_a)
        payload = {
            **PAYLOAD_FLAT,
            "modo_contribuicao": "progressivo",
            "faixas": [{"ate": "1500.00", "aliquota": "0.14"}],
        }
        r = client.post(URL, payload, format="json")
        assert r.status_code == 400

    def test_regime_aplicavel_invalido_eh_400(
        self, api_client_factory, usuario_financeiro_a, tenant_a
    ):
        client = api_client_factory(user=usuario_financeiro_a, tenant=tenant_a)
        payload = {**PAYLOAD_FLAT, "regimes_aplicaveis": ["inexistente"]}
        r = client.post(URL, payload, format="json")
        assert r.status_code == 400


@pytest.mark.django_db
class TestRegimePrevidenciarioIsolamento:
    def test_a_nao_aparece_em_b(
        self, api_client_factory, usuario_financeiro_a, usuario_admin_b, tenant_a, tenant_b
    ):
        fin = api_client_factory(user=usuario_financeiro_a, tenant=tenant_a)
        fin.post(URL, PAYLOAD_FLAT, format="json")
        admin_b = api_client_factory(user=usuario_admin_b, tenant=tenant_b)
        r = admin_b.get(URL)
        assert r.status_code == 200
        assert r.json()["count"] == 0
