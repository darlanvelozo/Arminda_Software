"""
Testes do 13º salário — Onda 3.1 (ADR-0015).

Cobre avos (ano cheio, admissão no meio, demissão), escopo de rubrica por
tipo de folha, 1ª parcela (adiantamento sem incidência) e 2ª parcela
(13º integral + INSS/IRRF/RPPS sobre o 13º + abatimento do adiantamento).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.core.management import call_command
from django_tenants.utils import schema_context

from apps.calculo import tabelas
from apps.payroll.models import (
    Folha,
    Lancamento,
    ModoContribuicaoRPPS,
    RegimePrevidenciario,
    StatusFolha,
    TipoFolha,
)
from apps.payroll.services.calculo import calcular_folha
from apps.payroll.services.decimo import avos_no_ano
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
# Avos (função pura)
# ============================================================


class TestAvos:
    def test_ano_cheio(self):
        assert avos_no_ano(date(2020, 1, 1), None, 2026) == 12

    def test_admitido_no_meio_conta_mes_com_15_dias(self):
        # Admitido em 16/03 → março tem 16 dias (≥15) → conta; total mar-dez = 10
        assert avos_no_ano(date(2026, 3, 16), None, 2026) == 10
        # Admitido em 17/03 → março tem 15 dias → conta (>=15)
        assert avos_no_ano(date(2026, 3, 17), None, 2026) == 10
        # Admitido em 18/03 → março tem 14 dias → não conta; abr-dez = 9
        assert avos_no_ano(date(2026, 3, 18), None, 2026) == 9

    def test_demitido_no_meio(self):
        # Trabalhou jan-jun (demissão 30/06) → 6 avos
        assert avos_no_ano(date(2020, 1, 1), date(2026, 6, 30), 2026) == 6

    def test_fora_do_ano(self):
        assert avos_no_ano(date(2027, 1, 1), None, 2026) == 0


# ============================================================
# Cálculo do 13º (integração)
# ============================================================

COMP_13 = date(2026, 12, 1)


def _folha(tipo):
    return Folha.objects.create(competencia=COMP_13, tipo=tipo, status=StatusFolha.ABERTA)


def _vals(folha, vin):
    return {
        lanc.rubrica.codigo: lanc.valor
        for lanc in Lancamento.objects.filter(folha=folha, vinculo=vin)
    }


@pytest.mark.django_db
class TestEscopoPorTipo:
    def test_folha_mensal_nao_roda_rubricas_de_13(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin = _setup_simple()
            folha = _folha(TipoFolha.MENSAL)
            calcular_folha(folha)
            codigos = set(_vals(folha, vin).keys())
            assert "SAL_BASE" in codigos
            assert not any(c.startswith("13_") for c in codigos)

    def test_folha_13_nao_roda_rubricas_mensais(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin = _setup_simple()
            folha = _folha(TipoFolha.DECIMO_SEGUNDO)
            calcular_folha(folha)
            codigos = set(_vals(folha, vin).keys())
            assert "SAL_BASE" not in codigos
            assert "13_PROV" in codigos


@pytest.mark.django_db
class TestParcelas:
    def test_primeira_parcela_eh_metade_sem_incidencia(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin = _setup_simple()
            folha = _folha(TipoFolha.DECIMO_PRIMEIRO)
            calcular_folha(folha)
            vals = _vals(folha, vin)
            # 4000 * 12/12 * 0.5 = 2000
            assert vals["13_ADIANT"] == Decimal("2000.00")
            assert set(vals.keys()) == {"13_ADIANT"}  # sem INSS/IRRF na 1ª

    def test_segunda_parcela_incidencias_sobre_o_13(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin = _setup_simple()
            folha = _folha(TipoFolha.DECIMO_SEGUNDO)
            calcular_folha(folha)
            vals = _vals(folha, vin)
            assert vals["13_PROV"] == Decimal("4000.00")
            # estatutário c/ RPPS: INSS=0, RPPS=14% de 4000=560
            assert vals["13_INSS"] == Decimal("0.00")
            assert vals["13_RPPS"] == Decimal("560.00")
            # IRRF sobre 4000 - 0 - 560
            assert vals["13_IRRF"] == tabelas.irrf(Decimal("3440.00"), 0, COMP_13)
            # abatimento do adiantamento = 2000
            assert vals["13_ADIANT_DESC"] == Decimal("2000.00")

    def test_avos_proporcional_reduz_13(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin = _setup_simple(admissao=date(2026, 7, 1))  # jul-dez = 6 avos
            folha = _folha(TipoFolha.DECIMO_SEGUNDO)
            calcular_folha(folha)
            vals = _vals(folha, vin)
            # 4000 * 6/12 = 2000
            assert vals["13_PROV"] == Decimal("2000.00")


# ---- helper de setup enxuto ----


def _setup_simple(admissao=date(2018, 1, 1)):
    RegimePrevidenciario.objects.create(
        nome="IPM", modo_contribuicao=ModoContribuicaoRPPS.FLAT,
        aliquota_servidor=Decimal("0.14"), aliquota_patronal=Decimal("0.22"),
        vigencia_inicio=date(2010, 1, 1),
    )
    call_command("seed_rubricas_incidencia")
    call_command("seed_rubricas_13")
    cargo = Cargo.objects.create(codigo="C1", nome="Analista", nivel_escolaridade=NivelEscolaridade.SUPERIOR)
    lot = Lotacao.objects.create(codigo="L1", nome="Sec", natureza=NaturezaLotacao.ADMINISTRACAO)
    srv = Servidor.objects.create(
        matricula="001", nome="Ana", cpf="000.000.000-00",
        data_nascimento=date(1985, 1, 1), sexo=Sexo.FEMININO,
    )
    return VinculoFuncional.objects.create(
        servidor=srv, cargo=cargo, lotacao=lot, regime=Regime.ESTATUTARIO,
        data_admissao=admissao, carga_horaria=40, salario_base=Decimal("4000.00"),
    )
