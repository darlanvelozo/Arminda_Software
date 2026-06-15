# ADR-0018 — Licença-prêmio: indenização por itens na folha

**Status:** Aceita · 2026-06-08 · Vigora para Bloco 3 (Onda 3.4)

## Contexto

Quarta onda do Bloco 3. A **licença-prêmio (assiduidade)** é uma ausência
remunerada adquirida por tempo de serviço (tipicamente 3 meses a cada
quinquênio, para estatutários). Tem dois destinos:

- **Gozo** — o servidor sai de licença recebendo o salário normal. Isso é a
  folha **mensal** continuando; não exige folha especial.
- **Indenização (conversão em pecúnia)** — quando a licença não é gozada, é
  paga em dinheiro (comumente na aposentadoria ou por decreto). É a parte
  calculável e o foco desta onda.

A indenização de licença-prêmio é verba **indenizatória** — não sofre INSS
nem IRRF (jurisprudência consolidada, análoga às férias indenizadas).

## Decisão

1. **Novo tipo de folha** `TipoFolha.LICENCA_PREMIO`.

2. **Programação por itens** (mesmo padrão de férias — ADR-0017): modelo
   `LicencaPremioItem(folha, vinculo, meses, dias)` (único por folha+vínculo).
   O operador adiciona os servidores e quantos meses/dias indenizar.

3. **Cálculo:** `indenização = salário × meses + salário/30 × dias`, **sem
   incidência** (indenizatória). DSL-driven, reusa o engine. Contexto ganha
   `MESES_LP` e `DIAS_LP`. Seletor de vínculos da folha vem dos itens (cada
   vínculo carrega o item em `_lp_item`). Rubrica seed
   (`seed_rubricas_licenca_premio`, `tipos_folha=['licenca_premio']`):
   - `LP_INDENIZ` (provento, sem incidência) =
     `ARRED(SALARIO_BASE * MESES_LP + SALARIO_BASE / 30 * DIAS_LP, 2)`.

## Consequências

### Positivas
- Reusa o padrão de itens-na-folha (férias) e o engine; pouco código novo.
- Indenização corretamente isenta de INSS/IRRF.

### Limitações (v1)
- Não controla o **saldo** de licença-prêmio adquirido por tempo de serviço
  (confia no que o operador programar). O cálculo automático do direito
  (quinquênios) fica para o Bloco 8 (RH operacional).
- Licença-prêmio **gozada** não gera folha própria (é a mensal).

## Implementação na Onda 3.4

- `apps/payroll`: `TipoFolha.LICENCA_PREMIO`, modelo `LicencaPremioItem`
  (+migration), `services/licenca_premio.py` (vars), seletor no
  `calcular_folha`, comando `seed_rubricas_licenca_premio`, API.
- Frontend: aba Programação na folha de licença-prêmio.
- Testes: cálculo (meses + dias), isenção de incidência, seletor por itens.

## Histórico

- 2026-06-08 — Aceita. Versão `v0.17.0` ao final da Onda 3.4.
