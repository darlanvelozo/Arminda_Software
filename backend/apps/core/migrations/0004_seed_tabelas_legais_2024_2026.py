"""
Seed das tabelas legais nacionais 2024–2026 (Onda 2.3).

Valores oficiais publicados pela Receita Federal e INSS:
- Salário mínimo: Decreto 11.864/2023 (2024), Decreto 11.937/2024 (2025/2026)
- INSS faixas: Portaria Interministerial MPS/MF 2/2024 e atualizações
- IRRF faixas: Lei 14.663/2023 e atualizações
- Dedução por dependente IRRF: Lei 14.663/2023

Esta migration é idempotente — usa update_or_create por (tipo, vigencia_inicio).
Pode ser reaplicada sem efeito colateral.
"""

from datetime import date
from decimal import Decimal

from django.db import migrations


SEED = [
    # ============================================================
    # Salário mínimo
    # ============================================================
    {
        "tipo": "salario_minimo",
        "vigencia_inicio": date(2024, 1, 1),
        "vigencia_fim": date(2024, 12, 31),
        "valores": {"valor": "1412.00"},
        "referencia_legal": "Decreto 11.864/2023",
    },
    {
        "tipo": "salario_minimo",
        "vigencia_inicio": date(2025, 1, 1),
        "vigencia_fim": date(2025, 12, 31),
        "valores": {"valor": "1518.00"},
        "referencia_legal": "Decreto 11.937/2024",
    },
    {
        "tipo": "salario_minimo",
        "vigencia_inicio": date(2026, 1, 1),
        "vigencia_fim": None,
        "valores": {"valor": "1518.00"},
        "referencia_legal": "Decreto 11.937/2024 (mantido em 2026 — referência provisória)",
    },
    # ============================================================
    # Dedução por dependente (IRRF)
    # ============================================================
    {
        "tipo": "deducao_dependente_irrf",
        "vigencia_inicio": date(2024, 1, 1),
        "vigencia_fim": None,
        "valores": {"valor": "189.59"},
        "referencia_legal": "Lei 14.663/2023, art. 2º",
    },
    # ============================================================
    # INSS — faixas progressivas
    # ============================================================
    # 2024
    {
        "tipo": "inss",
        "vigencia_inicio": date(2024, 1, 1),
        "vigencia_fim": date(2024, 12, 31),
        "valores": {
            "faixas": [
                {"ate": "1412.00", "aliquota": "0.075"},
                {"ate": "2666.68", "aliquota": "0.09"},
                {"ate": "4000.03", "aliquota": "0.12"},
                {"ate": "7786.02", "aliquota": "0.14"},
                {"ate": None, "aliquota": "0.14"},
            ],
            "teto": "7786.02",
        },
        "referencia_legal": "Portaria Interministerial MPS/MF 2/2024",
    },
    # 2025 e 2026 (mesmas faixas — teto reajustado anualmente; uso
    # valores oficiais publicados; em produção a tabela deve ser
    # atualizada pelo admin via /admin/core/tabelalegal/)
    {
        "tipo": "inss",
        "vigencia_inicio": date(2025, 1, 1),
        "vigencia_fim": date(2025, 12, 31),
        "valores": {
            "faixas": [
                {"ate": "1518.00", "aliquota": "0.075"},
                {"ate": "2793.88", "aliquota": "0.09"},
                {"ate": "4190.83", "aliquota": "0.12"},
                {"ate": "8157.41", "aliquota": "0.14"},
                {"ate": None, "aliquota": "0.14"},
            ],
            "teto": "8157.41",
        },
        "referencia_legal": "Portaria Interministerial MPS/MF 6/2025",
    },
    {
        "tipo": "inss",
        "vigencia_inicio": date(2026, 1, 1),
        "vigencia_fim": None,
        "valores": {
            "faixas": [
                {"ate": "1518.00", "aliquota": "0.075"},
                {"ate": "2793.88", "aliquota": "0.09"},
                {"ate": "4190.83", "aliquota": "0.12"},
                {"ate": "8157.41", "aliquota": "0.14"},
                {"ate": None, "aliquota": "0.14"},
            ],
            "teto": "8157.41",
        },
        "referencia_legal": "Tabela 2025 mantida provisoriamente (atualizar via admin)",
    },
    # ============================================================
    # IRRF — faixas progressivas com dedução
    # ============================================================
    {
        "tipo": "irrf",
        "vigencia_inicio": date(2024, 2, 1),
        "vigencia_fim": date(2025, 4, 30),
        "valores": {
            "faixas": [
                {"ate": "2259.20", "aliquota": "0", "deducao": "0"},
                {"ate": "2826.65", "aliquota": "0.075", "deducao": "169.44"},
                {"ate": "3751.05", "aliquota": "0.15", "deducao": "381.44"},
                {"ate": "4664.68", "aliquota": "0.225", "deducao": "662.77"},
                {"ate": None, "aliquota": "0.275", "deducao": "896.00"},
            ],
        },
        "referencia_legal": "Lei 14.663/2023 + MP 1206/2024",
    },
    {
        "tipo": "irrf",
        "vigencia_inicio": date(2025, 5, 1),
        "vigencia_fim": None,
        "valores": {
            "faixas": [
                {"ate": "2428.80", "aliquota": "0", "deducao": "0"},
                {"ate": "2826.65", "aliquota": "0.075", "deducao": "182.16"},
                {"ate": "3751.05", "aliquota": "0.15", "deducao": "394.16"},
                {"ate": "4664.68", "aliquota": "0.225", "deducao": "675.49"},
                {"ate": None, "aliquota": "0.275", "deducao": "908.73"},
            ],
        },
        "referencia_legal": "Lei 14.848/2024 (faixa de isenção até R$ 2.428,80)",
    },
]


def seed_tabelas(apps, schema_editor):
    TabelaLegal = apps.get_model("core", "TabelaLegal")
    for item in SEED:
        TabelaLegal.objects.update_or_create(
            tipo=item["tipo"],
            vigencia_inicio=item["vigencia_inicio"],
            defaults={
                "vigencia_fim": item["vigencia_fim"],
                "valores": item["valores"],
                "referencia_legal": item["referencia_legal"],
            },
        )


def remover_tabelas(apps, schema_editor):
    TabelaLegal = apps.get_model("core", "TabelaLegal")
    for item in SEED:
        TabelaLegal.objects.filter(
            tipo=item["tipo"], vigencia_inicio=item["vigencia_inicio"]
        ).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0003_tabelalegal")]
    operations = [migrations.RunPython(seed_tabelas, remover_tabelas)]
