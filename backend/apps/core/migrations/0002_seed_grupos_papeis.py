"""
Data migration: seed dos Groups (papeis-base do RBAC).

Cria os 5 grupos descritos em ADR-0007:
- staff_arminda
- admin_municipio
- rh_municipio
- financeiro_municipio
- leitura_municipio

Permissions granulares por grupo entram no Bloco 1.2, junto com os CRUDs.
"""

from __future__ import annotations

from django.db import migrations

GRUPOS_BASE = [
    "staff_arminda",
    "admin_municipio",
    "rh_municipio",
    "financeiro_municipio",
    "leitura_municipio",
]


def criar_grupos(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for nome in GRUPOS_BASE:
        Group.objects.get_or_create(name=nome)


def remover_grupos(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=GRUPOS_BASE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(criar_grupos, remover_grupos),
    ]
