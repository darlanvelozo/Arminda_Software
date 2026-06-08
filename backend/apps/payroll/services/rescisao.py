"""
Cálculo de parâmetros da rescisão — Onda 3.2 (ADR-0016).

- `avos_ferias`: avos do período aquisitivo de férias atual (mês com ≥15
  dias = 1/12), do último aniversário de admissão ≤ demissão até a demissão.
- `vars_rescisao`: variáveis expostas ao engine na folha de rescisão
  (saldo de dias, avos de férias, flags de motivo, saldo do FGTS).

Funções puras sobre o vínculo/datas (sem acesso ao banco).
"""

from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal

from apps.people.models import MotivoDemissao, Regime, VinculoFuncional


def _avos_periodo(inicio: date, fim: date) -> int:
    """Meses com ≥15 dias dentro de [inicio, fim] (cap 12)."""
    if fim < inicio:
        return 0
    avos = 0
    y, m = inicio.year, inicio.month
    while (y, m) <= (fim.year, fim.month):
        primeiro = date(y, m, 1)
        ultimo = date(y, m, calendar.monthrange(y, m)[1])
        ini = max(primeiro, inicio)
        f = min(ultimo, fim)
        if (f - ini).days + 1 >= 15:
            avos += 1
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return min(avos, 12)


def _aniversario_admissao(data_admissao: date, ref: date) -> date:
    """Último aniversário de admissão ≤ `ref` (início do período aquisitivo)."""
    def _no_ano(ano: int) -> date:
        try:
            return data_admissao.replace(year=ano)
        except ValueError:  # 29/02 em ano não-bissexto
            return data_admissao.replace(year=ano, day=28)

    aniv = _no_ano(ref.year)
    if aniv > ref:
        aniv = _no_ano(ref.year - 1)
    return aniv


def avos_ferias(data_admissao: date, data_demissao: date) -> int:
    """Avos de férias proporcionais no período aquisitivo atual (0–12)."""
    inicio = _aniversario_admissao(data_admissao, data_demissao)
    return _avos_periodo(inicio, data_demissao)


def vars_rescisao(vinculo: VinculoFuncional) -> dict[str, Decimal]:
    """Variáveis de rescisão para o contexto da fórmula (folha de rescisão)."""
    dem = vinculo.data_demissao
    motivo = vinculo.motivo_demissao
    saldo_dias = Decimal(dem.day) if dem else Decimal(30)
    avos_fer = avos_ferias(vinculo.data_admissao, dem) if dem else 0

    def flag(cond: bool) -> Decimal:
        return Decimal(1) if cond else Decimal(0)

    return {
        "SALDO_DIAS": saldo_dias,
        "AVOS_FERIAS": Decimal(avos_fer),
        "EH_SEM_JUSTA_CAUSA": flag(motivo == MotivoDemissao.SEM_JUSTA_CAUSA),
        "EH_JUSTA_CAUSA": flag(motivo == MotivoDemissao.COM_JUSTA_CAUSA),
        "EH_PEDIDO": flag(motivo == MotivoDemissao.PEDIDO_DEMISSAO),
        "EH_CELETISTA": flag(vinculo.regime == Regime.CELETISTA),
        "AVISO_INDENIZADO": flag(bool(vinculo.aviso_previo_indenizado)),
        "TEM_FERIAS_VENCIDAS": flag(bool(vinculo.tem_ferias_vencidas)),
        "SALDO_FGTS": Decimal(vinculo.saldo_fgts or 0),
    }
