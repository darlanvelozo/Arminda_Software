"""
Seed das rubricas de férias — Onda 3.3 (ADR-0017).

Escopo `tipos_folha=['ferias']`. Reusa o engine de duas fases: salário de
férias e 1/3 têm incide_* (formam as bases → INSS/IRRF/RPPS); o abono
pecuniário e seu 1/3 são indenizatórios (sem incidência).
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.payroll.models import Rubrica, TipoFolha, TipoRubrica

F = [TipoFolha.FERIAS]

# (codigo, nome, tipo, formula, inss, irrf, fgts, rpps)
RUBRICAS_FER = [
    ("FER_SALARIO", "Salário de férias", TipoRubrica.PROVENTO,
     "ARRED(SALARIO_BASE / 30 * DIAS_FERIAS, 2)", True, True, True, True),
    ("FER_TERCO", "1/3 constitucional de férias", TipoRubrica.PROVENTO,
     "ARRED(RUBRICA('FER_SALARIO') / 3, 2)", True, True, True, True),
    ("FER_ABONO", "Abono pecuniário (venda de férias)", TipoRubrica.PROVENTO,
     "ARRED(SALARIO_BASE / 30 * DIAS_ABONO, 2)", False, False, False, False),
    ("FER_ABONO_TERCO", "1/3 sobre abono pecuniário", TipoRubrica.PROVENTO,
     "ARRED(RUBRICA('FER_ABONO') / 3, 2)", False, False, False, False),
    ("FER_INSS", "INSS sobre férias", TipoRubrica.DESCONTO,
     "FAIXA_INSS(BASE_INSS) * EH_RGPS", False, False, False, False),
    ("FER_RPPS", "RPPS sobre férias", TipoRubrica.DESCONTO,
     "FAIXA_RPPS(BASE_RPPS) * EH_RPPS", False, False, False, False),
    ("FER_IRRF", "IRRF sobre férias", TipoRubrica.DESCONTO,
     "FAIXA_IRRF(BASE_IRRF - RUBRICA('FER_INSS') - RUBRICA('FER_RPPS'), DEPENDENTES)",
     False, False, False, False),
]


class Command(BaseCommand):
    help = "Cria as rubricas padrão de férias (gozo + 1/3 + abono) — Onda 3.3."

    def add_arguments(self, parser):
        parser.add_argument(
            "--substituir",
            action="store_true",
            help="Sobrescreve a fórmula/flags de rubricas já existentes com o mesmo código.",
        )

    def handle(self, *args, **options):
        substituir = options["substituir"]
        criadas, mantidas, atualizadas = 0, 0, 0
        for codigo, nome, tipo, formula, inss, irrf, fgts, rpps in RUBRICAS_FER:
            defaults = {
                "nome": nome,
                "tipo": tipo,
                "formula": formula,
                "incide_inss": inss,
                "incide_irrf": irrf,
                "incide_fgts": fgts,
                "incide_rpps": rpps,
                "tipos_folha": list(F),
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
                f"Rubricas de férias: {criadas} criadas, {atualizadas} atualizadas, "
                f"{mantidas} mantidas."
            )
        )
