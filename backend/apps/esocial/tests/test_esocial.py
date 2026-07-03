"""Testes do eSocial — Onda 4.1 (ADR-0020): geração XML + validação XSD."""

from __future__ import annotations

import pytest
from django_tenants.utils import schema_context

from apps.esocial.models import EventoESocial, StatusEvento, TipoEvento
from apps.esocial.services.geracao import gerar_evento, gerar_id_evento
from apps.esocial.services.validacao import validar_xml
from apps.payroll.models import Rubrica, TipoRubrica
from apps.people.models import OrgaoEmissor


def _orgao():
    return OrgaoEmissor.objects.create(
        nome="Prefeitura de Teste", cnpj="12.345.678/0001-90",
        cnae_principal="8411600",
    )


def _rubrica(natureza="1000"):
    return Rubrica.objects.create(
        codigo="SAL", nome="Salário base", tipo=TipoRubrica.PROVENTO,
        natureza_esocial=natureza, cod_inc_cp="11", cod_inc_irrf="11",
        cod_inc_fgts="11",
    )


@pytest.mark.django_db
class TestEsocial:
    def test_id_evento_bem_formado(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            orgao = _orgao()
            idev = gerar_id_evento(orgao, sequencial=1)
            # ID + tpInsc(1) + nrInsc(14) + AAAAMMDDHHMMSS(14) + seq(5) = 36
            assert len(idev) == 36
            assert idev.startswith("ID1") and "12345678000190" in idev
            assert idev.endswith("00001")

    def test_gera_s1000_valido_contra_xsd(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            orgao = _orgao()
            evento = gerar_evento(orgao, TipoEvento.S_1000)
            assert evento.status == StatusEvento.VALIDADO
            assert evento.tipo == TipoEvento.S_1000
            # re-valida o XML persistido (não levanta = válido)
            validar_xml(evento.xml, TipoEvento.S_1000)
            assert "<evtInfoEmpregador" in evento.xml
            assert EventoESocial.objects.filter(orgao_emissor=orgao).count() == 1

    def test_gera_s1005_valido_contra_xsd(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            orgao = _orgao()
            evento = gerar_evento(orgao, TipoEvento.S_1005)
            assert evento.status == StatusEvento.VALIDADO
            validar_xml(evento.xml, TipoEvento.S_1005)
            assert "<evtTabEstab" in evento.xml

    def test_gera_s1010_valido_contra_xsd(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            orgao = _orgao()
            rubrica = _rubrica()
            evento = gerar_evento(orgao, TipoEvento.S_1010, rubrica=rubrica)
            assert evento.status == StatusEvento.VALIDADO
            assert evento.rubrica_id == rubrica.id
            validar_xml(evento.xml, TipoEvento.S_1010)
            assert "<evtTabRubrica" in evento.xml
            assert "<natRubr>1000</natRubr>" in evento.xml

    def test_s1010_exige_rubrica_com_natureza(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            orgao = _orgao()
            # sem rubrica
            with pytest.raises(ValueError):
                gerar_evento(orgao, TipoEvento.S_1010)
            # rubrica sem natureza eSocial
            sem_nat = _rubrica(natureza="")
            with pytest.raises(ValueError):
                gerar_evento(orgao, TipoEvento.S_1010, rubrica=sem_nat)

    def test_tipo_nao_suportado(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            orgao = _orgao()
            with pytest.raises(ValueError):
                gerar_evento(orgao, "S-9999")

    def test_api_gerar_e_baixar(self, api_client_factory, usuario_factory, tenant_a):
        usuario = usuario_factory(
            email="fin@arminda.test", papeis=[(tenant_a, "financeiro_municipio")]
        )
        with schema_context(tenant_a.schema_name):
            orgao = _orgao()
        client = api_client_factory(user=usuario, tenant=tenant_a)
        r = client.post("/api/esocial/eventos/gerar/", {
            "tipo": "S-1000", "orgao_emissor": orgao.id,
        }, format="json")
        assert r.status_code == 201, r.json()
        evento_id = r.json()["id"]
        r2 = client.get(f"/api/esocial/eventos/{evento_id}/baixar/")
        assert r2.status_code == 200
        assert r2["Content-Type"].startswith("application/xml")
        assert b"evtInfoEmpregador" in r2.content
