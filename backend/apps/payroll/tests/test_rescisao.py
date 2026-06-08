"""
Testes da rescisão — Onda 3.2 (ADR-0016).

Cobre avos de férias, seletor de vínculos (demitido no mês entra mesmo
inativo), verbas (saldo, 13º prop, férias prop/vencidas + 1/3, aviso),
incidências (saldo e 13º tributam em separado; indenizadas não tributam),
gating por motivo e multa de 40% sobre o saldo do FGTS.
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
from apps.payroll.services.rescisao import avos_ferias
from apps.people.models import (
    Cargo,
    Lotacao,
    MotivoDemissao,
    NaturezaLotacao,
    NivelEscolaridade,
    Regime,
    Servidor,
    Sexo,
    VinculoFuncional,
)

COMP = date(2026, 6, 1)


class TestAvosFerias:
    def test_periodo_completo(self):
        # admitido 2018-01-01, demitido 2026-06-15 → aquisitivo 2026-01..06, jun 15 dias
        assert avos_ferias(date(2018, 1, 1), date(2026, 6, 15)) == 6

    def test_aniversario_no_meio(self):
        # admitido 2025-03-10; demitido 2026-06-15 → aquisitivo desde 2026-03-10
        # mar(10→fim=22d), abr, mai, jun(15) = 4
        assert avos_ferias(date(2025, 3, 10), date(2026, 6, 15)) == 4


def _setup(regime=Regime.CELETISTA, motivo=MotivoDemissao.SEM_JUSTA_CAUSA, *,
           aviso=True, vencidas=True, saldo_fgts="10000.00", ativo=False,
           demissao=date(2026, 6, 15), admissao=date(2018, 1, 1)):
    RegimePrevidenciario.objects.create(
        nome="IPM", modo_contribuicao=ModoContribuicaoRPPS.FLAT,
        aliquota_servidor=Decimal("0.14"), aliquota_patronal=Decimal("0.22"),
        vigencia_inicio=date(2010, 1, 1))
    call_command("seed_rubricas_incidencia")
    call_command("seed_rubricas_rescisao")
    cargo = Cargo.objects.create(codigo="C1", nome="Aux", nivel_escolaridade=NivelEscolaridade.MEDIO)
    lot = Lotacao.objects.create(codigo="L1", nome="Adm", natureza=NaturezaLotacao.ADMINISTRACAO)
    srv = Servidor.objects.create(matricula="R1", nome="Rescindido", cpf="000.000.000-00",
                                  data_nascimento=date(1985, 1, 1), sexo=Sexo.MASCULINO)
    return VinculoFuncional.objects.create(
        servidor=srv, cargo=cargo, lotacao=lot, regime=regime,
        data_admissao=admissao, data_demissao=demissao, ativo=ativo,
        carga_horaria=40, salario_base=Decimal("3000.00"),
        motivo_demissao=motivo, aviso_previo_indenizado=aviso,
        tem_ferias_vencidas=vencidas, saldo_fgts=Decimal(saldo_fgts))


def _folha():
    return Folha.objects.create(competencia=COMP, tipo=TipoFolha.RESCISAO, status=StatusFolha.ABERTA)


def _vals(folha, vin):
    return {
        lanc.rubrica.codigo: lanc.valor
        for lanc in Lancamento.objects.filter(folha=folha, vinculo=vin)
    }


@pytest.mark.django_db
class TestSeletorRescisao:
    def test_demitido_no_mes_entra_mesmo_inativo(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin = _setup(ativo=False)
            folha = _folha()
            rel = calcular_folha(folha)
            assert rel.vinculos_processados == 1
            assert "RESC_SALDO" in _vals(folha, vin)

    def test_nao_demitido_nao_entra(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            _setup(demissao=date(2026, 9, 20))  # fora de junho
            folha = _folha()
            rel = calcular_folha(folha)
            assert rel.vinculos_processados == 0


@pytest.mark.django_db
class TestVerbasSemJustaCausa:
    def test_verbas_e_incidencias(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin = _setup()  # celetista, sem justa causa, aviso, vencidas, saldo_fgts 10000
            folha = _folha()
            calcular_folha(folha)
            v = _vals(folha, vin)

            # Proventos
            assert v["RESC_SALDO"] == Decimal("1500.00")        # 3000/30*15
            assert v["RESC_13"] == Decimal("1500.00")           # 3000*6/12
            assert v["RESC_FERIAS_PROP"] == Decimal("1500.00")  # 3000*6/12
            assert v["RESC_FERIAS_PROP_13"] == Decimal("500.00")
            assert v["RESC_FERIAS_VENC"] == Decimal("3000.00")
            assert v["RESC_FERIAS_VENC_13"] == Decimal("1000.00")
            assert v["RESC_AVISO"] == Decimal("3000.00")        # celetista sem justa causa

            # Incidências: BASE_INSS = só o saldo (1500); indenizadas não tributam
            inss_saldo = tabelas.inss(Decimal("1500"), COMP)
            assert v["RESC_INSS"] == inss_saldo
            assert v["RESC_IRRF"] == tabelas.irrf(Decimal("1500") - inss_saldo, 0, COMP)
            # 13º em separado
            assert v["RESC_13_INSS"] == tabelas.inss(Decimal("1500"), COMP)

            # FGTS do mês = 8% de (saldo + 13º) = 8% de 3000 = 240; multa = 40% de 10000
            assert v["RESC_FGTS"] == Decimal("240.00")
            assert v["RESC_FGTS_MULTA"] == Decimal("4000.00")


@pytest.mark.django_db
class TestGatingMotivo:
    def test_justa_causa_perde_13_e_ferias_prop(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin = _setup(motivo=MotivoDemissao.COM_JUSTA_CAUSA, aviso=False)
            folha = _folha()
            calcular_folha(folha)
            v = _vals(folha, vin)
            assert v["RESC_13"] == Decimal("0.00")
            assert v["RESC_FERIAS_PROP"] == Decimal("0.00")
            assert v["RESC_AVISO"] == Decimal("0.00")
            assert v["RESC_FGTS_MULTA"] == Decimal("0.00")
            # mantém saldo e férias vencidas
            assert v["RESC_SALDO"] == Decimal("1500.00")
            assert v["RESC_FERIAS_VENC"] == Decimal("3000.00")

    def test_pedido_sem_aviso_nem_multa(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin = _setup(motivo=MotivoDemissao.PEDIDO_DEMISSAO, aviso=False)
            folha = _folha()
            calcular_folha(folha)
            v = _vals(folha, vin)
            # mantém 13º e férias proporcionais
            assert v["RESC_13"] == Decimal("1500.00")
            assert v["RESC_FERIAS_PROP"] == Decimal("1500.00")
            # sem aviso indenizado nem multa
            assert v["RESC_AVISO"] == Decimal("0.00")
            assert v["RESC_FGTS_MULTA"] == Decimal("0.00")

    def test_estatutario_sem_fgts_nem_aviso(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin = _setup(regime=Regime.ESTATUTARIO, motivo=MotivoDemissao.EXONERACAO, aviso=False)
            folha = _folha()
            calcular_folha(folha)
            v = _vals(folha, vin)
            assert v["RESC_AVISO"] == Decimal("0.00")     # não celetista
            assert v["RESC_FGTS"] == Decimal("0.00")       # estatutário não gera FGTS
            assert v["RESC_FGTS_MULTA"] == Decimal("0.00")
            # estatutário com RPPS: RPPS sobre o saldo
            assert v["RESC_RPPS"] == Decimal("210.00")     # 1500 * 0.14
