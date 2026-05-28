"""
Testes da qualidade cadastral (Onda 1.6b).

Cobre:
- Score 100 quando todos campos S-1005/S-2200 estão preenchidos.
- Score < 100 com breakdown de campos faltantes correto.
- Filtro ?cadastro_incompleto=true exposto via API.
- Endpoint agregado /qualidade-resumo/.
- Sugestão de natureza por nome de cargo.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from apps.people.models import (
    Cargo,
    Lotacao,
    NaturezaLotacao,
    NivelEscolaridade,
    OrgaoEmissor,
    Regime,
    Servidor,
    Sexo,
    Sindicato,
    TipoLogradouro,
    VinculoFuncional,
)
from apps.people.services.qualidade import avaliar_servidor, resumir
from apps.people.services.sugestao_area import sugerir_natureza

CNPJ_OE = "11.222.333/0001-81"
CNPJ_SI = "00.000.000/0001-91"


def _criar_servidor_basico(matricula: str = "M001", **extras) -> Servidor:
    defaults = dict(
        matricula=matricula,
        nome="José da Silva",
        cpf="11144477735",
        data_nascimento=date(1985, 3, 1),
        sexo=Sexo.MASCULINO,
    )
    defaults.update(extras)
    return Servidor.objects.create(**defaults)


def _criar_servidor_completo(matricula: str = "M001") -> Servidor:
    return _criar_servidor_basico(
        matricula=matricula,
        tipo_logradouro=TipoLogradouro.RUA,
        logradouro="Rua das Flores",
        numero="100",
        bairro="Centro",
        cidade="Aracaju",
        uf="SE",
        cep="49000-000",
        nome_mae="Maria",
        nacionalidade="10",
        raca="1",
        estado_civil="solteiro",
        instrucao="07",
        pis_pasep="12056875432",
    )


def _criar_vinculo(servidor: Servidor, *, com_orgao_e_sindicato: bool) -> VinculoFuncional:
    cargo = Cargo.objects.create(
        codigo=f"C{servidor.matricula}",
        nome="Auxiliar",
        nivel_escolaridade=NivelEscolaridade.MEDIO,
    )
    lotacao = Lotacao.objects.create(
        codigo=f"L{servidor.matricula}",
        nome="Secretaria",
        natureza=NaturezaLotacao.ADMINISTRACAO,
    )
    kwargs = dict(
        servidor=servidor,
        cargo=cargo,
        lotacao=lotacao,
        regime=Regime.ESTATUTARIO,
        data_admissao=date(2020, 1, 1),
        salario_base=Decimal("3000"),
        carga_horaria=40,
    )
    if com_orgao_e_sindicato:
        kwargs["orgao_emissor"] = OrgaoEmissor.objects.create(
            nome="Prefeitura",
            cnpj=CNPJ_OE,
            eh_principal=True,
        )
        kwargs["sindicato"] = Sindicato.objects.create(
            nome="SINDSEMP",
            cnpj=CNPJ_SI,
        )
    return VinculoFuncional.objects.create(**kwargs)


@pytest.mark.django_db
class TestAvaliarServidor:
    def test_score_100_quando_cadastro_completo(self, tenant_a, in_tenant):
        with in_tenant(tenant_a):
            servidor = _criar_servidor_completo()
            _criar_vinculo(servidor, com_orgao_e_sindicato=True)
            avaliacao = avaliar_servidor(servidor)
            assert avaliacao.score == 100
            assert avaliacao.completo is True
            assert avaliacao.campos_faltantes == []

    def test_score_zero_quando_tudo_em_branco(self, tenant_a, in_tenant):
        with in_tenant(tenant_a):
            servidor = _criar_servidor_basico()  # sem nada preenchido
            # sem vínculo → órgão+sindicato também contam
            avaliacao = avaliar_servidor(servidor)
            assert avaliacao.score == 0
            assert avaliacao.completo is False
            # 13 campos do servidor + 2 do vínculo = 15
            assert avaliacao.total_campos == 15
            assert len(avaliacao.campos_faltantes) == 15

    def test_campos_faltantes_especificos(self, tenant_a, in_tenant):
        with in_tenant(tenant_a):
            servidor = _criar_servidor_basico(
                tipo_logradouro=TipoLogradouro.RUA,
                logradouro="Rua A",
                numero="10",
                bairro="Centro",
                cidade="X",
                uf="MA",
                cep="65000-000",
                nome_mae="Mae",
                nacionalidade="10",
                raca="1",
                estado_civil="casado",
                instrucao="07",
                # falta pis_pasep
            )
            _criar_vinculo(servidor, com_orgao_e_sindicato=False)
            avaliacao = avaliar_servidor(servidor)
            assert "pis_pasep" in avaliacao.campos_faltantes
            assert "orgao_emissor" in avaliacao.campos_faltantes
            assert "sindicato" in avaliacao.campos_faltantes
            assert avaliacao.completo is False
            # 12/15 preenchidos = 80%
            assert avaliacao.score == 80


@pytest.mark.django_db
class TestResumir:
    def test_resumo_agregado(self, tenant_a, in_tenant):
        with in_tenant(tenant_a):
            # 1 completo + 1 parcial
            s1 = _criar_servidor_completo("MX01")
            _criar_vinculo(s1, com_orgao_e_sindicato=True)
            s2 = _criar_servidor_basico("MX02")
            _criar_vinculo(s2, com_orgao_e_sindicato=False)

            resumo = resumir(Servidor.objects.all())
            assert resumo.total_servidores == 2
            assert resumo.completos == 1
            assert resumo.incompletos == 1
            # score médio é (100 + 0) / 2 = 50
            assert resumo.score_medio == 50
            # PIS aparece como faltante em pelo menos 1
            assert resumo.breakdown_campos_faltantes.get("pis_pasep") == 1


@pytest.mark.django_db
class TestEndpointsQualidade:
    BASE = "/api/people/servidores/"

    def test_filtro_cadastro_incompleto(
        self, api_client_factory, usuario_admin_a, tenant_a, in_tenant
    ):
        with in_tenant(tenant_a):
            s_ok = _criar_servidor_completo("OK01")
            _criar_vinculo(s_ok, com_orgao_e_sindicato=True)
            s_pendente = _criar_servidor_basico("PEND01")
            _criar_vinculo(s_pendente, com_orgao_e_sindicato=False)

        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        resp = client.get(self.BASE, {"cadastro_incompleto": "true"})
        assert resp.status_code == 200, resp.content
        body = resp.json()
        matriculas = {r["matricula"] for r in body["results"]}
        assert "PEND01" in matriculas
        assert "OK01" not in matriculas

    def test_qualidade_resumo_endpoint(
        self, api_client_factory, usuario_admin_a, tenant_a, in_tenant
    ):
        with in_tenant(tenant_a):
            s = _criar_servidor_basico("RES01")
            _criar_vinculo(s, com_orgao_e_sindicato=False)
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        resp = client.get(self.BASE + "qualidade-resumo/")
        assert resp.status_code == 200, resp.content
        body = resp.json()
        assert body["total_servidores"] >= 1
        assert isinstance(body["breakdown_campos_faltantes"], list)
        if body["breakdown_campos_faltantes"]:
            primeiro = body["breakdown_campos_faltantes"][0]
            assert "campo" in primeiro
            assert "label" in primeiro
            assert "servidores_pendentes" in primeiro


@pytest.mark.django_db
class TestSugestaoArea:
    def test_professor_sugere_educacao(self):
        s = sugerir_natureza("Professor de Educação Infantil")
        assert s is not None
        assert s.natureza_sugerida == "educacao"
        assert s.confianca >= 90

    def test_enfermeiro_sugere_saude(self):
        s = sugerir_natureza("Enfermeiro Plantonista")
        assert s is not None
        assert s.natureza_sugerida == "saude"

    def test_cras_sugere_assistencia(self):
        s = sugerir_natureza("Coordenador CRAS")
        assert s is not None
        assert s.natureza_sugerida == "assistencia_social"

    def test_contador_sugere_administracao(self):
        s = sugerir_natureza("Contador Municipal")
        assert s is not None
        assert s.natureza_sugerida == "administracao"

    def test_cargo_desconhecido_retorna_none(self):
        s = sugerir_natureza("Astronauta Estelar")
        assert s is None
