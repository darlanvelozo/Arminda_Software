"""
Relatório da folha em PDF (Onda 4.4b) — a folha inteira exportável.

Diferente do holerite (1 servidor), este é o relatório analítico da
competência: quadro geral, uma linha por servidor (proventos/descontos/
líquido), totais por lotação e por órgão emissor. Gerado com ReportLab
(pure-Python, como o holerite — ADR-0014). Fonte: os mesmos serviços de
resumo da tela da folha, então funciona para qualquer folha calculada.
"""

from __future__ import annotations

from django.utils import timezone

from apps.payroll.models import Folha
from apps.payroll.services.holerite import (
    _competencia_extenso,
    _fmt_moeda,
    _municipio_nome,
)
from apps.payroll.services.resumo import resumo_por_area, resumo_por_servidor


def gerar_relatorio_pdf(folha: Folha) -> bytes:
    """Monta o PDF analítico da folha e devolve os bytes."""
    from io import BytesIO

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

    servidores = resumo_por_servidor(folha)
    areas = resumo_por_area(folha)
    geral = areas["geral"]

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title=f"Folha {folha.get_tipo_display()} — {folha.competencia:%m/%Y}",
    )
    styles = getSampleStyleSheet()
    corpo: list = []

    # Cabeçalho
    corpo.append(Paragraph(_municipio_nome() or "Município", styles["Title"]))
    corpo.append(
        Paragraph(
            f"Folha de pagamento — {folha.get_tipo_display()} · "
            f"{_competencia_extenso(folha.competencia)} · "
            f"situação: {folha.get_status_display()}",
            styles["Heading4"],
        )
    )
    corpo.append(
        Paragraph(
            f"Emitido em {timezone.localtime():%d/%m/%Y %H:%M} · "
            f"{len(servidores)} servidor(es)",
            styles["Normal"],
        )
    )
    corpo.append(Spacer(1, 6 * mm))

    estilo_tabela = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8ede9")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b9c4bd")),
            ("ALIGN", (-3, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7f5")]),
        ]
    )

    # Quadro geral
    quadro = [
        ["Total de proventos", "Total de descontos", "Líquido geral"],
        [
            _fmt_moeda(geral["proventos"]),
            _fmt_moeda(geral["descontos"]),
            _fmt_moeda(geral["liquido"]),
        ],
    ]
    t = Table(quadro, colWidths=[60 * mm, 60 * mm, 60 * mm])
    t.setStyle(estilo_tabela)
    corpo.append(t)
    corpo.append(Spacer(1, 6 * mm))

    # Por servidor
    corpo.append(Paragraph("Servidores", styles["Heading3"]))
    linhas = [["Matrícula", "Servidor", "Lotação", "Proventos", "Descontos", "Líquido"]]
    for s in servidores:
        linhas.append(
            [
                s["servidor_matricula"],
                s["servidor_nome"],
                s["lotacao"] or "—",
                _fmt_moeda(s["proventos"]),
                _fmt_moeda(s["descontos"]),
                _fmt_moeda(s["liquido"]),
            ]
        )
    t = Table(
        linhas,
        colWidths=[20 * mm, 55 * mm, 39 * mm, 22 * mm, 22 * mm, 24 * mm],
        repeatRows=1,
    )
    t.setStyle(estilo_tabela)
    corpo.append(t)
    corpo.append(Spacer(1, 6 * mm))

    # Totais por área
    for titulo, chave, rotulo in (
        ("Totais por lotação", "por_lotacao", "Lotação"),
        ("Totais por órgão emissor", "por_orgao", "Órgão"),
    ):
        grupos = areas[chave]
        if not grupos:
            continue
        corpo.append(Paragraph(titulo, styles["Heading3"]))
        linhas = [[rotulo, "Proventos", "Descontos", "Líquido"]]
        for g in grupos:
            linhas.append(
                [
                    g["nome"],
                    _fmt_moeda(g["proventos"]),
                    _fmt_moeda(g["descontos"]),
                    _fmt_moeda(g["liquido"]),
                ]
            )
        t = Table(linhas, colWidths=[96 * mm, 28 * mm, 28 * mm, 30 * mm], repeatRows=1)
        t.setStyle(estilo_tabela)
        corpo.append(t)
        corpo.append(Spacer(1, 5 * mm))

    doc.build(corpo)
    return buf.getvalue()
