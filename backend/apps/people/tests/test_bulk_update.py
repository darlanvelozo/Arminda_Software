"""
Testes do bulk-update (Onda 1.6b).

Cobre:
- Atualiza N servidores em uma chamada.
- Whitelist: campos como `cpf`, `matricula` são rejeitados.
- IDs inexistentes são reportados, não interrompem.
- Histórico (simple-history) é preservado (cria revisão por servidor).
- Bulk em vínculos resolve FKs por id (orgao_emissor, sindicato).
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
    VinculoFuncional,
)


def _servidor(matricula: str, cpf: str, cidade: str = "") -> Servidor:
    return Servidor.objects.create(
        matricula=matricula,
        nome=f"Servidor {matricula}",
        cpf=cpf,
        data_nascimento=date(1990, 1, 1),
        sexo=Sexo.MASCULINO,
        cidade=cidade,
    )


@pytest.mark.django_db
class TestBulkUpdateServidores:
    URL = "/api/people/servidores/bulk-update/"

    def test_atualiza_em_lote(
        self, api_client_factory, usuario_admin_a, tenant_a, in_tenant
    ):
        with in_tenant(tenant_a):
            s1 = _servidor("B001", "11144477735")
            s2 = _servidor("B002", "52998224725")
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        resp = client.post(
            self.URL,
            {
                "servidor_ids": [s1.id, s2.id],
                "updates": {"cidade": "Aracaju", "uf": "SE"},
            },
            format="json",
        )
        assert resp.status_code == 200, resp.content
        body = resp.json()
        assert body["atualizados"] == 2
        assert body["ids_nao_encontrados"] == []
        with in_tenant(tenant_a):
            s1.refresh_from_db()
            s2.refresh_from_db()
            assert s1.cidade == "Aracaju"
            assert s2.uf == "SE"

    def test_campo_nao_permitido_falha(
        self, api_client_factory, usuario_admin_a, tenant_a, in_tenant
    ):
        with in_tenant(tenant_a):
            s = _servidor("B003", "11144477735")
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        resp = client.post(
            self.URL,
            {"servidor_ids": [s.id], "updates": {"cpf": "99999999999"}},
            format="json",
        )
        assert resp.status_code == 400
        assert "CAMPO_NAO_PERMITIDO" in resp.content.decode()

    def test_ids_inexistentes_reportados(
        self, api_client_factory, usuario_admin_a, tenant_a, in_tenant
    ):
        with in_tenant(tenant_a):
            s = _servidor("B004", "11144477735")
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        resp = client.post(
            self.URL,
            {"servidor_ids": [s.id, 99999], "updates": {"cidade": "X"}},
            format="json",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["atualizados"] == 1
        assert 99999 in body["ids_nao_encontrados"]

    def test_historico_e_preservado(
        self, api_client_factory, usuario_admin_a, tenant_a, in_tenant
    ):
        with in_tenant(tenant_a):
            s = _servidor("B005", "11144477735", cidade="Antiga")
            assert s.history.count() == 1
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        resp = client.post(
            self.URL,
            {"servidor_ids": [s.id], "updates": {"cidade": "Nova"}},
            format="json",
        )
        assert resp.status_code == 200
        with in_tenant(tenant_a):
            s.refresh_from_db()
            assert s.cidade == "Nova"
            # 1 da criação + 1 da edição = 2 revisões
            assert s.history.count() == 2


@pytest.mark.django_db
class TestBulkUpdateVinculos:
    URL = "/api/people/vinculos/bulk-update/"

    def test_aplica_orgao_emissor_e_sindicato(
        self, api_client_factory, usuario_admin_a, tenant_a, in_tenant
    ):
        with in_tenant(tenant_a):
            cargo = Cargo.objects.create(
                codigo="CB1", nome="X", nivel_escolaridade=NivelEscolaridade.MEDIO
            )
            lotacao = Lotacao.objects.create(
                codigo="LB1", nome="L", natureza=NaturezaLotacao.ADMINISTRACAO
            )
            servidor = _servidor("BV001", "11144477735")
            v = VinculoFuncional.objects.create(
                servidor=servidor,
                cargo=cargo,
                lotacao=lotacao,
                regime=Regime.ESTATUTARIO,
                data_admissao=date(2020, 1, 1),
                salario_base=Decimal("3000"),
            )
            orgao = OrgaoEmissor.objects.create(
                nome="Prefeitura", cnpj="11.222.333/0001-81"
            )
            sindicato = Sindicato.objects.create(
                nome="SIND", cnpj="00.000.000/0001-91"
            )
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        resp = client.post(
            self.URL,
            {
                "vinculo_ids": [v.id],
                "updates": {"orgao_emissor": orgao.id, "sindicato": sindicato.id},
            },
            format="json",
        )
        assert resp.status_code == 200, resp.content
        body = resp.json()
        assert body["atualizados"] == 1
        with in_tenant(tenant_a):
            v.refresh_from_db()
            assert v.orgao_emissor_id == orgao.id
            assert v.sindicato_id == sindicato.id

    def test_fk_invalida_falha(
        self, api_client_factory, usuario_admin_a, tenant_a, in_tenant
    ):
        with in_tenant(tenant_a):
            cargo = Cargo.objects.create(
                codigo="CB2", nome="X", nivel_escolaridade=NivelEscolaridade.MEDIO
            )
            lotacao = Lotacao.objects.create(
                codigo="LB2", nome="L", natureza=NaturezaLotacao.ADMINISTRACAO
            )
            servidor = _servidor("BV002", "52998224725")
            v = VinculoFuncional.objects.create(
                servidor=servidor,
                cargo=cargo,
                lotacao=lotacao,
                regime=Regime.ESTATUTARIO,
                data_admissao=date(2020, 1, 1),
                salario_base=Decimal("3000"),
            )
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        resp = client.post(
            self.URL,
            {"vinculo_ids": [v.id], "updates": {"orgao_emissor": 99999}},
            format="json",
        )
        assert resp.status_code == 400
        assert "FK_INVALIDA" in resp.content.decode()
