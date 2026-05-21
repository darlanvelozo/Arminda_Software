"""
Signals do app core (Onda 2.3).

Invalidam o cache de `apps.calculo.tabelas` quando qualquer TabelaLegal
é salva ou removida no admin — garante que mudanças via admin são vistas
no próximo cálculo, sem reiniciar o processo.
"""

from __future__ import annotations

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.core.models import TabelaLegal


@receiver(post_save, sender=TabelaLegal)
def _invalidar_cache_save(sender, instance, **kwargs):  # noqa: ARG001
    from apps.calculo.tabelas import _invalidar_cache

    _invalidar_cache()


@receiver(post_delete, sender=TabelaLegal)
def _invalidar_cache_delete(sender, instance, **kwargs):  # noqa: ARG001
    from apps.calculo.tabelas import _invalidar_cache

    _invalidar_cache()
