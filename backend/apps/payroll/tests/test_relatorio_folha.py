"""Testes do relatório da folha em PDF (Onda 4.4b)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.core.management import call_command
from django_tenants.utils import schema_context

from apps.payroll.models import Folha, StatusFolha, TipoFolha
from apps.payroll.services.calculo import calcular_folha
from apps.payroll.services.relatorio_folha import gerar_relatorio_pdf
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
    call_command("seed_rubricas_incidencia")
    cargo = Cargo.objects.create(codigo="C1", nome="Aux", nivel_escolaridade=NivelEscolaridade.MEDIO)
    # nome longo de propósito: regressão do estouro de coluna no PDF
    lot = Lotacao.objects.create(
        codigo="L1",
        nome="Secretaria Municipal de Educação, Cultura, Esporte e Lazer",
        natureza=NaturezaLotacao.ADMINISTRACAO,
    )
    for i in (1, 2):
        srv = Servidor.objects.create(matricula=f"RF{i}", nome=f"Servidor {i}", cpf=f"00{i}.000.000-00",
                                      data_nascimento=date(1980, 1, 1), sexo=Sexo.MASCULINO)
        VinculoFuncional.objects.create(
            servidor=srv, cargo=cargo, lotacao=lot, regime=Regime.CELETISTA,
            data_admissao=date(2020, 1, 6), carga_horaria=40, salario_base=Decimal("2500.00"))
    folha = Folha.objects.create(competencia=COMP, tipo=TipoFolha.MENSAL, status=StatusFolha.ABERTA)
    calcular_folha(folha)
    return folha


@pytest.mark.django_db
class TestRelatorioFolhaPDF:
    def test_gera_pdf_valido(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            folha = _setup()
            pdf = gerar_relatorio_pdf(folha)
            assert pdf.startswith(b"%PDF")
            assert len(pdf) > 1500

    def test_api_relatorio_pdf(self, api_client_factory, usuario_factory, tenant_a):
        usuario = usuario_factory(email="le@arminda.test", papeis=[(tenant_a, "leitura_municipio")])
        with schema_context(tenant_a.schema_name):
            folha = _setup()
        client = api_client_factory(user=usuario, tenant=tenant_a)
        r = client.get(f"/api/payroll/folhas/{folha.id}/relatorio-pdf/")
        assert r.status_code == 200
        assert r["Content-Type"] == "application/pdf"
        assert r.content.startswith(b"%PDF")
        assert "folha-mensal-2026-07.pdf" in r["Content-Disposition"]
