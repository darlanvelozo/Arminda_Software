"""
Geração de XML de eventos eSocial (Onda 4.1 — ADR-0020).

Monta a árvore XML com `lxml` a partir do `OrgaoEmissor`, valida contra o
XSD oficial (S-1.3) e persiste um `EventoESocial`. Cobre S-1000 (informações
do empregador) e S-1005 (tabela de estabelecimentos).

Camada 1 do eSocial (gerar). Assinatura e transmissão entram em ondas
seguintes — por isso `tpAmb` default é 2 (produção restrita).
"""

from __future__ import annotations

import re
from datetime import date

from django.utils import timezone
from lxml import etree

from apps.esocial.models import EventoESocial, StatusEvento, TipoEvento
from apps.esocial.services.validacao import validar_xml
from apps.people.models import OrgaoEmissor

VERSAO = "v_S_01_03_00"
VER_PROC = "Arminda"

NS_POR_TIPO = {
    TipoEvento.S_1000: f"http://www.esocial.gov.br/schema/evt/evtInfoEmpregador/{VERSAO}",
    TipoEvento.S_1005: f"http://www.esocial.gov.br/schema/evt/evtTabEstab/{VERSAO}",
}
RAIZ_POR_TIPO = {
    TipoEvento.S_1000: "evtInfoEmpregador",
    TipoEvento.S_1005: "evtTabEstab",
}


def so_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def gerar_id_evento(orgao: OrgaoEmissor, sequencial: int = 1, agora=None) -> str:
    """ID do eSocial: ID + tpInsc(1) + nrInsc(14) + AAAAMMDDHHMMSS + seq(5)."""
    agora = agora or timezone.now()
    nr_insc = so_digitos(orgao.cnpj).zfill(14)[:14]
    carimbo = agora.strftime("%Y%m%d%H%M%S")
    return f"ID1{nr_insc}{carimbo}{sequencial:05d}"


def _sub(pai, tag: str, texto: str | None = None):
    el = etree.SubElement(pai, tag)
    if texto is not None:
        el.text = str(texto)
    return el


def _ide_evento(pai, tp_amb: int):
    ide = _sub(pai, "ideEvento")
    _sub(ide, "tpAmb", tp_amb)
    _sub(ide, "procEmi", 1)  # 1 = aplicativo do empregador
    _sub(ide, "verProc", VER_PROC)


def _periodo(competencia: date | None) -> str:
    competencia = competencia or timezone.now().date()
    return competencia.strftime("%Y-%m")


def construir_s1000(orgao: OrgaoEmissor, *, id_evento: str, tp_amb: int,
                    competencia: date | None, class_trib: str) -> etree._Element:
    ns = NS_POR_TIPO[TipoEvento.S_1000]
    raiz = etree.Element("eSocial", nsmap={None: ns})
    evt = _sub(raiz, "evtInfoEmpregador")
    evt.set("Id", id_evento)

    _ide_evento(evt, tp_amb)

    ide_emp = _sub(evt, "ideEmpregador")
    _sub(ide_emp, "tpInsc", 1)  # 1 = CNPJ
    _sub(ide_emp, "nrInsc", so_digitos(orgao.cnpj)[:8])  # raiz (8 dígitos)

    info = _sub(evt, "infoEmpregador")
    inclusao = _sub(info, "inclusao")
    ide_periodo = _sub(inclusao, "idePeriodo")
    _sub(ide_periodo, "iniValid", _periodo(competencia))
    info_cad = _sub(inclusao, "infoCadastro")
    _sub(info_cad, "classTrib", class_trib)
    _sub(info_cad, "indDesFolha", 0)
    _sub(info_cad, "indOptRegEletron", 1)
    return raiz


def construir_s1005(orgao: OrgaoEmissor, *, id_evento: str, tp_amb: int,
                    competencia: date | None) -> etree._Element:
    ns = NS_POR_TIPO[TipoEvento.S_1005]
    raiz = etree.Element("eSocial", nsmap={None: ns})
    evt = _sub(raiz, "evtTabEstab")
    evt.set("Id", id_evento)

    _ide_evento(evt, tp_amb)

    ide_emp = _sub(evt, "ideEmpregador")
    _sub(ide_emp, "tpInsc", 1)
    _sub(ide_emp, "nrInsc", so_digitos(orgao.cnpj)[:8])

    info = _sub(evt, "infoEstab")
    inclusao = _sub(info, "inclusao")
    ide_estab = _sub(inclusao, "ideEstab")
    _sub(ide_estab, "tpInsc", 1)
    _sub(ide_estab, "nrInsc", so_digitos(orgao.cnpj).zfill(14)[:14])
    _sub(ide_estab, "iniValid", _periodo(competencia))
    dados = _sub(inclusao, "dadosEstab")
    _sub(dados, "cnaePrep", so_digitos(orgao.cnae_principal).zfill(7)[:7])
    return raiz


_CONSTRUTORES = {
    TipoEvento.S_1000: construir_s1000,
    TipoEvento.S_1005: construir_s1005,
}


def gerar_evento(
    orgao: OrgaoEmissor,
    tipo: str,
    *,
    tp_amb: int = 2,
    competencia: date | None = None,
    class_trib: str = "60",
    sequencial: int = 1,
) -> EventoESocial:
    """Gera, valida (XSD) e persiste um `EventoESocial`.

    `class_trib` default "60" (ente público — Tabela 08). `tp_amb` default 2
    (produção restrita), já que esta onda não transmite.
    """
    if tipo not in _CONSTRUTORES:
        raise ValueError(f"Tipo de evento não suportado: {tipo!r}")

    id_evento = gerar_id_evento(orgao, sequencial=sequencial)
    construtor = _CONSTRUTORES[tipo]
    kwargs = {"id_evento": id_evento, "tp_amb": tp_amb, "competencia": competencia}
    if tipo == TipoEvento.S_1000:
        kwargs["class_trib"] = class_trib
    raiz = construtor(orgao, **kwargs)

    xml = etree.tostring(raiz, xml_declaration=True, encoding="UTF-8", pretty_print=True)
    validar_xml(xml, tipo, VERSAO)  # levanta ErroValidacaoXSD se inválido

    return EventoESocial.objects.create(
        tipo=tipo,
        orgao_emissor=orgao,
        id_evento=id_evento,
        versao_layout=VERSAO,
        xml=xml.decode("utf-8"),
        status=StatusEvento.VALIDADO,
    )
