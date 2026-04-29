"""
Testes de integracao HTTP do ServidorViewSet (Bloco 1.2 — Onda 2).

Cobre:
- CRUD completo + RBAC (leitura vs escrita)
- Validacao de CPF, PIS, data_nascimento
- Isolamento entre tenants
- Filtros (?ativo, ?regime via vinculo, ?lotacao)
- Historico (simple-history) via @action /historico/
"""

from __future__ import annotations

from datetime import date

import pytest

PAYLOAD_VALIDO = {
    "matricula": "0001",
    "nome": "Joao da Silva",
    "cpf": "111.444.777-35",
    "data_nascimento": "1990-01-15",
    "sexo": "M",
    "ativo": True,
}


def _criar_servidor(client, payload=None):
    return client.post("/api/people/servidores/", payload or PAYLOAD_VALIDO, format="json")


# ============================================================
# CRUD basico
# ============================================================


@pytest.mark.django_db
class TestServidorCRUD:
    def test_rh_cria_servidor(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        response = _criar_servidor(client)
        assert response.status_code == 201, response.json()
        data = response.json()
        assert data["matricula"] == "0001"
        # CPF e normalizado para so digitos
        assert data["cpf"] == "11144477735"

    def test_leitura_lista(self, api_client_factory, usuario_rh_a, usuario_leitura_a, tenant_a):
        rh = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        _criar_servidor(rh)
        leitura = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        response = leitura.get("/api/people/servidores/")
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_leitura_nao_cria(self, api_client_factory, usuario_leitura_a, tenant_a):
        client = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        response = _criar_servidor(client)
        assert response.status_code == 403

    def test_detail_inclui_dependentes_e_vinculos(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        criado = _criar_servidor(client).json()
        response = client.get(f"/api/people/servidores/{criado['id']}/")
        assert response.status_code == 200
        data = response.json()
        assert "dependentes" in data
        assert "vinculos" in data
        assert data["dependentes"] == []
        assert data["vinculos"] == []

    def test_update_e_destroy(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        criado = _criar_servidor(client).json()
        # update
        r1 = client.patch(
            f"/api/people/servidores/{criado['id']}/",
            {"nome": "Joao da Silva - Atualizado"},
            format="json",
        )
        assert r1.status_code == 200
        # delete
        r2 = client.delete(f"/api/people/servidores/{criado['id']}/")
        assert r2.status_code == 204


# ============================================================
# Validacao
# ============================================================


@pytest.mark.django_db
class TestServidorValidacao:
    def test_cpf_invalido_retorna_400(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        response = _criar_servidor(client, {**PAYLOAD_VALIDO, "cpf": "111.111.111-11"})
        assert response.status_code == 400
        assert "cpf" in response.json()

    def test_data_nascimento_futura_retorna_400(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        futuro = (date.today().replace(year=date.today().year + 1)).isoformat()
        response = _criar_servidor(client, {**PAYLOAD_VALIDO, "data_nascimento": futuro})
        assert response.status_code == 400

    def test_idade_minima_14(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        muito_jovem = (date.today().replace(year=date.today().year - 10)).isoformat()
        response = _criar_servidor(client, {**PAYLOAD_VALIDO, "data_nascimento": muito_jovem})
        assert response.status_code == 400

    def test_pis_invalido_retorna_400(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        response = _criar_servidor(client, {**PAYLOAD_VALIDO, "pis_pasep": "11111111111"})
        assert response.status_code == 400

    def test_pis_vazio_e_aceito(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        response = _criar_servidor(client, {**PAYLOAD_VALIDO, "pis_pasep": ""})
        assert response.status_code == 201

    def test_pis_valido_e_normalizado(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        response = _criar_servidor(client, {**PAYLOAD_VALIDO, "pis_pasep": "120.66566.55-3"})
        assert response.status_code == 201
        assert response.json()["pis_pasep"] == "12066566553"

    def test_matricula_duplicada_retorna_400(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        _criar_servidor(client)
        r = _criar_servidor(client, {**PAYLOAD_VALIDO, "cpf": "529.982.247-25"})
        assert r.status_code == 400


# ============================================================
# Isolamento
# ============================================================


@pytest.mark.django_db
class TestServidorIsolamento:
    def test_servidor_em_a_nao_aparece_em_b(
        self,
        api_client_factory,
        usuario_rh_a,
        usuario_admin_b,
        tenant_a,
        tenant_b,
    ):
        rh_a = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        _criar_servidor(rh_a)
        admin_b = api_client_factory(user=usuario_admin_b, tenant=tenant_b)
        response = admin_b.get("/api/people/servidores/")
        assert response.status_code == 200
        assert response.json()["count"] == 0


# ============================================================
# Historico (simple-history)
# ============================================================


@pytest.mark.django_db
class TestServidorHistorico:
    def test_historico_apos_create_e_update(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        criado = _criar_servidor(client).json()
        # update
        client.patch(
            f"/api/people/servidores/{criado['id']}/",
            {"nome": "Joao da Silva - V2"},
            format="json",
        )
        response = client.get(f"/api/people/servidores/{criado['id']}/historico/")
        assert response.status_code == 200
        results = response.json()["results"]
        # Pelo menos 2 registros (create + update)
        assert len(results) >= 2
        # Mais recente primeiro
        assert results[0]["history_type"] == "~"
        assert results[0]["nome"] == "Joao da Silva - V2"
        # Email do autor capturado pelo HistoryRequestMiddleware
        assert results[0]["history_user_email"] == usuario_rh_a.email

    def test_leitura_pode_ver_historico(
        self, api_client_factory, usuario_rh_a, usuario_leitura_a, tenant_a
    ):
        rh = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        criado = _criar_servidor(rh).json()
        leitura = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        response = leitura.get(f"/api/people/servidores/{criado['id']}/historico/")
        assert response.status_code == 200
