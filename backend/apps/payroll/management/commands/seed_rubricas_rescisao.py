"""
Seed das rubricas de rescisão — Onda 3.2 (ADR-0016).

Cria, de forma idempotente, as verbas rescisórias (escopo `tipos_folha=
['rescisao']`), com gating por motivo via variáveis de contexto:

- Saldo de salário (tributável) + INSS/IRRF/RPPS sobre ele.
- 13º proporcional (tributável; INSS/IRRF/RPPS do 13º em separado), perdido
  na justa causa.
- Férias proporcionais + 1/3 e férias vencidas + 1/3 (indenizatórias, não
  tributam); proporcionais perdidas na justa causa.
- Aviso prévio indenizado (sem justa causa × celetista).
- FGTS do mês (informativa) e multa de 40% sobre o saldo do FGTS (informativa).

Reusa o engine de duas fases: os proventos tributáveis formam as bases e os
descontos calculam as incidências; o 13º tem INSS/IRRF/RPPS próprios.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.payroll.models import Rubrica, TipoFolha, TipoRubrica

R = [TipoFolha.RESCISAO]

# (codigo, nome, tipo, formula, inss, irrf, fgts, rpps)
RUBRICAS_RESC = [
    # --- Proventos ---
    ("RESC_SALDO", "Saldo de salário", TipoRubrica.PROVENTO,
     "ARRED(SALARIO_BASE / 30 * SALDO_DIAS, 2)", True, True, True, True),
    ("RESC_13", "13º proporcional", TipoRubrica.PROVENTO,
     "ARRED(SALARIO_BASE * AVOS_13 / 12 * (1 - EH_JUSTA_CAUSA), 2)", False, False, True, False),
    ("RESC_FERIAS_PROP", "Férias proporcionais", TipoRubrica.PROVENTO,
     "ARRED(SALARIO_BASE * AVOS_FERIAS / 12 * (1 - EH_JUSTA_CAUSA), 2)", False, False, False, False),
    ("RESC_FERIAS_PROP_13", "1/3 sobre férias proporcionais", TipoRubrica.PROVENTO,
     "ARRED(RUBRICA('RESC_FERIAS_PROP') / 3, 2)", False, False, False, False),
    ("RESC_FERIAS_VENC", "Férias vencidas", TipoRubrica.PROVENTO,
     "ARRED(SALARIO_BASE * TEM_FERIAS_VENCIDAS, 2)", False, False, False, False),
    ("RESC_FERIAS_VENC_13", "1/3 sobre férias vencidas", TipoRubrica.PROVENTO,
     "ARRED(RUBRICA('RESC_FERIAS_VENC') / 3, 2)", False, False, False, False),
    ("RESC_AVISO", "Aviso prévio indenizado", TipoRubrica.PROVENTO,
     "ARRED(SALARIO_BASE * AVISO_INDENIZADO * EH_SEM_JUSTA_CAUSA * EH_CELETISTA, 2)",
     False, False, False, False),
    # --- Descontos: incidências sobre o saldo de salário ---
    ("RESC_INSS", "INSS sobre saldo", TipoRubrica.DESCONTO,
     "FAIXA_INSS(BASE_INSS) * EH_RGPS", False, False, False, False),
    ("RESC_RPPS", "RPPS sobre saldo", TipoRubrica.DESCONTO,
     "FAIXA_RPPS(BASE_RPPS) * EH_RPPS", False, False, False, False),
    ("RESC_IRRF", "IRRF sobre saldo", TipoRubrica.DESCONTO,
     "FAIXA_IRRF(BASE_IRRF - RUBRICA('RESC_INSS') - RUBRICA('RESC_RPPS'), DEPENDENTES)",
     False, False, False, False),
    # --- Descontos: incidências do 13º proporcional (em separado) ---
    ("RESC_13_INSS", "INSS sobre 13º", TipoRubrica.DESCONTO,
     "FAIXA_INSS(RUBRICA('RESC_13')) * EH_RGPS", False, False, False, False),
    ("RESC_13_RPPS", "RPPS sobre 13º", TipoRubrica.DESCONTO,
     "FAIXA_RPPS(RUBRICA('RESC_13')) * EH_RPPS", False, False, False, False),
    ("RESC_13_IRRF", "IRRF sobre 13º", TipoRubrica.DESCONTO,
     "FAIXA_IRRF(RUBRICA('RESC_13') - RUBRICA('RESC_13_INSS') - RUBRICA('RESC_13_RPPS'), DEPENDENTES)",
     False, False, False, False),
    # --- Informativas ---
    ("RESC_FGTS", "FGTS do mês (rescisão)", TipoRubrica.INFORMATIVA,
     "BASE_FGTS * ALIQ_FGTS * EH_FGTS", False, False, False, False),
    ("RESC_FGTS_MULTA", "Multa 40% do FGTS", TipoRubrica.INFORMATIVA,
     "ARRED(SALDO_FGTS * 0.40 * EH_SEM_JUSTA_CAUSA * EH_CELETISTA, 2)",
     False, False, False, False),
]


class Command(BaseCommand):
    help = "Cria as rubricas padrão de rescisão (verbas rescisórias) — Onda 3.2."

    def add_arguments(self, parser):
        parser.add_argument(
            "--substituir",
            action="store_true",
            help="Sobrescreve a fórmula/flags de rubricas já existentes com o mesmo código.",
        )

    def handle(self, *args, **options):
        substituir = options["substituir"]
        criadas, mantidas, atualizadas = 0, 0, 0
        for codigo, nome, tipo, formula, inss, irrf, fgts, rpps in RUBRICAS_RESC:
            defaults = {
                "nome": nome,
                "tipo": tipo,
                "formula": formula,
                "incide_inss": inss,
                "incide_irrf": irrf,
                "incide_fgts": fgts,
                "incide_rpps": rpps,
                "tipos_folha": list(R),
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
                f"Rubricas de rescisão: {criadas} criadas, {atualizadas} atualizadas, "
                f"{mantidas} mantidas."
            )
        )
