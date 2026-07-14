"""Testes dos eventos periódicos S-1200/S-1202/S-1210 — Onda 4.5."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.core.management import call_command
from django_tenants.utils import schema_context

from apps.esocial.models import StatusEvento, TipoEvento
from apps.esocial.services.geracao import gerar_evento, tipo_remuneracao_para
from apps.esocial.services.validacao import validar_xml
from apps.payroll.models import Folha, Rubrica, StatusFolha, TipoFolha
from apps.payroll.services.calculo import calcular_folha
from apps.people.models import (
    Cargo,
    Lotacao,
    NaturezaLotacao,
    NivelEscolaridade,
    OrgaoEmissor,
    Regime,
    Servidor,
    Sexo,
    VinculoFuncional,
)

COMP = date(2026, 7, 1)


def _setup(regime=Regime.CELETISTA):
    call_command("seed_rubricas_incidencia")
    # de-para eSocial nas rubricas do seed (pré-requisito dos periódicos)
    Rubrica.objects.filter(codigo="SAL_BASE").update(
        natureza_esocial="1000", cod_inc_cp="11", cod_inc_irrf="11", cod_inc_fgts="11")
    Rubrica.objects.filter(codigo="INSS").update(
        natureza_esocial="9201", cod_inc_cp="31", cod_inc_irrf="9")
    Rubrica.objects.filter(codigo="IRRF").update(natureza_esocial="9203", cod_inc_irrf="31")
    orgao = OrgaoEmissor.objects.create(
        nome="Prefeitura de Teste", cnpj="12.345.678/0001-90", cnae_principal="8411600")
    cargo = Cargo.objects.create(codigo="C1", nome="Aux", nivel_escolaridade=NivelEscolaridade.MEDIO)
    lot = Lotacao.objects.create(codigo="L1", nome="Adm", natureza=NaturezaLotacao.ADMINISTRACAO)
    srv = Servidor.objects.create(matricula="P1", nome="Periodico", cpf="529.982.247-25",
                                  data_nascimento=date(1980, 1, 1), sexo=Sexo.MASCULINO)
    vin = VinculoFuncional.objects.create(
        servidor=srv, cargo=cargo, lotacao=lot, regime=regime,
        data_admissao=date(2020, 1, 6), carga_horaria=40, salario_base=Decimal("3000.00"))
    folha = Folha.objects.create(competencia=COMP, tipo=TipoFolha.MENSAL, status=StatusFolha.ABERTA)
    calcular_folha(folha)
    return orgao, folha, vin


@pytest.mark.django_db
class TestPeriodicos:
    def test_s1200_celetista_valido(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            orgao, folha, vin = _setup(Regime.CELETISTA)
            assert tipo_remuneracao_para(vin) == TipoEvento.S_1200
            ev = gerar_evento(orgao, TipoEvento.S_1200, folha=folha, vinculo=vin)
            assert ev.status == StatusEvento.VALIDADO
            validar_xml(ev.xml, TipoEvento.S_1200)
            assert "<codCateg>101</codCateg>" in ev.xml
            assert "<codRubr>SAL_BASE</codRubr>" in ev.xml

    def test_s1202_estatutario_valido(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            orgao, folha, vin = _setup(Regime.ESTATUTARIO)
            assert tipo_remuneracao_para(vin) == TipoEvento.S_1202
            ev = gerar_evento(orgao, TipoEvento.S_1202, folha=folha, vinculo=vin)
            assert ev.status == StatusEvento.VALIDADO
            validar_xml(ev.xml, TipoEvento.S_1202)
            assert "<codCateg>301</codCateg>" in ev.xml

    def test_regime_errado_barrado(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            orgao, folha, vin = _setup(Regime.ESTATUTARIO)
            with pytest.raises(ValueError):
                gerar_evento(orgao, TipoEvento.S_1200, folha=folha, vinculo=vin)

    def test_s1210_pagamento_valido(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            orgao, folha, vin = _setup(Regime.CELETISTA)
            ev = gerar_evento(orgao, TipoEvento.S_1210, folha=folha, vinculo=vin, sequencial=2)
            assert ev.status == StatusEvento.VALIDADO
            validar_xml(ev.xml, TipoEvento.S_1210)
            assert "<vrLiq>" in ev.xml


@pytest.mark.django_db
class TestGeracaoEmLote:
    def test_gerar_folha_regimes_mistos(self, api_client_factory, usuario_factory, tenant_a):
        usuario = usuario_factory(
            email="fin@arminda.test", papeis=[(tenant_a, "financeiro_municipio")]
        )
        with schema_context(tenant_a.schema_name):
            orgao, folha, _ = _setup(Regime.CELETISTA)
            # segundo vínculo, estatutário → deve sair como S-1202
            cargo = Cargo.objects.first()
            lot = Lotacao.objects.first()
            srv2 = Servidor.objects.create(
                matricula="P2", nome="Estatutario", cpf="111.444.777-35",
                data_nascimento=date(1985, 1, 1), sexo=Sexo.FEMININO)
            VinculoFuncional.objects.create(
                servidor=srv2, cargo=cargo, lotacao=lot, regime=Regime.ESTATUTARIO,
                data_admissao=date(2019, 1, 7), carga_horaria=40,
                salario_base=Decimal("4000.00"))
            calcular_folha(folha)  # recalcula com os 2 vínculos
        client = api_client_factory(user=usuario, tenant=tenant_a)
        r = client.post("/api/esocial/eventos/gerar-folha/", {
            "orgao_emissor": orgao.id, "folha": folha.id, "incluir_pagamentos": True,
        }, format="json")
        assert r.status_code == 201, r.json()
        corpo = r.json()
        assert corpo["erros"] == []
        assert corpo["gerados"] == 4  # 1×S-1200 + 1×S-1202 + 2×S-1210
        with schema_context(tenant_a.schema_name):
            from apps.esocial.models import EventoESocial
            tipos = sorted(EventoESocial.objects.values_list("tipo", flat=True))
            assert tipos == ["S-1200", "S-1202", "S-1210", "S-1210"]
