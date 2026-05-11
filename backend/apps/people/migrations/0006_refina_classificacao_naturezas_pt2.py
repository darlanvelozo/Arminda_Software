"""
Data migration — terceira passada na classificação. Pega as abreviações
e siglas específicas que ficaram em "outros":
- ESC <nome> / G E <nome> → educação
- PSF / ESF → saúde (Programa/Estratégia Saúde da Família)
- SCFV → assistência social (Serviço de Convivência e Fortalecimento de Vínculos)
- CRIANÇA FELIZ → assistência social (programa federal)

Depois desta passada, o que sobra em "outros" é:
- O balde sem nome do SIP (precisa de DEPDESPESA do empenho)
- Secretarias-fim que não caem em saúde/educação/assistência: Cultura,
  Esporte, Obras, Meio Ambiente, Agricultura, Juventude, Mulher —
  ficam como "outros" intencionalmente (admin reclassifica via UI se
  necessário).
"""

from __future__ import annotations

import re

from django.db import migrations


PADROES_EXTRAS = {
    "educacao": [
        r"^\s*esc\b",
        r"^\s*g\s+e\b",
        r"^\s*ge\b",
    ],
    "saude": [
        r"\bpsf\b",
        r"\besf\b",
    ],
    "assistencia_social": [
        r"\bscfv\b",
        r"\bcrian[çc]a\s+feliz\b",
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
    for lot in Lotacao.objects.filter(natureza="outros"):
        nova = classifica(lot.nome)
        if nova != "outros":
            lot.natureza = nova
            lot.save(update_fields=["natureza"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("people", "0005_refina_classificacao_naturezas"),
    ]
    operations = [
        migrations.RunPython(reclassificar, noop),
    ]
