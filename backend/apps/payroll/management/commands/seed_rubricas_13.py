"""
Seed das rubricas de 13º salário (1ª e 2ª parcela) — Onda 3.1 (ADR-0015).

Cria, de forma idempotente, as rubricas escopadas por tipo de folha:
- 1ª parcela (`13_primeira`): adiantamento de 50%, sem incidências.
- 2ª parcela (`13_segunda`): 13º integral (forma as bases) + INSS/IRRF/RPPS
  calculados sobre o 13º + abatimento do adiantamento + FGTS/RPPS patronal
  informativos.

Reusa o engine de duas fases: o provento 13_PROV (com incide_*) forma
BASE_INSS/IRRF/FGTS/RPPS, e os descontos calculam as incidências sobre elas
— ou seja, INSS/IRRF do 13º saem naturalmente separados da folha mensal.

Roda no schema do tenant atual (use `tenant_command` para um município).
`--substituir` sobrescreve rubricas existentes com o mesmo código.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.payroll.models import Rubrica, TipoFolha, TipoRubrica

P1 = [TipoFolha.DECIMO_PRIMEIRO]
P2 = [TipoFolha.DECIMO_SEGUNDO]

# (codigo, nome, tipo, formula, inss, irrf, fgts, rpps, tipos_folha)
RUBRICAS_13 = [
    # --- 1ª parcela (adiantamento) ---
    (
        "13_ADIANT",
        "13º - Adiantamento (1ª parcela)",
        TipoRubrica.PROVENTO,
        "ARRED(BASE_13 * AVOS_13 / 12 * 0.5, 2)",
        False, False, False, False, P1,
    ),
    # --- 2ª parcela ---
    (
        "13_PROV",
        "13º salário",
        TipoRubrica.PROVENTO,
        "ARRED(BASE_13 * AVOS_13 / 12, 2)",
        True, True, True, True, P2,
    ),
    (
        "13_INSS",
        "13º - INSS",
        TipoRubrica.DESCONTO,
        "FAIXA_INSS(BASE_INSS) * EH_RGPS",
        False, False, False, False, P2,
    ),
    (
        "13_RPPS",
        "13º - Previdência própria (RPPS)",
        TipoRubrica.DESCONTO,
        "FAIXA_RPPS(BASE_RPPS) * EH_RPPS",
        False, False, False, False, P2,
    ),
    (
        "13_IRRF",
        "13º - IRRF",
        TipoRubrica.DESCONTO,
        "FAIXA_IRRF(BASE_IRRF - RUBRICA('13_INSS') - RUBRICA('13_RPPS'), DEPENDENTES)",
        False, False, False, False, P2,
    ),
    (
        "13_ADIANT_DESC",
        "13º - Abatimento do adiantamento",
        TipoRubrica.DESCONTO,
        "ARRED(BASE_13 * AVOS_13 / 12 * 0.5, 2)",
        False, False, False, False, P2,
    ),
    (
        "13_FGTS",
        "13º - FGTS (encargo patronal)",
        TipoRubrica.INFORMATIVA,
        "BASE_FGTS * ALIQ_FGTS * EH_FGTS",
        False, False, False, False, P2,
    ),
    (
        "13_RPPS_PATRON",
        "13º - RPPS patronal",
        TipoRubrica.INFORMATIVA,
        "BASE_RPPS * ALIQ_RPPS_PATRONAL * EH_RPPS",
        False, False, False, False, P2,
    ),
]


class Command(BaseCommand):
    help = "Cria as rubricas padrão do 13º salário (1ª e 2ª parcela) — Onda 3.1."

    def add_arguments(self, parser):
        parser.add_argument(
            "--substituir",
            action="store_true",
            help="Sobrescreve a fórmula/flags de rubricas já existentes com o mesmo código.",
        )

    def handle(self, *args, **options):
        substituir = options["substituir"]
        criadas, mantidas, atualizadas = 0, 0, 0

        for codigo, nome, tipo, formula, inss, irrf, fgts, rpps, tipos in RUBRICAS_13:
            defaults = {
                "nome": nome,
                "tipo": tipo,
                "formula": formula,
                "incide_inss": inss,
                "incide_irrf": irrf,
                "incide_fgts": fgts,
                "incide_rpps": rpps,
                "tipos_folha": list(tipos),
                "ativo": True,
            }
            existente = Rubrica.objects.filter(codigo=codigo).first()
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
                f"Rubricas de 13º: {criadas} criadas, {atualizadas} atualizadas, "
                f"{mantidas} mantidas."
            )
        )
