"""
Testes dos resumos agregados da folha (v0.13.0).

resumo_por_servidor (1 linha por vínculo) e resumo_por_area (por lotação,
por órgão e geral). Garante que as somas batem com os totais da folha.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django_tenants.utils import schema_context

from apps.payroll.models import Folha, Rubrica, StatusFolha, TipoFolha, TipoRubrica
from apps.payroll.services.calculo import calcular_folha
from apps.payroll.services.resumo import resumo_por_area, resumo_por_servidor
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


def _cargo(c="C1"):
    return Cargo.objects.create(codigo=c, nome="Cargo " + c, nivel_escolaridade=NivelEscolaridade.MEDIO)


def _lot(c, nome):
    return Lotacao.objects.create(codigo=c, nome=nome, natureza=NaturezaLotacao.ADMINISTRACAO)


def _vinc(mat, nome, cargo, lot, salario):
    srv = Servidor.objects.create(
        matricula=mat, nome=nome, cpf="000.000.000-00",
        data_nascimento=date(1985, 1, 1), sexo=Sexo.MASCULINO,
    )
    return VinculoFuncional.objects.create(
        servidor=srv, cargo=cargo, lotacao=lot, regime=Regime.ESTATUTARIO,
        data_admissao=date(2018, 1, 1), carga_horaria=40, salario_base=Decimal(salario),
    )


def _setup():
    """2 servidores em lotações diferentes; SAL (provento) + TX (desconto fixo)."""
    cargo = _cargo()
    educ = _lot("L1", "Educação")
    saude = _lot("L2", "Saúde")
    _vinc("001", "Ana", cargo, educ, "3000.00")
    _vinc("002", "Bruno", cargo, saude, "5000.00")
    Rubrica.objects.create(codigo="SAL", nome="Salário", tipo=TipoRubrica.PROVENTO, formula="SALARIO_BASE")
    Rubrica.objects.create(codigo="TX", nome="Taxa", tipo=TipoRubrica.DESCONTO, formula="100")
    folha = Folha.objects.create(competencia=COMP, tipo=TipoFolha.MENSAL, status=StatusFolha.ABERTA)
    calcular_folha(folha)
    return folha


@pytest.mark.django_db
class TestResumoPorServidor:
    def test_uma_linha_por_servidor_com_totais(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            folha = _setup()
            linhas = resumo_por_servidor(folha)
            assert len(linhas) == 2
            por_nome = {ln["servidor_nome"]: ln for ln in linhas}
            assert por_nome["Ana"]["proventos"] == "3000.00"
            assert por_nome["Ana"]["descontos"] == "100.00"
            assert por_nome["Ana"]["liquido"] == "2900.00"
            assert por_nome["Bruno"]["liquido"] == "4900.00"
            assert por_nome["Ana"]["lotacao"] == "Educação"


@pytest.mark.django_db
class TestResumoPorArea:
    def test_por_lotacao_e_geral_batem_com_folha(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            folha = _setup()
            r = resumo_por_area(folha)
            lot = {x["nome"]: x for x in r["por_lotacao"]}
            assert lot["Educação"]["liquido"] == "2900.00"
            assert lot["Saúde"]["liquido"] == "4900.00"
            # Geral bate com os totais persistidos na folha
            folha.refresh_from_db()
            assert r["geral"]["proventos"] == str(folha.total_proventos)
            assert r["geral"]["descontos"] == str(folha.total_descontos)
            assert r["geral"]["liquido"] == str(folha.total_liquido)

    def test_sem_orgao_emissor_vira_rotulo_padrao(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            folha = _setup()  # vínculos sem orgao_emissor
            r = resumo_por_area(folha)
            nomes = {x["nome"] for x in r["por_orgao"]}
            assert "(sem órgão)" in nomes


@pytest.mark.django_db
class TestResumoEndpoints:
    def test_endpoint_servidores(self, api_client_factory, usuario_leitura_a, tenant_a):
        with schema_context(tenant_a.schema_name):
            folha = _setup()
        client = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        r = client.get(f"/api/payroll/folhas/{folha.id}/servidores/")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_endpoint_resumo(self, api_client_factory, usuario_leitura_a, tenant_a):
        with schema_context(tenant_a.schema_name):
            folha = _setup()
        client = api_client_factory(user=usuario_leitura_a, tenant=tenant_a)
        r = client.get(f"/api/payroll/folhas/{folha.id}/resumo/")
        assert r.status_code == 200
        body = r.json()
        assert {"por_lotacao", "por_orgao", "geral"} <= set(body)
