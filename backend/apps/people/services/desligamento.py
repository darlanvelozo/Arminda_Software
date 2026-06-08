"""
Service: desligar_servidor (Bloco 1.2 — Onda 3).

Encerra todos os vinculos ativos do servidor e marca o servidor como inativo,
em uma transacao atomica.

Validacoes (todas levantam DesligamentoInvalidoError):
- servidor existe
- servidor esta ativo (DESLIGAMENTO_DUPLICADO)
- data_desligamento nao futura (DATA_DESLIGAMENTO_FUTURA)
- data_desligamento >= data de admissao do vinculo mais antigo ativo (DATA_INVALIDA)
- pelo menos 1 vinculo ativo a encerrar (SEM_VINCULO_ATIVO)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db import transaction

from apps.people.models import Servidor
from apps.people.services.exceptions import DesligamentoInvalidoError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DadosDesligamento:
    servidor_id: int
    data_desligamento: date
    motivo: str = ""
    # Rescisão estruturada (Onda 3.2) — gravada nos vínculos encerrados.
    motivo_demissao: str = ""
    aviso_previo_indenizado: bool = False
    tem_ferias_vencidas: bool = False
    saldo_fgts: Decimal = Decimal(0)


@transaction.atomic
def desligar_servidor(dados: DadosDesligamento) -> Servidor:
    """Desliga um servidor do municipio (tenant atual).

    Marca o servidor como inativo e encerra todos os vinculos ativos com
    `data_demissao = data_desligamento`.

    Levanta `DesligamentoInvalidoError` em caso de invariante quebrado.
    """
    if dados.data_desligamento > date.today():
        raise DesligamentoInvalidoError(
            "Data de desligamento nao pode ser futura.",
            code="DATA_DESLIGAMENTO_FUTURA",
        )

    servidor = Servidor.objects.select_for_update().filter(id=dados.servidor_id).first()
    if not servidor:
        raise DesligamentoInvalidoError("Servidor nao encontrado.", code="SERVIDOR_NAO_ENCONTRADO")

    if not servidor.ativo:
        raise DesligamentoInvalidoError(
            "Servidor ja esta desligado.", code="DESLIGAMENTO_DUPLICADO"
        )

    vinculos_ativos = list(servidor.vinculos.filter(ativo=True))
    if not vinculos_ativos:
        raise DesligamentoInvalidoError(
            "Servidor nao possui vinculo ativo a encerrar.",
            code="SEM_VINCULO_ATIVO",
        )

    admissao_mais_antiga = min(v.data_admissao for v in vinculos_ativos)
    if dados.data_desligamento < admissao_mais_antiga:
        raise DesligamentoInvalidoError(
            "Data de desligamento nao pode ser anterior a admissao.",
            code="DATA_INVALIDA",
        )

    for vinculo in vinculos_ativos:
        vinculo.ativo = False
        vinculo.data_demissao = dados.data_desligamento
        vinculo.motivo_demissao = dados.motivo_demissao
        vinculo.aviso_previo_indenizado = dados.aviso_previo_indenizado
        vinculo.tem_ferias_vencidas = dados.tem_ferias_vencidas
        vinculo.saldo_fgts = dados.saldo_fgts
        vinculo.save(
            update_fields=[
                "ativo",
                "data_demissao",
                "motivo_demissao",
                "aviso_previo_indenizado",
                "tem_ferias_vencidas",
                "saldo_fgts",
                "atualizado_em",
            ]
        )

    servidor.ativo = False
    servidor.save(update_fields=["ativo", "atualizado_em"])

    logger.info(
        "people.desligamento.concluido",
        extra={
            "servidor_id": servidor.id,
            "matricula": servidor.matricula,
            "data": dados.data_desligamento.isoformat(),
            "motivo": dados.motivo,
            "vinculos_encerrados": len(vinculos_ativos),
        },
    )
    # Side effect post-commit (eSocial S-2299 sera adicionado no Bloco 4).
    return servidor
