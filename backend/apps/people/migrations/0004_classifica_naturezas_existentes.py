"""
Data migration — classifica as Lotações já cadastradas em uma das 5
naturezas baseado em padrões no nome. Servidores em lotações que não
casarem com nenhum padrão ficam como "outros" para revisão manual.

Os padrões refletem o vocabulário típico de prefeituras brasileiras:
- Saúde: ACS, UBS, hospital, posto, médico, enfermagem, SAMU, vigilância sanitária
- Educação: escola, creche, EMEF, EMEI, biblioteca, NIIPED, ensino, pedagogia
- Assistência: CRAS, CREAS, conselho tutelar, bolsa, abrigo, social
- Administração: prefeitura, gabinete, finanças, fazenda, controladoria, jurídico, RH, TI
- Outros: o restante (cultura, esporte, obras, agricultura, meio ambiente)
"""

from __future__ import annotations

import re

from django.db import migrations


PADROES = {
    "saude": [
        r"\bsa[uú]de\b",
        r"\bacs\b",
        r"\bubs\b",
        r"\bhospital\b",
        r"\bposto\b.*\bsa[uú]de\b",
        r"\bsamu\b",
        r"\bvigil[âa]ncia\s+sanit[áa]ria\b",
        r"\bsesau\b",
        r"\bsemsa\b",
        r"\bsms\b",
        r"\bfundo\s+municipal\s+de\s+sa[uú]de\b",
        r"\benfermagem\b",
        r"\bm[eé]dico\b",
        r"\bsa[uú]de\s+da\s+fam[íi]lia\b",
    ],
    "educacao": [
        r"\beduca[çc][ãa]o\b",
        r"\bescola\b",
        r"\bcreche\b",
        r"\bemef\b",
        r"\bemei\b",
        r"\bem\b\s+(jardim|santa|s[ãa]o|prof|dom|nossa)",
        r"\bbiblioteca\b",
        r"\bcentro\s+multi.*pedag[óo]gico\b",
        r"\bniiped\b",
        r"\bensino\b",
        r"\bsemed\b",
        r"\bcentro\s+educacional\b",
        r"\bcrescer\b",
        r"\binfantil\b",
    ],
    "assistencia_social": [
        r"\bassist[êe]ncia\s+social\b",
        r"\bcras\b",
        r"\bcreas\b",
        r"\bconselho\s+tutelar\b",
        r"\babrigo\b",
        r"\bbolsa\s+fam[íi]lia\b",
        r"\bcad[uú]nico\b",
        r"\bsemtas\b",
        r"\bsemas\b",
        r"\bdesenvolvimento\s+social\b",
        r"\bidoso\b",
    ],
    "administracao": [
        r"\bgabinete\b",
        r"\bprefeit[oa]\b",
        r"\bvice-?prefeit[oa]\b",
        r"\bvereador\b",
        r"\bc[âa]mara\b",
        r"\bfinan[çc]as?\b",
        r"\bfazenda\b",
        r"\btribut",
        r"\bcontroladoria\b",
        r"\bjur[íi]dico\b",
        r"\bprocuradoria\b",
        r"\brecursos\s+humanos\b",
        r"\bcentro\s+administrativo\b",
        r"\badmin",
        r"\bsmadm\b",
        r"\bsema\b",
        r"\bplanejamento\b",
        r"\borçamento\b",
        r"\bauditoria\b",
    ],
}


def classifica_por_nome(nome: str) -> str:
    """Retorna a natureza correspondente ao nome, ou 'outros' se nenhum casar."""
    if not nome:
        return "outros"
    n = nome.lower()
    for natureza, padroes in PADROES.items():
        for p in padroes:
            if re.search(p, n):
                return natureza
    return "outros"


def classificar(apps, schema_editor):
    Lotacao = apps.get_model("people", "Lotacao")
    qs = Lotacao.objects.all()
    for lot in qs:
        natureza = classifica_por_nome(lot.nome)
        if natureza != lot.natureza:
            lot.natureza = natureza
            lot.save(update_fields=["natureza"])


def reverter(apps, schema_editor):
    # Reverter coloca tudo de volta como "outros" — útil para rollback
    Lotacao = apps.get_model("people", "Lotacao")
    Lotacao.objects.update(natureza="outros")


class Migration(migrations.Migration):
    dependencies = [
        ("people", "0003_historicallotacao_natureza_lotacao_natureza_and_more"),
    ]
    operations = [
        migrations.RunPython(classificar, reverter),
    ]
