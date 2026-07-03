"""
Validação de eventos eSocial contra o XSD oficial (Onda 4.1 — ADR-0020).

Os schemas da versão vigente (S-1.3) ficam versionados em
`apps/esocial/schemas/<versao>/`. Um evento só passa a `validado` se bate no
XSD. O `XMLSchema` compilado é cacheado por (tipo, versão).

Detalhe importante: o XSD oficial exige `ds:Signature` como filho obrigatório
do `eSocial` — ou seja, o documento só é XSD-válido **depois de assinado**.
A Onda 4.1 não assina (ADR-0020), então ao compilar o schema marcamos *apenas*
o `Signature` como opcional (`minOccurs=0`). Todo o resto continua sendo o
schema oficial, bit a bit; a validação do documento assinado entra na onda de
assinatura.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

from lxml import etree

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"

XS = "http://www.w3.org/2001/XMLSchema"

# Tipo de evento → arquivo XSD raiz.
XSD_POR_TIPO = {
    "S-1000": "evtInfoEmpregador.xsd",
    "S-1005": "evtTabEstab.xsd",
    "S-1010": "evtTabRubrica.xsd",
}


class ErroValidacaoXSD(Exception):
    """O XML não bate no XSD. `erros` traz as mensagens do validador."""

    def __init__(self, erros: list[str]):
        self.erros = erros
        super().__init__("; ".join(erros) or "XML inválido contra o XSD.")


@cache
def _schema(tipo: str, versao: str) -> etree.XMLSchema:
    arquivo = XSD_POR_TIPO.get(tipo)
    if arquivo is None:
        raise ValueError(f"Sem XSD mapeado para o tipo {tipo!r}.")
    caminho = SCHEMAS_DIR / versao / arquivo
    # Parse mantendo a base_url do arquivo (includes/imports resolvem relativo).
    arvore = etree.parse(str(caminho))
    # Assinatura é adicionada/validada na onda de assinatura — aqui é opcional.
    for el in arvore.iter(f"{{{XS}}}element"):
        ref = el.get("ref", "")
        if ref.endswith(":Signature") or ref == "Signature":
            el.set("minOccurs", "0")
    return etree.XMLSchema(arvore)


def validar_xml(xml: str | bytes, tipo: str, versao: str = "v_S_01_03_00") -> None:
    """Valida o XML contra o XSD do tipo. Levanta `ErroValidacaoXSD` se falhar."""
    doc = etree.fromstring(xml.encode("utf-8") if isinstance(xml, str) else xml)
    schema = _schema(tipo, versao)
    if not schema.validate(doc):
        raise ErroValidacaoXSD([str(e.message) for e in schema.error_log])
