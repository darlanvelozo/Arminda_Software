"""Testes de licença-prêmio (indenização) — Onda 3.4 (ADR-0018)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.core.management import call_command
from django_tenants.utils import schema_context

from apps.payroll.models import (
    Folha,
    Lancamento,
    LicencaPremioItem,
    StatusFolha,
    TipoFolha,
)
from apps.payroll.services.calculo import calcular_folha
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

COMP = date(2026, 7, 1)


def _setup(salario="3000.00"):
    call_command("seed_rubricas_licenca_premio")
    cargo = Cargo.objects.create(codigo="C1", nome="Aux", nivel_escolaridade=NivelEscolaridade.MEDIO)
    lot = Lotacao.objects.create(codigo="L1", nome="Adm", natureza=NaturezaLotacao.ADMINISTRACAO)
    srv = Servidor.objects.create(matricula="LP1", nome="Premiado", cpf="000.000.000-00",
                                  data_nascimento=date(1980, 1, 1), sexo=Sexo.MASCULINO)
    vin = VinculoFuncional.objects.create(
        servidor=srv, cargo=cargo, lotacao=lot, regime=Regime.ESTATUTARIO,
        data_admissao=date(2010, 1, 1), carga_horaria=40, salario_base=Decimal(salario))
    folha = Folha.objects.create(competencia=COMP, tipo=TipoFolha.LICENCA_PREMIO, status=StatusFolha.ABERTA)
    return vin, folha


def _vals(folha, vin):
    return {l.rubrica.codigo: l.valor for l in Lancamento.objects.filter(folha=folha, vinculo=vin)}  # noqa: E741


@pytest.mark.django_db
class TestLicencaPremio:
    def test_so_entra_quem_tem_item(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin, folha = _setup()
            assert calcular_folha(folha).vinculos_processados == 0
            LicencaPremioItem.objects.create(folha=folha, vinculo=vin, meses=3, dias=0)
            assert calcular_folha(folha).vinculos_processados == 1

    def test_indenizacao_meses_e_dias_sem_incidencia(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin, folha = _setup()  # salário 3000
            LicencaPremioItem.objects.create(folha=folha, vinculo=vin, meses=3, dias=15)
            calcular_folha(folha)
            v = _vals(folha, vin)
            # 3000*3 + 3000/30*15 = 9000 + 1500 = 10500; indenizatória → só LP_INDENIZ
            assert v == {"LP_INDENIZ": Decimal("10500.00")}

    def test_api_cria_item(self, api_client_factory, usuario_factory, tenant_a):
        usuario = usuario_factory(email="fin@arminda.test", papeis=[(tenant_a, "financeiro_municipio")])
        with schema_context(tenant_a.schema_name):
            vin, folha = _setup()
        client = api_client_factory(user=usuario, tenant=tenant_a)
        r = client.post("/api/payroll/licenca-premio-itens/", {
            "folha": folha.id, "vinculo": vin.id, "meses": 3, "dias": 0,
        }, format="json")
        assert r.status_code == 201, r.json()
