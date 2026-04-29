"""
Testes de integracao HTTP do CargoViewSet (Bloco 1.2 — Onda 1).

Cobre:
- CRUD completo (list, retrieve, create, update, partial_update, destroy)
- RBAC: leitura permite, escrita exige RH/admin/staff
- Isolamento entre tenants (Cargo de A nao aparece em B)
- Filtros e busca
"""

from __future__ import annotations

import pytest

# ============================================================
# Helpers
# ============================================================


def _criar_cargo(client, payload=None):
    """POST /api/people/cargos/ com payload default."""
    payload = payload or {
        "codigo": "PROF1",
        "nome": "Professor I",
        "cbo": "2312-05",
        "nivel_escolaridade": "superior",
        "ativo": True,
    }
    return client.post("/api/people/cargos/", payload, format="json")


# ============================================================
# Sem autenticacao
# ============================================================


@pytest.mark.django_db
class TestCargoSemAuth:
    def test_list_sem_auth_retorna_401(self, api_client, tenant_a):
        api_client.defaults["HTTP_X_TENANT"] = tenant_a.schema_name
        response = api_client.get("/api/people/cargos/")
        assert response.status_code == 401

    def test_list_sem_tenant_retorna_400(self, api_client_factory, usuario_admin_a):
        client = api_client_factory(user=usuario_admin_a)  # sem tenant
        response = client.get("/api/people/cargos/")
        assert response.status_code == 400


# ============================================================
# Leitura (list, retrieve)
# ============================================================


@pytest.mark.django_db
class TestCargoLeitura:
    def test_leitura_lista_vazia(self, api_client_factory, usuario_leitura_a, tenant_a):
        client = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        response = client.get("/api/people/cargos/")
        assert response.status_code == 200
        assert response.json()["count"] == 0

    def test_leitura_lista_apos_criar(
        self, api_client_factory, usuario_leitura_a, usuario_rh_a, tenant_a
    ):
        # Cria via RH
        rh = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        _criar_cargo(rh)
        # Le via leitura
        leitura = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        response = leitura.get("/api/people/cargos/")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["results"][0]["codigo"] == "PROF1"

    def test_retrieve_retorna_detail(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        criado = _criar_cargo(client).json()
        response = client.get(f"/api/people/cargos/{criado['id']}/")
        assert response.status_code == 200
        data = response.json()
        assert data["codigo"] == "PROF1"
        assert data["cbo"] == "2312-05"
        assert "criado_em" in data
        assert "nivel_escolaridade_display" in data


# ============================================================
# Escrita (create, update, partial_update, destroy)
# ============================================================


@pytest.mark.django_db
class TestCargoEscrita:
    def test_rh_cria_cargo(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        response = _criar_cargo(client)
        assert response.status_code == 201
        data = response.json()
        assert data["codigo"] == "PROF1"  # codigo eh upper-stripped no validator

    def test_codigo_e_normalizado_para_upper(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        response = _criar_cargo(client, {"codigo": "  prof2 ", "nome": "P2"})
        assert response.status_code == 201
        assert response.json()["codigo"] == "PROF2"

    def test_codigo_vazio_retorna_400(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        response = _criar_cargo(client, {"codigo": "  ", "nome": "X"})
        assert response.status_code == 400

    def test_codigo_duplicado_retorna_400(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        _criar_cargo(client)
        # Mesmo codigo de novo
        response = _criar_cargo(client)
        assert response.status_code == 400

    def test_leitura_nao_pode_criar(self, api_client_factory, usuario_leitura_a, tenant_a):
        client = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        response = _criar_cargo(client)
        assert response.status_code == 403

    def test_update_nao_permitido_para_leitura(
        self, api_client_factory, usuario_rh_a, usuario_leitura_a, tenant_a
    ):
        rh = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        criado = _criar_cargo(rh).json()
        leitura = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        response = leitura.patch(
            f"/api/people/cargos/{criado['id']}/",
            {"nome": "Tentei mudar"},
            format="json",
        )
        assert response.status_code == 403

    def test_update_via_rh(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        criado = _criar_cargo(client).json()
        response = client.patch(
            f"/api/people/cargos/{criado['id']}/",
            {"nome": "Professor I - Atualizado"},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["nome"] == "Professor I - Atualizado"

    def test_destroy_via_rh(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        criado = _criar_cargo(client).json()
        response = client.delete(f"/api/people/cargos/{criado['id']}/")
        assert response.status_code == 204

    def test_admin_arminda_cria_em_qualquer_tenant(
        self, api_client_factory, usuario_staff_arminda, tenant_b
    ):
        client = api_client_factory(user=usuario_staff_arminda, tenant=tenant_b)
        response = _criar_cargo(client)
        assert response.status_code == 201


# ============================================================
# Isolamento entre tenants
# ============================================================


@pytest.mark.django_db
class TestCargoIsolamento:
    def test_cargo_em_a_nao_aparece_em_b(
        self,
        api_client_factory,
        usuario_rh_a,
        usuario_admin_b,
        tenant_a,
        tenant_b,
    ):
        rh_a = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        _criar_cargo(rh_a, {"codigo": "AA1", "nome": "Cargo de A"})

        admin_b = api_client_factory(user=usuario_admin_b, tenant=tenant_b)
        response = admin_b.get("/api/people/cargos/")
        assert response.status_code == 200
        assert response.json()["count"] == 0

    def test_mesmo_codigo_em_dois_tenants_e_permitido(
        self,
        api_client_factory,
        usuario_rh_a,
        usuario_admin_b,
        tenant_a,
        tenant_b,
    ):
        """codigo=PROF1 em A E em B nao gera conflito (escopo do schema)."""
        rh_a = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        admin_b = api_client_factory(user=usuario_admin_b, tenant=tenant_b)

        r1 = _criar_cargo(rh_a)
        r2 = _criar_cargo(admin_b)
        assert r1.status_code == 201
        assert r2.status_code == 201


# ============================================================
# Filtros e busca
# ============================================================


@pytest.mark.django_db
class TestCargoFiltros:
    def _seed(self, client):
        _criar_cargo(
            client, {"codigo": "ENF1", "nome": "Enfermeiro I", "nivel_escolaridade": "superior"}
        )
        _criar_cargo(
            client, {"codigo": "ENF2", "nome": "Enfermeiro II", "nivel_escolaridade": "superior"}
        )
        _criar_cargo(
            client,
            {"codigo": "AUX1", "nome": "Auxiliar Administrativo", "nivel_escolaridade": "medio"},
        )

    def test_filtra_por_nivel(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        self._seed(client)
        response = client.get("/api/people/cargos/?nivel_escolaridade=medio")
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 1
        assert results[0]["codigo"] == "AUX1"

    def test_search_por_nome(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        self._seed(client)
        response = client.get("/api/people/cargos/?search=Enfermeiro")
        assert response.status_code == 200
        assert response.json()["count"] == 2
