"""
Cálculo de avos do 13º salário — Onda 3.1 (ADR-0015).

Avos = meses do ano com ao menos 15 dias dentro do período de vínculo
(`[data_admissao, data_demissao | 31/12]`). Mês com ≥ 15 dias conta 1/12.
Função pura sobre datas (não toca o banco).
"""

from __future__ import annotations

import calendar
from datetime import date


def _dias_no_mes(ano: int, mes: int) -> int:
    return calendar.monthrange(ano, mes)[1]


def avos_no_ano(data_admissao: date, data_demissao: date | None, ano: int) -> int:
    """
    Quantos avos (0–12) o vínculo acumula no `ano`.

    Para cada mês, conta os dias em que o vínculo esteve ativo
    (interseção entre o mês e `[data_admissao, data_demissao | fim do ano]`).
    Mês com ≥ 15 dias ativos conta 1 avo.
    """
    inicio_periodo = data_admissao
    fim_periodo = data_demissao or date(ano, 12, 31)
    avos = 0
    for mes in range(1, 13):
        primeiro = date(ano, mes, 1)
        ultimo = date(ano, mes, _dias_no_mes(ano, mes))
        ini = max(primeiro, inicio_periodo)
        fim = min(ultimo, fim_periodo)
        if fim < ini:
            continue  # vínculo não cobre este mês
        dias_ativos = (fim - ini).days + 1
        if dias_ativos >= 15:
            avos += 1
    return avos
