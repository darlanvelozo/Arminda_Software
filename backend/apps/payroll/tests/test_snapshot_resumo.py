"""Testes da Onda 4.4 (ADR-0021): snapshot fiscal + ResumoFolha + folha imutável."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.core.management import call_command
from django_tenants.utils import schema_context

from apps.payroll.models import (
    Folha,
    Lancamento,
    ResumoFolha,
    Rubrica,
    StatusFolha,
    TipoFolha,
)
from apps.payroll.services.calculo import FolhaFechadaError, calcular_folha
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
    call_command("seed_rubricas_incidencia")
    cargo = Cargo.objects.create(codigo="C1", nome="Aux", nivel_escolaridade=NivelEscolaridade.MEDIO)
    lot = Lotacao.objects.create(codigo="L1", nome="Adm", natureza=NaturezaLotacao.ADMINISTRACAO)
    srv = Servidor.objects.create(matricula="SN1", nome="Snapshotado", cpf="000.000.000-00",
                                  data_nascimento=date(1980, 1, 1), sexo=Sexo.MASCULINO)
    vin = VinculoFuncional.objects.create(
        servidor=srv, cargo=cargo, lotacao=lot, regime=Regime.CELETISTA,
        data_admissao=date(2020, 1, 6), carga_horaria=40, salario_base=Decimal(salario))
    folha = Folha.objects.create(competencia=COMP, tipo=TipoFolha.MENSAL, status=StatusFolha.ABERTA)
    return vin, folha


@pytest.mark.django_db
class TestSnapshotFiscal:
    def test_lancamento_congela_incidencias_da_rubrica(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin, folha = _setup()
            Rubrica.objects.filter(codigo="SAL_BASE").update(natureza_esocial="1000")
            calcular_folha(folha)
            lanc = Lancamento.objects.get(folha=folha, vinculo=vin, rubrica__codigo="SAL_BASE")
            assert lanc.snap_incide_inss is True
            assert lanc.snap_natureza_esocial == "1000"
            # editar a rubrica DEPOIS não altera o lançamento já calculado
            Rubrica.objects.filter(codigo="SAL_BASE").update(incide_inss=False, natureza_esocial="9999")
            lanc.refresh_from_db()
            assert lanc.snap_incide_inss is True
            assert lanc.snap_natureza_esocial == "1000"

    def test_folha_fechada_nao_recalcula(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin, folha = _setup()
            calcular_folha(folha)
            folha.status = StatusFolha.FECHADA
            folha.save(update_fields=["status"])
            with pytest.raises(FolhaFechadaError):
                calcular_folha(folha)


@pytest.mark.django_db
class TestResumoFolha:
    def test_resumo_persistido_com_bases(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin, folha = _setup()  # salário 3000, celetista
            calcular_folha(folha)
            resumo = ResumoFolha.objects.get(folha=folha, vinculo=vin)
            assert resumo.total_liquido == resumo.total_proventos - resumo.total_descontos
            # bases acumuladas pelos proventos (o gating por regime acontece
            # no desconto via EH_*; a base é o potencial por flag)
            assert resumo.base_inss > 0
            assert resumo.base_fgts > 0
            assert resumo.base_irrf > 0
            # coerência com a soma dos lançamentos-provento que incidem INSS
            soma_inss = sum(
                lc.valor for lc in Lancamento.objects.filter(
                    folha=folha, vinculo=vin, snap_incide_inss=True,
                    rubrica__tipo="provento",
                )
            )
            assert resumo.base_inss == soma_inss
            # idempotente: recalcular não duplica
            calcular_folha(folha)
            assert ResumoFolha.objects.filter(folha=folha).count() == 1

    def test_api_bases(self, api_client_factory, usuario_factory, tenant_a):
        usuario = usuario_factory(email="fin@arminda.test", papeis=[(tenant_a, "financeiro_municipio")])
        with schema_context(tenant_a.schema_name):
            vin, folha = _setup()
            calcular_folha(folha)
        client = api_client_factory(user=usuario, tenant=tenant_a)
        r = client.get(f"/api/payroll/folhas/{folha.id}/bases/")
        assert r.status_code == 200, r.json()
        corpo = r.json()
        assert len(corpo) == 1
        assert Decimal(corpo[0]["base_inss"]) > 0
        assert corpo[0]["excluir_s1200"] is False
