# ADR-0016 — Rescisão: verbas rescisórias, motivo no vínculo e avos de férias

**Status:** Aceita · 2026-06-07 · Vigora para Bloco 3 (Onda 3.2)

## Contexto

Segunda onda do Bloco 3 (após o 13º). A **rescisão** paga as verbas
rescisórias quando um vínculo é desligado. O que entra depende do
**motivo** do desligamento. O `VinculoFuncional` só tinha `data_demissao`
— faltava o motivo e os parâmetros de rescisão.

Verbas (CLT / estatutário análogo):
- **Saldo de salário** — dias trabalhados no mês × salário/30 (tributável).
- **13º proporcional** — avos/12 do salário (tributável; INSS/IRRF do 13º
  em separado, como na Onda 3.1).
- **Férias proporcionais + 1/3** e **férias vencidas + 1/3** — verbas
  **indenizatórias** (não sofrem INSS/IRRF).
- **Aviso prévio indenizado** — só na dispensa **sem justa causa**
  (celetista); indenizatório.
- **Multa de 40% do FGTS** — sobre o **saldo do FGTS** acumulado, na
  dispensa sem justa causa (celetista).

Gating por motivo (regras clássicas):
- `com_justa_causa` perde 13º proporcional, férias proporcionais e aviso;
  mantém saldo de salário e férias vencidas.
- `pedido_demissao` mantém 13º/férias proporcionais e saldo; sem aviso
  indenizado nem multa 40%.
- `sem_justa_causa` recebe tudo, incluindo aviso indenizado e multa 40%.

## Decisão

1. **Motivo e parâmetros no `VinculoFuncional`** (a rescisão é propriedade
   do vínculo desligado): campos novos
   - `motivo_demissao` (choices: pedido_demissao, sem_justa_causa,
     com_justa_causa, termino_contrato, aposentadoria, falecimento,
     exoneracao);
   - `aviso_previo_indenizado` (bool);
   - `tem_ferias_vencidas` (bool);
   - `saldo_fgts` (Decimal, default 0) — base da multa de 40%.

2. **Escopo v1 = núcleo + CLT básico.** Saldo + 13º prop + férias
   prop/vencidas + 1/3 (todos os regimes, com gating por motivo) + aviso
   prévio indenizado e multa 40% (celetista sem justa causa).

3. **Avos de férias automático.** `apps.payroll.services.rescisao.avos_ferias`
   conta os meses do **período aquisitivo atual** (do último aniversário de
   admissão ≤ demissão até a demissão; mês com ≥15 dias = 1/12). Férias
   vencidas (período completo não gozado) entram pelo flag.

4. **DSL-driven** (reusa o engine de duas fases). O engine expõe, na folha
   de rescisão:
   - `SALDO_DIAS` — dias do mês trabalhados até a demissão.
   - `AVOS_13` — reusa `avos_no_ano` (capa na data de demissão).
   - `AVOS_FERIAS` — avos do período aquisitivo.
   - `TEM_FERIAS_VENCIDAS`, `AVISO_INDENIZADO`, `SALDO_FGTS` — do vínculo.
   - Flags de motivo: `EH_SEM_JUSTA_CAUSA`, `EH_JUSTA_CAUSA`,
     `EH_PEDIDO`, `EH_CELETISTA`.

   **Seletor de vínculos da rescisão:** diferente das outras folhas —
   `calcular_folha` seleciona os vínculos com `data_demissao` **dentro do
   mês da competência** (independente de `ativo`), pois o desligado deixa de
   ser ativo. As demais folhas continuam com o seletor de ativos.

   Rubricas seed (`seed_rubricas_rescisao`, `tipos_folha=['rescisao']`):
   - `RESC_SALDO` (provento, incide tudo) = saldo de salário.
   - `RESC_13` (provento, só `incide_fgts`) = 13º prop; INSS/IRRF/RPPS do
     13º calculados **em separado** via rubricas dedicadas (como na Onda 3.1).
   - `RESC_FERIAS_PROP` + `RESC_FERIAS_PROP_13` (1/3), `RESC_FERIAS_VENC` +
     `RESC_FERIAS_VENC_13` — proventos **sem incidência** (indenizados).
   - `RESC_AVISO` (provento sem incidência) — sem justa causa × celetista.
   - `RESC_INSS`/`RESC_RPPS`/`RESC_IRRF` sobre o saldo (BASE_*).
   - `RESC_13_INSS`/`RESC_13_RPPS`/`RESC_13_IRRF` sobre o 13º.
   - `RESC_FGTS` (informativa) e `RESC_FGTS_MULTA` (informativa = 40% do
     `SALDO_FGTS`).

## Consequências

### Positivas
- Reusa avos (13º) + engine de duas fases + bases + `tipos_folha`.
- Verbas indenizatórias não tributam; 13º e saldo tributam em separado,
  com o INSS/IRRF correto por base.
- Motivo no vínculo alimenta o gating de forma declarativa.

### Negativas / limitações (v1)
- **Multa 40%** depende do `saldo_fgts` informado no vínculo — o sistema
  ainda não rastreia o saldo do FGTS (virá com a integração de FGTS/eSocial).
  Sem o saldo, a multa sai 0.
- Avos de férias é uma aproximação do período aquisitivo (não trata
  afastamentos que suspendem o período — refinamento futuro).
- Projeção do aviso prévio sobre 13º/férias (dias adicionais) fica para
  depois.

## Implementação na Onda 3.2

- `apps/people`: campos de rescisão no `VinculoFuncional` (+migration).
- `apps/payroll/services/rescisao.py`: `avos_ferias`, `saldo_dias`,
  flags de motivo; `calcular_folha` ganha o seletor de vínculos de rescisão
  e as variáveis de contexto; comando `seed_rubricas_rescisao`.
- Testes: avos de férias, saldo, gating por motivo (justa causa perde
  prop.), verbas indenizadas sem incidência, multa sobre saldo_fgts.

## Histórico

- 2026-06-07 — Aceita. Versão `v0.15.0` ao final da Onda 3.2.
