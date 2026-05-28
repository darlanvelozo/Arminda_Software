"""
Testes HTTP de OrgaoEmissor e Sindicato (Onda 1.6a).

Cobre:
- CRUD completo dos dois recursos.
- Validação CNPJ no body.
- Isolamento por tenant (OrgaoEmissor de A não aparece em B).
- RBAC: leitura permite, escrita exige RH/admin/staff.
- FK de Vinculo apontando para OrgaoEmissor/Sindicato funciona.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django_tenants.utils import schema_context

from apps.people.models import (
    Cargo,
    Lotacao,
    NaturezaLotacao,
    NivelEscolaridade,
    OrgaoEmissor,
    Regime,
    Servidor,
    Sexo,
    Sindicato,
    VinculoFuncional,
)

# ============================================================
# Payloads de teste
# ============================================================

CNPJ_VALIDO_1 = "11.222.333/0001-81"   # Receita Federal exemplo
CNPJ_VALIDO_2 = "00.000.000/0001-91"   # Banco do Brasil matriz
CNPJ_INVALIDO = "11.222.333/0001-82"   # último dígito errado

ORGAO_PAYLOAD = {
    "nome": "Prefeitura Municipal de Smoke Test",
    "sigla": "PMST",
    "cnpj": CNPJ_VALIDO_1,
    "eh_principal": True,
    "cnae_principal": "8411600",
    "tipo_logradouro": "avenida",
    "logradouro": "Brasil",
    "numero": "1000",
    "bairro": "Centro",
    "cidade": "Smoke",
    "uf": "MA",
    "cep": "65900-000",
    "ativo": True,
}

SINDICATO_PAYLOAD = {
    "nome": "Sindicato dos Servidores Municipais de Smoke",
    "cnpj": CNPJ_VALIDO_2,
    "codigo_sindical": "001.123.45678-9",
    "categoria": "Servidores Públicos Municipais",
    "base_territorial": "Smoke/MA",
    "ativo": True,
}


# ============================================================
# OrgaoEmissor — CRUD + validações
# ============================================================


@pytest.mark.django_db
class TestOrgaoEmissorCrud:
    BASE = "/api/people/orgaos-emissores/"

    def test_cria_orgao_emissor(self, api_client_factory, usuario_admin_a, tenant_a):
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        response = client.post(self.BASE, ORGAO_PAYLOAD, format="json")
        assert response.status_code == 201, response.content
        body = response.json()
        assert body["nome"] == "Prefeitura Municipal de Smoke Test"
        # CNPJ serializa em dígitos puros (validador normaliza)
        assert body["cnpj"] == "11222333000181"
        assert body["cnae_principal"] == "8411600"
        assert body["eh_principal"] is True

    def test_lista_orgaos(self, api_client_factory, usuario_leitura_a, tenant_a):
        with schema_context(tenant_a.schema_name):
            OrgaoEmissor.objects.create(**{**ORGAO_PAYLOAD, "cnpj": "11222333000181"})
        client = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        response = client.get(self.BASE)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1

    def test_cnpj_invalido_rejeitado(
        self, api_client_factory, usuario_admin_a, tenant_a
    ):
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        payload = {**ORGAO_PAYLOAD, "cnpj": CNPJ_INVALIDO}
        response = client.post(self.BASE, payload, format="json")
        assert response.status_code == 400
        assert "cnpj" in response.json()

    def test_cnpj_duplicado_rejeitado(
        self, api_client_factory, usuario_admin_a, tenant_a
    ):
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        client.post(self.BASE, ORGAO_PAYLOAD, format="json")
        response = client.post(self.BASE, ORGAO_PAYLOAD, format="json")
        assert response.status_code == 400

    def test_cnae_tamanho_errado(self, api_client_factory, usuario_admin_a, tenant_a):
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        payload = {**ORGAO_PAYLOAD, "cnae_principal": "841"}  # < 7 dígitos
        response = client.post(self.BASE, payload, format="json")
        assert response.status_code == 400

    def test_leitura_nao_pode_criar(
        self, api_client_factory, usuario_leitura_a, tenant_a
    ):
        client = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        response = client.post(self.BASE, ORGAO_PAYLOAD, format="json")
        assert response.status_code == 403

    def test_sem_auth_falha(self, api_client, tenant_a):
        api_client.defaults["HTTP_X_TENANT"] = tenant_a.schema_name
        response = api_client.get(self.BASE)
        assert response.status_code == 401


# ============================================================
# Sindicato — CRUD + validações
# ============================================================


@pytest.mark.django_db
class TestSindicatoCrud:
    BASE = "/api/people/sindicatos/"

    def test_cria_sindicato(self, api_client_factory, usuario_admin_a, tenant_a):
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        response = client.post(self.BASE, SINDICATO_PAYLOAD, format="json")
        assert response.status_code == 201, response.content
        body = response.json()
        assert body["nome"].startswith("Sindicato")
        assert body["cnpj"] == "00000000000191"
        assert body["categoria"] == "Servidores Públicos Municipais"

    def test_cnpj_invalido_rejeitado(
        self, api_client_factory, usuario_admin_a, tenant_a
    ):
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        payload = {**SINDICATO_PAYLOAD, "cnpj": CNPJ_INVALIDO}
        response = client.post(self.BASE, payload, format="json")
        assert response.status_code == 400

    def test_lista(self, api_client_factory, usuario_leitura_a, tenant_a):
        with schema_context(tenant_a.schema_name):
            Sindicato.objects.create(
                **{**SINDICATO_PAYLOAD, "cnpj": "00000000000191"}
            )
        client = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        response = client.get(self.BASE)
        assert response.status_code == 200


# ============================================================
# Isolamento entre tenants
# ============================================================


@pytest.mark.django_db
class TestIsolamentoTenants:
    def test_orgao_de_a_invisivel_em_b(
        self, api_client_factory, usuario_admin_a, usuario_admin_b, tenant_a, tenant_b
    ):
        # Cria em A
        with schema_context(tenant_a.schema_name):
            OrgaoEmissor.objects.create(**{**ORGAO_PAYLOAD, "cnpj": "11222333000181"})
        # Lista em B
        client_b = api_client_factory(user=usuario_admin_b, tenant=tenant_b)
        response = client_b.get("/api/people/orgaos-emissores/")
        assert response.status_code == 200
        # B não enxerga nada de A
        assert response.json()["count"] == 0


# ============================================================
# FKs: Vinculo aponta para OrgaoEmissor/Sindicato
# ============================================================


@pytest.mark.django_db
class TestVinculoComOrgaoESindicato:
    def test_cria_vinculo_com_orgao_e_sindicato(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            cargo = Cargo.objects.create(
                codigo="C1", nome="Aux", nivel_escolaridade=NivelEscolaridade.MEDIO
            )
            lot = Lotacao.objects.create(
                codigo="L1", nome="ADM", natureza=NaturezaLotacao.ADMINISTRACAO
            )
            srv = Servidor.objects.create(
                matricula="V001",
                nome="Servidor Teste",
                cpf="529.982.247-25",
                data_nascimento=date(1980, 1, 1),
                sexo=Sexo.MASCULINO,
            )
            orgao = OrgaoEmissor.objects.create(**{**ORGAO_PAYLOAD, "cnpj": "11222333000181"})
            sind = Sindicato.objects.create(**{**SINDICATO_PAYLOAD, "cnpj": "00000000000191"})

            v = VinculoFuncional.objects.create(
                servidor=srv,
                cargo=cargo,
                lotacao=lot,
                orgao_emissor=orgao,
                sindicato=sind,
                regime=Regime.ESTATUTARIO,
                data_admissao=date(2020, 1, 1),
                carga_horaria=40,
                salario_base=Decimal("3000.00"),
            )
            assert v.orgao_emissor == orgao
            assert v.sindicato == sind

    def test_sindicato_apaga_seta_null_no_vinculo(self, tenant_a):
        """on_delete=SET_NULL no Sindicato — vínculo continua existindo."""
        with schema_context(tenant_a.schema_name):
            cargo = Cargo.objects.create(
                codigo="C2", nome="X", nivel_escolaridade=NivelEscolaridade.MEDIO
            )
            lot = Lotacao.objects.create(
                codigo="L2", nome="Y", natureza=NaturezaLotacao.OUTROS
            )
            srv = Servidor.objects.create(
                matricula="V002",
                nome="Outro",
                cpf="248.438.034-80",
                data_nascimento=date(1985, 6, 1),
                sexo=Sexo.FEMININO,
            )
            sind = Sindicato.objects.create(**{**SINDICATO_PAYLOAD, "cnpj": "00000000000191"})
            v = VinculoFuncional.objects.create(
                servidor=srv,
                cargo=cargo,
                lotacao=lot,
                sindicato=sind,
                regime=Regime.ESTATUTARIO,
                data_admissao=date(2021, 3, 1),
                carga_horaria=40,
                salario_base=Decimal("2500.00"),
            )
            sind.delete()
            v.refresh_from_db()
            assert v.sindicato is None
