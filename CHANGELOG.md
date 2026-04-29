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

### Bloco 1.1 — Fundação técnica (multi-tenant + auth + RBAC) · 2026-04-29

> ⚠ **BREAKING.** O schema do banco foi reestruturado de zero. A DB de dev precisa ser recriada (drop & migrate). Nenhum dado de Bloco 0 é compatível.

#### Adicionado

- **feat(core):** `User` customizado com identificação por e-mail (ADR-0005).
  - **Por quê:** produto SaaS B2G — `username` separado é UX ruim; e-mail unique é a chave natural. Trocar `AUTH_USER_MODEL` depois de produção é doloroso, então decidimos antes do primeiro dado real.
  - **Arquivos:** `apps/core/models.py`, `apps/core/admin.py`, `arminda/settings/base.py`.
  - **Impacto:** `createsuperuser` agora pede `email`+`password`. Todo código que referencia User deve usar `get_user_model()`.

- **feat(core):** Multi-tenant ativo via `django-tenants` por schema PostgreSQL (ADR-0006, refina ADR-0004).
  - `Municipio` herda `TenantMixin`, com `auto_create_schema=True` e `auto_drop_schema=False`.
  - `Domain` (DomainMixin) para roteamento por hostname em prod.
  - `SHARED_APPS` no schema `public` (core, auth, sessions, admin, DRF, JWT, OpenAPI).
  - `TENANT_APPS` no schema do município (people, payroll, reports, simple_history).
  - `ENGINE = django_tenants.postgresql_backend`.
  - **Models tenant sem FK redundante para `Municipio`** — isolamento real via `search_path`.
  - **Por quê:** ADR-0004 fixou a estratégia; Bloco 0 deixou o pacote inativo. Sem essa ativação, todas as features futuras seriam comprometidas.
  - **Arquivos:** `apps/core/models.py`, `apps/people/models.py`, `apps/payroll/models.py`, `apps/reports/models.py`, `arminda/settings/base.py`.

- **feat(core):** Middleware `TenantHeaderOrHostMiddleware` com fallback header `X-Tenant` → hostname.
  - Lista pública (`/admin/`, `/health/`, `/status/`, `/api/auth/*`, `/api/schema/`, `/api/docs/`, `/api/redoc/`, `/static/`, `/media/`) roda no schema `public`; tudo o mais exige tenant.
  - Erro 400 com `code=TENANT_NAO_ENCONTRADO` se header inválido.
  - **Arquivos:** `apps/core/middleware/tenant.py`.

- **feat(core):** Modelo de RBAC `UsuarioMunicipioPapel` (User × Município × Group) — ADR-0007.
  - 5 papéis-base seedados via data migration: `staff_arminda`, `admin_municipio`, `rh_municipio`, `financeiro_municipio`, `leitura_municipio`.
  - **Permissions DRF base** em `apps/core/permissions.py`: `IsStaffArminda`, `IsAdminMunicipio`, `IsRHMunicipio`, `IsFinanceiroMunicipio`, `IsLeituraMunicipio`. `staff_arminda` é override global cross-tenant.
  - **Arquivos:** `apps/core/models.py` (UsuarioMunicipioPapel), `apps/core/migrations/0002_seed_grupos_papeis.py`, `apps/core/permissions.py`.

- **feat(auth):** Autenticação JWT com `djangorestframework-simplejwt` (ADR-0007).
  - Endpoints públicos: `POST /api/auth/login/`, `POST /api/auth/refresh/`, `POST /api/auth/logout/`, `GET /api/auth/me/`.
  - Access TTL 30 min, refresh TTL 7 dias, com `ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION`.
  - Claim customizada `municipios` no access token (lista de `{schema, papel}`).
  - `ArmindaTokenObtainPairSerializer` enriquece resposta de login com dados do user.
  - **Arquivos:** `apps/core/auth/{serializers,views,urls}.py`, `arminda/settings/base.py` (SIMPLE_JWT).

- **feat(audit):** `simple-history` ativo nos models críticos do tenant (`Cargo`, `Lotacao`, `Servidor`, `VinculoFuncional`).
  - `HistoryRequestMiddleware` capturando o autor de cada mudança.
  - **Arquivos:** `apps/people/models.py`, `apps/people/admin.py` (SimpleHistoryAdmin), `arminda/settings/base.py` (middleware).

- **feat(ops):** Management commands.
  - `criar_municipio`: cria tenant + Domain, dispara `auto_create_schema`.
  - `listar_tenants`: lista municípios cadastrados.
  - **Arquivos:** `apps/core/management/commands/*`.

- **test:** Suíte multi-tenant completa.
  - Fixtures session-scoped: `tenant_a`, `tenant_b` em `backend/conftest.py`.
  - Fixtures function-scoped: `usuario_factory`, `usuario_admin_a`, `usuario_rh_a`, `usuario_leitura_a`, `usuario_staff_arminda`, `api_client`, `api_client_factory`, `in_tenant` (context manager).
  - **48 testes passando**, **95% de cobertura geral** (>90% em todo módulo de domínio do Bloco 1.1).
  - Cobre: User, isolamento por schema, middleware, JWT (login/refresh/logout/me/claims), RBAC (todas as combinações de papel), simple-history (create/update/delete), management commands.

- **docs:** ADR-0005 (User), ADR-0006 (Multi-tenant impl), ADR-0007 (JWT + RBAC), `docs/BLOCO_1.1_RESUMO.md`, `docs/MULTI_TENANT_PLAYBOOK.md`.

#### Modificado

- **⚠ BREAKING refactor(models):** removido FK `municipio = ForeignKey(...)` de TODOS os models tenant (`Cargo`, `Lotacao`, `Servidor`, `VinculoFuncional`, `Dependente`, `Documento`, `Rubrica`, `Folha`, `Lancamento`, `RelatorioGerado`).
  - **Por quê:** `django-tenants` já isola por schema; FK redundante criaria possibilidade de cross-tenant por bug.
  - **Impacto:** unique constraints simplificadas — `unique_together = [("municipio", "codigo")]` virou `unique=True` em `codigo` (escopo do schema).

- **chore(migrations):** todas as migrations 0001 dos apps `core`, `people`, `payroll`, `reports` foram **deletadas e regeneradas**. Nenhum dado de Bloco 0 é recuperável.
  - **Por quê:** trocar `AUTH_USER_MODEL` + ativar `django-tenants` exige regeneração total das migrations.
  - **Como aplicar (dev):** drop DB → recreate → `python manage.py migrate_schemas --shared` → `python manage.py criar_municipio --schema=...`.

- **chore(deps):** `django-tenants`, `simple_history`, `rest_framework_simplejwt`, `rest_framework_simplejwt.token_blacklist` ativos em `INSTALLED_APPS` (estavam comentados no Bloco 0).

- **refactor(choices):** todas as `choices` de string foram migradas para `models.TextChoices` em `apps/people` e `apps/payroll`.

#### Removido

- **chore:** referências a `municipio` em `admin.py` de `people`/`payroll`/`reports` (não existe mais).

#### Validações realizadas

- `python manage.py check` — sem warnings.
- `python manage.py migrate_schemas --shared` — verde, public schema com 16 tabelas SHARED.
- `python manage.py criar_municipio` em 2 tenants reais (mun_sao_raimundo, mun_teresina) — schemas criados, 16 tabelas TENANT em cada.
- `pytest` — **48/48 passando** em ~22s.
- `pytest --cov` — **95% de cobertura** geral; ≥ 90% em todos os módulos de domínio.
- `ruff format` + `ruff check` — verdes.

#### Próximos passos

- **Bloco 1.2** — CRUDs de domínio (servidor, cargo, lotação, vínculo, rubrica esqueleto), serializers, viewsets com permissions, services (admissão, desligamento, transferência).
- Criar usuários reais para os 2 municípios via management command (`criar_usuario` ou seed).
- Migrar geração de tipos TS do OpenAPI para o frontend (ADR-0008, no Bloco 1.3).

---

### Documentação

- **2026-04-28 · docs:** sistema de contexto distribuído implantado.
  - **Por quê:** garantir rastreabilidade, padronização e que nenhuma implementação ocorra sem contexto, conforme política do projeto.
  - **Arquivos:** `CONTEXT.md`, `CHANGELOG.md`, `backend/CONTEXT.md`, `backend/CONTEXT_MODELS.md`, `backend/CONTEXT_SERVICES.md`, `backend/apps/CONTEXT.md`, `frontend/CONTEXT.md`, `frontend/src/pages/CONTEXT.md`, `frontend/src/components/CONTEXT.md`.
  - **Impacto:** toda alteração futura deve consultar o `CONTEXT.md` pertinente antes e atualizar o `CHANGELOG.md` depois. Não é regressão; é processo novo.

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
