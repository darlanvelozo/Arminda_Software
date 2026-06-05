# Análise de estado — 02/06/2026 (pós v0.13.0)

> Snapshot de saúde do projeto após as Ondas 2.4 (incidências), 2.5 (holerite)
> e os refinos operacionais da folha (v0.13.0). Verificação executada de fato
> (testes rodados, produção consultada), não de memória.

## 1. Resumo executivo

Projeto **saudável e consistente**. `dev` = `main` = **produção** = `23d7bad`
(**v0.13.0**). Backend **477 testes verdes** + ruff limpo; frontend lint/tsc/
vitest (10) / build OK. Produção no ar (`https://arminda.site`, health `ok`) e
painel público atualizado (02/06/2026, ordem correta). Bloco 2 (engine de
folha) em **85%** — falta apenas a Onda 2.7 (paridade Fiorilli).

## 2. Versão e git

| Item | Estado |
|---|---|
| Branch de trabalho | `develop` = `23d7bad` (sincronizada com `origin`) |
| `main` | `23d7bad` (= develop) |
| Produção (`/opt/arminda`) | `23d7bad` (alinhado; backend rodando v0.13.0) |
| Tags | v0.10.0 · v0.11.0 (2.4) · v0.12.0 (2.5) · v0.13.0 (refinos) |
| Working tree | limpo (fora `.env.production` e `dist/`, não versionados) |

## 3. Backend (`apps/`)

- **Apps:** core, people, calculo, payroll, imports, reports.
- **Testes:** 477 (pytest), ruff limpo, `manage.py check` sem issues. 42 arquivos de teste.
- **Engine de folha (Bloco 2):**
  - DSL via AST whitelist (2.1, ADR-0012).
  - Cálculo mensal idempotente (2.2).
  - Tabelas legais 2024–2026, INSS/IRRF reais (2.3).
  - Incidências automáticas em **duas fases** (proventos → bases → descontos),
    FGTS + RPPS municipal, `RegimePrevidenciario` por tenant (2.4, ADR-0013).
  - Holerite JSON + PDF via ReportLab (2.5, ADR-0014).
  - Resumos da folha por servidor e por lotação/órgão (refinos v0.13.0).

## 4. Frontend (`frontend/src`)

- **Páginas:** 34 `.tsx`. Tela de folha com abas Servidores / Por área /
  Lançamentos / Erros / Informações. Config de Previdência (RPPS) em
  Configurações. Holerite via download de PDF (blob autenticado).
- **Validação:** lint 0 erros (6 warnings pré-existentes de fast-refresh), tsc
  0 erros, vitest 10/10, build OK.
- **Tipos:** gerados do OpenAPI (`openapi-typescript`).

## 5. Página de status (painel público)

- Servida do `main` via GitHub Pages (`status-page/`). No ar com
  `ultima_atualizacao: 2026-06-02`, Bloco 2 = 85%, changelog na ordem correta.
- **Bug corrigido nesta sessão:** o comparador de ordenação do changelog
  retornava `-1` para datas iguais (em vez de `0`), embaralhando entregas do
  mesmo dia — a Onda 2.4 aparecia no topo no lugar da v0.13.0. Corrigido para
  preservar a ordem de entrada (sort estável); validado com os dados reais.
- **Datas corrigidas:** o relógio da VPS estava ~3 dias atrasado no início da
  sessão; o conteúdo foi recarimbado de 30/05 → **02/06/2026** (o relógio já se
  auto-corrigiu via NTP).

## 6. Documentação

- **14 ADRs** (0001–0014). CHANGELOG, CONTEXT.md's, guias vivos (operador + dev)
  e CLAUDE.md consistentes com a v0.13.0 (versão, contagem de testes, bloco).
- Memória interna do agente atualizada (dev×prod, fluxo de deploy, push via PAT).

## 7. Produção

- **URL:** https://arminda.site · health `{"status":"ok"}` · gunicorn `active`.
- **Tenant:** apenas `smoke_arminda` (Smoke Test/MA) — 23 servidores, 11 rubricas,
  3 folhas calculadas (mar–mai/2026). É um ambiente de demonstração/smoke, **não
  um município real em produção** ainda.
- **Usuários:** `smoke-admin@arminda.test` (admin do tenant). Sem superuser para
  o `/admin`.
- Deploy: `deploy.sh` (backend) + build/rsync manual (frontend). Sem CI/CD de
  deploy — ver dívidas.

## 8. Pontos de atenção / dívidas

1. **Paridade Fiorilli (Onda 2.7) pendente** — é o gate que fecha o Bloco 2 e
   exige dados de referência reais (SIP.FDB ou planilha de casos esperados).
2. **Cobertura de teste do frontend é fina** (10 testes, 3 arquivos) — o backend
   está bem coberto; o frontend não. Candidato a reforço.
3. **Deploy do frontend é manual** (build + rsync) — risco de drift entre app e
   `main`. Backlog: GitHub Action `build + deploy` no push de `main`.
4. **Produção sem município real** — só o tenant smoke. Para uso real falta
   provisionar o município, importar base e criar usuários reais.
5. **Sem observabilidade** (Sentry/métricas) e sem rotina de backup documentada
   do `arminda_prod`.
6. **Timestamps de commit de 30/05** (relógio atrasado) permanecem no histórico
   já publicado — apenas cosmético; conteúdo corrigido.
7. **Bundle do frontend > 500 KB** (aviso do Vite) — code-splitting adicional é
   possível, sem urgência.

## 9. Próximos passos recomendados

- **Fechar o Bloco 2:** Onda 2.7 (paridade Fiorilli) quando houver dados de
  referência — ou montar o arcabouço de paridade com casos sintéticos.
- **Ou avançar para o Bloco 3** (13º, férias, rescisão), que reaproveita o
  engine reforçado (bases automáticas + incidências) — não depende de dado
  externo e tem alto valor.
- **Endurecimento de produção** (paralelo): observabilidade, backup, CI/CD de
  frontend, provisionamento de município real.
