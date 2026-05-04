"""Loader de Lotação — LOCAL_TRABALHO (SIP) → apps.people.Lotacao (Arminda)."""

from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.imports.models import TipoEntidadeSip
from apps.imports.services.loaders import LoaderStats, grava_erro, grava_sucesso
from apps.imports.services.mapping import map_lotacao, payload_hash
from apps.people.models import Lotacao


def load_lotacoes(rows: list[dict[str, Any]]) -> LoaderStats:
    """Persiste locais de trabalho como Lotações no Arminda."""
    stats = LoaderStats(tipo="lotacao")

    for row in rows:
        stats.lidos += 1
        try:
            chave_sip, defaults = map_lotacao(row)
        except Exception as exc:
            chave_fallback = f"{row.get('empresa', '?')}-LT-{row.get('codigo', '?')}"[:120]
            stats.log_erro(f"map_lotacao falhou: {exc} (chave={chave_fallback})")
            grava_erro(TipoEntidadeSip.LOTACAO, chave_fallback, str(exc))
            continue

        try:
            with transaction.atomic():
                lotacao, created = Lotacao.objects.update_or_create(
                    codigo=defaults["codigo"], defaults=defaults
                )
                grava_sucesso(
                    TipoEntidadeSip.LOTACAO, chave_sip, lotacao.id, payload_hash(defaults)
                )
                if created:
                    stats.criados += 1
                else:
                    stats.atualizados += 1
        except Exception as exc:
            stats.log_erro(f"persistência de lotação {chave_sip} falhou: {exc}")
            grava_erro(TipoEntidadeSip.LOTACAO, chave_sip, str(exc))

    return stats
