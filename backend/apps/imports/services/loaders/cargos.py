"""Loader de Cargo — CARGOS (SIP) → apps.people.Cargo (Arminda)."""

from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.imports.models import TipoEntidadeSip
from apps.imports.services.loaders import LoaderStats, grava_erro, grava_sucesso
from apps.imports.services.mapping import map_cargo, payload_hash
from apps.people.models import Cargo


def load_cargos(rows: list[dict[str, Any]]) -> LoaderStats:
    """
    Persiste cargos no schema atual. Retorna estatísticas.

    Idempotente — re-run produz o mesmo estado final via `update_or_create`
    com chave `Cargo.codigo`.
    """
    stats = LoaderStats(tipo="cargo")

    for row in rows:
        stats.lidos += 1
        try:
            chave_sip, defaults = map_cargo(row)
        except Exception as exc:
            chave_fallback = f"{row.get('empresa', '?')}-{row.get('codigo', '?')}"[:120]
            stats.log_erro(f"map_cargo falhou: {exc} (chave={chave_fallback})")
            grava_erro(TipoEntidadeSip.CARGO, chave_fallback, str(exc))
            continue

        try:
            with transaction.atomic():
                cargo, created = Cargo.objects.update_or_create(
                    codigo=defaults["codigo"], defaults=defaults
                )
                grava_sucesso(
                    TipoEntidadeSip.CARGO, chave_sip, cargo.id, payload_hash(defaults)
                )
                if created:
                    stats.criados += 1
                else:
                    stats.atualizados += 1
        except Exception as exc:
            stats.log_erro(f"persistência de cargo {chave_sip} falhou: {exc}")
            grava_erro(TipoEntidadeSip.CARGO, chave_sip, str(exc))

    return stats
