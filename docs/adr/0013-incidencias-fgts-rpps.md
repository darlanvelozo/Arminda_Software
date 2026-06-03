# ADR-0013 — Incidências automáticas (FGTS + previdência municipal RPPS)

**Status:** Aceita · 2026-06-02 · Vigora para Bloco 2 (Onda 2.4)

## Contexto

O cálculo de folha (Ondas 2.2/2.3) já produz proventos e descontos via
rubricas com fórmula DSL, e INSS/IRRF funcionam pelos builtins
`FAIXA_INSS`/`FAIXA_IRRF` lendo `apps.core.TabelaLegal` (federal,
schema `public`, compartilhada).

Faltam as demais **incidências**:

- **FGTS** — encargo patronal de 8% sobre a remuneração dos celetistas
  (não desconta do servidor; é custo do empregador). Federal, fixo.
- **Previdência municipal própria (RPPS)** — contribuição do servidor
  efetivo (desconto) + contribuição patronal (encargo), quando o
  município mantém regime próprio (IPM). As alíquotas são **municipais**
  e variam entre municípios (pré e pós-EC 103/2019).

Dois problemas estruturais bloqueavam isso:

1. Os flags `Rubrica.incide_inss/incide_irrf/incide_fgts` existiam mas
   **o engine não os usava** — cada fórmula remontava a base de
   incidência na mão (`RUBRICA('SAL') + RUBRICA('GRAT') + ...`), o que
   é frágil e some a cada município novo.
2. Não havia onde guardar a config do RPPS, que é por município, nem
   como o engine sabia se um vínculo é RGPS (INSS) ou RPPS.

### Opções avaliadas

**Onde guardar a config do RPPS**
- (A) Estender `TabelaLegal` (schema public, compartilhado) com tipo
  `rpps`. Simples, mas **errado**: a alíquota de um município vazaria
  para todos. RPPS não é federal.
- (B) Modelo próprio em `apps.payroll` (TENANT_APP) — vive no schema de
  cada município. Correto e isolado.

**Forma da contribuição do servidor**
- Alíquota única (flat, ex. 11%/14%) — comum em municípios menores.
- Tabela progressiva estilo EC 103 (alíquota efetiva por faixa, com
  teto do RGPS na parcela RGPS) — municípios que adotaram a reforma.

**Como expor a config ao engine sem acoplar `apps.calculo` a `apps.payroll`**
- (A) Builtin `FAIXA_RPPS` consulta o banco (import de payroll dentro de
  calculo). Quebra a pureza do engine e cria acoplamento.
- (B) A config resolvida flui como **dado** dentro do `ContextoFolha`
  (`rpps_config: dict`). O engine continua puro; quem resolve no banco
  é `apps.payroll.services.previdencia`.

## Decisão

1. **Config RPPS = modelo por-tenant** `apps.payroll.RegimePrevidenciario`
   (opção B), com vigência por competência (igual `TabelaLegal`), modo
   `flat` **ou** `progressivo` (configurável), alíquota patronal, teto e
   a lista de regimes de vínculo aos quais se aplica.

2. **Contribuição do servidor configurável** (flat ou progressivo). A
   matemática é pura e vive em `apps.calculo.previdencia.contribuicao_rpps`;
   o builtin `FAIXA_RPPS(base)` a invoca.

3. **Bases de incidência automáticas.** O `calcular_folha` passa a rodar
   em **duas fases** por vínculo:
   - Fase 1 — calcula os **proventos** (ordem topológica entre eles),
     acumulando as bases pelos flags: `BASE_INSS`, `BASE_IRRF`,
     `BASE_FGTS`, `BASE_RPPS` (novo flag `incide_rpps`).
   - Fase 2 — calcula **descontos** e **informativas** (ordem topológica),
     já com as bases + variáveis de regime no contexto.

4. **Variáveis de contexto novas** (preenchidas pelo engine por vínculo):
   - `BASE_INSS`, `BASE_IRRF`, `BASE_FGTS`, `BASE_RPPS` — somatórios.
   - `EH_RGPS`, `EH_RPPS`, `EH_FGTS` — 1/0, derivadas do `regime` do
     vínculo cruzado com a config do município.
   - `ALIQ_RPPS_PATRONAL`, `ALIQ_FGTS` — alíquotas para as fórmulas
     patronais/informativas.

5. **`rpps_config` flui como dado** no `ContextoFolha` (opção B): o
   `apps.calculo` permanece sem importar `apps.payroll`.

### Mapeamento regime → previdência

- `estatutario` (efetivo) **e** município com RPPS vigente **e** regime
  listado em `regimes_aplicaveis` → **RPPS** (`EH_RPPS=1`).
- Caso contrário → **RGPS/INSS** (`EH_RGPS=1`).
- `celetista` → **FGTS** (`EH_FGTS=1`). Demais regimes não geram FGTS.

A base do IRRF subtrai a previdência oficial: a rubrica seed de IRRF usa
`FAIXA_IRRF(BASE_IRRF - RUBRICA('INSS') - RUBRICA('RPPS'), DEPENDENTES)`
— como o vínculo é RGPS *ou* RPPS, uma das duas é sempre 0.

## Consequências

### Positivas
- Os flags `incide_*` finalmente valem; fórmulas de incidência ficam
  triviais (`FAIXA_INSS(BASE_INSS)`).
- RPPS isolado por município, versionado por competência.
- Engine segue puro e testável; config entra como dado.
- Base correta para todas as incidências e folhas futuras (13º, férias).

### Negativas / trade-offs
- O cálculo passa a depender da convenção "proventos antes de descontos".
  Uma fórmula de **provento** que referencie um desconto via `RUBRICA()`
  vai falhar com `FORMULA_RUBRICA_NAO_EXISTE` (rubrica ainda não
  calculada) — comportamento aceitável e documentado.
- Municípios sem RPPS cadastrado têm `EH_RPPS=0` e a rubrica RPPS
  resulta em 0 — exige o conjunto de rubricas seed consistente
  (comando `seed_rubricas_incidencia`).

## Implementação na Onda 2.4

- `apps/calculo`: `previdencia.py` (puro), `funcoes.make_fn_faixa_rpps`,
  `FAIXA_RPPS` na whitelist, `ContextoFolha.rpps_config`.
- `apps/payroll`: modelo `RegimePrevidenciario` + flag `incide_rpps`,
  `services/previdencia.py`, `calcular_folha` em duas fases, API
  (serializer/viewset/urls/admin/filter), comando
  `seed_rubricas_incidencia`.
- Testes: `FAIXA_RPPS` (flat/progressivo), duas fases/bases, gating por
  regime, FGTS, RPPS, API. Cobertura ≥ 95% no engine.

## Histórico

- 2026-06-02 — Aceita. Versão `v0.11.0` ao final da Onda 2.4.
