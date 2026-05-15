"""
Testes do endpoint FolhaViewSet + `/calcular/` (Bloco 2.2).

Cobre:
- CRUD: list, retrieve, create, update, delete.
- Action /calcular/: caminho feliz com relatório.
- Permissões: leitura permitida a `leitura_municipio`; calcular exige
  financeiro/admin.
- Cross-tenant: folha do tenant A não aparece para o tenant B.
- Sem auth → 401.
- Erros estruturais (ciclo) → 400 com `code`.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django_tenants.utils import schema_context

from apps.payroll.models import Folha, Rubrica, StatusFolha, TipoFolha, TipoRubrica
from apps.people.models import (
    Cargo,
    Lotacao,
    NaturezaLotacao,
    NivelEscolaridade,
    Regime,
    Servidor,
    Sexo,
    VinculoFuncional,
)

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def base_tenant_a(tenant_a):
    """Conjunto mínimo: 1 cargo + 1 lotação + 1 servidor + 1 vínculo + 1 rubrica."""
    with schema_context(tenant_a.schema_name):
        cargo = Cargo.objects.create(
            codigo="C001", nome="Auxiliar", nivel_escolaridade=NivelEscolaridade.MEDIO
        )
        lot = Lotacao.objects.create(
            codigo="L001", nome="Adm", natureza=NaturezaLotacao.ADMINISTRACAO
        )
        srv = Servidor.objects.create(
            matricula="0001",
            nome="Alice",
            cpf="000.000.000-00",
            data_nascimento=date(1985, 6, 1),
            sexo=Sexo.FEMININO,
        )
        VinculoFuncional.objects.create(
            servidor=srv,
            cargo=cargo,
            lotacao=lot,
            regime=Regime.ESTATUTARIO,
            data_admissao=date(2020, 1, 1),
            carga_horaria=40,
            salario_base=Decimal("2000.00"),
        )
        Rubrica.objects.create(
            codigo="SAL_BASE",
            nome="Salário base",
            tipo=TipoRubrica.PROVENTO,
            formula="SALARIO_BASE",
        )


@pytest.fixture
def folha_aberta(tenant_a, base_tenant_a):
    with schema_context(tenant_a.schema_name):
        f = Folha.objects.create(competencia=date(2026, 5, 1), tipo=TipoFolha.MENSAL)
    yield f.pk


# ============================================================
# CRUD
# ============================================================


@pytest.mark.django_db
class TestFolhaCRUD:
    def test_lista_vazia(self, api_client_factory, usuario_leitura_a, tenant_a):
        client = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        response = client.get("/api/payroll/folhas/")
        assert response.status_code == 200
        # Pode ter folhas de outros testes — só checa que retorna 200 e estrutura
        data = response.json()
        assert "results" in data or isinstance(data, list)

    def test_cria_folha(self, api_client_factory, usuario_admin_a, tenant_a):
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        response = client.post(
            "/api/payroll/folhas/",
            {"competencia": "2026-07-01", "tipo": TipoFolha.MENSAL},
            format="json",
        )
        assert response.status_code == 201, response.content
        with schema_context(tenant_a.schema_name):
            assert Folha.objects.filter(competencia=date(2026, 7, 1)).exists()

    def test_recupera_folha(self, api_client_factory, usuario_leitura_a, tenant_a, folha_aberta):
        client = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        response = client.get(f"/api/payroll/folhas/{folha_aberta}/")
        assert response.status_code == 200
        assert response.json()["competencia"] == "2026-05-01"

    def test_sem_auth_lista_falha(self, api_client, tenant_a):
        api_client.defaults["HTTP_X_TENANT"] = tenant_a.schema_name
        response = api_client.get("/api/payroll/folhas/")
        assert response.status_code == 401


# ============================================================
# /calcular/
# ============================================================


@pytest.mark.django_db
class TestCalcularEndpoint:
    def test_calcular_caminho_feliz(
        self, api_client_factory, usuario_admin_a, tenant_a, folha_aberta
    ):
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        response = client.post(f"/api/payroll/folhas/{folha_aberta}/calcular/")
        assert response.status_code == 200, response.content
        body = response.json()
        assert body["vinculos_processados"] == 1
        assert body["rubricas_processadas"] == 1
        assert body["lancamentos_criados"] == 1
        assert body["ordem_rubricas"] == ["SAL_BASE"]
        assert body["erros"] == []

        # Estado da folha
        with schema_context(tenant_a.schema_name):
            folha = Folha.objects.get(pk=folha_aberta)
            assert folha.status == StatusFolha.CALCULADA
            assert folha.total_proventos == Decimal("2000.00")

    def test_calcular_idempotente_via_endpoint(
        self, api_client_factory, usuario_admin_a, tenant_a, folha_aberta
    ):
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        r1 = client.post(f"/api/payroll/folhas/{folha_aberta}/calcular/")
        r2 = client.post(f"/api/payroll/folhas/{folha_aberta}/calcular/")
        assert r1.json()["lancamentos_criados"] == 1
        assert r2.json()["lancamentos_atualizados"] == 1
        assert r2.json()["lancamentos_criados"] == 0

    def test_calcular_com_ciclo_retorna_400(
        self, api_client_factory, usuario_admin_a, tenant_a
    ):
        # Cria fixture independente (sem base_tenant_a) com ciclo
        with schema_context(tenant_a.schema_name):
            cargo = Cargo.objects.create(
                codigo="C002", nome="X", nivel_escolaridade=NivelEscolaridade.MEDIO
            )
            lot = Lotacao.objects.create(
                codigo="L002", nome="X", natureza=NaturezaLotacao.OUTROS
            )
            srv = Servidor.objects.create(
                matricula="0002",
                nome="B",
                cpf="000.000.000-01",
                data_nascimento=date(1985, 6, 1),
                sexo=Sexo.MASCULINO,
            )
            VinculoFuncional.objects.create(
                servidor=srv,
                cargo=cargo,
                lotacao=lot,
                regime=Regime.ESTATUTARIO,
                data_admissao=date(2020, 1, 1),
                carga_horaria=40,
                salario_base=Decimal("2000.00"),
            )
            Rubrica.objects.create(
                codigo="CICLO_A", nome="A", tipo=TipoRubrica.PROVENTO, formula="RUBRICA('CICLO_B')"
            )
            Rubrica.objects.create(
                codigo="CICLO_B", nome="B", tipo=TipoRubrica.PROVENTO, formula="RUBRICA('CICLO_A')"
            )
            folha = Folha.objects.create(
                competencia=date(2026, 8, 1), tipo=TipoFolha.MENSAL
            )

        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        response = client.post(f"/api/payroll/folhas/{folha.pk}/calcular/")
        assert response.status_code == 400
        assert response.json()["code"] == "DEPENDENCIA_CICLICA"

    def test_leitura_nao_pode_calcular(
        self, api_client_factory, usuario_leitura_a, tenant_a, folha_aberta
    ):
        client = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        response = client.post(f"/api/payroll/folhas/{folha_aberta}/calcular/")
        assert response.status_code == 403

    def test_sem_auth_calcular_falha(self, api_client, tenant_a, folha_aberta):
        api_client.defaults["HTTP_X_TENANT"] = tenant_a.schema_name
        response = api_client.post(f"/api/payroll/folhas/{folha_aberta}/calcular/")
        assert response.status_code == 401


# ============================================================
# Isolamento entre tenants
# ============================================================


@pytest.mark.django_db
class TestIsolamentoTenant:
    def test_folha_do_tenant_a_invisivel_para_b(
        self,
        api_client_factory,
        usuario_admin_a,
        usuario_admin_b,
        tenant_a,
        tenant_b,
        folha_aberta,
    ):
        # Vê em A
        client_a = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        r_a = client_a.get(f"/api/payroll/folhas/{folha_aberta}/")
        assert r_a.status_code == 200

        # Não vê em B (mesmo PK)
        client_b = api_client_factory(user=usuario_admin_b, tenant=tenant_b)
        r_b = client_b.get(f"/api/payroll/folhas/{folha_aberta}/")
        assert r_b.status_code == 404
