"""Loader de Unidade Orçamentária — UNIDADE (SIP) → apps.people.UnidadeOrcamentaria."""

from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.imports.models import TipoEntidadeSip
from apps.imports.services.loaders import LoaderStats, grava_erro, grava_sucesso
from apps.imports.services.mapping import map_unidade_orcamentaria, payload_hash
from apps.people.models import UnidadeOrcamentaria


def load_unidades_orcamentarias(rows: list[dict[str, Any]]) -> LoaderStats:
    """
    Persiste unidades orçamentárias. Chave unique: (codigo, ano).

    Idempotente: rerun atualiza nome/sigla/natureza sem duplicar.
    """
    stats = LoaderStats(tipo="unidade_orcamentaria")

    for row in rows:
        stats.lidos += 1
        try:
            chave_sip, defaults = map_unidade_orcamentaria(row)
        except Exception as exc:
            chave_fallback = (
                f"{row.get('ano', '?')}-{row.get('empresa', '?')}-"
                f"{row.get('depdespesa', '?')}"
            )[:120]
            stats.log_erro(f"map_unidade_orcamentaria falhou: {exc}")
            grava_erro(TipoEntidadeSip.UNIDADE_ORCAMENTARIA, chave_fallback, str(exc))
            continue

        try:
            with transaction.atomic():
                unidade, created = UnidadeOrcamentaria.objects.update_or_create(
                    codigo=defaults["codigo"],
                    ano=defaults["ano"],
                    defaults=defaults,
                )
                grava_sucesso(
                    TipoEntidadeSip.UNIDADE_ORCAMENTARIA,
                    chave_sip,
                    unidade.id,
                    payload_hash(defaults),
                )
                if created:
                    stats.criados += 1
                else:
                    stats.atualizados += 1
        except Exception as exc:
            stats.log_erro(f"persistência {chave_sip} falhou: {exc}")
            grava_erro(TipoEntidadeSip.UNIDADE_ORCAMENTARIA, chave_sip, str(exc))

    return stats
