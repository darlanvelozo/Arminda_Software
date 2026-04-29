"""Testes do service `transferir_lotacao` (Bloco 1.2 — Onda 3)."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.people.services.admissao import DadosAdmissao, admitir_servidor
from apps.people.services.exceptions import TransferenciaInvalidaError
from apps.people.services.transferencia import (
    DadosTransferencia,
    transferir_lotacao,
)


@pytest.fixture
def cenario(tenant_a, in_tenant):
    """Servidor admitido + segunda lotacao disponivel.

    Retorna IDs (nao instances) para os testes resolverem dentro do
    proprio contexto de tenant — fixture nao deve manter querysets vivos
    fora do schema correto.
    """
    from apps.people.models import Cargo, Lotacao

    with in_tenant(tenant_a):
        cargo = Cargo.objects.create(codigo="ANL", nome="Analista", ativo=True)
        lotacao_a = Lotacao.objects.create(codigo="A", nome="Lotacao A", ativo=True)
        lotacao_b = Lotacao.objects.create(codigo="B", nome="Lotacao B", ativo=True)
        lotacao_inativa = Lotacao.objects.create(codigo="X", nome="Inativa", ativo=False)
        servidor = admitir_servidor(
            DadosAdmissao(
                matricula="T1",
                nome="Pedro Lima",
                cpf="111.444.777-35",
                data_nascimento=date(1980, 5, 5),
                sexo="M",
                cargo_id=cargo.id,
                lotacao_id=lotacao_a.id,
                regime="estatutario",
                data_admissao=date(2022, 1, 10),
                salario_base=Decimal("5500.00"),
            )
        )
        vinculo_id = servidor.vinculos.first().id
    return {
        "servidor_id": servidor.id,
        "vinculo_id": vinculo_id,
        "lotacao_atual_id": lotacao_a.id,
        "lotacao_destino_id": lotacao_b.id,
        "lotacao_inativa_id": lotacao_inativa.id,
    }


@pytest.mark.django_db
class TestTransferirLotacao:
    def test_transfere_com_sucesso(self, tenant_a, in_tenant, cenario):
        from apps.people.models import VinculoFuncional

        with in_tenant(tenant_a):
            antes = VinculoFuncional.objects.get(id=cenario["vinculo_id"])
            novo = transferir_lotacao(
                DadosTransferencia(
                    vinculo_id=cenario["vinculo_id"],
                    nova_lotacao_id=cenario["lotacao_destino_id"],
                    data_transferencia=date.today(),
                )
            )
            antigo = VinculoFuncional.objects.get(id=cenario["vinculo_id"])
            assert antigo.ativo is False
            assert antigo.data_demissao == date.today()
            assert novo.ativo is True
            assert novo.lotacao_id == cenario["lotacao_destino_id"]
            # Preserva atributos
            assert novo.cargo_id == antes.cargo_id
            assert novo.regime == antes.regime
            assert novo.salario_base == antes.salario_base

    def test_data_futura_falha(self, tenant_a, in_tenant, cenario):
        futuro = date.today() + timedelta(days=5)
        with in_tenant(tenant_a), pytest.raises(TransferenciaInvalidaError) as exc:
            transferir_lotacao(
                DadosTransferencia(
                    vinculo_id=cenario["vinculo_id"],
                    nova_lotacao_id=cenario["lotacao_destino_id"],
                    data_transferencia=futuro,
                )
            )
        assert exc.value.code == "DATA_FUTURA"

    def test_vinculo_inexistente(self, tenant_a, in_tenant, cenario):
        with in_tenant(tenant_a), pytest.raises(TransferenciaInvalidaError) as exc:
            transferir_lotacao(
                DadosTransferencia(
                    vinculo_id=99999,
                    nova_lotacao_id=cenario["lotacao_destino_id"],
                    data_transferencia=date.today(),
                )
            )
        assert exc.value.code == "VINCULO_INVALIDO"

    def test_data_anterior_a_admissao(self, tenant_a, in_tenant, cenario):
        with in_tenant(tenant_a), pytest.raises(TransferenciaInvalidaError) as exc:
            transferir_lotacao(
                DadosTransferencia(
                    vinculo_id=cenario["vinculo_id"],
                    nova_lotacao_id=cenario["lotacao_destino_id"],
                    data_transferencia=date(2020, 1, 1),
                )
            )
        assert exc.value.code == "DATA_INVALIDA"

    def test_lotacao_destino_inativa(self, tenant_a, in_tenant, cenario):
        with in_tenant(tenant_a), pytest.raises(TransferenciaInvalidaError) as exc:
            transferir_lotacao(
                DadosTransferencia(
                    vinculo_id=cenario["vinculo_id"],
                    nova_lotacao_id=cenario["lotacao_inativa_id"],
                    data_transferencia=date.today(),
                )
            )
        assert exc.value.code == "LOTACAO_INVALIDA"

    def test_transferencia_redundante(self, tenant_a, in_tenant, cenario):
        """Transferir para a mesma lotacao em que ja esta."""
        with in_tenant(tenant_a), pytest.raises(TransferenciaInvalidaError) as exc:
            transferir_lotacao(
                DadosTransferencia(
                    vinculo_id=cenario["vinculo_id"],
                    nova_lotacao_id=cenario["lotacao_atual_id"],
                    data_transferencia=date.today(),
                )
            )
        assert exc.value.code == "TRANSFERENCIA_REDUNDANTE"
