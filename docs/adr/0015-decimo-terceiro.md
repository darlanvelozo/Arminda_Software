# ADR-0015 — 13º salário (gratificação natalina): escopo por tipo de folha, avos e parcelas

**Status:** Aceita · 2026-06-05 · Vigora para Bloco 3 (Onda 3.1)

## Contexto

O Bloco 3 (folhas especiais) começa pelo **13º salário**. O engine de folha
(Bloco 2) calcula bem a folha **mensal**, mas:

1. `calcular_folha` é **genérico** — aplica todas as rubricas ativas a toda
   folha, sem distinguir o `tipo`. Uma folha de 13º não pode rodar o salário
   mensal; precisa rodar rubricas próprias de 13º.
2. Não há **avos** (meses trabalhados no ano) nem base do 13º.

Regras legais do 13º (CLT art. 1º da Lei 4.090/62; estatutários por lei
municipal análoga):
- **Avos:** 1/12 da remuneração por mês trabalhado; mês com **≥ 15 dias**
  trabalhados conta 1 avo.
- **1ª parcela (adiantamento):** até 30/11, = 50% da remuneração, **sem**
  desconto de INSS/IRRF.
- **2ª parcela:** até 20/12, = 13º integral − 1ª parcela, com **INSS e IRRF
  do 13º calculados em separado** da folha mensal (IRRF é tributação
  exclusiva). FGTS e RPPS também incidem sobre o 13º.

## Decisão

1. **Escopo de rubrica por tipo de folha.** Novo campo
   `Rubrica.tipos_folha` (lista de `TipoFolha`). `calcular_folha` filtra as
   rubricas pelo `folha.tipo`. Migration define as rubricas existentes como
   `['mensal']` (comportamento atual preservado). Extensível a férias/rescisão.

2. **Avos automáticos.** `apps.payroll.services.decimo.avos_no_ano(vinculo,
   ano)` conta os meses do ano com ≥ 15 dias dentro de
   `[data_admissao, data_demissao | fim do ano]`. Exposto no contexto como
   `AVOS_13` (0–12). Ajuste manual por afastamentos/faltas fica para uma onda
   posterior (override).

3. **DSL-driven** (reusa o engine de duas fases + bases + `FAIXA_*`). O engine
   expõe no contexto:
   - `AVOS_13` — avos do vínculo no ano da competência.
   - `BASE_13` — base do 13º (v1 = `SALARIO_BASE`; médias de variáveis habituais
     ficam para refinamento futuro).
   - `PARCELA_13` — 1 ou 2 conforme `folha.tipo` (`13_primeira`/`13_segunda`).

   O 13º vira **rubricas seed** (comando `seed_rubricas_13`):
   - **1ª parcela** (`tipos_folha=['13_primeira']`): provento
     `ARRED(SALARIO_BASE * AVOS_13 / 12 * 0.5, 2)`, sem incidências.
   - **2ª parcela** (`tipos_folha=['13_segunda']`):
     - provento `13_PROV = ARRED(SALARIO_BASE * AVOS_13 / 12, 2)` com
       `incide_inss/irrf/fgts/rpps = True` (forma as bases na fase 1);
     - `13_INSS = FAIXA_INSS(BASE_INSS) * EH_RGPS`;
     - `13_RPPS = FAIXA_RPPS(BASE_RPPS) * EH_RPPS`;
     - `13_IRRF = FAIXA_IRRF(BASE_IRRF - RUBRICA('13_INSS') - RUBRICA('13_RPPS'), DEPENDENTES)`;
     - `13_ADIANT_DESC` (desconto) = 50% (abate a 1ª parcela já paga);
     - `13_FGTS` / `13_RPPS_PATRONAL` (informativas).

   Como o engine já calcula incidências em duas fases sobre as bases formadas
   pelos proventos da própria folha, o INSS/IRRF/RPPS do 13º saem
   **naturalmente separados** da folha mensal — sem código novo de incidência.

### Vínculos da folha de 13º

Usa o conjunto de `_vinculos_da_competencia(folha.competencia)` (ativos na
competência — tipicamente dezembro). Servidores desligados no meio do ano
recebem o 13º proporcional na **rescisão** (onda futura), não nesta folha.

## Consequências

### Positivas
- 13º reusa todo o engine (duas fases, bases, FAIXA_*), sem lógica de
  incidência duplicada. Incidências do 13º já saem em separado.
- `tipos_folha` abre caminho para férias/rescisão/complementar.
- Cálculo configurável por município via rubricas (igual ao mensal).

### Negativas / trade-offs
- `BASE_13 = SALARIO_BASE` no v1 — médias de rubricas variáveis habituais
  (horas extras, adicionais) ficam para refinamento.
- Avos só automático nesta onda; override manual (afastamentos) vem depois.
- Migration precisa marcar rubricas existentes como `['mensal']`.

## Implementação na Onda 3.1

- `apps/payroll`: `Rubrica.tipos_folha` (+migration data-migration p/ existentes),
  `services/decimo.py` (avos), contexto (`AVOS_13`/`BASE_13`/`PARCELA_13`),
  filtro por tipo no `calcular_folha`, comando `seed_rubricas_13`.
- Testes: avos (ano cheio, admissão no meio, demissão), escopo por tipo,
  1ª parcela (sem incidência), 2ª parcela (INSS/IRRF/RPPS sobre o 13º +
  abatimento do adiantamento).

## Histórico

- 2026-06-05 — Aceita. Versão `v0.14.0` ao final da Onda 3.1.
