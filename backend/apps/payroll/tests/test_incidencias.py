"""
Testes de incidências automáticas — FGTS + RPPS (Onda 2.4 — ADR-0013).

Cobre:
- Bases automáticas: o flag `incide_*` alimenta BASE_* (sem RUBRICA() na mão).
- Gating por regime: estatutário com RPPS paga RPPS e não INSS; celetista
  paga INSS e gera FGTS; sem RPPS cadastrado, estatutário cai no INSS.
- RPPS flat e progressivo batem com `contribuicao_rpps`.
- Base do IRRF subtrai a previdência oficial (INSS ou RPPS).
- Convenção de fase: provento que depende de desconto erra (não calculado).
- Seed idempotente de rubricas de incidência.

INSS/IRRF usam as TabelaLegal seedadas (migration 0004) — os valores
esperados são calculados via `apps.calculo.tabelas` para não hardcodar.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.core.management import call_command
from django_tenants.utils import schema_context

from apps.calculo import tabelas
from apps.calculo.previdencia import contribuicao_rpps
from apps.payroll.models import (
    Folha,
    Lancamento,
    ModoContribuicaoRPPS,
    RegimePrevidenciario,
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

COMP = date(2026, 5, 1)


# ---------- helpers ----------


def _cargo():
    return Cargo.objects.create(
        codigo="C001", nome="Auxiliar", nivel_escolaridade=NivelEscolaridade.MEDIO
    )


def _lotacao():
    return Lotacao.objects.create(
        codigo="L001", nome="Administração", natureza=NaturezaLotacao.ADMINISTRACAO
    )


def _servidor(matricula="0001", nome="Servidor"):
    return Servidor.objects.create(
        matricula=matricula,
        nome=nome,
        cpf="000.000.000-00",
        data_nascimento=date(1985, 6, 1),
        sexo=Sexo.MASCULINO,
    )


def _vinculo(servidor, cargo, lotacao, *, regime=Regime.ESTATUTARIO, salario="4000.00"):
    return VinculoFuncional.objects.create(
        servidor=servidor,
        cargo=cargo,
        lotacao=lotacao,
        regime=regime,
        data_admissao=date(2020, 1, 1),
        carga_horaria=40,
        salario_base=Decimal(salario),
    )


def _rubrica(codigo, nome, formula, tipo=TipoRubrica.PROVENTO, **flags):
    return Rubrica.objects.create(
        codigo=codigo, nome=nome, tipo=tipo, formula=formula, **flags
    )


def _rpps_flat(aliquota="0.14", patronal="0.22", teto=None):
    return RegimePrevidenciario.objects.create(
        nome="IPM",
        modo_contribuicao=ModoContribuicaoRPPS.FLAT,
        aliquota_servidor=Decimal(aliquota),
        aliquota_patronal=Decimal(patronal),
        teto=Decimal(teto) if teto else None,
        vigencia_inicio=date(2020, 1, 1),
    )


def _folha():
    return Folha.objects.create(competencia=COMP, tipo=TipoFolha.MENSAL, status=StatusFolha.ABERTA)


def _valores(folha, vinculo):
    return {
        lanc.rubrica.codigo: lanc.valor
        for lanc in Lancamento.objects.filter(folha=folha, vinculo=vinculo)
    }


# ---------- testes ----------


@pytest.mark.django_db
class TestBasesAutomaticas:
    def test_flag_incide_inss_alimenta_base_inss(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            srv = _servidor()
            vin = _vinculo(srv, _cargo(), _lotacao())
            # Provento que entra na base do INSS + provento que não entra.
            _rubrica("PROV_TRIB", "Tributável", "1000", incide_inss=True)
            _rubrica("PROV_NTRIB", "Não tributável", "500", incide_inss=False)
            _rubrica("INSS", "INSS", "FAIXA_INSS(BASE_INSS)", TipoRubrica.DESCONTO)
            folha = _folha()

            calcular_folha(folha)
            vals = _valores(folha, vin)
            # BASE_INSS = 1000 (só PROV_TRIB) → INSS = tabela aplicada sobre 1000
            assert vals["INSS"] == tabelas.inss(Decimal("1000"), COMP)


@pytest.mark.django_db
class TestGatingPorRegime:
    def _seed_municipio_misto(self):
        """Município com RPPS flat 14%, rubricas padrão, 1 estatutário + 1 celetista."""
        _rpps_flat()
        call_command("seed_rubricas_incidencia")
        cargo, lot = _cargo(), _lotacao()
        est = _vinculo(_servidor("0001", "Efetivo"), cargo, lot, regime=Regime.ESTATUTARIO)
        clt = _vinculo(_servidor("0002", "Celetista"), cargo, lot, regime=Regime.CELETISTA)
        return est, clt

    def test_estatutario_paga_rpps_e_nao_inss(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            est, _ = self._seed_municipio_misto()
            folha = _folha()
            calcular_folha(folha)
            vals = _valores(folha, est)

            assert vals["INSS"] == Decimal("0.00")
            # RPPS flat 14% sobre 4000 = 560.00
            assert vals["RPPS"] == Decimal("560.00")
            # FGTS não incide para estatutário
            assert vals["FGTS"] == Decimal("0.00")
            # RPPS patronal informativo = 4000 * 0.22 = 880.00
            assert vals["RPPS_PATRONAL"] == Decimal("880.00")
            # IRRF: base 4000 - INSS(0) - RPPS(560), sem dependentes
            assert vals["IRRF"] == tabelas.irrf(Decimal("3440.00"), 0, COMP)

    def test_celetista_paga_inss_e_gera_fgts(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            _, clt = self._seed_municipio_misto()
            folha = _folha()
            calcular_folha(folha)
            vals = _valores(folha, clt)

            inss_esperado = tabelas.inss(Decimal("4000"), COMP)
            assert vals["INSS"] == inss_esperado
            assert vals["RPPS"] == Decimal("0.00")
            # FGTS 8% sobre 4000 = 320.00 (informativa)
            assert vals["FGTS"] == Decimal("320.00")
            assert vals["RPPS_PATRONAL"] == Decimal("0.00")
            # IRRF: base 4000 - INSS - RPPS(0)
            assert vals["IRRF"] == tabelas.irrf(Decimal("4000") - inss_esperado, 0, COMP)

    def test_sem_rpps_cadastrado_estatutario_cai_no_inss(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            # Sem RegimePrevidenciario → EH_RPPS=0 para todos.
            call_command("seed_rubricas_incidencia")
            est = _vinculo(_servidor(), _cargo(), _lotacao(), regime=Regime.ESTATUTARIO)
            folha = _folha()
            calcular_folha(folha)
            vals = _valores(folha, est)

            assert vals["RPPS"] == Decimal("0.00")
            assert vals["INSS"] == tabelas.inss(Decimal("4000"), COMP)

    def test_fgts_informativa_nao_entra_nos_totais(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            _, clt = self._seed_municipio_misto()
            folha = _folha()
            calcular_folha(folha)
            folha.refresh_from_db()
            # total de proventos = só SAL_BASE (4000) por vínculo × 2 vínculos
            assert folha.total_proventos == Decimal("8000.00")


@pytest.mark.django_db
class TestRPPSProgressivo:
    def test_rpps_progressivo_bate_com_funcao_pura(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            regime = RegimePrevidenciario.objects.create(
                nome="IPM Progressivo",
                modo_contribuicao=ModoContribuicaoRPPS.PROGRESSIVO,
                aliquota_patronal=Decimal("0.22"),
                faixas=[
                    {"ate": "1500.00", "aliquota": "0.075"},
                    {"ate": "3000.00", "aliquota": "0.12"},
                    {"ate": None, "aliquota": "0.14"},
                ],
                vigencia_inicio=date(2020, 1, 1),
            )
            call_command("seed_rubricas_incidencia")
            est = _vinculo(_servidor(), _cargo(), _lotacao(), salario="5000.00")
            folha = _folha()
            calcular_folha(folha)
            vals = _valores(folha, est)

            esperado = contribuicao_rpps(Decimal("5000"), regime.como_config())
            assert vals["RPPS"] == esperado
            assert esperado > Decimal("0")


@pytest.mark.django_db
class TestConvencaoDeFase:
    def test_provento_que_depende_de_desconto_erra(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            vin = _vinculo(_servidor(), _cargo(), _lotacao())
            # Provento referencia um desconto — só calculado na fase 2.
            _rubrica("PROV_RUIM", "Depende de desconto", "RUBRICA('INSS')")
            _rubrica("INSS", "INSS", "FAIXA_INSS(BASE_INSS)", TipoRubrica.DESCONTO)
            folha = _folha()

            rel = calcular_folha(folha)
            assert any(
                e.rubrica_codigo == "PROV_RUIM" and e.code == "FORMULA_RUBRICA_NAO_EXISTE"
                for e in rel.erros
            )
            # INSS (desconto) ainda é calculado normalmente.
            assert Lancamento.objects.filter(
                folha=folha, vinculo=vin, rubrica__codigo="INSS"
            ).exists()


@pytest.mark.django_db
class TestSeedRubricasIncidencia:
    def test_idempotente(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            call_command("seed_rubricas_incidencia")
            n1 = Rubrica.objects.count()
            call_command("seed_rubricas_incidencia")
            n2 = Rubrica.objects.count()
            assert n1 == n2 == 6
            # Conjunto esperado
            codigos = set(Rubrica.objects.values_list("codigo", flat=True))
            assert codigos == {"SAL_BASE", "INSS", "RPPS", "IRRF", "FGTS", "RPPS_PATRONAL"}
