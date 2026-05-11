"""
Data migration — segunda passada na classificação de natureza de lotação.

A primeira passada (0004) deixou alguns casos óbvios em "outros":
- "UNIDADE ESCOLAR X" (não casava com `\bescola\b`)
- "SEC MUN DE EDUC..." (EDUC sem ç não casava com `\beduca`)
- "SEC DE ASS SOCIAL" (ASS sem expansão de assistência)

Esta migration adiciona padrões mais permissivos e re-classifica tudo
que estiver em "outros" — não mexe nas que já foram classificadas
manualmente (admin pode ter ajustado entre as migrations).
"""

from __future__ import annotations

import re

from django.db import migrations


PADROES_EXTRAS = {
    "saude": [
        r"\bunidade\s+(de\s+)?sa[uú]de\b",
        r"\bcaps\b",
    ],
    "educacao": [
        r"\bunidade\s+escolar\b",
        r"\bui\s+",
        r"\bem\s+",
        r"\bsec\s+mun\s+de\s+edu[ck]",
        r"\bsec(retaria)?\s+(municipal\s+)?de\s+edu[ck]",
        r"\bcentro\s+multidisciplinar.*pedag",
    ],
    "assistencia_social": [
        r"\bsec(retaria)?\s+(municipal\s+)?de\s+ass(ist)?",
        r"\bsec(retaria)?\s+de\s+(ass|desenvolv)",
        r"\bcaps\b",
    ],
    "administracao": [
        r"\bsec(retaria)?\s+(municipal\s+)?de\s+admin",
        r"\bsec(retaria)?\s+(de\s+)?rela[çc][õo]es",
        r"\bsec(retaria)?\s+(de\s+)?gov",
        r"\bsec(retaria)?\s+(de\s+)?juventude\b",
        r"\bsec(retaria)?\s+(de\s+)?(art|articula)",
        r"\bsec(retaria)?\s+(de\s+)?comunica",
    ],
}


def classifica(nome: str) -> str:
    if not nome:
        return "outros"
    n = nome.lower()
    for natureza, padroes in PADROES_EXTRAS.items():
        for p in padroes:
            if re.search(p, n):
                return natureza
    return "outros"


def reclassificar(apps, schema_editor):
    Lotacao = apps.get_model("people", "Lotacao")
    # Só toca em quem ficou como "outros" depois da primeira passada
    for lot in Lotacao.objects.filter(natureza="outros"):
        nova = classifica(lot.nome)
        if nova != "outros":
            lot.natureza = nova
            lot.save(update_fields=["natureza"])


def noop(apps, schema_editor):
    # Reverter este passo é no-op — manter o estado já reclassificado é mais
    # útil do que voltar a "outros".
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("people", "0004_classifica_naturezas_existentes"),
    ]
    operations = [
        migrations.RunPython(reclassificar, noop),
    ]
