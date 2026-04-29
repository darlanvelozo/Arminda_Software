"""Management command: lista todos os tenants (municipios) cadastrados."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.core.models import Municipio


class Command(BaseCommand):
    help = "Lista todos os municipios (tenants) cadastrados"

    def handle(self, *args, **options):
        municipios = Municipio.objects.all().order_by("nome")
        if not municipios.exists():
            self.stdout.write("Nenhum municipio cadastrado.")
            return

        self.stdout.write(f"{'Schema':<30} {'Codigo IBGE':<12} {'UF':<4} {'Nome'}")
        self.stdout.write("-" * 80)
        for m in municipios:
            self.stdout.write(f"{m.schema_name:<30} {m.codigo_ibge:<12} {m.uf:<4} {m.nome}")
        self.stdout.write(f"\nTotal: {municipios.count()}")
