"""Loader de Dependente — DEPENDENTES (SIP) → apps.people.Dependente."""

from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.imports.models import SipImportRecord, TipoEntidadeSip
from apps.imports.services.loaders import LoaderStats, grava_erro, grava_sucesso
from apps.imports.services.mapping import map_dependente, payload_hash
from apps.people.models import Dependente


def load_dependentes(rows: list[dict[str, Any]]) -> LoaderStats:
    """
    Persiste dependentes. Resolve servidor via CPF do titular.

    Idempotência via chave SIP composta: '<CPF_TITULAR>-<NOME_NORM>-<NASCIMENTO>'.
    Como Dependente não tem campo único natural no Arminda, usamos
    `(servidor_id, nome, data_nascimento)` no `update_or_create`.
    """
    stats = LoaderStats(tipo="dependente")
    servidores_map = {
        r.chave_sip: r.arminda_id
        for r in SipImportRecord.objects.filter(
            tipo=TipoEntidadeSip.SERVIDOR, status="ok"
        ).exclude(arminda_id=None)
    }

    for row in rows:
        stats.lidos += 1
        cpf_titular = str(row.get("cpf_titular", "")).strip()
        servidor_id = servidores_map.get(cpf_titular)

        if servidor_id is None:
            msg = f"Servidor com CPF titular '{cpf_titular}' não importado"
            stats.log_erro(msg)
            grava_erro(
                TipoEntidadeSip.DEPENDENTE,
                _key_fallback(row, cpf_titular),
                msg,
            )
            continue

        try:
            chave_sip, defaults = map_dependente(row, servidor_id=servidor_id)
        except Exception as exc:
            stats.log_erro(f"map_dependente falhou: {exc}")
            grava_erro(
                TipoEntidadeSip.DEPENDENTE, _key_fallback(row, cpf_titular), str(exc)
            )
            continue

        try:
            with transaction.atomic():
                dep, created = Dependente.objects.update_or_create(
                    servidor_id=servidor_id,
                    nome=defaults["nome"],
                    data_nascimento=defaults["data_nascimento"],
                    defaults=defaults,
                )
                grava_sucesso(
                    TipoEntidadeSip.DEPENDENTE,
                    chave_sip,
                    dep.id,
                    payload_hash(defaults),
                )
                if created:
                    stats.criados += 1
                else:
                    stats.atualizados += 1
        except Exception as exc:
            stats.log_erro(f"persistência de dependente {chave_sip} falhou: {exc}")
            grava_erro(TipoEntidadeSip.DEPENDENTE, chave_sip, str(exc))

    return stats


def _key_fallback(row: dict[str, Any], cpf_titular: str) -> str:
    nome = str(row.get("nome", "?"))[:30]
    return f"{cpf_titular}-{nome}"[:120]
