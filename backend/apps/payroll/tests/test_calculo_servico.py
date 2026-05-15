"""
Testes do serviço `calcular_folha` (Bloco 2.2).

Cobertura:
- Caminho feliz: 1 vínculo × 2 rubricas em sequência (dependência).
- Idempotência: 2 execuções da mesma folha = mesmo estado.
- Limpeza de órfãos: rubrica desativada entre runs → lançamento removido.
- Erro de fórmula isolado: vínculo com fórmula problemática não para o batch.
- Vínculo desligado antes da competência fica de fora.
- Vínculo admitido depois da competência fica de fora.
- Ciclo de dependência aborta o cálculo (transação inteira).
- Dependência inexistente aborta o cálculo.
- Totais da folha (proventos, descontos, líquido) são atualizados.
- Status `aberta` → `calculada` ao final.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django_tenants.utils import schema_context

from apps.calculo.dependencias import DependenciaCiclicaError, DependenciaInexistenteError
from apps.payroll.models import Folha, Lancamento, Rubrica, StatusFolha, TipoFolha, TipoRubrica
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

# ============================================================
# Helpers de criação (a chamada de cada teste fica enxuta)
# ============================================================


def _criar_cargo(codigo="C001", nome="Auxiliar"):
    return Cargo.objects.create(
        codigo=codigo,
        nome=nome,
        nivel_escolaridade=NivelEscolaridade.MEDIO,
    )


def _criar_lotacao(codigo="L001", nome="Secretaria Administracao"):
    return Lotacao.objects.create(
        codigo=codigo,
        nome=nome,
        natureza=NaturezaLotacao.ADMINISTRACAO,
    )


def _criar_servidor(matricula="0001", nome="Servidor Teste", nascimento=date(1980, 1, 1)):
    return Servidor.objects.create(
        matricula=matricula,
        nome=nome,
        cpf="000.000.000-00",
        data_nascimento=nascimento,
        sexo=Sexo.MASCULINO,
    )


def _criar_vinculo(
    servidor,
    cargo,
    lotacao,
    *,
    salario=Decimal("3000.00"),
    admissao=date(2020, 1, 1),
    demissao=None,
    ativo=True,
):
    return VinculoFuncional.objects.create(
        servidor=servidor,
        cargo=cargo,
        lotacao=lotacao,
        regime=Regime.ESTATUTARIO,
        data_admissao=admissao,
        data_demissao=demissao,
        carga_horaria=40,
        salario_base=salario,
        ativo=ativo,
    )


def _criar_rubrica(codigo, nome, formula, tipo=TipoRubrica.PROVENTO):
    return Rubrica.objects.create(
        codigo=codigo,
        nome=nome,
        tipo=tipo,
        formula=formula,
    )


def _criar_folha(competencia=date(2026, 5, 1)):
    return Folha.objects.create(
        competencia=competencia,
        tipo=TipoFolha.MENSAL,
        status=StatusFolha.ABERTA,
    )


# ============================================================
# Testes
# ============================================================


@pytest.mark.django_db
class TestCalcularFolha:
    def test_caminho_feliz_com_dependencia(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            cargo = _criar_cargo()
            lot = _criar_lotacao()
            srv = _criar_servidor()
            vin = _criar_vinculo(srv, cargo, lot, salario=Decimal("3000.00"))
            _criar_rubrica("SAL_BASE", "Salário base", "SALARIO_BASE", TipoRubrica.PROVENTO)
            _criar_rubrica(
                "INSS",
                "INSS 11%",
                "RUBRICA('SAL_BASE') * 0.11",
                TipoRubrica.DESCONTO,
            )
            folha = _criar_folha()

            rel = calcular_folha(folha)

            assert rel.vinculos_processados == 1
            assert rel.rubricas_processadas == 2
            assert rel.lancamentos_criados == 2
            assert rel.lancamentos_atualizados == 0
            assert rel.erros == []
            assert rel.ordem_rubricas == ["SAL_BASE", "INSS"]

            # Lançamentos
            lancs = Lancamento.objects.filter(folha=folha, vinculo=vin)
            por_codigo = {lanc.rubrica.codigo: lanc.valor for lanc in lancs}
            assert por_codigo["SAL_BASE"] == Decimal("3000.00")
            # 3000 * 0.11 = 330
            assert por_codigo["INSS"] == Decimal("330.00")

            # Totais da folha
            folha.refresh_from_db()
            assert folha.total_proventos == Decimal("3000.00")
            assert folha.total_descontos == Decimal("330.00")
            assert folha.total_liquido == Decimal("2670.00")
            assert folha.status == StatusFolha.CALCULADA

    def test_idempotencia(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            cargo = _criar_cargo()
            lot = _criar_lotacao()
            srv = _criar_servidor()
            _criar_vinculo(srv, cargo, lot, salario=Decimal("2000.00"))
            _criar_rubrica("SAL_BASE", "Salário", "SALARIO_BASE")
            folha = _criar_folha()

            rel1 = calcular_folha(folha)
            assert rel1.lancamentos_criados == 1
            assert rel1.lancamentos_atualizados == 0
            qtd_apos_1 = Lancamento.objects.filter(folha=folha).count()

            rel2 = calcular_folha(folha)
            assert rel2.lancamentos_criados == 0
            assert rel2.lancamentos_atualizados == 1
            qtd_apos_2 = Lancamento.objects.filter(folha=folha).count()
            assert qtd_apos_1 == qtd_apos_2 == 1

            folha.refresh_from_db()
            assert folha.total_proventos == Decimal("2000.00")

    def test_limpa_orfaos_quando_rubrica_some(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            cargo = _criar_cargo()
            lot = _criar_lotacao()
            srv = _criar_servidor()
            _criar_vinculo(srv, cargo, lot)
            _criar_rubrica("A", "Rubrica A", "100")
            r_b = _criar_rubrica("B", "Rubrica B", "200")
            folha = _criar_folha()

            calcular_folha(folha)
            assert Lancamento.objects.filter(folha=folha).count() == 2

            # Desativa B — próxima execução deve remover o lançamento órfão
            r_b.ativo = False
            r_b.save(update_fields=["ativo"])

            rel = calcular_folha(folha)
            assert rel.lancamentos_removidos == 1
            assert Lancamento.objects.filter(folha=folha).count() == 1
            assert Lancamento.objects.get(folha=folha).rubrica.codigo == "A"

    def test_erro_de_formula_em_um_vinculo_nao_para_o_batch(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            cargo = _criar_cargo()
            lot = _criar_lotacao()
            srv1 = _criar_servidor(matricula="0001", nome="Alice")
            srv2 = _criar_servidor(matricula="0002", nome="Bruno")
            _criar_vinculo(srv1, cargo, lot)
            _criar_vinculo(srv2, cargo, lot)
            # Fórmula referencia variável inexistente — falha runtime, não estrutura
            _criar_rubrica("MISTERIO", "Variável inexistente", "VAR_QUE_NAO_EXISTE * 2")
            _criar_rubrica("OK", "Rubrica OK", "100")
            folha = _criar_folha()

            rel = calcular_folha(folha)

            # 2 vínculos × 2 rubricas, mas MISTERIO erra para os 2 → 2 erros
            assert len(rel.erros) == 2
            assert all(e.rubrica_codigo == "MISTERIO" for e in rel.erros)
            assert all(e.code == "FORMULA_VARIAVEL_AUSENTE" for e in rel.erros)
            # Mas OK foi calculada para os 2 vínculos
            assert Lancamento.objects.filter(folha=folha, rubrica__codigo="OK").count() == 2
            assert Lancamento.objects.filter(folha=folha, rubrica__codigo="MISTERIO").count() == 0

    def test_vinculo_desligado_antes_da_competencia_eh_ignorado(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            cargo = _criar_cargo()
            lot = _criar_lotacao()
            srv_ativo = _criar_servidor(matricula="0001", nome="Ativo")
            srv_demitido = _criar_servidor(matricula="0002", nome="Demitido")
            _criar_vinculo(srv_ativo, cargo, lot)
            _criar_vinculo(
                srv_demitido, cargo, lot, demissao=date(2026, 3, 15)
            )  # antes de mai/2026
            _criar_rubrica("SAL", "Salário", "SALARIO_BASE")
            folha = _criar_folha(competencia=date(2026, 5, 1))

            rel = calcular_folha(folha)
            assert rel.vinculos_processados == 1
            assert Lancamento.objects.filter(folha=folha).count() == 1

    def test_vinculo_admitido_depois_da_competencia_eh_ignorado(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            cargo = _criar_cargo()
            lot = _criar_lotacao()
            srv_antigo = _criar_servidor(matricula="0001", nome="Antigo")
            srv_novato = _criar_servidor(matricula="0002", nome="Novato")
            _criar_vinculo(srv_antigo, cargo, lot, admissao=date(2020, 1, 1))
            _criar_vinculo(srv_novato, cargo, lot, admissao=date(2026, 6, 15))  # depois
            _criar_rubrica("SAL", "Salário", "SALARIO_BASE")
            folha = _criar_folha(competencia=date(2026, 5, 1))

            rel = calcular_folha(folha)
            assert rel.vinculos_processados == 1

    def test_ciclo_de_dependencia_aborta(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            cargo = _criar_cargo()
            lot = _criar_lotacao()
            srv = _criar_servidor()
            _criar_vinculo(srv, cargo, lot)
            _criar_rubrica("A", "A", "RUBRICA('B')")
            _criar_rubrica("B", "B", "RUBRICA('A')")
            folha = _criar_folha()

            with pytest.raises(DependenciaCiclicaError):
                calcular_folha(folha)

            # Nada foi gravado (transação abortada)
            assert Lancamento.objects.filter(folha=folha).count() == 0

    def test_dependencia_inexistente_aborta(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            cargo = _criar_cargo()
            lot = _criar_lotacao()
            srv = _criar_servidor()
            _criar_vinculo(srv, cargo, lot)
            _criar_rubrica("X", "X", "RUBRICA('NAO_EXISTE') + 1")
            folha = _criar_folha()

            with pytest.raises(DependenciaInexistenteError):
                calcular_folha(folha)
            assert Lancamento.objects.filter(folha=folha).count() == 0

    def test_folha_sem_rubricas_eh_estado_legitimo(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            folha = _criar_folha()
            rel = calcular_folha(folha)
            assert rel.lancamentos_criados == 0
            assert rel.vinculos_processados == 0
            # Status NÃO muda — nada foi calculado
            folha.refresh_from_db()
            assert folha.status == StatusFolha.ABERTA

    def test_rubrica_sem_formula_eh_ignorada(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            cargo = _criar_cargo()
            lot = _criar_lotacao()
            srv = _criar_servidor()
            _criar_vinculo(srv, cargo, lot)
            _criar_rubrica("MANUAL", "Manual", "")  # sem fórmula
            _criar_rubrica("AUTO", "Auto", "100")
            folha = _criar_folha()

            rel = calcular_folha(folha)
            assert rel.lancamentos_criados == 1
            assert Lancamento.objects.get(folha=folha).rubrica.codigo == "AUTO"
            # Sem erros — rubrica sem fórmula é placeholder legítimo
            assert rel.erros == []

    def test_rubricas_informativas_nao_entram_nos_totais(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            cargo = _criar_cargo()
            lot = _criar_lotacao()
            srv = _criar_servidor()
            _criar_vinculo(srv, cargo, lot, salario=Decimal("1000.00"))
            _criar_rubrica("PROV", "Provento", "SALARIO_BASE", TipoRubrica.PROVENTO)
            _criar_rubrica("DESC", "Desconto", "100", TipoRubrica.DESCONTO)
            _criar_rubrica("INFO", "Informativa", "999", TipoRubrica.INFORMATIVA)
            folha = _criar_folha()

            calcular_folha(folha)
            folha.refresh_from_db()
            assert folha.total_proventos == Decimal("1000.00")
            assert folha.total_descontos == Decimal("100.00")
            assert folha.total_liquido == Decimal("900.00")
            # Lançamento informativo existe mas não entra nos totais
            assert Lancamento.objects.filter(folha=folha).count() == 3
