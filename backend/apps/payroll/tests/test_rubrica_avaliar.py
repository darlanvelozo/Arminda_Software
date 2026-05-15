"""
Testes do endpoint POST /api/payroll/rubricas/{id}/avaliar/ (Bloco 2.1).

Cobre o caminho feliz + cada `code` de erro de fórmula traduzido para
HTTP 400 com payload `{detail, code}`.
"""

from __future__ import annotations

import pytest
from django_tenants.utils import schema_context

from apps.payroll.models import Rubrica, TipoRubrica


@pytest.fixture
def rubrica_simples(tenant_a):
    with schema_context(tenant_a.schema_name):
        r = Rubrica.objects.create(
            codigo="SALARIO-10P",
            nome="10% do salário-base",
            tipo=TipoRubrica.PROVENTO,
            formula="SALARIO_BASE * 0.10",
        )
    yield r.pk


@pytest.fixture
def rubrica_com_dependentes(tenant_a):
    with schema_context(tenant_a.schema_name):
        r = Rubrica.objects.create(
            codigo="IRRF-SIMPL",
            nome="IRRF simplificado",
            tipo=TipoRubrica.DESCONTO,
            formula=(
                "ARRED("
                "SE(DEPENDENTES > 0, SALARIO_BASE * 0.10 - DEPENDENTES * 189.59, "
                "SALARIO_BASE * 0.10)"
                ", 2)"
            ),
        )
    yield r.pk


@pytest.mark.django_db
class TestAvaliarEndpoint:
    def test_avalia_formula_simples(
        self, api_client_factory, usuario_admin_a, tenant_a, rubrica_simples
    ):
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        response = client.post(
            f"/api/payroll/rubricas/{rubrica_simples}/avaliar/",
            {"contexto": {"SALARIO_BASE": "1320.00"}},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["valor"] == "132.000"

    def test_avalia_formula_complexa_com_dependentes(
        self,
        api_client_factory,
        usuario_admin_a,
        tenant_a,
        rubrica_com_dependentes,
    ):
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        response = client.post(
            f"/api/payroll/rubricas/{rubrica_com_dependentes}/avaliar/",
            {"contexto": {"SALARIO_BASE": "1320.00", "DEPENDENTES": 2}},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["valor"] == "-247.18"

    def test_variavel_ausente_retorna_400_com_code(
        self, api_client_factory, usuario_admin_a, tenant_a, rubrica_simples
    ):
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        response = client.post(
            f"/api/payroll/rubricas/{rubrica_simples}/avaliar/",
            {"contexto": {}},  # SALARIO_BASE ausente
            format="json",
        )
        assert response.status_code == 400
        body = response.json()
        assert body["code"] == "FORMULA_VARIAVEL_AUSENTE"

    def test_rubrica_sem_formula_retorna_400(
        self, api_client_factory, usuario_admin_a, tenant_a
    ):
        with schema_context(tenant_a.schema_name):
            r = Rubrica.objects.create(
                codigo="VAZIA",
                nome="Sem fórmula",
                tipo=TipoRubrica.PROVENTO,
                formula="",
            )
            pk = r.pk
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        response = client.post(
            f"/api/payroll/rubricas/{pk}/avaliar/",
            {"contexto": {}},
            format="json",
        )
        assert response.status_code == 400
        assert response.json()["code"] == "FORMULA_VAZIA"

    def test_papel_leitura_pode_avaliar(
        self,
        api_client_factory,
        usuario_leitura_a,
        tenant_a,
        rubrica_simples,
    ):
        # Avaliação é leitura — leitura_municipio também pode disparar
        client = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        response = client.post(
            f"/api/payroll/rubricas/{rubrica_simples}/avaliar/",
            {"contexto": {"SALARIO_BASE": "1000"}},
            format="json",
        )
        assert response.status_code == 200

    def test_sem_auth_falha(self, api_client, tenant_a, rubrica_simples):
        api_client.defaults["HTTP_X_TENANT"] = tenant_a.schema_name
        response = api_client.post(
            f"/api/payroll/rubricas/{rubrica_simples}/avaliar/",
            {"contexto": {"SALARIO_BASE": "1000"}},
            format="json",
        )
        assert response.status_code == 401
