"""
Testes de integracao HTTP do LotacaoViewSet (Bloco 1.2 — Onda 1).

Foca no que e diferente de Cargo:
- Hierarquia (lotacao_pai)
- Filtro raiz (lotacao_pai__isnull=True)
- Validacao de ciclo (impedir self-parent)

CRUD/RBAC/isolamento basicos sao identicos a Cargo, validados aqui de forma
mais enxuta para nao duplicar matriz.
"""

from __future__ import annotations

import pytest


def _criar_lotacao(client, payload=None):
    payload = payload or {
        "codigo": "SEC-EDU",
        "nome": "Secretaria de Educacao",
        "sigla": "SEDUC",
        "ativo": True,
    }
    return client.post("/api/people/lotacoes/", payload, format="json")


# ============================================================
# CRUD basico
# ============================================================


@pytest.mark.django_db
class TestLotacaoCRUD:
    def test_rh_cria_lotacao(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        response = _criar_lotacao(client)
        assert response.status_code == 201
        assert response.json()["sigla"] == "SEDUC"

    def test_leitura_lista(self, api_client_factory, usuario_rh_a, usuario_leitura_a, tenant_a):
        rh = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        _criar_lotacao(rh)
        leitura = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        response = leitura.get("/api/people/lotacoes/")
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_leitura_nao_cria(self, api_client_factory, usuario_leitura_a, tenant_a):
        client = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        response = _criar_lotacao(client)
        assert response.status_code == 403


# ============================================================
# Hierarquia
# ============================================================


@pytest.mark.django_db
class TestLotacaoHierarquia:
    def test_cria_sublotacao(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        pai = _criar_lotacao(client).json()
        filha = _criar_lotacao(
            client,
            {
                "codigo": "SEC-EDU-EI",
                "nome": "Diretoria de Educacao Infantil",
                "sigla": "DEI",
                "lotacao_pai": pai["id"],
                "ativo": True,
            },
        ).json()
        # GET retorna o pai expandido
        detail = client.get(f"/api/people/lotacoes/{filha['id']}/").json()
        assert detail["lotacao_pai"] == pai["id"]
        assert detail["lotacao_pai_nome"] == pai["nome"]

    def test_filtro_raiz_so_retorna_sem_pai(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        pai = _criar_lotacao(client).json()
        _criar_lotacao(
            client,
            {
                "codigo": "FILHA",
                "nome": "Filha",
                "lotacao_pai": pai["id"],
                "ativo": True,
            },
        )
        response = client.get("/api/people/lotacoes/?raiz=true")
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 1
        assert results[0]["codigo"] == "SEC-EDU"

    def test_lotacao_nao_pode_ser_pai_de_si_mesma(self, api_client_factory, usuario_rh_a, tenant_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        criada = _criar_lotacao(client).json()
        response = client.patch(
            f"/api/people/lotacoes/{criada['id']}/",
            {"lotacao_pai": criada["id"]},
            format="json",
        )
        assert response.status_code == 400


# ============================================================
# Isolamento
# ============================================================


@pytest.mark.django_db
class TestLotacaoIsolamento:
    def test_lotacao_em_a_nao_aparece_em_b(
        self,
        api_client_factory,
        usuario_rh_a,
        usuario_admin_b,
        tenant_a,
        tenant_b,
    ):
        rh_a = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        _criar_lotacao(rh_a)
        admin_b = api_client_factory(user=usuario_admin_b, tenant=tenant_b)
        response = admin_b.get("/api/people/lotacoes/")
        assert response.status_code == 200
        assert response.json()["count"] == 0
