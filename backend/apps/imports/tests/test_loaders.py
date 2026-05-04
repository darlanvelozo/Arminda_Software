"""
Testes dos loaders contra Postgres (Bloco 1.4).

Usam fixtures de tenant + apenas o schema dele (não tocam Firebird —
passamos rows simulados como input).
"""

from __future__ import annotations

from datetime import date

import pytest
from django_tenants.utils import schema_context

from apps.imports.models import SipImportRecord, StatusImportacao, TipoEntidadeSip
from apps.imports.services.loaders.cargos import load_cargos
from apps.imports.services.loaders.dependentes import load_dependentes
from apps.imports.services.loaders.lotacoes import load_lotacoes
from apps.imports.services.loaders.servidores import load_servidores
from apps.imports.services.loaders.vinculos import load_vinculos
from apps.people.models import Cargo, Dependente, Lotacao, Servidor, VinculoFuncional


@pytest.fixture
def tenant_schema(tenant_a):
    """Reusa o tenant_a do conftest global; rolling-back fica com o pytest-django."""
    return tenant_a.schema_name


# ============================================================
# load_cargos
# ============================================================


class TestLoadCargos:
    def test_cria_cargos_e_registra_audit(self, tenant_schema):
        with schema_context(tenant_schema):
            rows = [
                {
                    "empresa": "001",
                    "codigo": "PROFE",
                    "nome": "Professor",
                    "cbo": "2312",
                    "instrucao": "06",
                    "dtcriacao": date(2010, 1, 1),
                    "dtextincao": None,
                    "vagacargo": 5,
                    "vagafuncao": 0,
                    "vagaemprego": 0,
                    "dedicacao_exclusiva": "S",
                    "atribuicoes": "Lecionar",
                },
                {
                    "empresa": "001",
                    "codigo": "AUX",
                    "nome": "Auxiliar",
                    "cbo": "",
                    "instrucao": "03",
                    "dtcriacao": None,
                    "dtextincao": None,
                    "vagacargo": 10,
                    "vagafuncao": 0,
                    "vagaemprego": 0,
                    "dedicacao_exclusiva": "N",
                    "atribuicoes": "",
                },
            ]
            stats = load_cargos(rows)

            assert stats.lidos == 2
            assert stats.criados == 2
            assert stats.atualizados == 0
            assert stats.erros == 0

            assert Cargo.objects.count() == 2
            cargo = Cargo.objects.get(codigo="001-PROFE")
            assert cargo.nome == "Professor"
            assert cargo.dedicacao_exclusiva is True

            audits = SipImportRecord.objects.filter(tipo=TipoEntidadeSip.CARGO)
            assert audits.count() == 2
            assert audits.filter(status=StatusImportacao.OK).count() == 2

    def test_re_run_e_idempotente(self, tenant_schema):
        with schema_context(tenant_schema):
            row = {
                "empresa": "001",
                "codigo": "PROFE",
                "nome": "Professor",
                "cbo": "2312",
                "instrucao": "06",
                "dtcriacao": date(2010, 1, 1),
                "dtextincao": None,
                "vagacargo": 5,
                "vagafuncao": 0,
                "vagaemprego": 0,
                "dedicacao_exclusiva": "N",
                "atribuicoes": "",
            }
            load_cargos([row])
            stats2 = load_cargos([row])

            assert stats2.criados == 0
            assert stats2.atualizados == 1
            assert Cargo.objects.count() == 1

    def test_linha_invalida_nao_para_batch(self, tenant_schema):
        with schema_context(tenant_schema):
            rows = [
                # Inválida (sem campo obrigatório nome)
                {"empresa": "", "codigo": "", "nome": "", "instrucao": "06"},
                # Válida
                {
                    "empresa": "001",
                    "codigo": "PROFE",
                    "nome": "Professor",
                    "cbo": "",
                    "instrucao": "06",
                    "dtcriacao": None,
                    "dtextincao": None,
                    "vagacargo": 0,
                    "vagafuncao": 0,
                    "vagaemprego": 0,
                    "dedicacao_exclusiva": "N",
                    "atribuicoes": "",
                },
            ]
            stats = load_cargos(rows)
            # Empresa/codigo vazios viram chave "-" — não falha o map mas
            # provavelmente quebra no `unique=True` se houver outra linha
            # com mesma chave; o teste verifica que ao menos a 2ª foi ok.
            assert stats.criados >= 1


# ============================================================
# load_lotacoes
# ============================================================


class TestLoadLotacoes:
    def test_cria_lotacoes(self, tenant_schema):
        with schema_context(tenant_schema):
            rows = [
                {"empresa": "001", "codigo": "5", "nome": "Secretaria de Educacao"},
                {"empresa": "001", "codigo": "6", "nome": "Secretaria de Saude"},
            ]
            stats = load_lotacoes(rows)
            assert stats.criados == 2
            assert Lotacao.objects.count() == 2


# ============================================================
# load_servidores
# ============================================================


class TestLoadServidores:
    def test_cria_servidor(self, tenant_schema):
        with schema_context(tenant_schema):
            rows = [
                {
                    "cpf": "11122233344",
                    "nome": "Maria da Silva",
                    "sexo": "F",
                    "nacionalidade": "10",
                    "dtnascimento": date(1985, 3, 15),
                    "instrucao": "06",
                    "estadocivil": "C",
                    "nomepai": "João Silva",
                    "nomemae": "Ana Silva",
                    "raca": "1",
                    "cep": "65000000",
                    "endereco": "Rua das Flores",
                    "numero": "100",
                    "bairro": "Centro",
                    "compl": "",
                    "cidade": "São Raimundo",
                    "uf": "MA",
                    "telefone": "9988887777",
                    "celular": "98899998888",
                    "email": "maria@example.com",
                    "pis": "12345678910",
                }
            ]
            stats = load_servidores(rows)
            assert stats.criados == 1
            servidor = Servidor.objects.get(cpf="11122233344")
            assert servidor.nome == "Maria da Silva"
            assert servidor.nome_mae == "Ana Silva"


# ============================================================
# load_vinculos (depende de cargo + lotacao + servidor importados)
# ============================================================


class TestLoadVinculos:
    def test_vinculo_completo(self, tenant_schema):
        with schema_context(tenant_schema):
            # Pré-condições
            load_cargos(
                [
                    {
                        "empresa": "001",
                        "codigo": "PROFE",
                        "nome": "Professor",
                        "cbo": "",
                        "instrucao": "06",
                        "dtcriacao": None,
                        "dtextincao": None,
                        "vagacargo": 0,
                        "vagafuncao": 0,
                        "vagaemprego": 0,
                        "dedicacao_exclusiva": "N",
                        "atribuicoes": "",
                    }
                ]
            )
            load_lotacoes(
                [{"empresa": "001", "codigo": "5", "nome": "Secretaria de Educacao"}]
            )
            load_servidores(
                [
                    {
                        "cpf": "11122233344",
                        "nome": "Maria da Silva",
                        "sexo": "F",
                        "nacionalidade": "10",
                        "dtnascimento": date(1985, 3, 15),
                        "instrucao": "06",
                        "estadocivil": "C",
                        "nomepai": "",
                        "nomemae": "",
                        "raca": "",
                        "cep": "",
                        "endereco": "",
                        "numero": "",
                        "bairro": "",
                        "compl": "",
                        "cidade": "",
                        "uf": "",
                        "telefone": "",
                        "celular": "",
                        "email": "",
                        "pis": "",
                    }
                ]
            )

            stats = load_vinculos(
                [
                    {
                        "empresa": "001",
                        "registro": "0001",
                        "matricula": 1,
                        "contrato": 1,
                        "cpf": "11122233344",
                        "cargoatual": "PROFE",
                        "local_trabalho": "5",
                        "vinculo": "03",
                        "situacao": "A",
                        "dtadmissao": date(2020, 3, 1),
                        "dtdemissao": None,
                        "tipoadmissao": "01",
                        "horasemanal": 40.0,
                        "processo": "PROC-2020-1",
                    }
                ]
            )
            assert stats.criados == 1
            v = VinculoFuncional.objects.get(matricula_contrato="0001")
            assert v.servidor.cpf == "11122233344"
            assert v.cargo.codigo == "001-PROFE"
            assert v.lotacao.codigo == "001-LT-5"

    def test_vinculo_sem_cargo_importado_gera_erro(self, tenant_schema):
        with schema_context(tenant_schema):
            stats = load_vinculos(
                [
                    {
                        "empresa": "001",
                        "registro": "0001",
                        "cpf": "11122233344",
                        "cargoatual": "INEXISTENTE",
                        "local_trabalho": "5",
                        "vinculo": "03",
                        "situacao": "A",
                        "dtadmissao": date(2020, 3, 1),
                        "dtdemissao": None,
                        "tipoadmissao": "01",
                        "horasemanal": 40.0,
                        "processo": "",
                    }
                ]
            )
            assert stats.criados == 0
            assert stats.erros == 1
            assert "Cargo SIP" in stats.mensagens_erro[0]


# ============================================================
# load_dependentes (depende de servidor importado)
# ============================================================


class TestLoadDependentes:
    def test_cria_dependente_resolve_servidor_por_cpf(self, tenant_schema):
        with schema_context(tenant_schema):
            load_servidores(
                [
                    {
                        "cpf": "11122233344",
                        "nome": "Maria",
                        "sexo": "F",
                        "nacionalidade": "10",
                        "dtnascimento": date(1985, 1, 1),
                        "instrucao": "06",
                        "estadocivil": "C",
                        "nomepai": "",
                        "nomemae": "",
                        "raca": "",
                        "cep": "",
                        "endereco": "",
                        "numero": "",
                        "bairro": "",
                        "compl": "",
                        "cidade": "",
                        "uf": "",
                        "telefone": "",
                        "celular": "",
                        "email": "",
                        "pis": "",
                    }
                ]
            )
            stats = load_dependentes(
                [
                    {
                        "empresa": "001",
                        "registro": "0001",
                        "nome": "Joaozinho",
                        "dtnascimento": date(2015, 6, 1),
                        "cpf": "",
                        "parentesco": "03",
                        "irrf": "S",
                        "salfamilia": "S",
                        "cpf_titular": "11122233344",
                    }
                ]
            )
            assert stats.criados == 1
            assert Dependente.objects.count() == 1
            d = Dependente.objects.first()
            assert d.servidor.cpf == "11122233344"
            assert d.ir is True
