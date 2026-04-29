"""
Testes do service `admitir_servidor` (Bloco 1.2 — Onda 3).

Cobre caminho feliz e cada code de excecao.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.people.services.admissao import DadosAdmissao, admitir_servidor
from apps.people.services.exceptions import AdmissaoInvalidaError


@pytest.fixture
def cargo(tenant_a, in_tenant):
    from apps.people.models import Cargo

    with in_tenant(tenant_a):
        return Cargo.objects.create(codigo="PROF1", nome="Professor I", ativo=True)


@pytest.fixture
def cargo_inativo(tenant_a, in_tenant):
    from apps.people.models import Cargo

    with in_tenant(tenant_a):
        return Cargo.objects.create(codigo="OBSOL", nome="Obsoleto", ativo=False)


@pytest.fixture
def lotacao(tenant_a, in_tenant):
    from apps.people.models import Lotacao

    with in_tenant(tenant_a):
        return Lotacao.objects.create(codigo="EDUC", nome="Educacao", ativo=True)


def _dados_validos(cargo_id: int, lotacao_id: int, **overrides) -> DadosAdmissao:
    base = {
        "matricula": "0001",
        "nome": "Joao da Silva",
        "cpf": "111.444.777-35",
        "data_nascimento": date(1990, 1, 15),
        "sexo": "M",
        "cargo_id": cargo_id,
        "lotacao_id": lotacao_id,
        "regime": "estatutario",
        "data_admissao": date(2024, 6, 1),
        "salario_base": Decimal("3500.00"),
        "carga_horaria": 40,
    }
    base.update(overrides)
    return DadosAdmissao(**base)


@pytest.mark.django_db
class TestAdmitirServidorCaminhoFeliz:
    def test_admite_servidor_basico(self, tenant_a, in_tenant, cargo, lotacao):
        with in_tenant(tenant_a):
            servidor = admitir_servidor(_dados_validos(cargo.id, lotacao.id))

            assert servidor.id is not None
            assert servidor.matricula == "0001"
            assert servidor.cpf == "11144477735"  # normalizado
            assert servidor.ativo is True
            assert servidor.vinculos.count() == 1

            vinculo = servidor.vinculos.first()
            assert vinculo.cargo_id == cargo.id
            assert vinculo.lotacao_id == lotacao.id
            assert vinculo.ativo is True
            assert vinculo.salario_base == Decimal("3500.00")

    def test_pis_pasep_normalizado(self, tenant_a, in_tenant, cargo, lotacao):
        with in_tenant(tenant_a):
            servidor = admitir_servidor(
                _dados_validos(cargo.id, lotacao.id, pis_pasep="123.45678.90-0")
            )
            assert servidor.pis_pasep == "12345678900"

    def test_email_e_telefone_strip(self, tenant_a, in_tenant, cargo, lotacao):
        with in_tenant(tenant_a):
            servidor = admitir_servidor(
                _dados_validos(
                    cargo.id,
                    lotacao.id,
                    email="  joao@x.test  ",
                    telefone=" 99999999 ",
                )
            )
            assert servidor.email == "joao@x.test"
            assert servidor.telefone == "99999999"


@pytest.mark.django_db
class TestAdmitirServidorExcecoes:
    def test_matricula_vazia(self, tenant_a, in_tenant, cargo, lotacao):
        with in_tenant(tenant_a), pytest.raises(AdmissaoInvalidaError) as exc:
            admitir_servidor(_dados_validos(cargo.id, lotacao.id, matricula="  "))
        assert exc.value.code == "MATRICULA_INVALIDA"

    def test_nome_curto(self, tenant_a, in_tenant, cargo, lotacao):
        with in_tenant(tenant_a), pytest.raises(AdmissaoInvalidaError) as exc:
            admitir_servidor(_dados_validos(cargo.id, lotacao.id, nome="X"))
        assert exc.value.code == "NOME_INVALIDO"

    def test_sexo_invalido(self, tenant_a, in_tenant, cargo, lotacao):
        with in_tenant(tenant_a), pytest.raises(AdmissaoInvalidaError) as exc:
            admitir_servidor(_dados_validos(cargo.id, lotacao.id, sexo="X"))
        assert exc.value.code == "SEXO_INVALIDO"

    def test_estado_civil_invalido(self, tenant_a, in_tenant, cargo, lotacao):
        with in_tenant(tenant_a), pytest.raises(AdmissaoInvalidaError) as exc:
            admitir_servidor(_dados_validos(cargo.id, lotacao.id, estado_civil="errado"))
        assert exc.value.code == "ESTADO_CIVIL_INVALIDO"

    def test_regime_invalido(self, tenant_a, in_tenant, cargo, lotacao):
        with in_tenant(tenant_a), pytest.raises(AdmissaoInvalidaError) as exc:
            admitir_servidor(_dados_validos(cargo.id, lotacao.id, regime="???"))
        assert exc.value.code == "REGIME_INVALIDO"

    def test_data_admissao_futura(self, tenant_a, in_tenant, cargo, lotacao):
        with in_tenant(tenant_a), pytest.raises(AdmissaoInvalidaError) as exc:
            admitir_servidor(
                _dados_validos(
                    cargo.id, lotacao.id, data_admissao=date.today() + timedelta(days=30)
                )
            )
        assert exc.value.code == "DATA_ADMISSAO_FUTURA"

    def test_data_nascimento_futura(self, tenant_a, in_tenant, cargo, lotacao):
        with in_tenant(tenant_a), pytest.raises(AdmissaoInvalidaError) as exc:
            admitir_servidor(
                _dados_validos(
                    cargo.id,
                    lotacao.id,
                    data_nascimento=date.today() + timedelta(days=1),
                )
            )
        assert exc.value.code == "DATA_NASCIMENTO_FUTURA"

    def test_idade_minima(self, tenant_a, in_tenant, cargo, lotacao):
        with in_tenant(tenant_a), pytest.raises(AdmissaoInvalidaError) as exc:
            admitir_servidor(
                _dados_validos(
                    cargo.id,
                    lotacao.id,
                    data_nascimento=date(2020, 1, 1),
                    data_admissao=date(2024, 1, 1),
                )
            )
        assert exc.value.code == "IDADE_MINIMA"

    def test_salario_zero(self, tenant_a, in_tenant, cargo, lotacao):
        with in_tenant(tenant_a), pytest.raises(AdmissaoInvalidaError) as exc:
            admitir_servidor(_dados_validos(cargo.id, lotacao.id, salario_base=Decimal("0")))
        assert exc.value.code == "SALARIO_INVALIDO"

    def test_carga_horaria_invalida(self, tenant_a, in_tenant, cargo, lotacao):
        with in_tenant(tenant_a), pytest.raises(AdmissaoInvalidaError) as exc:
            admitir_servidor(_dados_validos(cargo.id, lotacao.id, carga_horaria=80))
        assert exc.value.code == "CARGA_HORARIA_INVALIDA"

    def test_cargo_inexistente(self, tenant_a, in_tenant, lotacao):
        with in_tenant(tenant_a), pytest.raises(AdmissaoInvalidaError) as exc:
            admitir_servidor(_dados_validos(99999, lotacao.id))
        assert exc.value.code == "CARGO_INVALIDO"

    def test_cargo_inativo(self, tenant_a, in_tenant, cargo_inativo, lotacao):
        with in_tenant(tenant_a), pytest.raises(AdmissaoInvalidaError) as exc:
            admitir_servidor(_dados_validos(cargo_inativo.id, lotacao.id))
        assert exc.value.code == "CARGO_INVALIDO"

    def test_lotacao_inexistente(self, tenant_a, in_tenant, cargo):
        with in_tenant(tenant_a), pytest.raises(AdmissaoInvalidaError) as exc:
            admitir_servidor(_dados_validos(cargo.id, 99999))
        assert exc.value.code == "LOTACAO_INVALIDA"

    def test_cpf_invalido(self, tenant_a, in_tenant, cargo, lotacao):
        with in_tenant(tenant_a), pytest.raises(AdmissaoInvalidaError) as exc:
            admitir_servidor(
                _dados_validos(cargo.id, lotacao.id, cpf="111.111.111-11")
            )
        assert exc.value.code == "CPF_INVALIDO"

    def test_pis_invalido(self, tenant_a, in_tenant, cargo, lotacao):
        with in_tenant(tenant_a), pytest.raises(AdmissaoInvalidaError) as exc:
            admitir_servidor(
                _dados_validos(cargo.id, lotacao.id, pis_pasep="11111111111")
            )
        assert exc.value.code == "PIS_INVALIDO"

    def test_matricula_duplicada(self, tenant_a, in_tenant, cargo, lotacao):
        with in_tenant(tenant_a):
            admitir_servidor(_dados_validos(cargo.id, lotacao.id))
            with pytest.raises(AdmissaoInvalidaError) as exc:
                admitir_servidor(_dados_validos(cargo.id, lotacao.id))
        assert exc.value.code == "MATRICULA_DUPLICADA"


@pytest.mark.django_db
class TestAdmitirServidorAtomicidade:
    def test_falha_no_meio_nao_deixa_servidor_orfao(self, tenant_a, in_tenant, cargo, lotacao):
        """Se a criacao do vinculo falhasse, o servidor nao pode persistir.

        Forcamos uma falha passando lotacao_id=99999 — mas a validacao
        rejeita ANTES de criar o servidor. Validamos que apos a excecao
        nenhum servidor foi criado.
        """
        from apps.people.models import Servidor

        with in_tenant(tenant_a):
            assert Servidor.objects.count() == 0
            with pytest.raises(AdmissaoInvalidaError):
                admitir_servidor(_dados_validos(cargo.id, 99999))
            assert Servidor.objects.count() == 0
