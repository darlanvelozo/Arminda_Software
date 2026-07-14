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
from apps.payroll.models import Rubrica, TipoRubrica
from apps.people.models import OrgaoEmissor

VERSAO = "v_S_01_03_00"
VER_PROC = "Arminda"

NS_POR_TIPO = {
    TipoEvento.S_1000: f"http://www.esocial.gov.br/schema/evt/evtInfoEmpregador/{VERSAO}",
    TipoEvento.S_1005: f"http://www.esocial.gov.br/schema/evt/evtTabEstab/{VERSAO}",
    TipoEvento.S_1010: f"http://www.esocial.gov.br/schema/evt/evtTabRubrica/{VERSAO}",
    TipoEvento.S_1200: f"http://www.esocial.gov.br/schema/evt/evtRemun/{VERSAO}",
    TipoEvento.S_1202: f"http://www.esocial.gov.br/schema/evt/evtRmnRPPS/{VERSAO}",
    TipoEvento.S_1210: f"http://www.esocial.gov.br/schema/evt/evtPgtos/{VERSAO}",
}
RAIZ_POR_TIPO = {
    TipoEvento.S_1000: "evtInfoEmpregador",
    TipoEvento.S_1005: "evtTabEstab",
    TipoEvento.S_1010: "evtTabRubrica",
    TipoEvento.S_1200: "evtRemun",
    TipoEvento.S_1202: "evtRmnRPPS",
    TipoEvento.S_1210: "evtPgtos",
}

# Regime do vínculo → código de categoria do trabalhador (Tabela 1 do eSocial).
COD_CATEG = {
    "estatutario": "301",   # servidor titular de cargo efetivo
    "comissionado": "302",  # cargo exclusivamente em comissão
    "eletivo": "303",       # agente político / mandato eletivo
    "celetista": "101",     # empregado CLT
    "temporario": "106",    # contrato por prazo determinado
    "estagiario": "901",    # estagiário (evento próprio no eSocial real; aqui só mapa)
}

# Regimes cujo evento de remuneração é o S-1202 (RPPS); demais vão no S-1200.
REGIMES_S1202 = {"estatutario"}

# Rubrica interna → tpRubr do eSocial (1=vencimento, 2=desconto, 3=informativa).
TP_RUBR = {
    TipoRubrica.PROVENTO: "1",
    TipoRubrica.DESCONTO: "2",
    TipoRubrica.INFORMATIVA: "3",
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


def construir_s1010(orgao: OrgaoEmissor, *, rubrica: Rubrica, id_evento: str,
                    tp_amb: int, competencia: date | None,
                    ide_tab_rubr: str = "1") -> etree._Element:
    ns = NS_POR_TIPO[TipoEvento.S_1010]
    raiz = etree.Element("eSocial", nsmap={None: ns})
    evt = _sub(raiz, "evtTabRubrica")
    evt.set("Id", id_evento)

    _ide_evento(evt, tp_amb)

    ide_emp = _sub(evt, "ideEmpregador")
    _sub(ide_emp, "tpInsc", 1)
    _sub(ide_emp, "nrInsc", so_digitos(orgao.cnpj)[:8])

    info = _sub(evt, "infoRubrica")
    inclusao = _sub(info, "inclusao")
    ide_rubrica = _sub(inclusao, "ideRubrica")
    _sub(ide_rubrica, "codRubr", rubrica.codigo)
    _sub(ide_rubrica, "ideTabRubr", ide_tab_rubr)
    _sub(ide_rubrica, "iniValid", _periodo(competencia))
    dados = _sub(inclusao, "dadosRubrica")
    _sub(dados, "dscRubr", rubrica.nome)
    _sub(dados, "natRubr", rubrica.natureza_esocial)
    _sub(dados, "tpRubr", TP_RUBR.get(rubrica.tipo, "1"))
    # Códigos de incidência: em branco vira "00" (não é base) — sempre exigidos.
    _sub(dados, "codIncCP", rubrica.cod_inc_cp or "00")
    _sub(dados, "codIncIRRF", rubrica.cod_inc_irrf or "00")
    _sub(dados, "codIncFGTS", rubrica.cod_inc_fgts or "00")
    if rubrica.cod_inc_cprp:
        _sub(dados, "codIncCPRP", rubrica.cod_inc_cprp)
    return raiz




def _ide_evento_folha(pai, tp_amb: int, competencia: date):
    """ideEvento dos periódicos (T_ideEvento_folha*): original, apuração mensal."""
    ide = _sub(pai, "ideEvento")
    _sub(ide, "indRetif", 1)          # 1 = original
    _sub(ide, "indApuracao", 1)       # 1 = mensal
    _sub(ide, "perApur", competencia.strftime("%Y-%m"))
    _sub(ide, "tpAmb", tp_amb)
    _sub(ide, "procEmi", 1)
    _sub(ide, "verProc", VER_PROC)


def _lancamentos_com_natureza(folha, vinculo):
    """Lançamentos do vínculo com natureza eSocial no snapshot (itens do dmDev)."""
    from apps.payroll.models import Lancamento

    return list(
        Lancamento.objects.filter(folha=folha, vinculo=vinculo)
        .exclude(snap_natureza_esocial="")
        .select_related("rubrica")
        .order_by("rubrica__codigo")
    )


def _itens_remun(pai, lancamentos) -> None:
    for lanc in lancamentos:
        item = _sub(pai, "itensRemun")
        _sub(item, "codRubr", lanc.rubrica.codigo)
        _sub(item, "ideTabRubr", "1")
        _sub(item, "vrRubr", f"{lanc.valor:.2f}")
        _sub(item, "indApurIR", 0)  # 0 = tributação normal na folha


def _remuneracao_base(tipo, orgao, folha, vinculo, id_evento, tp_amb):
    """Esqueleto comum do S-1200/S-1202 até o dmDev (devolve raiz e dmDev)."""
    ns = NS_POR_TIPO[tipo]
    raiz = etree.Element("eSocial", nsmap={None: ns})
    evt = _sub(raiz, RAIZ_POR_TIPO[tipo])
    evt.set("Id", id_evento)
    _ide_evento_folha(evt, tp_amb, folha.competencia)
    ide_emp = _sub(evt, "ideEmpregador")
    _sub(ide_emp, "tpInsc", 1)
    _sub(ide_emp, "nrInsc", so_digitos(orgao.cnpj)[:8])
    ide_trab = _sub(evt, "ideTrabalhador")
    _sub(ide_trab, "cpfTrab", so_digitos(vinculo.servidor.cpf).zfill(11)[:11])
    dm = _sub(evt, "dmDev")
    _sub(dm, "ideDmDev", "1")
    _sub(dm, "codCateg", COD_CATEG.get(vinculo.regime, "101"))
    return raiz, dm


def construir_s1200(orgao: OrgaoEmissor, *, folha, vinculo, id_evento: str,
                    tp_amb: int) -> etree._Element:
    """S-1200 — remuneração RGPS (celetista/comissionado/temporário/eletivo)."""
    lancs = _lancamentos_com_natureza(folha, vinculo)
    if not lancs:
        raise ValueError(
            "Nenhum lançamento com natureza eSocial no snapshot — preencha a "
            "natureza (Tabela 3) nas rubricas e recalcule a folha."
        )
    raiz, dm = _remuneracao_base(TipoEvento.S_1200, orgao, folha, vinculo, id_evento, tp_amb)
    info = _sub(dm, "infoPerApur")
    ide_estab = _sub(info, "ideEstabLot")
    _sub(ide_estab, "tpInsc", 1)
    _sub(ide_estab, "nrInsc", so_digitos(orgao.cnpj).zfill(14)[:14])
    # Lotação tributária (Tabela S-1020). Enquanto o S-1020 não é gerado,
    # usamos um código único padrão por órgão.
    _sub(ide_estab, "codLotacao", "GERAL")
    remun = _sub(ide_estab, "remunPerApur")
    _sub(remun, "matricula", vinculo.servidor.matricula[:30])
    _itens_remun(remun, lancs)
    return raiz


def construir_s1202(orgao: OrgaoEmissor, *, folha, vinculo, id_evento: str,
                    tp_amb: int) -> etree._Element:
    """S-1202 — remuneração de servidor vinculado a RPPS (estatutário)."""
    lancs = _lancamentos_com_natureza(folha, vinculo)
    if not lancs:
        raise ValueError(
            "Nenhum lançamento com natureza eSocial no snapshot — preencha a "
            "natureza (Tabela 3) nas rubricas e recalcule a folha."
        )
    raiz, dm = _remuneracao_base(TipoEvento.S_1202, orgao, folha, vinculo, id_evento, tp_amb)
    info = _sub(dm, "infoPerApur")
    ide_estab = _sub(info, "ideEstab")
    _sub(ide_estab, "tpInsc", 1)
    _sub(ide_estab, "nrInsc", so_digitos(orgao.cnpj).zfill(14)[:14])
    remun = _sub(ide_estab, "remunPerApur")
    _sub(remun, "matricula", vinculo.servidor.matricula[:30])
    _itens_remun(remun, lancs)
    return raiz


def construir_s1210(orgao: OrgaoEmissor, *, folha, vinculo, id_evento: str,
                    tp_amb: int) -> etree._Element:
    """S-1210 — pagamento do líquido apurado na folha (ResumoFolha)."""
    from apps.payroll.models import ResumoFolha

    try:
        resumo = ResumoFolha.objects.get(folha=folha, vinculo=vinculo)
    except ResumoFolha.DoesNotExist as exc:
        raise ValueError(
            "Folha sem ResumoFolha para o vínculo — recalcule a folha (Onda 4.4)."
        ) from exc
    ns = NS_POR_TIPO[TipoEvento.S_1210]
    raiz = etree.Element("eSocial", nsmap={None: ns})
    evt = _sub(raiz, RAIZ_POR_TIPO[TipoEvento.S_1210])
    evt.set("Id", id_evento)
    # ideEvento do S-1210 não tem indApuracao (difere dos demais periódicos).
    ide = _sub(evt, "ideEvento")
    _sub(ide, "indRetif", 1)
    _sub(ide, "perApur", folha.competencia.strftime("%Y-%m"))
    _sub(ide, "tpAmb", tp_amb)
    _sub(ide, "procEmi", 1)
    _sub(ide, "verProc", VER_PROC)
    ide_emp = _sub(evt, "ideEmpregador")
    _sub(ide_emp, "tpInsc", 1)
    _sub(ide_emp, "nrInsc", so_digitos(orgao.cnpj)[:8])
    ide_benef = _sub(evt, "ideBenef")
    _sub(ide_benef, "cpfBenef", so_digitos(vinculo.servidor.cpf).zfill(11)[:11])
    info = _sub(ide_benef, "infoPgto")
    # Pagamento no 5º dia útil (simplificação: dia 5 do mês seguinte).
    comp = folha.competencia
    prox_mes = date(comp.year + (comp.month // 12), (comp.month % 12) + 1, 5)
    _sub(info, "dtPgto", prox_mes.isoformat())
    _sub(info, "tpPgto", 1)  # 1 = remuneração do período de apuração
    _sub(info, "perRef", comp.strftime("%Y-%m"))
    _sub(info, "ideDmDev", "1")
    _sub(info, "vrLiq", f"{resumo.total_liquido:.2f}")
    return raiz

_CONSTRUTORES = {
    TipoEvento.S_1000: construir_s1000,
    TipoEvento.S_1005: construir_s1005,
    TipoEvento.S_1010: construir_s1010,
    TipoEvento.S_1200: construir_s1200,
    TipoEvento.S_1202: construir_s1202,
    TipoEvento.S_1210: construir_s1210,
}

TIPOS_PERIODICOS = {TipoEvento.S_1200, TipoEvento.S_1202, TipoEvento.S_1210}


def _validar_entrada(tipo: str, *, rubrica, folha, vinculo) -> None:
    if tipo not in _CONSTRUTORES:
        raise ValueError(f"Tipo de evento não suportado: {tipo!r}")
    if tipo == TipoEvento.S_1010:
        if rubrica is None:
            raise ValueError("S-1010 exige uma rubrica.")
        if not rubrica.natureza_esocial:
            raise ValueError(f"Rubrica {rubrica.codigo} sem natureza eSocial (Tabela 3).")
    if tipo in TIPOS_PERIODICOS:
        if folha is None or vinculo is None:
            raise ValueError(f"{tipo} exige folha e vínculo.")
        # Remuneração: o regime decide o evento correto (RPPS → S-1202).
        if tipo == TipoEvento.S_1200 and vinculo.regime in REGIMES_S1202:
            raise ValueError("Vínculo de regime próprio (RPPS): use o S-1202, não o S-1200.")
        if tipo == TipoEvento.S_1202 and vinculo.regime not in REGIMES_S1202:
            raise ValueError("Vínculo fora do regime próprio: use o S-1200, não o S-1202.")


def gerar_evento(
    orgao: OrgaoEmissor,
    tipo: str,
    *,
    tp_amb: int = 2,
    competencia: date | None = None,
    class_trib: str = "60",
    rubrica: Rubrica | None = None,
    folha=None,
    vinculo=None,
    sequencial: int = 1,
) -> EventoESocial:
    """Gera, valida (XSD) e persiste um `EventoESocial`.

    `class_trib` default "60" (ente público — Tabela 08). `tp_amb` default 2
    (produção restrita), já que esta onda não transmite. `rubrica` é
    obrigatória para S-1010 (o evento é por rubrica).
    """
    _validar_entrada(tipo, rubrica=rubrica, folha=folha, vinculo=vinculo)

    id_evento = gerar_id_evento(orgao, sequencial=sequencial)
    construtor = _CONSTRUTORES[tipo]
    if tipo in TIPOS_PERIODICOS:
        kwargs = {"id_evento": id_evento, "tp_amb": tp_amb, "folha": folha,
                  "vinculo": vinculo}
    else:
        kwargs = {"id_evento": id_evento, "tp_amb": tp_amb, "competencia": competencia}
        if tipo == TipoEvento.S_1000:
            kwargs["class_trib"] = class_trib
        if tipo == TipoEvento.S_1010:
            kwargs["rubrica"] = rubrica
    raiz = construtor(orgao, **kwargs)

    xml = etree.tostring(raiz, xml_declaration=True, encoding="UTF-8", pretty_print=True)
    validar_xml(xml, tipo, VERSAO)  # levanta ErroValidacaoXSD se inválido

    return EventoESocial.objects.create(
        tipo=tipo,
        orgao_emissor=orgao,
        rubrica=rubrica,
        folha=folha,
        vinculo=vinculo,
        id_evento=id_evento,
        versao_layout=VERSAO,
        xml=xml.decode("utf-8"),
        status=StatusEvento.VALIDADO,
    )


def tipo_remuneracao_para(vinculo) -> str:
    """S-1202 para regime próprio (estatutário); S-1200 para os demais."""
    return TipoEvento.S_1202 if vinculo.regime in REGIMES_S1202 else TipoEvento.S_1200


def gerar_remuneracoes_da_folha(
    orgao: OrgaoEmissor,
    folha,
    *,
    incluir_pagamentos: bool = False,
    tp_amb: int = 2,
) -> dict:
    """Gera os eventos de remuneração de TODOS os vínculos da folha (Onda 4.5).

    Para cada vínculo com `ResumoFolha`, escolhe S-1200 ou S-1202 pelo regime
    e gera o evento (validado no XSD). Com `incluir_pagamentos`, gera também o
    S-1210. Vínculos com erro (ex.: rubricas sem natureza) não interrompem o
    lote — voltam listados em `erros`.
    """
    from apps.payroll.models import ResumoFolha

    resumos = (
        ResumoFolha.objects.filter(folha=folha)
        .select_related("vinculo__servidor")
        .order_by("vinculo__servidor__nome")
    )
    gerados, erros = [], []
    seq = 1
    for resumo in resumos:
        vinculo = resumo.vinculo
        tipo = tipo_remuneracao_para(vinculo)
        try:
            ev = gerar_evento(orgao, tipo, folha=folha, vinculo=vinculo,
                              tp_amb=tp_amb, sequencial=seq)
            gerados.append(ev)
            seq += 1
            if incluir_pagamentos:
                ev2 = gerar_evento(orgao, TipoEvento.S_1210, folha=folha,
                                   vinculo=vinculo, tp_amb=tp_amb, sequencial=seq)
                gerados.append(ev2)
                seq += 1
        except ValueError as exc:
            erros.append({
                "vinculo_id": vinculo.id,
                "servidor": vinculo.servidor.nome,
                "erro": str(exc),
            })
    return {"gerados": len(gerados), "erros": erros}
