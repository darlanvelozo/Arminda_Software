"""
Service: transferir_lotacao (Bloco 1.2 — Onda 3).

Transfere um vinculo funcional para outra lotacao do mesmo municipio.
Encerra o vinculo atual e cria um novo com mesma combinacao
(cargo, regime, carga_horaria, salario_base) na nova lotacao.

Validacoes (todas levantam TransferenciaInvalidaError):
- vinculo existe e esta ativo (VINCULO_INVALIDO)
- nova_lotacao existe, esta ativa (LOTACAO_INVALIDA)
- nova_lotacao != atual (TRANSFERENCIA_REDUNDANTE)
- data_transferencia nao futura (DATA_FUTURA)
- data_transferencia > data_admissao do vinculo (DATA_INVALIDA)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from django.db import transaction

from apps.people.models import Lotacao, VinculoFuncional
from apps.people.services.exceptions import TransferenciaInvalidaError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DadosTransferencia:
    vinculo_id: int
    nova_lotacao_id: int
    data_transferencia: date


@transaction.atomic
def transferir_lotacao(dados: DadosTransferencia) -> VinculoFuncional:
    """Transfere o vinculo para outra lotacao.

    Retorna o NOVO vinculo criado na nova lotacao.
    """
    if dados.data_transferencia > date.today():
        raise TransferenciaInvalidaError(
            "Data de transferencia nao pode ser futura.", code="DATA_FUTURA"
        )

    vinculo_atual = (
        VinculoFuncional.objects.select_for_update()
        .select_related("servidor", "cargo", "lotacao")
        .filter(id=dados.vinculo_id)
        .first()
    )
    if not vinculo_atual or not vinculo_atual.ativo:
        raise TransferenciaInvalidaError(
            "Vinculo nao encontrado ou ja inativo.",
            code="VINCULO_INVALIDO",
        )

    if dados.data_transferencia < vinculo_atual.data_admissao:
        raise TransferenciaInvalidaError(
            "Data de transferencia nao pode ser anterior a admissao.",
            code="DATA_INVALIDA",
        )

    nova_lotacao = Lotacao.objects.filter(id=dados.nova_lotacao_id, ativo=True).first()
    if not nova_lotacao:
        raise TransferenciaInvalidaError(
            "Lotacao destino invalida ou inativa.", code="LOTACAO_INVALIDA"
        )

    if vinculo_atual.lotacao_id == nova_lotacao.id:
        raise TransferenciaInvalidaError(
            "Servidor ja esta nesta lotacao.",
            code="TRANSFERENCIA_REDUNDANTE",
        )

    # Encerra vinculo antigo
    vinculo_atual.ativo = False
    vinculo_atual.data_demissao = dados.data_transferencia
    vinculo_atual.save(update_fields=["ativo", "data_demissao", "atualizado_em"])

    # Cria novo vinculo na nova lotacao, preservando demais atributos
    novo_vinculo = VinculoFuncional.objects.create(
        servidor=vinculo_atual.servidor,
        cargo=vinculo_atual.cargo,
        lotacao=nova_lotacao,
        regime=vinculo_atual.regime,
        data_admissao=dados.data_transferencia,
        carga_horaria=vinculo_atual.carga_horaria,
        salario_base=vinculo_atual.salario_base,
        ativo=True,
    )

    logger.info(
        "people.transferencia.concluida",
        extra={
            "servidor_id": vinculo_atual.servidor_id,
            "vinculo_anterior_id": vinculo_atual.id,
            "vinculo_novo_id": novo_vinculo.id,
            "lotacao_anterior_id": vinculo_atual.lotacao_id,
            "lotacao_nova_id": nova_lotacao.id,
        },
    )
    return novo_vinculo
