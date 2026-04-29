"""
Testes de auditoria via simple-history.

Garante que mudancas em models tenant geram registros Historical*
e que o autor (quem mudou) e capturado quando o middleware esta ativo.
"""

from __future__ import annotations

import pytest


@pytest.mark.django_db
class TestSimpleHistory:
    def test_cargo_gera_historico_em_create(self, tenant_a, in_tenant):
        from apps.people.models import Cargo

        with in_tenant(tenant_a):
            cargo = Cargo.objects.create(codigo="ENF1", nome="Enfermeiro I")
            historico = cargo.history.all()
            assert historico.count() == 1
            primeiro = historico.first()
            assert primeiro.history_type == "+"  # create

    def test_cargo_gera_historico_em_update(self, tenant_a, in_tenant):
        from apps.people.models import Cargo

        with in_tenant(tenant_a):
            cargo = Cargo.objects.create(codigo="ENF2", nome="Enfermeiro II")
            cargo.nome = "Enfermeiro II - atualizado"
            cargo.save()

            historico = cargo.history.all().order_by("history_date")
            assert historico.count() == 2
            assert historico.first().history_type == "+"
            assert historico.last().history_type == "~"
            assert historico.first().nome == "Enfermeiro II"
            assert historico.last().nome == "Enfermeiro II - atualizado"

    def test_servidor_gera_historico_em_delete(self, tenant_a, in_tenant):
        from apps.people.models import Servidor

        with in_tenant(tenant_a):
            servidor = Servidor.objects.create(
                matricula="999",
                nome="Para deletar",
                cpf="222.222.222-22",
                data_nascimento="1980-01-01",
                sexo="F",
            )
            servidor.delete()

            from apps.people.models import Servidor as Modelo

            # apos delete, ainda ha registro historico (history_type=-)
            historico = Modelo.history.filter(matricula="999")
            assert historico.filter(history_type="-").count() == 1
