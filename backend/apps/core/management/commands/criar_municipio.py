"""
Management command: cria um Municipio (tenant) + Domain associado.

Uso:
    python manage.py criar_municipio \\
        --nome "Sao Raimundo do Doca Bezerra" \\
        --uf MA \\
        --codigo-ibge 2110005 \\
        --schema mun_sao_raimundo \\
        --domain mun-sao-raimundo.localhost

Cria o schema do tenant automaticamente (auto_create_schema=True).
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models import Domain, Municipio


class Command(BaseCommand):
    help = "Cria um municipio (tenant) e seu Domain associado"

    def add_arguments(self, parser):
        parser.add_argument("--nome", required=True, help="Nome do municipio")
        parser.add_argument("--uf", required=True, help="UF (sigla, 2 letras)")
        parser.add_argument("--codigo-ibge", required=True, help="Codigo IBGE (7 digitos)")
        parser.add_argument(
            "--schema",
            required=True,
            help="Nome do schema PostgreSQL (ex: mun_sao_raimundo)",
        )
        parser.add_argument(
            "--domain",
            default=None,
            help="Hostname para resolucao em prod (opcional em dev)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        nome: str = options["nome"]
        uf: str = options["uf"].upper()
        codigo_ibge: str = options["codigo_ibge"]
        schema_name: str = options["schema"]
        domain: str | None = options["domain"]

        if Municipio.objects.filter(schema_name=schema_name).exists():
            raise CommandError(f"Schema '{schema_name}' ja existe")
        if Municipio.objects.filter(codigo_ibge=codigo_ibge).exists():
            raise CommandError(f"Codigo IBGE '{codigo_ibge}' ja existe")

        municipio = Municipio.objects.create(
            schema_name=schema_name,
            nome=nome,
            uf=uf,
            codigo_ibge=codigo_ibge,
        )
        self.stdout.write(
            self.style.SUCCESS(f"Municipio criado: {municipio} (schema={schema_name})")
        )

        if domain:
            Domain.objects.create(domain=domain, tenant=municipio, is_primary=True)
            self.stdout.write(self.style.SUCCESS(f"Domain '{domain}' associado"))
