"""
Testes de integracao HTTP dos endpoints @action (Bloco 1.2 — Onda 3).

- POST /api/people/servidores/admitir/
- POST /api/people/servidores/<id>/desligar/
- POST /api/people/vinculos/<id>/transferir/
"""

from __future__ import annotations

from datetime import date

import pytest


@pytest.fixture
def cargo_a_id(api_client_factory, usuario_rh_a, tenant_a):
    client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
    response = client.post(
        "/api/people/cargos/",
        {"codigo": "ENF", "nome": "Enfermeiro", "ativo": True},
        format="json",
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.fixture
def lotacao_a_id(api_client_factory, usuario_rh_a, tenant_a):
    client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
    response = client.post(
        "/api/people/lotacoes/",
        {"codigo": "SAU", "nome": "Saude", "ativo": True},
        format="json",
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.fixture
def lotacao_destino_id(api_client_factory, usuario_rh_a, tenant_a):
    client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
    response = client.post(
        "/api/people/lotacoes/",
        {"codigo": "EDUC", "nome": "Educacao", "ativo": True},
        format="json",
    )
    assert response.status_code == 201
    return response.json()["id"]


def _payload_admissao(cargo_id, lotacao_id):
    return {
        "matricula": "100",
        "nome": "Ana Souza",
        "cpf": "529.982.247-25",
        "data_nascimento": "1985-03-20",
        "sexo": "F",
        "cargo_id": cargo_id,
        "lotacao_id": lotacao_id,
        "regime": "estatutario",
        "data_admissao": "2024-06-01",
        "salario_base": "4500.00",
        "carga_horaria": 40,
    }


# ============================================================
# admitir/
# ============================================================


@pytest.mark.django_db
class TestAdmitirEndpoint:
    def test_rh_admite_servidor(
        self, api_client_factory, usuario_rh_a, tenant_a, cargo_a_id, lotacao_a_id
    ):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        response = client.post(
            "/api/people/servidores/admitir/",
            _payload_admissao(cargo_a_id, lotacao_a_id),
            format="json",
        )
        assert response.status_code == 201, response.json()
        data = response.json()
        assert data["matricula"] == "100"
        assert data["cpf"] == "52998224725"
        assert len(data["vinculos"]) == 1

    def test_leitura_nao_admite(
        self,
        api_client_factory,
        usuario_leitura_a,
        usuario_rh_a,
        tenant_a,
        cargo_a_id,
        lotacao_a_id,
    ):
        client = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        response = client.post(
            "/api/people/servidores/admitir/",
            _payload_admissao(cargo_a_id, lotacao_a_id),
            format="json",
        )
        assert response.status_code == 403

    def test_cargo_inativo_retorna_400_com_code(
        self,
        api_client_factory,
        usuario_rh_a,
        tenant_a,
        lotacao_a_id,
    ):
        # Cria um cargo inativo via API
        rh = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        cargo_inativo = rh.post(
            "/api/people/cargos/",
            {"codigo": "X", "nome": "Inativo", "ativo": False},
            format="json",
        ).json()

        response = rh.post(
            "/api/people/servidores/admitir/",
            _payload_admissao(cargo_inativo["id"], lotacao_a_id),
            format="json",
        )
        assert response.status_code == 400
        body = response.json()
        # ValidationError com {detail, code} embrulhado em lista
        codes = str(body)
        assert "CARGO_INVALIDO" in codes


# ============================================================
# desligar/
# ============================================================


@pytest.mark.django_db
class TestDesligarEndpoint:
    def test_rh_desliga_servidor(
        self,
        api_client_factory,
        usuario_rh_a,
        tenant_a,
        cargo_a_id,
        lotacao_a_id,
    ):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        admitido = client.post(
            "/api/people/servidores/admitir/",
            _payload_admissao(cargo_a_id, lotacao_a_id),
            format="json",
        ).json()

        response = client.post(
            f"/api/people/servidores/{admitido['id']}/desligar/",
            {"data_desligamento": str(date.today()), "motivo": "exoneracao"},
            format="json",
        )
        assert response.status_code == 200, response.json()
        assert response.json()["ativo"] is False

    def test_desligar_duas_vezes_retorna_400(
        self,
        api_client_factory,
        usuario_rh_a,
        tenant_a,
        cargo_a_id,
        lotacao_a_id,
    ):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        admitido = client.post(
            "/api/people/servidores/admitir/",
            _payload_admissao(cargo_a_id, lotacao_a_id),
            format="json",
        ).json()
        # Primeiro desligamento OK
        r1 = client.post(
            f"/api/people/servidores/{admitido['id']}/desligar/",
            {"data_desligamento": str(date.today())},
            format="json",
        )
        assert r1.status_code == 200
        # Segundo deve falhar
        r2 = client.post(
            f"/api/people/servidores/{admitido['id']}/desligar/",
            {"data_desligamento": str(date.today())},
            format="json",
        )
        assert r2.status_code == 400
        assert "DESLIGAMENTO_DUPLICADO" in str(r2.json())


# ============================================================
# transferir/
# ============================================================


@pytest.mark.django_db
class TestTransferirEndpoint:
    def test_rh_transfere_lotacao(
        self,
        api_client_factory,
        usuario_rh_a,
        tenant_a,
        cargo_a_id,
        lotacao_a_id,
        lotacao_destino_id,
    ):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        admitido = client.post(
            "/api/people/servidores/admitir/",
            _payload_admissao(cargo_a_id, lotacao_a_id),
            format="json",
        ).json()
        vinculo_id = admitido["vinculos"][0]["id"]

        response = client.post(
            f"/api/people/vinculos/{vinculo_id}/transferir/",
            {
                "nova_lotacao_id": lotacao_destino_id,
                "data_transferencia": str(date.today()),
            },
            format="json",
        )
        assert response.status_code == 201, response.json()
        novo_vinculo = response.json()
        assert novo_vinculo["lotacao"] == lotacao_destino_id
        assert novo_vinculo["ativo"] is True

    def test_transferencia_para_mesma_lotacao_falha(
        self,
        api_client_factory,
        usuario_rh_a,
        tenant_a,
        cargo_a_id,
        lotacao_a_id,
    ):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        admitido = client.post(
            "/api/people/servidores/admitir/",
            _payload_admissao(cargo_a_id, lotacao_a_id),
            format="json",
        ).json()
        vinculo_id = admitido["vinculos"][0]["id"]

        response = client.post(
            f"/api/people/vinculos/{vinculo_id}/transferir/",
            {
                "nova_lotacao_id": lotacao_a_id,
                "data_transferencia": str(date.today()),
            },
            format="json",
        )
        assert response.status_code == 400
        assert "TRANSFERENCIA_REDUNDANTE" in str(response.json())
