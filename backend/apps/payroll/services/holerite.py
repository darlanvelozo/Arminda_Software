"""
Geração de holerite (contracheque) — Onda 2.5 (ADR-0014).

Duas funções:
- `montar_holerite(folha, vinculo)` agrega os Lancamento de um vínculo numa
  folha em um dict estruturado (proventos/descontos/informativas + totais +
  cabeçalho). Fonte da verdade do JSON.
- `gerar_pdf(holerite)` renderiza esse dict em PDF via ReportLab (recebe o
  dict pronto — testável e desacoplado do banco).
"""

from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from typing import Any

from django.db import connection

from apps.payroll.models import Folha, Lancamento, TipoRubrica
from apps.people.models import VinculoFuncional

CENTAVOS = Decimal("0.01")

MESES = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


def _competencia_extenso(competencia) -> str:
    return f"{MESES[competencia.month - 1]} de {competencia.year}"


def _municipio_nome() -> str:
    """Nome do município (tenant atual). Cai para o schema se indisponível."""
    tenant = getattr(connection, "tenant", None)
    if tenant is not None:
        return getattr(tenant, "nome", None) or getattr(tenant, "schema_name", "")
    return ""


def _linha(lanc: Lancamento) -> dict[str, str]:
    return {
        "codigo": lanc.rubrica.codigo,
        "nome": lanc.rubrica.nome,
        "referencia": str(lanc.referencia),
        "valor": str(lanc.valor),
    }


def montar_holerite(folha: Folha, vinculo: VinculoFuncional) -> dict[str, Any]:
    """
    Monta o holerite de um vínculo numa folha. Não persiste nada.

    Raises:
        Lancamento.DoesNotExist: se o vínculo não tem lançamentos na folha
            (tratado como 404 pela view).
    """
    lancs = list(
        Lancamento.objects.filter(folha=folha, vinculo=vinculo)
        .select_related("rubrica", "servidor")
        .order_by("rubrica__codigo")
    )
    if not lancs:
        raise Lancamento.DoesNotExist(
            "Vínculo sem lançamentos nesta folha — calcule a folha primeiro."
        )

    proventos, descontos, informativas = [], [], []
    total_prov, total_desc = Decimal(0), Decimal(0)
    for lanc in lancs:
        if lanc.rubrica.tipo == TipoRubrica.PROVENTO:
            proventos.append(_linha(lanc))
            total_prov += lanc.valor
        elif lanc.rubrica.tipo == TipoRubrica.DESCONTO:
            descontos.append(_linha(lanc))
            total_desc += lanc.valor
        else:
            informativas.append(_linha(lanc))

    servidor = vinculo.servidor
    return {
        "competencia": folha.competencia.isoformat(),
        "competencia_extenso": _competencia_extenso(folha.competencia),
        "tipo_folha": folha.get_tipo_display(),
        "municipio": _municipio_nome(),
        "servidor": {
            "nome": servidor.nome,
            "matricula": servidor.matricula,
            "cpf": servidor.cpf,
        },
        "vinculo": {
            "cargo": vinculo.cargo.nome,
            "lotacao": vinculo.lotacao.nome,
            "regime": vinculo.get_regime_display(),
            "data_admissao": vinculo.data_admissao.isoformat(),
            "salario_base": str(vinculo.salario_base),
        },
        "proventos": proventos,
        "descontos": descontos,
        "informativas": informativas,
        "totais": {
            "proventos": str(total_prov.quantize(CENTAVOS)),
            "descontos": str(total_desc.quantize(CENTAVOS)),
            "liquido": str((total_prov - total_desc).quantize(CENTAVOS)),
        },
    }


# ============================================================
# PDF (ReportLab)
# ============================================================


def _fmt_moeda(valor: str) -> str:
    """'1234.5' → '1.234,50' (formatação BR sem locale do SO)."""
    d = Decimal(valor).quantize(CENTAVOS)
    inteiro, _, dec = f"{abs(d):.2f}".partition(".")
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    sinal = "-" if d < 0 else ""
    return f"{sinal}{'.'.join(grupos)},{dec}"


def gerar_pdf(holerite: dict[str, Any]) -> bytes:
    """Renderiza o dict de `montar_holerite` em PDF (bytes)."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"Holerite {holerite['servidor']['nome']} {holerite['competencia']}",
    )
    styles = getSampleStyleSheet()
    pequeno = styles["Normal"].clone("pequeno")
    pequeno.fontSize = 8
    elems: list[Any] = []

    # Cabeçalho
    elems.append(Paragraph(f"<b>{holerite['municipio']}</b>", styles["Title"]))
    elems.append(
        Paragraph(
            f"Demonstrativo de pagamento — {holerite['tipo_folha']} · "
            f"{holerite['competencia_extenso']}",
            styles["Normal"],
        )
    )
    elems.append(Spacer(1, 6 * mm))

    # Dados do servidor
    s, v = holerite["servidor"], holerite["vinculo"]
    cab = [
        ["Servidor", s["nome"], "Matrícula", s["matricula"]],
        ["Cargo", v["cargo"], "Lotação", v["lotacao"]],
        ["Regime", v["regime"], "Admissão", v["data_admissao"]],
    ]
    t_cab = Table(cab, colWidths=[24 * mm, 64 * mm, 24 * mm, 62 * mm])
    t_cab.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
                ("TEXTCOLOR", (2, 0), (2, -1), colors.grey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ]
        )
    )
    elems.append(t_cab)
    elems.append(Spacer(1, 5 * mm))

    # Tabela de proventos/descontos
    linhas = [["Cód.", "Descrição", "Ref.", "Provento", "Desconto"]]
    for p in holerite["proventos"]:
        linhas.append([p["codigo"], p["nome"], p["referencia"], _fmt_moeda(p["valor"]), ""])
    for d in holerite["descontos"]:
        linhas.append([d["codigo"], d["nome"], d["referencia"], "", _fmt_moeda(d["valor"])])
    tot = holerite["totais"]
    linhas.append(["", "Totais", "", _fmt_moeda(tot["proventos"]), _fmt_moeda(tot["descontos"])])
    linhas.append(["", "Líquido a receber", "", "", _fmt_moeda(tot["liquido"])])

    t = Table(linhas, colWidths=[18 * mm, 78 * mm, 16 * mm, 31 * mm, 31 * mm])
    n = len(linhas)
    t.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (3, 0), (4, -1), "RIGHT"),
                ("ALIGN", (2, 0), (2, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, n - 3), [colors.white, colors.HexColor("#f3f4f6")]),
                ("LINEABOVE", (0, n - 2), (-1, n - 2), 0.5, colors.grey),
                ("FONTNAME", (0, n - 2), (-1, -1), "Helvetica-Bold"),
                ("LINEABOVE", (0, n - 1), (-1, n - 1), 0.25, colors.lightgrey),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    elems.append(t)

    # Informativas (FGTS, RPPS patronal, bases) — rodapé
    if holerite["informativas"]:
        elems.append(Spacer(1, 4 * mm))
        elems.append(Paragraph("Informativas (não somam no líquido):", pequeno))
        info = [["Cód.", "Descrição", "Valor"]]
        for i in holerite["informativas"]:
            info.append([i["codigo"], i["nome"], _fmt_moeda(i["valor"])])
        t_info = Table(info, colWidths=[18 * mm, 94 * mm, 31 * mm])
        t_info.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.grey),
                    ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                ]
            )
        )
        elems.append(t_info)

    doc.build(elems)
    return buffer.getvalue()
