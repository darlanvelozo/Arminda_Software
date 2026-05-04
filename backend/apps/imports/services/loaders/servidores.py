"""Loader de Servidor — PESSOA (SIP) → apps.people.Servidor (Arminda)."""

from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.imports.models import TipoEntidadeSip
from apps.imports.services.loaders import LoaderStats, grava_erro, grava_sucesso
from apps.imports.services.mapping import map_servidor, payload_hash
from apps.people.models import Servidor


def load_servidores(rows: list[dict[str, Any]]) -> LoaderStats:
    """
    Persiste pessoas como Servidores no Arminda. Chave SIP = CPF.

    Importante: a `matricula` aqui é provisória (CPF). O loader de Vínculo
    deve atualizar para a `REGISTRO` real do TRABALHADOR. Como `matricula`
    é unique no Arminda, isso requer cuidado quando o mesmo CPF tem N
    vínculos — eles ficarão na mesma matrícula final do último vínculo
    importado. Para casos com múltiplos vínculos por servidor, cada
    Vínculo guarda seu próprio `matricula_contrato`.
    """
    stats = LoaderStats(tipo="servidor")

    for row in rows:
        stats.lidos += 1
        try:
            chave_sip, defaults = map_servidor(row)
        except Exception as exc:
            chave_fallback = str(row.get("cpf", "?"))[:120]
            stats.log_erro(f"map_servidor falhou: {exc} (CPF={chave_fallback})")
            grava_erro(TipoEntidadeSip.SERVIDOR, chave_fallback, str(exc))
            continue

        try:
            with transaction.atomic():
                servidor, created = Servidor.objects.update_or_create(
                    cpf=defaults["cpf"], defaults=defaults
                )
                grava_sucesso(
                    TipoEntidadeSip.SERVIDOR,
                    chave_sip,
                    servidor.id,
                    payload_hash(defaults),
                )
                if created:
                    stats.criados += 1
                else:
                    stats.atualizados += 1
        except Exception as exc:
            stats.log_erro(f"persistência de servidor {chave_sip} falhou: {exc}")
            grava_erro(TipoEntidadeSip.SERVIDOR, chave_sip, str(exc))

    return stats
