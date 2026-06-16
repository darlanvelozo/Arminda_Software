"""Testes de folha complementar — Onda 3.5 (ADR-0019)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django_tenants.utils import schema_context

from apps.payroll.models import (
    ComplementarItem,
    Folha,
    Lancamento,
    Rubrica,
    StatusFolha,
    TipoFolha,
    TipoRubrica,
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


def _setup():
    prov = Rubrica.objects.create(
        codigo="DIF_SALARIO", nome="Diferença salarial", tipo=TipoRubrica.PROVENTO,
        tipos_folha=[TipoFolha.COMPLEMENTAR], formula="")
    desc = Rubrica.objects.create(
        codigo="DIF_INSS", nome="INSS complementar", tipo=TipoRubrica.DESCONTO,
        tipos_folha=[TipoFolha.COMPLEMENTAR], formula="")
    cargo = Cargo.objects.create(codigo="C1", nome="Aux", nivel_escolaridade=NivelEscolaridade.MEDIO)
    lot = Lotacao.objects.create(codigo="L1", nome="Adm", natureza=NaturezaLotacao.ADMINISTRACAO)
    srv = Servidor.objects.create(matricula="CP1", nome="Complementado", cpf="000.000.000-00",
                                  data_nascimento=date(1980, 1, 1), sexo=Sexo.MASCULINO)
    vin = VinculoFuncional.objects.create(
        servidor=srv, cargo=cargo, lotacao=lot, regime=Regime.ESTATUTARIO,
        data_admissao=date(2010, 1, 1), carga_horaria=40, salario_base=Decimal("3000.00"))
    folha = Folha.objects.create(competencia=COMP, tipo=TipoFolha.COMPLEMENTAR, status=StatusFolha.ABERTA)
    return vin, folha, prov, desc


@pytest.mark.django_db
class TestComplementar:
    def test_so_entra_quem_tem_item(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin, folha, prov, _ = _setup()
            assert calcular_folha(folha).vinculos_processados == 0
            ComplementarItem.objects.create(folha=folha, vinculo=vin, rubrica=prov, valor=Decimal("500.00"))
            assert calcular_folha(folha).vinculos_processados == 1

    def test_proventos_e_descontos_explicitos(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin, folha, prov, desc = _setup()
            ComplementarItem.objects.create(folha=folha, vinculo=vin, rubrica=prov, valor=Decimal("500.00"))
            ComplementarItem.objects.create(folha=folha, vinculo=vin, rubrica=desc, valor=Decimal("55.00"))
            calcular_folha(folha)
            # valores explícitos viram lançamentos, sem fórmula
            vals = {lc.rubrica.codigo: lc.valor for lc in Lancamento.objects.filter(folha=folha)}
            assert vals == {"DIF_SALARIO": Decimal("500.00"), "DIF_INSS": Decimal("55.00")}
            folha.refresh_from_db()
            assert folha.total_proventos == Decimal("500.00")
            assert folha.total_descontos == Decimal("55.00")
            assert folha.total_liquido == Decimal("445.00")
            # idempotente: re-rodar não duplica nem altera totais
            calcular_folha(folha)
            folha.refresh_from_db()
            assert Lancamento.objects.filter(folha=folha).count() == 2
            assert folha.total_liquido == Decimal("445.00")

    def test_api_cria_item(self, api_client_factory, usuario_factory, tenant_a):
        usuario = usuario_factory(email="fin@arminda.test", papeis=[(tenant_a, "financeiro_municipio")])
        with schema_context(tenant_a.schema_name):
            vin, folha, prov, _ = _setup()
        client = api_client_factory(user=usuario, tenant=tenant_a)
        r = client.post("/api/payroll/complementar-itens/", {
            "folha": folha.id, "vinculo": vin.id, "rubrica": prov.id, "valor": "500.00",
        }, format="json")
        assert r.status_code == 201, r.json()
        # valor <= 0 é rejeitado
        r2 = client.post("/api/payroll/complementar-itens/", {
            "folha": folha.id, "vinculo": vin.id, "rubrica": prov.id, "valor": "0.00",
        }, format="json")
        assert r2.status_code == 400
