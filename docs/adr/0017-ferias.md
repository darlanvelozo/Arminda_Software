# ADR-0017 — Férias: programação por itens na folha, salário + 1/3 e abono pecuniário

**Status:** Aceita · 2026-06-07 · Vigora para Bloco 3 (Onda 3.3)

## Contexto

Terceira onda do Bloco 3 (após 13º e rescisão). Diferente das anteriores,
a folha de **férias** depende de **dado por servidor**: quem sai de férias,
quantos dias de gozo e quantos dias vendidos (abono pecuniário). Não dá para
derivar automaticamente como os avos do 13º.

Verbas:
- **Salário de férias** = salário/30 × dias de gozo — **tributável** (INSS/IRRF).
- **1/3 constitucional** sobre o salário de férias — **tributável**.
- **Abono pecuniário** (venda de até 10 dias) = salário/30 × dias vendidos, com
  seu **1/3** — **indenizatório** (não sofre INSS/IRRF).

## Decisão

1. **Programação por itens na folha.** Modelo `FeriasItem(folha, vinculo,
   dias_gozo, dias_abono, data_inicio)` (único por folha+vínculo). O operador
   monta a folha de férias adicionando servidores e seus dias; o engine
   calcula a partir dos itens.

2. **Escopo v1** = salário de férias + 1/3 + abono pecuniário + 1/3, com as
   incidências corretas (gozo tributa; abono não). Adiantamento (timing de
   pagamento) e antecipação do 13º junto das férias ficam fora.

3. **Sem validação de período aquisitivo** no v1 — calcula o que foi
   programado. Controle de saldo de dias/direito a férias é refinamento futuro.

4. **DSL-driven** (reusa o engine de duas fases). Para a folha de férias:
   - **Seletor de vínculos:** os que têm `FeriasItem` na folha (cada vínculo
     carrega seu item via atributo, evitando N queries).
   - **Contexto:** `DIAS_FERIAS`, `DIAS_ABONO`.
   - Rubricas seed (`seed_rubricas_ferias`, `tipos_folha=['ferias']`):
     - `FER_SALARIO` = `ARRED(SALARIO_BASE/30*DIAS_FERIAS, 2)` (incide tudo).
     - `FER_TERCO` = `ARRED(RUBRICA('FER_SALARIO')/3, 2)` (incide tudo).
     - `FER_ABONO` = `ARRED(SALARIO_BASE/30*DIAS_ABONO, 2)` (sem incidência).
     - `FER_ABONO_TERCO` = `ARRED(RUBRICA('FER_ABONO')/3, 2)` (sem incidência).
     - `FER_INSS`/`FER_RPPS`/`FER_IRRF` sobre as bases (só gozo + 1/3).

   Como gozo e 1/3 têm `incide_*` e o abono não, o INSS/IRRF saem só sobre a
   parcela tributável — sem código novo de incidência.

## Consequências

### Positivas
- Reusa engine de duas fases, bases e `tipos_folha`.
- Abono corretamente isento; gozo + 1/3 tributados.
- Programação por itens é simples e serve de base para escala/agenda futura.

### Negativas / limitações (v1)
- Sem validação de período aquisitivo/saldo de dias (confia no operador).
- Sem adiantamento de 13º junto das férias nem timing de pagamento.
- Médias de variáveis habituais sobre a base de férias ficam para refinamento
  (igual `BASE_13`).

## Implementação na Onda 3.3

- `apps/payroll`: modelo `FeriasItem` (+migration), `services/ferias.py`
  (vars), seletor de vínculos de férias no `calcular_folha`, comando
  `seed_rubricas_ferias`, API (serializer/viewset/urls) para CRUD dos itens.
- Frontend: gestão de itens na folha de férias (adicionar servidor + dias).
- Testes: cálculo gozo + 1/3 + abono, incidências (abono não tributa),
  seletor por itens.

## Histórico

- 2026-06-07 — Aceita. Versão `v0.16.0` ao final da Onda 3.3.
