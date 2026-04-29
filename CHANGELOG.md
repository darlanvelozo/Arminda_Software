# CHANGELOG

> Memória do projeto Arminda. Toda alteração relevante deve ter uma entrada aqui.
>
> Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
> com seção adicional **Por quê** (motivação) e **Impacto** (consequências).
>
> Versionamento: ver `docs/ROADMAP.md` — versão minor por bloco entregue.

---

## Como registrar uma mudança

Cada entrada deve responder:

- **O quê** — descrição curta e objetiva da alteração.
- **Por quê** — motivação (referência ao bloco do roadmap, ADR, bug, requisito legal, etc.).
- **Arquivos** — caminhos principais alterados (não precisa exaustivo; aponte os críticos).
- **Impacto** — o que muda para quem? Quebra contrato? Migration? Variável de ambiente nova?
- **Próximos passos** — se a alteração abre frentes ou tem dívida residual.

Categorias permitidas (Conventional Commits):
- **feat** — nova funcionalidade
- **fix** — correção de bug
- **refactor** — mudança sem alterar comportamento
- **chore** — manutenção (deps, build, configs)
- **docs** — documentação
- **test** — testes
- **perf** — performance
- **ci** — pipeline

Mudanças que afetam contrato de API, schema de banco ou semântica de cálculo recebem o marcador **⚠ BREAKING**.

---

## [Não lançado] — em construção

### Documentação

- **2026-04-28 · docs:** sistema de contexto distribuído implantado.
  - **Por quê:** garantir rastreabilidade, padronização e que nenhuma implementação ocorra sem contexto, conforme política do projeto.
  - **Arquivos:** `CONTEXT.md`, `CHANGELOG.md`, `backend/CONTEXT.md`, `backend/CONTEXT_MODELS.md`, `backend/CONTEXT_SERVICES.md`, `backend/apps/CONTEXT.md`, `frontend/CONTEXT.md`, `frontend/src/pages/CONTEXT.md`, `frontend/src/components/CONTEXT.md`.
  - **Impacto:** toda alteração futura deve consultar o `CONTEXT.md` pertinente antes e atualizar o `CHANGELOG.md` depois. Não é regressão; é processo novo.
  - **Próximos passos:** ao iniciar Bloco 1, validar se as regras de modelagem/services estão sendo seguidas no primeiro PR e calibrar.

---

## [0.1.0] — 2026-04-27 — Bloco 0: Estrutura inicial

> Snapshot do que estava entregue antes da implantação do sistema de contexto.
> Detalhes em `docs/BLOCO_0_RESUMO.md`.

### Adicionado

- **feat(repo):** monorepo organizado (`backend/`, `frontend/`, `docs/`, `scripts/`, `status-page/`).
  - **Por quê:** ADR-0001 — versionamento e contexto unificado para dev solo.
- **feat(backend):** esqueleto Django 5.1 com settings split (`base`/`dev`/`prod`).
  - **Apps esqueletadas:** `core`, `people`, `payroll`, `reports`.
  - **Endpoints:** `/health/`, `/status/`, `/api/docs/` (Swagger), `/api/redoc/`.
  - **Models iniciais:** `Municipio`, `Servidor`, `Cargo`, `Lotacao`, `VinculoFuncional`, `Dependente`, `Documento`, `Rubrica`, `Folha`, `Lancamento`, `RelatorioGerado`, `TimeStampedModel` (abstrato), `ConfiguracaoGlobal`.
  - **Por quê:** ADR-0002 — base relacional sólida antes de cálculo.
- **feat(frontend):** Vite 6 + React 18 + TS + Tailwind 3 + shadcn-ready.
  - **Páginas:** `HomePage`, `HealthPage` (consome `/health/` e `/status/`), `NotFoundPage`.
  - **Lib:** `api.ts` (axios), `utils.ts` (`cn` helper).
  - **Por quê:** ADR-0003 — UX moderna como diferencial de produto.
- **feat(infra):** Docker Compose com Postgres 16 e Redis 7 (healthchecks).
- **feat(ci):** GitHub Actions para backend (ruff + check + pytest) e frontend (eslint + prettier + tsc + vitest + build).
- **docs:** `README.md`, `docs/ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/CONTRIBUTING.md`, ADRs 0001–0004.

### Validações

- `python manage.py check` sem warnings.
- `ruff check` e `ruff format --check` verdes.
- Smoke test (`tests/test_smoke.py`) passando.
- `/health/` retornando `{"status": "ok", "service": "arminda"}`.

### Conhecidas (dívida explícita do Bloco 0)

- `django-tenants` ainda comentado em `INSTALLED_APPS` — ativar no Bloco 1.
- `simple-history` ainda comentado — ativar no Bloco 1.
- JWT (`djangorestframework-simplejwt`) presente no `requirements.txt` mas não configurado em `REST_FRAMEWORK` — ativar no Bloco 1.
- `frontend/src/components/` ainda não existe — será criada quando entrar a primeira tela do Bloco 1.
- Não há camada de **services** ainda; será introduzida no primeiro app que precisar de regra de negócio (provavelmente `people` no Bloco 1).

---

## Convenção de versão

| Versão | Marco |
|--------|-------|
| 0.1.0  | Fim do Bloco 0 (estrutura inicial) |
| 0.2.0  | Fim do Bloco 1 (multi-tenant + cadastros) |
| 0.3.0  | Fim do Bloco 2 (engine de cálculo) |
| ...    | um minor por bloco |
| 1.0.0  | Fim do Bloco 6 (piloto em produção, paridade ≥ 99,9%) |

Patches (`0.1.x`, `0.2.x`) cobrem fixes pontuais entre blocos.
