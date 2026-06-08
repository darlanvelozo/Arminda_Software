"""
Testes de férias — Onda 3.3 (ADR-0017).

Cobre o cálculo (salário de férias + 1/3 tributáveis; abono pecuniário + 1/3
indenizados), o seletor por FeriasItem e a API dos itens.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.core.management import call_command
from django_tenants.utils import schema_context

from apps.calculo import tabelas
from apps.payroll.models import (
    FeriasItem,
    Folha,
    Lancamento,
    ModoContribuicaoRPPS,
    RegimePrevidenciario,
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


def _setup(regime=Regime.CELETISTA, salario="3000.00"):
    RegimePrevidenciario.objects.create(
        nome="IPM", modo_contribuicao=ModoContribuicaoRPPS.FLAT,
        aliquota_servidor=Decimal("0.14"), aliquota_patronal=Decimal("0.22"),
        vigencia_inicio=date(2010, 1, 1))
    call_command("seed_rubricas_incidencia")
    call_command("seed_rubricas_ferias")
    cargo = Cargo.objects.create(codigo="C1", nome="Aux", nivel_escolaridade=NivelEscolaridade.MEDIO)
    lot = Lotacao.objects.create(codigo="L1", nome="Adm", natureza=NaturezaLotacao.ADMINISTRACAO)
    srv = Servidor.objects.create(matricula="F1", nome="Feriado", cpf="000.000.000-00",
                                  data_nascimento=date(1985, 1, 1), sexo=Sexo.MASCULINO)
    vin = VinculoFuncional.objects.create(
        servidor=srv, cargo=cargo, lotacao=lot, regime=regime,
        data_admissao=date(2018, 1, 1), carga_horaria=40, salario_base=Decimal(salario))
    folha = Folha.objects.create(competencia=COMP, tipo=TipoFolha.FERIAS, status=StatusFolha.ABERTA)
    return vin, folha


def _vals(folha, vin):
    return {
        lanc.rubrica.codigo: lanc.valor
        for lanc in Lancamento.objects.filter(folha=folha, vinculo=vin)
    }


@pytest.mark.django_db
class TestSeletorFerias:
    def test_so_entra_quem_tem_item(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin, folha = _setup()
            # sem item → ninguém na folha
            rel = calcular_folha(folha)
            assert rel.vinculos_processados == 0
            # com item → entra
            FeriasItem.objects.create(folha=folha, vinculo=vin, dias_gozo=30, dias_abono=0)
            rel = calcular_folha(folha)
            assert rel.vinculos_processados == 1


@pytest.mark.django_db
class TestCalculoFerias:
    def test_gozo_30_dias_com_terco_e_incidencias(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin, folha = _setup()  # celetista 3000
            FeriasItem.objects.create(folha=folha, vinculo=vin, dias_gozo=30, dias_abono=0)
            calcular_folha(folha)
            v = _vals(folha, vin)
            # 30 dias = salário cheio
            assert v["FER_SALARIO"] == Decimal("3000.00")
            assert v["FER_TERCO"] == Decimal("1000.00")  # 3000/3
            assert v["FER_ABONO"] == Decimal("0.00")
            # INSS sobre base = salário + 1/3 = 4000 (celetista → RGPS)
            assert v["FER_INSS"] == tabelas.inss(Decimal("4000"), COMP)
            assert v["FER_RPPS"] == Decimal("0.00")

    def test_abono_pecuniario_nao_tributa(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin, folha = _setup()  # celetista 3000
            # 20 dias de gozo + 10 vendidos
            FeriasItem.objects.create(folha=folha, vinculo=vin, dias_gozo=20, dias_abono=10)
            calcular_folha(folha)
            v = _vals(folha, vin)
            assert v["FER_SALARIO"] == Decimal("2000.00")   # 3000/30*20
            assert v["FER_TERCO"] == Decimal("666.67")      # 2000/3
            assert v["FER_ABONO"] == Decimal("1000.00")     # 3000/30*10
            assert v["FER_ABONO_TERCO"] == Decimal("333.33")
            # INSS só sobre gozo+1/3 (2000+666.67=2666.67); abono fora
            assert v["FER_INSS"] == tabelas.inss(Decimal("2666.67"), COMP)

    def test_estatutario_rpps_sobre_ferias(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin, folha = _setup(regime=Regime.ESTATUTARIO)
            FeriasItem.objects.create(folha=folha, vinculo=vin, dias_gozo=30, dias_abono=0)
            calcular_folha(folha)
            v = _vals(folha, vin)
            # base 4000 (sal+1/3) * 0.14 = 560
            assert v["FER_RPPS"] == Decimal("560.00")
            assert v["FER_INSS"] == Decimal("0.00")


@pytest.mark.django_db
class TestFeriasItemAPI:
    @pytest.fixture
    def usuario_financeiro_a(self, usuario_factory, tenant_a):
        return usuario_factory(email="fin-a@arminda.test", papeis=[(tenant_a, "financeiro_municipio")])

    def test_cria_item_e_limita_abono(self, api_client_factory, usuario_financeiro_a, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin, folha = _setup()
        client = api_client_factory(user=usuario_financeiro_a, tenant=tenant_a)
        ok = client.post("/api/payroll/ferias-itens/", {
            "folha": folha.id, "vinculo": vin.id, "dias_gozo": 30, "dias_abono": 10,
        }, format="json")
        assert ok.status_code == 201, ok.json()
        ruim = client.post("/api/payroll/ferias-itens/", {
            "folha": folha.id, "vinculo": vin.id, "dias_gozo": 20, "dias_abono": 15,
        }, format="json")
        assert ruim.status_code == 400  # abono > 10
