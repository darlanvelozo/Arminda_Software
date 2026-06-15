"""
Seed da rubrica de licença-prêmio (indenização) — Onda 3.4 (ADR-0018).

Escopo `tipos_folha=['licenca_premio']`. Verba indenizatória — sem incidência.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.payroll.models import Rubrica, TipoFolha, TipoRubrica

LP = [TipoFolha.LICENCA_PREMIO]

RUBRICAS_LP = [
    ("LP_INDENIZ", "Licença-prêmio (indenização)", TipoRubrica.PROVENTO,
     "ARRED(SALARIO_BASE * MESES_LP + SALARIO_BASE / 30 * DIAS_LP, 2)",
     False, False, False, False),
]


class Command(BaseCommand):
    help = "Cria a rubrica de indenização de licença-prêmio — Onda 3.4."

    def add_arguments(self, parser):
        parser.add_argument("--substituir", action="store_true",
                            help="Sobrescreve rubricas existentes com o mesmo código.")

    def handle(self, *args, **options):
        substituir = options["substituir"]
        criadas, mantidas, atualizadas = 0, 0, 0
        for codigo, nome, tipo, formula, inss, irrf, fgts, rpps in RUBRICAS_LP:
            defaults = {
                "nome": nome, "tipo": tipo, "formula": formula,
                "incide_inss": inss, "incide_irrf": irrf,
                "incide_fgts": fgts, "incide_rpps": rpps,
                "tipos_folha": list(LP), "ativo": True,
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
        self.stdout.write(self.style.SUCCESS(
            f"Rubricas de licença-prêmio: {criadas} criadas, {atualizadas} atualizadas, "
            f"{mantidas} mantidas."
        ))
