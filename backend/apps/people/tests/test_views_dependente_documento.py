"""
Testes de integracao HTTP de Dependente e Documento.

Cobertura mais enxuta — pattern ja foi exercitado em Cargo/Lotacao/Servidor.
"""

from __future__ import annotations

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.fixture
def servidor_a(api_client_factory, usuario_rh_a, tenant_a):
    client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
    response = client.post(
        "/api/people/servidores/",
        {
            "matricula": "DEP-1",
            "nome": "Carlos Lima",
            "cpf": "529.982.247-25",
            "data_nascimento": "1980-06-10",
            "sexo": "M",
            "ativo": True,
        },
        format="json",
    )
    assert response.status_code == 201
    return response.json()["id"]


# ============================================================
# Dependente
# ============================================================


@pytest.mark.django_db
class TestDependente:
    def test_rh_cria_dependente(self, api_client_factory, usuario_rh_a, tenant_a, servidor_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        response = client.post(
            "/api/people/dependentes/",
            {
                "servidor": servidor_a,
                "nome": "Maria Lima",
                "data_nascimento": "2015-04-20",
                "parentesco": "filho",
                "ir": True,
                "salario_familia": False,
            },
            format="json",
        )
        assert response.status_code == 201, response.json()

    def test_filtra_por_servidor(self, api_client_factory, usuario_rh_a, tenant_a, servidor_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        client.post(
            "/api/people/dependentes/",
            {
                "servidor": servidor_a,
                "nome": "Filho 1",
                "data_nascimento": "2018-01-01",
                "parentesco": "filho",
            },
            format="json",
        )
        response = client.get(f"/api/people/dependentes/?servidor={servidor_a}")
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_cpf_invalido_retorna_400(self, api_client_factory, usuario_rh_a, tenant_a, servidor_a):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        response = client.post(
            "/api/people/dependentes/",
            {
                "servidor": servidor_a,
                "nome": "Maria",
                "cpf": "111.111.111-11",
                "data_nascimento": "2015-04-20",
                "parentesco": "filho",
            },
            format="json",
        )
        assert response.status_code == 400


# ============================================================
# Documento (upload via multipart)
# ============================================================


@pytest.mark.django_db
class TestDocumento:
    def test_rh_envia_arquivo(
        self, api_client_factory, usuario_rh_a, tenant_a, servidor_a, tmp_path
    ):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        arquivo = SimpleUploadedFile(
            "rg.pdf",
            b"%PDF-1.4 conteudo de teste",
            content_type="application/pdf",
        )
        response = client.post(
            "/api/people/documentos/",
            {
                "servidor": servidor_a,
                "tipo": "rg",
                "descricao": "RG digitalizado",
                "arquivo": arquivo,
            },
            format="multipart",
        )
        assert response.status_code == 201, response.content
        data = response.json()
        assert data["tipo"] == "rg"
        assert data["arquivo"].endswith(".pdf")

    def test_leitura_lista(
        self, api_client_factory, usuario_rh_a, usuario_leitura_a, tenant_a, servidor_a
    ):
        rh = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        arquivo = SimpleUploadedFile("doc.pdf", b"x", content_type="application/pdf")
        rh.post(
            "/api/people/documentos/",
            {"servidor": servidor_a, "tipo": "outro", "descricao": "X", "arquivo": arquivo},
            format="multipart",
        )
        leitura = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        response = leitura.get("/api/people/documentos/")
        assert response.status_code == 200
        assert response.json()["count"] == 1
