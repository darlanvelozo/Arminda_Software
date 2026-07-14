"""Testes da transmissão em lotes — Onda 4.6 (ADR-0024). Tudo offline."""

from __future__ import annotations

import pytest
from django_tenants.utils import schema_context

from apps.esocial.models import GrupoLote, StatusLote, TipoEvento
from apps.esocial.services.assinatura import assinar_evento
from apps.esocial.services.cofre import guardar_certificado
from apps.esocial.services.geracao import gerar_evento
from apps.esocial.services.transmissao import (
    LoteInvalido,
    TransmissaoDesabilitada,
    enviar_lote,
    montar_lote,
)
from apps.esocial.tests.test_cofre_assinatura import SENHA, _orgao, _pfx_teste


def _evento_assinado(orgao, tipo=TipoEvento.S_1000, seq=1):
    ev = gerar_evento(orgao, tipo, sequencial=seq)
    return assinar_evento(ev)


@pytest.mark.django_db
class TestMontarLote:
    def test_lote_valido_contra_xsd(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            orgao = _orgao()
            guardar_certificado(orgao, _pfx_teste(), SENHA)
            e1 = _evento_assinado(orgao, TipoEvento.S_1000, 1)
            e2 = _evento_assinado(orgao, TipoEvento.S_1005, 2)
            lote = montar_lote(orgao, [e1, e2])
            assert lote.status == StatusLote.MONTADO
            assert lote.grupo == GrupoLote.TABELAS
            assert 'grupo="1"' in lote.xml_envio
            e1.refresh_from_db()
            assert e1.lote_envio_id == lote.id

    def test_evento_nao_assinado_barrado(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            orgao = _orgao()
            ev = gerar_evento(orgao, TipoEvento.S_1000)  # só validado
            with pytest.raises(LoteInvalido):
                montar_lote(orgao, [ev])

    def test_grupos_misturados_barrados(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            orgao = _orgao()
            guardar_certificado(orgao, _pfx_teste(), SENHA)
            e1 = _evento_assinado(orgao, TipoEvento.S_1000, 1)
            # S-1200 exige folha/vinculo; para o teste de grupo basta forjar o tipo
            e2 = _evento_assinado(orgao, TipoEvento.S_1005, 2)
            e2.tipo = TipoEvento.S_1200
            e2.save(update_fields=["tipo"])
            with pytest.raises(LoteInvalido):
                montar_lote(orgao, [e1, e2])


@pytest.mark.django_db
class TestEnvioGateado:
    def test_envio_bloqueado_por_default(self, tenant_a, settings):
        settings.ESOCIAL_TRANSMISSAO_HABILITADA = False
        with schema_context(tenant_a.schema_name):
            orgao = _orgao()
            guardar_certificado(orgao, _pfx_teste(), SENHA)
            lote = montar_lote(orgao, [_evento_assinado(orgao)])
            with pytest.raises(TransmissaoDesabilitada):
                enviar_lote(lote)

    def test_envio_sem_ambiente_bloqueado(self, tenant_a, settings):
        settings.ESOCIAL_TRANSMISSAO_HABILITADA = True
        settings.ESOCIAL_AMBIENTE = ""
        with schema_context(tenant_a.schema_name):
            orgao = _orgao()
            guardar_certificado(orgao, _pfx_teste(), SENHA)
            lote = montar_lote(orgao, [_evento_assinado(orgao)])
            with pytest.raises(TransmissaoDesabilitada):
                enviar_lote(lote)


@pytest.mark.django_db
class TestApiLotes:
    def test_montar_e_enviar_gateado(self, api_client_factory, usuario_factory, tenant_a, settings):
        settings.ESOCIAL_TRANSMISSAO_HABILITADA = False
        usuario = usuario_factory(
            email="fin@arminda.test", papeis=[(tenant_a, "financeiro_municipio")]
        )
        with schema_context(tenant_a.schema_name):
            orgao = _orgao()
            guardar_certificado(orgao, _pfx_teste(), SENHA)
            e1 = _evento_assinado(orgao, TipoEvento.S_1000, 1)
        client = api_client_factory(user=usuario, tenant=tenant_a)
        r = client.post("/api/esocial/lotes/montar/", {
            "orgao_emissor": orgao.id, "eventos": [e1.id],
        }, format="json")
        assert r.status_code == 201, r.json()
        lote_id = r.json()["id"]
        assert r.json()["status"] == "montado"
        # envio bloqueado por configuração
        r2 = client.post(f"/api/esocial/lotes/{lote_id}/enviar/")
        assert r2.status_code == 400
        assert r2.json()["code"] == "TRANSMISSAO_DESABILITADA"
