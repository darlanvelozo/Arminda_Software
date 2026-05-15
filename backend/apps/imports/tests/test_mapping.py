"""
Testes puros das funções de mapping (Bloco 1.4).

Não tocam o banco — só transformam dicts. Permitem alta cobertura sem
spinning up de Postgres.
"""

from __future__ import annotations

from datetime import date

import pytest

from apps.imports.services.mapping import (
    map_cargo,
    map_dependente,
    map_lotacao,
    map_servidor,
    map_unidade_orcamentaria,
    map_vinculo,
    payload_hash,
)
from apps.people.models import (
    EstadoCivil,
    NivelEscolaridade,
    Parentesco,
    Regime,
    Sexo,
)

# ============================================================
# map_cargo
# ============================================================


class TestMapCargo:
    def test_mapeamento_basico(self):
        row = {
            "empresa": "001",
            "codigo": "PROFE",
            "nome": "Professor",
            "cbo": "2312",
            "instrucao": "06",
            "dtcriacao": date(2010, 5, 1),
            "dtextincao": None,
            "vagacargo": 5,
            "vagafuncao": 0,
            "vagaemprego": 0,
            "dedicacao_exclusiva": "S",
            "atribuicoes": "Lecionar",
        }
        chave, defaults = map_cargo(row)
        assert chave == "001-PROFE"
        assert defaults["codigo"] == "001-PROFE"
        assert defaults["nome"] == "Professor"
        assert defaults["cbo"] == "2312"
        assert defaults["nivel_escolaridade"] == NivelEscolaridade.SUPERIOR
        assert defaults["data_criacao"] == date(2010, 5, 1)
        assert defaults["data_extincao"] is None
        assert defaults["vagas_total"] == 5
        assert defaults["dedicacao_exclusiva"] is True
        assert defaults["atribuicoes"] == "Lecionar"
        assert defaults["ativo"] is True

    def test_cargo_extinto_marca_inativo(self):
        row = {
            "empresa": "001",
            "codigo": "AUX",
            "nome": "Auxiliar",
            "cbo": "",
            "instrucao": "03",
            "dtcriacao": date(2000, 1, 1),
            "dtextincao": date(2020, 12, 31),
            "vagacargo": 0,
            "vagafuncao": 0,
            "vagaemprego": 0,
            "dedicacao_exclusiva": "N",
            "atribuicoes": "",
        }
        _, defaults = map_cargo(row)
        assert defaults["ativo"] is False
        assert defaults["data_extincao"] == date(2020, 12, 31)

    def test_instrucao_desconhecida_cai_para_medio(self):
        row = {
            "empresa": "001",
            "codigo": "X",
            "nome": "X",
            "cbo": "",
            "instrucao": "99",  # desconhecido
            "dtcriacao": None,
            "dtextincao": None,
            "vagacargo": 0,
            "vagafuncao": 0,
            "vagaemprego": 0,
            "dedicacao_exclusiva": "N",
            "atribuicoes": "",
        }
        _, defaults = map_cargo(row)
        assert defaults["nivel_escolaridade"] == NivelEscolaridade.MEDIO

    def test_vagas_somadas_de_3_campos_sip(self):
        row = {
            "empresa": "001",
            "codigo": "X",
            "nome": "X",
            "cbo": "",
            "instrucao": "06",
            "dtcriacao": None,
            "dtextincao": None,
            "vagacargo": 10,
            "vagafuncao": 5,
            "vagaemprego": 2,
            "dedicacao_exclusiva": "N",
            "atribuicoes": "",
        }
        _, defaults = map_cargo(row)
        assert defaults["vagas_total"] == 17

    def test_codigo_truncado_em_20_chars(self):
        row = {
            "empresa": "999",
            "codigo": "X" * 30,
            "nome": "X",
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
        _, defaults = map_cargo(row)
        assert len(defaults["codigo"]) == 20


# ============================================================
# map_lotacao
# ============================================================


class TestMapLotacao:
    def test_sigla_de_iniciais(self):
        row = {"empresa": "001", "codigo": "15", "nome": "Secretaria Municipal de Educacao"}
        chave, defaults = map_lotacao(row)
        assert chave == "001-LT-15"
        assert defaults["nome"] == "Secretaria Municipal de Educacao"
        assert defaults["sigla"] == "SMDE"
        assert defaults["lotacao_pai"] is None
        # Padrão "educacao" no nome classifica como Educação
        assert defaults["natureza"] == "educacao"

    def test_uma_palavra_usa_primeiros_6_chars(self):
        row = {"empresa": "001", "codigo": "5", "nome": "Saúde"}
        _, defaults = map_lotacao(row)
        assert defaults["sigla"] == "SAÚDE"
        assert defaults["natureza"] == "saude"

    def test_classifica_psf_como_saude(self):
        _, defaults = map_lotacao({"empresa": "001", "codigo": "30", "nome": "PSF SEDE"})
        assert defaults["natureza"] == "saude"

    def test_classifica_cras_como_assistencia(self):
        _, defaults = map_lotacao({"empresa": "001", "codigo": "40", "nome": "CRAS Centro"})
        assert defaults["natureza"] == "assistencia_social"

    def test_nome_sem_match_vira_outros(self):
        _, defaults = map_lotacao(
            {"empresa": "001", "codigo": "70", "nome": "Sec de Cultura"}
        )
        assert defaults["natureza"] == "outros"


# ============================================================
# map_servidor
# ============================================================


class TestMapServidor:
    def _row(self, **overrides):
        base = {
            "cpf": "12345678901",
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
            "compl": "Apto 2",
            "cidade": "São Raimundo",
            "uf": "MA",
            "telefone": "9988887777",
            "celular": "98899998888",
            "email": "maria@example.com",
            "pis": "12345678910",
        }
        base.update(overrides)
        return base

    def test_mapeamento_basico(self):
        chave, defaults = map_servidor(self._row())
        assert chave == "12345678901"
        assert defaults["cpf"] == "12345678901"
        assert defaults["matricula"] == "12345678901"  # provisório
        assert defaults["nome"] == "Maria da Silva"
        assert defaults["sexo"] == Sexo.FEMININO
        assert defaults["estado_civil"] == EstadoCivil.CASADO
        assert defaults["nome_pai"] == "João Silva"
        assert defaults["nome_mae"] == "Ana Silva"
        assert defaults["raca"] == "1"
        assert defaults["nacionalidade"] == "10"
        assert defaults["instrucao"] == "06"
        assert defaults["pis_pasep"] == "12345678910"
        assert defaults["uf"] == "MA"

    def test_celular_preferido_sobre_telefone(self):
        _, defaults = map_servidor(self._row(celular="98899998888", telefone="9988887777"))
        assert defaults["telefone"] == "98899998888"

    def test_telefone_usado_se_celular_vazio(self):
        _, defaults = map_servidor(self._row(celular="", telefone="9988887777"))
        assert defaults["telefone"] == "9988887777"

    def test_cpf_curto_levanta_erro(self):
        with pytest.raises(ValueError, match="CPF inválido"):
            map_servidor(self._row(cpf="123"))

    def test_estado_civil_codigo_numerico(self):
        _, defaults = map_servidor(self._row(estadocivil="2"))
        assert defaults["estado_civil"] == EstadoCivil.CASADO

    def test_data_nascimento_default_se_ausente(self):
        _, defaults = map_servidor(self._row(dtnascimento=None))
        assert defaults["data_nascimento"] == date(1970, 1, 1)


# ============================================================
# map_vinculo
# ============================================================


class TestMapVinculo:
    def _row(self, **overrides):
        base = {
            "empresa": "001",
            "registro": "12345",
            "matricula": 12345,
            "contrato": 1,
            "cpf": "12345678901",
            "cargoatual": "PROFE",
            "local_trabalho": "15",
            "vinculo": "03",
            "situacao": "A",
            "dtadmissao": date(2020, 3, 1),
            "dtdemissao": None,
            "tipoadmissao": "01",
            "horasemanal": 40.0,
            "processo": "PROC-2020-1",
        }
        base.update(overrides)
        return base

    def test_mapeamento_basico(self):
        chave, defaults = map_vinculo(self._row(), servidor_id=1, cargo_id=2, lotacao_id=3)
        assert chave == "001-12345"
        assert defaults["servidor_id"] == 1
        assert defaults["cargo_id"] == 2
        assert defaults["lotacao_id"] == 3
        assert defaults["regime"] == Regime.ESTATUTARIO
        assert defaults["data_admissao"] == date(2020, 3, 1)
        assert defaults["data_demissao"] is None
        assert defaults["carga_horaria"] == 40
        assert defaults["matricula_contrato"] == "12345"
        assert defaults["tipo_admissao"] == "01"
        assert defaults["processo_admissao"] == "PROC-2020-1"
        assert defaults["ativo"] is True

    def test_situacao_demitido_marca_inativo(self):
        _, defaults = map_vinculo(
            self._row(situacao="D"), servidor_id=1, cargo_id=2, lotacao_id=3
        )
        assert defaults["ativo"] is False

    def test_carga_horaria_invalida_cai_para_40(self):
        _, defaults = map_vinculo(
            self._row(horasemanal=999), servidor_id=1, cargo_id=2, lotacao_id=3
        )
        assert defaults["carga_horaria"] == 40

    def test_vinculo_codigo_desconhecido_cai_para_estatutario(self):
        _, defaults = map_vinculo(
            self._row(vinculo="ZZ"), servidor_id=1, cargo_id=2, lotacao_id=3
        )
        assert defaults["regime"] == Regime.ESTATUTARIO

    def test_agente_politico_codigo_01_vira_eletivo(self):
        # Prefeito, Vice-Prefeito e Vereadores no SIP têm VINCULO=01 (AGENTE
        # POLITICO). No Arminda esse é regime ELETIVO, não comissionado.
        _, defaults = map_vinculo(
            self._row(vinculo="01"), servidor_id=1, cargo_id=2, lotacao_id=3
        )
        assert defaults["regime"] == Regime.ELETIVO

    def test_aceita_unidade_orcamentaria_id_opcional(self):
        # Onda 1.4-bis: vínculo pode opcionalmente apontar para uma
        # unidade orçamentária (FK nullable).
        _, defaults = map_vinculo(
            self._row(),
            servidor_id=1,
            cargo_id=2,
            lotacao_id=3,
            unidade_orcamentaria_id=42,
        )
        assert defaults["unidade_orcamentaria_id"] == 42

    def test_unidade_orcamentaria_omitida_vira_none(self):
        _, defaults = map_vinculo(
            self._row(), servidor_id=1, cargo_id=2, lotacao_id=3
        )
        assert defaults["unidade_orcamentaria_id"] is None


# ============================================================
# map_dependente
# ============================================================


class TestMapDependente:
    def _row(self, **overrides):
        base = {
            "empresa": "001",
            "registro": "12345",
            "nome": "Maria Filha",
            "dtnascimento": date(2010, 6, 1),
            "cpf": "11122233344",
            "parentesco": "03",
            "irrf": "S",
            "salfamilia": "S",
            "cpf_titular": "12345678901",
        }
        base.update(overrides)
        return base

    def test_mapeamento_basico(self):
        chave, defaults = map_dependente(self._row(), servidor_id=42)
        assert chave.startswith("12345678901-MARIAFILHA-2010-06-01")
        assert defaults["servidor_id"] == 42
        assert defaults["nome"] == "Maria Filha"
        assert defaults["parentesco"] == Parentesco.FILHO
        assert defaults["ir"] is True
        assert defaults["salario_familia"] is True

    def test_sem_titular_levanta(self):
        with pytest.raises(ValueError, match="CPF do titular"):
            map_dependente(self._row(cpf_titular=""), servidor_id=42)

    def test_sem_data_nascimento_levanta(self):
        with pytest.raises(ValueError, match="data de nascimento"):
            map_dependente(self._row(dtnascimento=None), servidor_id=42)

    def test_parentesco_desconhecido_vira_outro(self):
        _, defaults = map_dependente(self._row(parentesco="99"), servidor_id=42)
        assert defaults["parentesco"] == Parentesco.OUTRO


# ============================================================
# map_unidade_orcamentaria (Onda 1.4-bis)
# ============================================================


class TestMapUnidadeOrcamentaria:
    def _row(self, **overrides):
        base = {
            "empresa": "001",
            "depdespesa": "201013",
            "ano": "2026",
            "nome": "SEC. DE SAUDE",
            "sigla": "SAU",
        }
        base.update(overrides)
        return base

    def test_basico_inferindo_natureza_por_nome(self):
        chave, defaults = map_unidade_orcamentaria(self._row())
        assert chave == "2026-001-201013"
        assert defaults["codigo"] == "201013"
        assert defaults["ano"] == 2026
        assert defaults["nome"] == "SEC. DE SAUDE"
        assert defaults["natureza"] == "saude"

    def test_prefixo_3_classifica_educacao_quando_nome_nao_decide(self):
        # Nome genérico sem padrão claro; só o prefixo 3 = educação
        _, defaults = map_unidade_orcamentaria(
            self._row(depdespesa="302011", nome="FUNDEB MDE")
        )
        assert defaults["natureza"] == "educacao"

    def test_prefixo_4_classifica_assistencia_social(self):
        _, defaults = map_unidade_orcamentaria(
            self._row(depdespesa="402004", nome="FUNDO ASS. SOC. - CRAS")
        )
        assert defaults["natureza"] == "assistencia_social"

    def test_nome_tem_prioridade_sobre_prefixo(self):
        # Prefixo 1 (administração) mas nome diz "SAUDE" — vence o nome
        _, defaults = map_unidade_orcamentaria(
            self._row(depdespesa="100100", nome="ESPECIAL DA SAUDE")
        )
        assert defaults["natureza"] == "saude"

    def test_outros_quando_nada_decide(self):
        _, defaults = map_unidade_orcamentaria(
            self._row(depdespesa="999999", nome="ALGUMA COISA")
        )
        assert defaults["natureza"] == "outros"

    def test_ano_invalido_levanta(self):
        import pytest as _pytest

        with _pytest.raises(ValueError, match="ANO inválido"):
            map_unidade_orcamentaria(self._row(ano="abc"))


# ============================================================
# payload_hash
# ============================================================


class TestPayloadHash:
    def test_hash_estavel_independente_de_ordem(self):
        a = {"x": 1, "y": 2}
        b = {"y": 2, "x": 1}
        assert payload_hash(a) == payload_hash(b)

    def test_hash_muda_com_conteudo(self):
        a = {"x": 1}
        b = {"x": 2}
        assert payload_hash(a) != payload_hash(b)

    def test_hash_serializa_dates(self):
        h = payload_hash({"data": date(2020, 1, 1)})
        assert isinstance(h, str)
        assert len(h) == 64
