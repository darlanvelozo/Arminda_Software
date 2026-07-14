"""
Transmissão de lotes ao eSocial (Onda 4.6 — ADR-0024).

Camada completa e testável offline: monta o envelope `envioLoteEventos`
(validado contra o XSD oficial de comunicação v1.5.0) a partir de eventos
**assinados**, e implementa o cliente SOAP com mTLS (certificado do cofre).

O envio real é **gateado**: só executa com
`settings.ESOCIAL_TRANSMISSAO_HABILITADA=True` e ambiente definido — sem
isso, `enviar_lote` levanta `TransmissaoDesabilitada`. Nenhuma chamada ao
governo acontece por acidente.
"""

from __future__ import annotations

import tempfile
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from lxml import etree

from apps.esocial.models import (
    EventoESocial,
    GrupoLote,
    LoteESocial,
    StatusEvento,
    StatusLote,
    TipoEvento,
)
from apps.esocial.services.cofre import carregar_material
from apps.esocial.services.geracao import so_digitos

NS_ENVIO = "http://www.esocial.gov.br/schema/lote/eventos/envio/v1_1_1"
XSD_ENVIO = (
    Path(__file__).resolve().parent.parent
    / "schemas" / "comunicacao" / "EnvioLoteEventos-v1_1_1.xsd"
)

MAX_EVENTOS_POR_LOTE = 50

# Tipo de evento → grupo do lote (o eSocial exige lotes homogêneos por grupo).
GRUPO_POR_TIPO = {
    TipoEvento.S_1000: GrupoLote.TABELAS,
    TipoEvento.S_1005: GrupoLote.TABELAS,
    TipoEvento.S_1010: GrupoLote.TABELAS,
    TipoEvento.S_1200: GrupoLote.PERIODICOS,
    TipoEvento.S_1202: GrupoLote.PERIODICOS,
    TipoEvento.S_1210: GrupoLote.PERIODICOS,
}

# Endpoints oficiais por ambiente (conferir no dia do primeiro envio).
URLS_ENVIO = {
    "producao_restrita": (
        "https://webservices.producaorestrita.esocial.gov.br"
        "/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc"
    ),
    "producao": (
        "https://webservices.envio.esocial.gov.br"
        "/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos.svc"
    ),
}


class LoteInvalido(Exception):
    """O conjunto de eventos não pode formar um lote válido."""


class TransmissaoDesabilitada(Exception):
    """Envio bloqueado por configuração (ESOCIAL_TRANSMISSAO_HABILITADA)."""


@lru_cache(maxsize=1)
def _schema_envio() -> etree.XMLSchema:
    return etree.XMLSchema(etree.parse(str(XSD_ENVIO)))


def montar_lote(orgao, eventos: list[EventoESocial]) -> LoteESocial:
    """Monta e valida o lote a partir de eventos ASSINADOS do mesmo grupo."""
    if not eventos:
        raise LoteInvalido("Lote sem eventos.")
    if len(eventos) > MAX_EVENTOS_POR_LOTE:
        raise LoteInvalido(f"Máximo de {MAX_EVENTOS_POR_LOTE} eventos por lote.")
    grupos = {GRUPO_POR_TIPO.get(e.tipo) for e in eventos}
    if len(grupos) != 1 or None in grupos:
        raise LoteInvalido("Todos os eventos do lote devem ser do mesmo grupo.")
    nao_assinados = [e.id_evento for e in eventos if e.status != StatusEvento.ASSINADO]
    if nao_assinados:
        raise LoteInvalido(
            f"Só eventos assinados entram no lote (pendentes: {len(nao_assinados)})."
        )
    grupo = grupos.pop()

    raiz = etree.Element("eSocial", nsmap={None: NS_ENVIO})
    envio = etree.SubElement(raiz, "envioLoteEventos")
    envio.set("grupo", str(int(grupo)))
    nr_insc_raiz = so_digitos(orgao.cnpj)[:8]
    for tag in ("ideEmpregador", "ideTransmissor"):
        ide = etree.SubElement(envio, tag)
        etree.SubElement(ide, "tpInsc").text = "1"
        etree.SubElement(ide, "nrInsc").text = nr_insc_raiz
    eventos_el = etree.SubElement(envio, "eventos")
    for e in eventos:
        ev_el = etree.SubElement(eventos_el, "evento")
        ev_el.set("Id", e.id_evento)
        ev_el.append(etree.fromstring(e.xml.encode("utf-8")))

    # Serializa e re-parseia antes de validar: é no reparse que o namespace
    # default qualifica o root/filhos (mesmo padrão do validar_xml dos eventos).
    xml_bytes = etree.tostring(raiz, xml_declaration=True, encoding="UTF-8")
    doc = etree.fromstring(xml_bytes)
    if not _schema_envio().validate(doc):
        erros = [str(x.message) for x in _schema_envio().error_log]
        raise LoteInvalido("Envelope inválido contra o XSD: " + "; ".join(erros[:3]))

    lote = LoteESocial.objects.create(
        orgao_emissor=orgao,
        grupo=grupo,
        status=StatusLote.MONTADO,
        xml_envio=xml_bytes.decode(),
    )
    EventoESocial.objects.filter(pk__in=[e.pk for e in eventos]).update(lote_envio=lote)
    return lote


def _soap_envelope(corpo_xml: str) -> bytes:
    soap = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">'
        "<soap:Body>"
        '<ns:EnviarLoteEventos xmlns:ns='
        '"http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/v1_1_0">'
        "<ns:loteEventos>"
        f"{corpo_xml}"
        "</ns:loteEventos>"
        "</ns:EnviarLoteEventos>"
        "</soap:Body>"
        "</soap:Envelope>"
    )
    return soap.encode("utf-8")


def enviar_lote(lote: LoteESocial, *, ambiente: str | None = None) -> LoteESocial:
    """Envia o lote ao webservice (SOAP 1.2 + mTLS). GATEADO por configuração.

    O material do certificado sai do cofre, vira arquivos PEM temporários só
    durante a chamada, e é apagado em seguida.
    """
    if not getattr(settings, "ESOCIAL_TRANSMISSAO_HABILITADA", False):
        raise TransmissaoDesabilitada(
            "Transmissão desabilitada (ESOCIAL_TRANSMISSAO_HABILITADA=False). "
            "O primeiro envio será feito em ambiente supervisionado."
        )
    ambiente = ambiente or getattr(settings, "ESOCIAL_AMBIENTE", "")
    if ambiente not in URLS_ENVIO:
        raise TransmissaoDesabilitada(
            f"Ambiente de envio não configurado/é inválido: {ambiente!r}."
        )
    cert = getattr(lote.orgao_emissor, "certificado", None)
    if cert is None:
        raise TransmissaoDesabilitada("Órgão sem certificado no cofre.")

    import requests
    from cryptography.hazmat.primitives.serialization import (
        Encoding,
        NoEncryption,
        PrivateFormat,
    )

    material = carregar_material(cert)
    corpo = lote.xml_envio.split("?>", 1)[-1]  # sem a declaração XML interna

    with tempfile.NamedTemporaryFile(suffix=".pem") as f_cert, \
            tempfile.NamedTemporaryFile(suffix=".pem") as f_key:
        f_cert.write(material.certificado.public_bytes(Encoding.PEM))
        f_cert.flush()
        f_key.write(material.chave_privada.private_bytes(
            Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))
        f_key.flush()
        resp = requests.post(
            URLS_ENVIO[ambiente],
            data=_soap_envelope(corpo),
            headers={"Content-Type": "application/soap+xml; charset=utf-8"},
            cert=(f_cert.name, f_key.name),
            timeout=60,
        )

    lote.xml_retorno = resp.text
    lote.status = StatusLote.ENVIADO if resp.ok else StatusLote.ERRO
    # Protocolo de envio (se presente no retorno)
    try:
        doc = etree.fromstring(resp.content)
        proto = doc.find(".//{*}protocoloEnvio")
        if proto is not None and proto.text:
            lote.protocolo_envio = proto.text.strip()
    except etree.XMLSyntaxError:
        lote.status = StatusLote.ERRO
    lote.save(update_fields=["xml_retorno", "status", "protocolo_envio", "atualizado_em"])
    return lote
