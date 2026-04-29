"""
Testes de integracao HTTP do VinculoFuncionalViewSet.

CRUD basico + validacao de datas + isolamento.
"""

from __future__ import annotations

from decimal import Decimal

import pytest


@pytest.fixture
def cargo_a(api_client_factory, usuario_rh_a, tenant_a):
    """Cria um cargo no tenant_a e retorna o id."""
    client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
    response = client.post(
        "/api/people/cargos/",
        {"codigo": "PROF", "nome": "Professor", "ativo": True},
        format="json",
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.fixture
def lotacao_a(api_client_factory, usuario_rh_a, tenant_a):
    client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
    response = client.post(
        "/api/people/lotacoes/",
        {"codigo": "EDUC", "nome": "Educacao", "ativo": True},
        format="json",
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.fixture
def servidor_a(api_client_factory, usuario_rh_a, tenant_a):
    client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
    response = client.post(
        "/api/people/servidores/",
        {
            "matricula": "S1",
            "nome": "Maria Souza",
            "cpf": "529.982.247-25",
            "data_nascimento": "1985-03-20",
            "sexo": "F",
            "ativo": True,
        },
        format="json",
    )
    assert response.status_code == 201
    return response.json()["id"]


def _criar_vinculo(client, servidor_id, cargo_id, lotacao_id, **overrides):
    payload = {
        "servidor": servidor_id,
        "cargo": cargo_id,
        "lotacao": lotacao_id,
        "regime": "estatutario",
        "data_admissao": "2024-01-15",
        "carga_horaria": 40,
        "salario_base": "3500.00",
        "ativo": True,
        **overrides,
    }
    return client.post("/api/people/vinculos/", payload, format="json")


@pytest.mark.django_db
class TestVinculoCRUD:
    def test_rh_cria_vinculo(
        self,
        api_client_factory,
        usuario_rh_a,
        tenant_a,
        servidor_a,
        cargo_a,
        lotacao_a,
    ):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        response = _criar_vinculo(client, servidor_a, cargo_a, lotacao_a)
        assert response.status_code == 201, response.json()
        data = response.json()
        assert Decimal(data["salario_base"]) == Decimal("3500.00")

    def test_list_inclui_resumo(
        self,
        api_client_factory,
        usuario_rh_a,
        tenant_a,
        servidor_a,
        cargo_a,
        lotacao_a,
    ):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        _criar_vinculo(client, servidor_a, cargo_a, lotacao_a)
        response = client.get("/api/people/vinculos/")
        assert response.status_code == 200
        result = response.json()["results"][0]
        assert result["servidor_matricula"] == "S1"
        assert result["cargo_nome"] == "Professor"


@pytest.mark.django_db
class TestVinculoValidacao:
    def test_carga_horaria_invalida(
        self,
        api_client_factory,
        usuario_rh_a,
        tenant_a,
        servidor_a,
        cargo_a,
        lotacao_a,
    ):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        response = _criar_vinculo(client, servidor_a, cargo_a, lotacao_a, carga_horaria=80)
        assert response.status_code == 400

    def test_data_demissao_anterior_a_admissao(
        self,
        api_client_factory,
        usuario_rh_a,
        tenant_a,
        servidor_a,
        cargo_a,
        lotacao_a,
    ):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        response = _criar_vinculo(
            client,
            servidor_a,
            cargo_a,
            lotacao_a,
            data_admissao="2024-01-15",
            data_demissao="2023-12-01",
        )
        assert response.status_code == 400

    def test_data_admissao_futura(
        self,
        api_client_factory,
        usuario_rh_a,
        tenant_a,
        servidor_a,
        cargo_a,
        lotacao_a,
    ):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        response = _criar_vinculo(
            client,
            servidor_a,
            cargo_a,
            lotacao_a,
            data_admissao="2030-01-01",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestVinculoFiltros:
    def test_filtra_por_servidor(
        self,
        api_client_factory,
        usuario_rh_a,
        tenant_a,
        servidor_a,
        cargo_a,
        lotacao_a,
    ):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        _criar_vinculo(client, servidor_a, cargo_a, lotacao_a)
        response = client.get(f"/api/people/vinculos/?servidor={servidor_a}")
        assert response.status_code == 200
        assert response.json()["count"] == 1
