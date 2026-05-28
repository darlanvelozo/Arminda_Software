"""
Testes do importador CSV/XLSX (Onda 1.6b).

Cobre:
- Atualiza servidor existente por matrícula.
- Atualiza por CPF (alternativo).
- dry_run não persiste; preview tem antes/depois.
- Linha com matrícula inexistente vai para "ignorados_servidor_nao_encontrado".
- Colunas desconhecidas são ignoradas sem erro.
- Cabeçalho sem identificador devolve erro estrutural.
"""

from __future__ import annotations

import io
from datetime import date

import pytest

from apps.imports.services.csv_importer import importar_servidores_csv
from apps.people.models import Servidor, Sexo

CSV_BASICO = (
    "matricula,raca,nome_da_mae,cep\n"
    "M001,1,Maria das Dores,49000-000\n"
    "M002,4,Joana de Souza,57000-000\n"
)

CSV_INEXISTENTE = (
    "matricula,raca\n"
    "M001,2\n"
    "MX999,3\n"  # não existe
)


def _criar_servidores(in_tenant_ctx):
    Servidor.objects.create(
        matricula="M001",
        nome="João",
        cpf="11144477735",
        data_nascimento=date(1990, 1, 1),
        sexo=Sexo.MASCULINO,
    )
    Servidor.objects.create(
        matricula="M002",
        nome="Ana",
        cpf="52998224725",
        data_nascimento=date(1991, 1, 1),
        sexo=Sexo.FEMININO,
    )


@pytest.mark.django_db
class TestCsvImporter:
    def test_dry_run_nao_persiste(self, tenant_a, in_tenant):
        with in_tenant(tenant_a):
            _criar_servidores(in_tenant)
            resultado = importar_servidores_csv(
                conteudo_bytes=CSV_BASICO.encode(),
                nome_arquivo="t.csv",
                coluna_identificador="matricula",
                dry_run=True,
            )
            assert resultado["total_linhas"] == 2
            assert resultado["atualizados"] == 2
            assert len(resultado["preview"]) == 2
            # Não persistiu
            s = Servidor.objects.get(matricula="M001")
            assert s.raca == ""
            assert s.nome_mae == ""

    def test_aplica_de_verdade(self, tenant_a, in_tenant):
        with in_tenant(tenant_a):
            _criar_servidores(in_tenant)
            resultado = importar_servidores_csv(
                conteudo_bytes=CSV_BASICO.encode(),
                nome_arquivo="t.csv",
                coluna_identificador="matricula",
                dry_run=False,
            )
            assert resultado["atualizados"] == 2
            s = Servidor.objects.get(matricula="M001")
            assert s.raca == "1"
            assert s.nome_mae == "Maria das Dores"
            assert s.cep == "49000-000"

    def test_servidor_inexistente(self, tenant_a, in_tenant):
        with in_tenant(tenant_a):
            _criar_servidores(in_tenant)
            resultado = importar_servidores_csv(
                conteudo_bytes=CSV_INEXISTENTE.encode(),
                nome_arquivo="t.csv",
                coluna_identificador="matricula",
                dry_run=False,
            )
            assert resultado["atualizados"] == 1
            assert resultado["ignorados_servidor_nao_encontrado"] == 1

    def test_colunas_desconhecidas_sao_ignoradas(self, tenant_a, in_tenant):
        with in_tenant(tenant_a):
            _criar_servidores(in_tenant)
            csv = (
                "matricula,raca,coluna_desconhecida,outro_lixo\n"
                "M001,3,xpto,abc\n"
            )
            resultado = importar_servidores_csv(
                conteudo_bytes=csv.encode(),
                nome_arquivo="t.csv",
                coluna_identificador="matricula",
                dry_run=False,
            )
            assert resultado["atualizados"] == 1
            assert "coluna_desconhecida" in resultado["colunas_ignoradas"]
            s = Servidor.objects.get(matricula="M001")
            assert s.raca == "3"

    def test_cabecalho_sem_identificador(self, tenant_a, in_tenant):
        with in_tenant(tenant_a):
            csv = "raca\n1\n"
            resultado = importar_servidores_csv(
                conteudo_bytes=csv.encode(),
                nome_arquivo="t.csv",
                coluna_identificador="matricula",
                dry_run=False,
            )
            assert resultado["atualizados"] == 0
            assert any(
                "não encontrada" in e["mensagem"].lower() for e in resultado["erros"]
            )

    def test_separador_ponto_e_virgula(self, tenant_a, in_tenant):
        with in_tenant(tenant_a):
            _criar_servidores(in_tenant)
            csv = "matricula;raca;nome_da_mae\nM001;2;Aparecida\n"
            resultado = importar_servidores_csv(
                conteudo_bytes=csv.encode(),
                nome_arquivo="t.csv",
                coluna_identificador="matricula",
                dry_run=False,
            )
            assert resultado["atualizados"] == 1
            s = Servidor.objects.get(matricula="M001")
            assert s.nome_mae == "Aparecida"

    def test_importacao_por_cpf(self, tenant_a, in_tenant):
        with in_tenant(tenant_a):
            _criar_servidores(in_tenant)
            csv = "cpf,raca\n111.444.777-35,4\n"
            resultado = importar_servidores_csv(
                conteudo_bytes=csv.encode(),
                nome_arquivo="t.csv",
                coluna_identificador="cpf",
                dry_run=False,
            )
            assert resultado["atualizados"] == 1
            s = Servidor.objects.get(matricula="M001")
            assert s.raca == "4"


@pytest.mark.django_db
class TestEndpointImporterCsv:
    URL = "/api/imports/csv/servidores/"

    def test_upload_csv_atualiza(
        self, api_client_factory, usuario_admin_a, tenant_a, in_tenant
    ):
        with in_tenant(tenant_a):
            _criar_servidores(in_tenant)
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        arquivo = io.BytesIO(CSV_BASICO.encode())
        arquivo.name = "smoke.csv"
        resp = client.post(
            self.URL,
            {"arquivo": arquivo, "coluna_identificador": "matricula", "dry_run": "false"},
            format="multipart",
        )
        assert resp.status_code == 200, resp.content
        body = resp.json()
        assert body["atualizados"] == 2
        with in_tenant(tenant_a):
            assert Servidor.objects.get(matricula="M001").cep == "49000-000"

    def test_upload_sem_arquivo_falha(
        self, api_client_factory, usuario_admin_a, tenant_a
    ):
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        resp = client.post(self.URL, {}, format="multipart")
        assert resp.status_code == 400
