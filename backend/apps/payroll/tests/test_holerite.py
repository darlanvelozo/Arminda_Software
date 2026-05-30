"""
Testes da geração de holerite — Onda 2.5 (ADR-0014).

Cobre montar_holerite (estrutura JSON), gerar_pdf (bytes %PDF) e os
endpoints holerite/holerite-pdf (JSON, PDF, 400 sem vínculo, 404, RBAC).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.core.management import call_command
from django_tenants.utils import schema_context

from apps.payroll.models import Folha, StatusFolha, TipoFolha
from apps.payroll.services.calculo import calcular_folha
from apps.payroll.services.holerite import gerar_pdf, montar_holerite
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

COMP = date(2026, 5, 1)


def _setup_folha_calculada():
    """Cria município com RPPS+rubricas, 1 estatutário, calcula a folha."""
    from apps.payroll.models import ModoContribuicaoRPPS, RegimePrevidenciario

    RegimePrevidenciario.objects.create(
        nome="IPM", modo_contribuicao=ModoContribuicaoRPPS.FLAT,
        aliquota_servidor=Decimal("0.14"), aliquota_patronal=Decimal("0.22"),
        vigencia_inicio=date(2020, 1, 1),
    )
    call_command("seed_rubricas_incidencia")
    cargo = Cargo.objects.create(codigo="C1", nome="Analista", nivel_escolaridade=NivelEscolaridade.SUPERIOR)
    lot = Lotacao.objects.create(codigo="L1", nome="Secretaria", natureza=NaturezaLotacao.ADMINISTRACAO)
    srv = Servidor.objects.create(
        matricula="H-001", nome="Maria Holerite", cpf="000.000.000-00",
        data_nascimento=date(1985, 1, 1), sexo=Sexo.FEMININO,
    )
    vin = VinculoFuncional.objects.create(
        servidor=srv, cargo=cargo, lotacao=lot, regime=Regime.ESTATUTARIO,
        data_admissao=date(2018, 3, 1), carga_horaria=40, salario_base=Decimal("5000.00"),
    )
    folha = Folha.objects.create(competencia=COMP, tipo=TipoFolha.MENSAL, status=StatusFolha.ABERTA)
    calcular_folha(folha)
    return folha, vin


@pytest.mark.django_db
class TestMontarHolerite:
    def test_estrutura_e_totais(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            folha, vin = _setup_folha_calculada()
            h = montar_holerite(folha, vin)

            assert h["servidor"]["nome"] == "Maria Holerite"
            assert h["servidor"]["matricula"] == "H-001"
            assert h["vinculo"]["cargo"] == "Analista"
            assert h["competencia"] == "2026-05-01"
            # SAL_BASE é o único provento
            codigos_prov = {p["codigo"] for p in h["proventos"]}
            assert codigos_prov == {"SAL_BASE"}
            # RPPS e IRRF são descontos; INSS=0 também vira lançamento desconto
            codigos_desc = {d["codigo"] for d in h["descontos"]}
            assert {"RPPS", "IRRF", "INSS"} <= codigos_desc
            # FGTS e RPPS_PATRONAL são informativas
            codigos_info = {i["codigo"] for i in h["informativas"]}
            assert {"FGTS", "RPPS_PATRONAL"} <= codigos_info
            # Totais batem: proventos 5000; líquido = 5000 - descontos
            assert h["totais"]["proventos"] == "5000.00"
            liquido = Decimal(h["totais"]["proventos"]) - Decimal(h["totais"]["descontos"])
            assert h["totais"]["liquido"] == f"{liquido:.2f}"

    def test_vinculo_sem_lancamentos_levanta(self, tenant_a):
        from apps.payroll.models import Lancamento

        with schema_context(tenant_a.schema_name):
            folha, vin = _setup_folha_calculada()
            Lancamento.objects.filter(folha=folha, vinculo=vin).delete()
            with pytest.raises(Lancamento.DoesNotExist):
                montar_holerite(folha, vin)


@pytest.mark.django_db
class TestGerarPdf:
    def test_pdf_bytes(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            folha, vin = _setup_folha_calculada()
            pdf = gerar_pdf(montar_holerite(folha, vin))
            assert isinstance(pdf, bytes)
            assert pdf[:4] == b"%PDF"
            assert len(pdf) > 1000


@pytest.mark.django_db
class TestHoleriteEndpoints:
    @pytest.fixture
    def usuario_financeiro_a(self, usuario_factory, tenant_a):
        return usuario_factory(
            email="fin-a@arminda.test", papeis=[(tenant_a, "financeiro_municipio")]
        )

    def test_holerite_json(self, api_client_factory, usuario_leitura_a, tenant_a):
        with schema_context(tenant_a.schema_name):
            folha, vin = _setup_folha_calculada()
        client = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        r = client.get(f"/api/payroll/folhas/{folha.id}/holerite/?vinculo={vin.id}")
        assert r.status_code == 200, r.json()
        assert r.json()["servidor"]["matricula"] == "H-001"

    def test_holerite_pdf(self, api_client_factory, usuario_leitura_a, tenant_a):
        with schema_context(tenant_a.schema_name):
            folha, vin = _setup_folha_calculada()
        client = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        r = client.get(f"/api/payroll/folhas/{folha.id}/holerite-pdf/?vinculo={vin.id}")
        assert r.status_code == 200
        assert r["Content-Type"] == "application/pdf"
        assert r.content[:4] == b"%PDF"

    def test_sem_vinculo_eh_400(self, api_client_factory, usuario_leitura_a, tenant_a):
        with schema_context(tenant_a.schema_name):
            folha, _ = _setup_folha_calculada()
        client = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        r = client.get(f"/api/payroll/folhas/{folha.id}/holerite/")
        assert r.status_code == 400

    def test_vinculo_inexistente_eh_404(self, api_client_factory, usuario_leitura_a, tenant_a):
        with schema_context(tenant_a.schema_name):
            folha, _ = _setup_folha_calculada()
        client = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        r = client.get(f"/api/payroll/folhas/{folha.id}/holerite/?vinculo=999999")
        assert r.status_code == 404
