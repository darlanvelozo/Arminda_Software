"""
Service: admitir_servidor (Bloco 1.2 — Onda 3).

Cria Servidor + VinculoFuncional inicial em uma transacao atomica.
Roda no contexto do tenant resolvido pelo middleware (search_path do Postgres).

Validacoes (todas levantam AdmissaoInvalidaError com `code` estavel):
- matricula nao duplicada (MATRICULA_DUPLICADA)
- cargo existe e esta ativo (CARGO_INVALIDO)
- lotacao existe e esta ativa (LOTACAO_INVALIDA)
- data de admissao nao futura (DATA_ADMISSAO_FUTURA)
- salario base > 0 (SALARIO_INVALIDO)
- carga horaria entre 1 e 60 (CARGA_HORARIA_INVALIDA)

Side effects: cria Servidor + VinculoFuncional. Eventos eSocial S-2200
sao Bloco 4 — disparam aqui via transaction.on_commit() futuramente.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from apps.core.validators import validar_cpf, validar_pis_pasep
from apps.people.models import (
    Cargo,
    EstadoCivil,
    Lotacao,
    Regime,
    Servidor,
    Sexo,
    VinculoFuncional,
)
from apps.people.services.exceptions import AdmissaoInvalidaError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DadosAdmissao:
    """Dados para admitir um servidor.

    Forcamos dataclass (nao dict solto) para tipagem explicita e imutabilidade.
    """

    # Pessoais
    matricula: str
    nome: str
    cpf: str
    data_nascimento: date
    sexo: str  # Sexo.choices

    # Vinculo
    cargo_id: int
    lotacao_id: int
    regime: str  # Regime.choices
    data_admissao: date
    salario_base: Decimal
    carga_horaria: int = 40

    # Opcionais
    estado_civil: str = ""
    pis_pasep: str = ""
    email: str = ""
    telefone: str = ""


@transaction.atomic
def admitir_servidor(dados: DadosAdmissao) -> Servidor:
    """Admite um servidor no tenant atual.

    Cria o Servidor e seu VinculoFuncional inicial em uma transacao.
    Levanta `AdmissaoInvalidaError` com code estavel se algum invariante quebrar.
    """
    _validar(dados)

    cargo = Cargo.objects.filter(id=dados.cargo_id, ativo=True).first()
    if not cargo:
        raise AdmissaoInvalidaError("Cargo invalido ou inativo.", code="CARGO_INVALIDO")

    lotacao = Lotacao.objects.filter(id=dados.lotacao_id, ativo=True).first()
    if not lotacao:
        raise AdmissaoInvalidaError("Lotacao invalida ou inativa.", code="LOTACAO_INVALIDA")

    if Servidor.objects.filter(matricula=dados.matricula).exists():
        raise AdmissaoInvalidaError(
            f"Matricula '{dados.matricula}' ja existe neste municipio.",
            code="MATRICULA_DUPLICADA",
        )

    try:
        cpf_normalizado = validar_cpf(dados.cpf)
    except DjangoValidationError as exc:
        raise AdmissaoInvalidaError(
            "CPF invalido.", code="CPF_INVALIDO"
        ) from exc

    try:
        pis_normalizado = (
            validar_pis_pasep(dados.pis_pasep) if dados.pis_pasep else ""
        )
    except DjangoValidationError as exc:
        raise AdmissaoInvalidaError(
            "PIS/PASEP invalido.", code="PIS_INVALIDO"
        ) from exc

    servidor = Servidor.objects.create(
        matricula=dados.matricula.strip(),
        nome=dados.nome.strip(),
        cpf=cpf_normalizado,
        data_nascimento=dados.data_nascimento,
        sexo=dados.sexo,
        estado_civil=dados.estado_civil or "",
        pis_pasep=pis_normalizado,
        email=(dados.email or "").strip(),
        telefone=(dados.telefone or "").strip(),
        ativo=True,
    )
    VinculoFuncional.objects.create(
        servidor=servidor,
        cargo=cargo,
        lotacao=lotacao,
        regime=dados.regime,
        data_admissao=dados.data_admissao,
        carga_horaria=dados.carga_horaria,
        salario_base=dados.salario_base,
        ativo=True,
    )

    logger.info(
        "people.admissao.concluida",
        extra={
            "servidor_id": servidor.id,
            "matricula": servidor.matricula,
            "cargo_id": cargo.id,
            "lotacao_id": lotacao.id,
        },
    )
    # Side effect post-commit (eSocial S-2200 sera adicionado no Bloco 4).
    return servidor


def _validar(dados: DadosAdmissao) -> None:  # noqa: C901
    """Validacoes que dispensam consulta ao banco.

    Sequencia linear de invariantes — quebrar em sub-funcoes prejudicaria
    a leitura. Aceitamos a complexidade.
    """
    if not dados.matricula or not dados.matricula.strip():
        raise AdmissaoInvalidaError("Matricula e obrigatoria.", code="MATRICULA_INVALIDA")
    if not dados.nome or len(dados.nome.strip()) < 2:
        raise AdmissaoInvalidaError("Nome muito curto.", code="NOME_INVALIDO")
    if dados.sexo not in dict(Sexo.choices):
        raise AdmissaoInvalidaError(f"Sexo '{dados.sexo}' invalido.", code="SEXO_INVALIDO")
    if dados.estado_civil and dados.estado_civil not in dict(EstadoCivil.choices):
        raise AdmissaoInvalidaError(
            f"Estado civil '{dados.estado_civil}' invalido.",
            code="ESTADO_CIVIL_INVALIDO",
        )
    if dados.regime not in dict(Regime.choices):
        raise AdmissaoInvalidaError(f"Regime '{dados.regime}' invalido.", code="REGIME_INVALIDO")
    if dados.data_admissao > date.today():
        raise AdmissaoInvalidaError(
            "Data de admissao nao pode ser futura.", code="DATA_ADMISSAO_FUTURA"
        )
    if dados.data_nascimento > date.today():
        raise AdmissaoInvalidaError(
            "Data de nascimento nao pode ser futura.",
            code="DATA_NASCIMENTO_FUTURA",
        )
    idade = (dados.data_admissao - dados.data_nascimento).days / 365.25
    if idade < 14:
        raise AdmissaoInvalidaError(
            "Servidor deve ter ao menos 14 anos na data da admissao.",
            code="IDADE_MINIMA",
        )
    if dados.salario_base <= 0:
        raise AdmissaoInvalidaError(
            "Salario base deve ser maior que zero.", code="SALARIO_INVALIDO"
        )
    if not (1 <= dados.carga_horaria <= 60):
        raise AdmissaoInvalidaError(
            "Carga horaria deve estar entre 1 e 60 horas semanais.",
            code="CARGA_HORARIA_INVALIDA",
        )
