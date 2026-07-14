"""
Paridade Fiorilli — compara o cálculo do Arminda contra a folha real do
SIP (Onda 2.7, fecha o Bloco 2).

O SIP publica, por servidor e competência, as **bases** e os **valores**
finais de previdência, IRRF e FGTS na tabela BASES. Este serviço toma
essas bases como entrada e roda as **nossas** funções tributárias de
produção (`apps.calculo.tabelas`) sobre elas, comparando o valor que o
Arminda calcularia contra o valor que o Fiorilli publicou.

Objetivo: validar o motor tributário (o que é determinístico e
juridicamente crítico) contra dados reais, sem depender de reconstruir
as 137 rubricas do município. O relatório é **agregado e sem PII** —
só contagens, taxas de acerto e faixas de divergência.

Convenção de tolerância: divergência de até 1 centavo conta como acerto
(arredondamento). Acima disso é divergência real, classificada em faixas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from apps.calculo.tabelas import inss, irrf

CENTAVO = Decimal("0.01")
ALIQUOTA_FGTS = Decimal("0.08")


def _dec(value: object) -> Decimal:
    """Converte valor bruto do Firebird em Decimal quantizado (0.00)."""
    if value is None or value == "":
        return Decimal(0)
    try:
        return Decimal(str(value)).quantize(CENTAVO)
    except Exception:
        return Decimal(0)


@dataclass
class ResultadoTributo:
    """Estatística de paridade de um tributo numa competência."""

    tributo: str
    comparados: int = 0
    exatos: int = 0  # divergência <= 1 centavo
    divergentes: int = 0
    soma_abs_divergencia: Decimal = field(default_factory=lambda: Decimal(0))
    maior_divergencia: Decimal = field(default_factory=lambda: Decimal(0))
    # Faixas de divergência (só magnitude, sem identificar servidor)
    faixas: dict[str, int] = field(default_factory=dict)

    def registrar(self, nosso: Decimal, deles: Decimal) -> None:
        self.comparados += 1
        diff = (nosso - deles).copy_abs()
        if diff <= CENTAVO:
            self.exatos += 1
            return
        self.divergentes += 1
        self.soma_abs_divergencia += diff
        if diff > self.maior_divergencia:
            self.maior_divergencia = diff
        self.faixas[_faixa(diff)] = self.faixas.get(_faixa(diff), 0) + 1

    @property
    def taxa_acerto(self) -> float:
        return (self.exatos / self.comparados * 100) if self.comparados else 0.0


def _faixa(diff: Decimal) -> str:
    """Rótulo da faixa de divergência (magnitude, sem PII)."""
    if diff <= Decimal("1.00"):
        return "≤ R$1,00"
    if diff <= Decimal("10.00"):
        return "R$1–10"
    if diff <= Decimal("100.00"):
        return "R$10–100"
    if diff <= Decimal("1000.00"):
        return "R$100–1.000"
    return "> R$1.000"


@dataclass
class RelatorioParidade:
    """Relatório agregado de uma competência — PII-safe."""

    competencia: date
    total_servidores: int = 0
    tributos: dict[str, ResultadoTributo] = field(default_factory=dict)
    # Distribuição de regime (contagem, sem PII)
    regimes: dict[str, int] = field(default_factory=dict)
    # Alíquota efetiva de previdência observada (RPPS): {rate_str: contagem}
    rpps_aliquotas: dict[str, int] = field(default_factory=dict)

    def tributo(self, nome: str) -> ResultadoTributo:
        if nome not in self.tributos:
            self.tributos[nome] = ResultadoTributo(tributo=nome)
        return self.tributos[nome]


def comparar_competencia(
    *,
    competencia: date,
    bases: list[dict],
    regimes: dict[str, str] | None = None,
) -> RelatorioParidade:
    """
    Compara a folha do Arminda contra o BASES do SIP para uma competência.

    - `bases`: linhas de BASES (via fetch_bases_competencia).
    - `regimes`: {registro: regime} (opcional; só para relatório).

    Compara:
    - Previdência (progressiva): nossa `inss(base)` vs VALORPREVIDENCIAMES.
      A base real de SJB usa a tabela progressiva federal (efetivas em
      7,5–14%, sem pico em 11/14% — não é alíquota RPPS fixa). O histograma
      de alíquota efetiva é sempre reportado para caracterizar a regra.
    - IRRF (federal, todos): nossa `irrf(base, deps)` vs VALORIRRFMES.
    - FGTS: base × 8% vs VALORFGTSMES (N/A em município 100% estatutário).
    """
    regimes = regimes or {}
    rel = RelatorioParidade(competencia=competencia, total_servidores=len(bases))

    for row in bases:
        reg = str(row.get("registro", "")).strip()
        if regimes:
            regime = regimes.get(reg, "indefinido")
            rel.regimes[regime] = rel.regimes.get(regime, 0) + 1

        # --- Previdência (tabela progressiva) ---
        base_prev = _dec(row.get("baseprevidenciames"))
        valor_prev = _dec(row.get("valorprevidenciames"))
        if base_prev > 0:
            aliq = (valor_prev / base_prev).quantize(Decimal("0.0001"))
            rel.rpps_aliquotas[str(aliq)] = rel.rpps_aliquotas.get(str(aliq), 0) + 1
            nosso_prev = inss(base_prev, competencia)
            rel.tributo("Previdência (progressiva)").registrar(nosso_prev, valor_prev)

        # --- IRRF (federal, todos os regimes) ---
        # BASEIRRFMES é a base ANTES da dedução; DEDUIRRFMES é a dedução total
        # que o SIP publicou (dependentes + demais). Alimentamos a nossa
        # função de produção com a base já líquida da dedução deles (deps=0)
        # para isolar a aplicação da tabela — que é o que queremos validar.
        base_irrf = _dec(row.get("baseirrfmes"))
        valor_irrf = _dec(row.get("valorirrfmes"))
        if base_irrf > 0:
            dedu = _dec(row.get("deduirrfmes"))
            base_liquida = base_irrf - dedu
            nosso_irrf = irrf(base_liquida, 0, competencia)
            rel.tributo("IRRF").registrar(nosso_irrf, valor_irrf)

        # --- FGTS (8% linear) ---
        base_fgts = _dec(row.get("basefgtsmes"))
        valor_fgts = _dec(row.get("valorfgtsmes"))
        if base_fgts > 0:
            nosso_fgts = (base_fgts * ALIQUOTA_FGTS).quantize(CENTAVO)
            rel.tributo("FGTS").registrar(nosso_fgts, valor_fgts)

    return rel
