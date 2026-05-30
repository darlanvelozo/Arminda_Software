"""
Seed do conjunto padrão de rubricas de incidência (Onda 2.4 — ADR-0013).

Cria, de forma idempotente, as rubricas que dependem das bases
automáticas e do gating por regime (INSS, RPPS servidor, RPPS patronal,
FGTS, IRRF) mais um SAL_BASE de exemplo que compõe todas as bases.

Roda no schema do tenant atual. Para um município específico:

    python manage.py tenant_command seed_rubricas_incidencia --schema=mun_x

ou dentro de um `schema_context` em testes. Use `--substituir` para
sobrescrever fórmulas de rubricas já existentes com o mesmo código.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.payroll.models import Rubrica, TipoRubrica

# (codigo, nome, tipo, formula, incide_inss, incide_irrf, incide_fgts, incide_rpps)
RUBRICAS_PADRAO = [
    (
        "SAL_BASE",
        "Salário base",
        TipoRubrica.PROVENTO,
        "SALARIO_BASE",
        True,
        True,
        True,
        True,
    ),
    (
        "INSS",
        "INSS (RGPS)",
        TipoRubrica.DESCONTO,
        "FAIXA_INSS(BASE_INSS) * EH_RGPS",
        False,
        False,
        False,
        False,
    ),
    (
        "RPPS",
        "Previdência própria (RPPS) - servidor",
        TipoRubrica.DESCONTO,
        "FAIXA_RPPS(BASE_RPPS) * EH_RPPS",
        False,
        False,
        False,
        False,
    ),
    (
        "IRRF",
        "IRRF",
        TipoRubrica.DESCONTO,
        "FAIXA_IRRF(BASE_IRRF - RUBRICA('INSS') - RUBRICA('RPPS'), DEPENDENTES)",
        False,
        False,
        False,
        False,
    ),
    (
        "FGTS",
        "FGTS (encargo patronal)",
        TipoRubrica.INFORMATIVA,
        "BASE_FGTS * ALIQ_FGTS * EH_FGTS",
        False,
        False,
        False,
        False,
    ),
    (
        "RPPS_PATRONAL",
        "RPPS - contribuição patronal",
        TipoRubrica.INFORMATIVA,
        "BASE_RPPS * ALIQ_RPPS_PATRONAL * EH_RPPS",
        False,
        False,
        False,
        False,
    ),
]


class Command(BaseCommand):
    help = "Cria as rubricas padrão de incidência (INSS, RPPS, IRRF, FGTS) — Onda 2.4."

    def add_arguments(self, parser):
        parser.add_argument(
            "--substituir",
            action="store_true",
            help="Sobrescreve a fórmula/flags de rubricas já existentes com o mesmo código.",
        )

    def handle(self, *args, **options):
        substituir = options["substituir"]
        criadas, mantidas, atualizadas = 0, 0, 0

        for codigo, nome, tipo, formula, inss, irrf, fgts, rpps in RUBRICAS_PADRAO:
            existente = Rubrica.objects.filter(codigo=codigo).first()
            defaults = {
                "nome": nome,
                "tipo": tipo,
                "formula": formula,
                "incide_inss": inss,
                "incide_irrf": irrf,
                "incide_fgts": fgts,
                "incide_rpps": rpps,
                "ativo": True,
            }
            if existente is None:
                Rubrica.objects.create(codigo=codigo, **defaults)
                criadas += 1
            elif substituir:
                for campo, valor in defaults.items():
                    setattr(existente, campo, valor)
                existente.save()
                atualizadas += 1
            else:
                mantidas += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Rubricas de incidência: {criadas} criadas, "
                f"{atualizadas} atualizadas, {mantidas} mantidas."
            )
        )
