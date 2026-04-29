"""Testes do service `desligar_servidor` (Bloco 1.2 — Onda 3)."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.people.services.admissao import DadosAdmissao, admitir_servidor
from apps.people.services.desligamento import (
    DadosDesligamento,
    desligar_servidor,
)
from apps.people.services.exceptions import DesligamentoInvalidoError


@pytest.fixture
def cenario_servidor_admitido(tenant_a, in_tenant):
    """Cria cargo + lotacao + servidor admitido. Retorna o servidor."""
    from apps.people.models import Cargo, Lotacao

    with in_tenant(tenant_a):
        cargo = Cargo.objects.create(codigo="ENF", nome="Enfermeiro", ativo=True)
        lotacao = Lotacao.objects.create(codigo="SAU", nome="Saude", ativo=True)
        servidor = admitir_servidor(
            DadosAdmissao(
                matricula="999",
                nome="Carla Souza",
                cpf="529.982.247-25",
                data_nascimento=date(1985, 3, 20),
                sexo="F",
                cargo_id=cargo.id,
                lotacao_id=lotacao.id,
                regime="estatutario",
                data_admissao=date(2020, 1, 15),
                salario_base=Decimal("4500.00"),
            )
        )
    return servidor


@pytest.mark.django_db
class TestDesligarServidor:
    def test_desliga_com_sucesso(self, tenant_a, in_tenant, cenario_servidor_admitido):
        with in_tenant(tenant_a):
            servidor = desligar_servidor(
                DadosDesligamento(
                    servidor_id=cenario_servidor_admitido.id,
                    data_desligamento=date.today(),
                    motivo="exoneracao a pedido",
                )
            )
            assert servidor.ativo is False
            assert servidor.vinculos.filter(ativo=True).count() == 0
            assert servidor.vinculos.filter(ativo=False).count() == 1
            vinculo = servidor.vinculos.first()
            assert vinculo.data_demissao == date.today()

    def test_data_futura_falha(self, tenant_a, in_tenant, cenario_servidor_admitido):
        futuro = date.today() + timedelta(days=10)
        with in_tenant(tenant_a), pytest.raises(DesligamentoInvalidoError) as exc:
            desligar_servidor(
                DadosDesligamento(
                    servidor_id=cenario_servidor_admitido.id,
                    data_desligamento=futuro,
                )
            )
        assert exc.value.code == "DATA_DESLIGAMENTO_FUTURA"

    def test_servidor_inexistente(self, tenant_a, in_tenant):
        with in_tenant(tenant_a), pytest.raises(DesligamentoInvalidoError) as exc:
            desligar_servidor(DadosDesligamento(servidor_id=99999, data_desligamento=date.today()))
        assert exc.value.code == "SERVIDOR_NAO_ENCONTRADO"

    def test_desligar_duas_vezes_falha(self, tenant_a, in_tenant, cenario_servidor_admitido):
        with in_tenant(tenant_a):
            desligar_servidor(
                DadosDesligamento(
                    servidor_id=cenario_servidor_admitido.id,
                    data_desligamento=date.today(),
                )
            )
            with pytest.raises(DesligamentoInvalidoError) as exc:
                desligar_servidor(
                    DadosDesligamento(
                        servidor_id=cenario_servidor_admitido.id,
                        data_desligamento=date.today(),
                    )
                )
        assert exc.value.code == "DESLIGAMENTO_DUPLICADO"

    def test_data_anterior_a_admissao(self, tenant_a, in_tenant, cenario_servidor_admitido):
        with in_tenant(tenant_a), pytest.raises(DesligamentoInvalidoError) as exc:
            desligar_servidor(
                DadosDesligamento(
                    servidor_id=cenario_servidor_admitido.id,
                    data_desligamento=date(2019, 1, 1),  # antes da admissao
                )
            )
        assert exc.value.code == "DATA_INVALIDA"

    def test_servidor_sem_vinculo_ativo(self, tenant_a, in_tenant):
        """Servidor 'ativo' mas sem nenhum vinculo ativo (cenario raro mas possivel)."""
        from apps.people.models import Servidor

        with in_tenant(tenant_a):
            srv = Servidor.objects.create(
                matricula="888",
                nome="Sem Vinculo",
                cpf="11144477735",
                data_nascimento=date(1990, 1, 1),
                sexo="F",
                ativo=True,
            )
            with pytest.raises(DesligamentoInvalidoError) as exc:
                desligar_servidor(
                    DadosDesligamento(servidor_id=srv.id, data_desligamento=date.today())
                )
        assert exc.value.code == "SEM_VINCULO_ATIVO"
