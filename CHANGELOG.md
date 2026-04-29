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

### Bloco 1.3 — Onda 1.3a: Frontend autenticado · 2026-04-29

> Primeira fatia do frontend autenticado. O esqueleto de login, layout
> e troca de tenant está pronto. Telas de domínio (Servidor, Cargo,
> Lotação, Rubrica) entram na Onda 1.3b.

#### Adicionado

- **feat(frontend):** Geração automática de tipos OpenAPI via
  `openapi-typescript` (ADR-0008).
  - `npm run gen:types` lê `/api/schema/?format=json` do backend
    rodando em `:8000` e escreve `src/types/api.ts`.
  - `npm run gen:types:offline` lê do snapshot `openapi-schema.json`
    commitado.
  - `src/types/index.ts` faz aliases legíveis: `Servidor`,
    `CargoWrite`, `AdmissaoInput`, `LoginResponse`, etc.
  - Tipos manuais à mão são proibidos em código novo a partir desta
    ADR (com exceções documentadas para `UserMe` e
    `HistoricoServidorEntry`, onde drf-spectacular não tipa o
    response — TODO: adicionar `@extend_schema` no backend).

- **feat(frontend/auth):** Camada completa de autenticação JWT.
  - `src/lib/auth-storage.ts` — wrappers de localStorage para tokens
    e tenant ativo.
  - `src/lib/auth.ts` — `login()`, `logout()`, `fetchMe()`.
  - `src/lib/auth-context.tsx` — `<AuthProvider>` + `useAuth()` hook
    com `user`, `activeTenant`, `papelAtual`, `switchTenant`.
  - `src/lib/api.ts` reescrito: interceptor de request injeta
    `Authorization: Bearer <access>` + `X-Tenant: <schema>`;
    interceptor de response tenta refresh em 401 (com lock para evitar
    múltiplas chamadas concorrentes), redireciona para `/login` se
    refresh falhar.

- **feat(frontend/components):** 11 primitivos shadcn/ui adicionados
  via `npx shadcn add` (button, input, label, card, dropdown-menu,
  sheet, separator, avatar, skeleton, sonner, form). Versionados em
  `src/components/ui/`.

- **feat(frontend/layout):** AppShell + Sidebar + Topbar.
  - `Sidebar` com 6 itens (Dashboard, Servidores, Cargos, Lotações,
    Rubricas, Relatórios) — esconde abaixo de `lg`.
  - `Topbar` com seletor de município (dropdown se >1, label estático
    se 1) + dropdown de perfil com logout.
  - Trocar de município chama `queryClient.clear()` para evitar
    vazamento de cache entre tenants.

- **feat(frontend/pages):**
  - `LoginPage` (`/login`) — formulário com validação HTML5,
    mensagens de erro com `code` do backend, redireciona pós-login.
  - `SelecionarMunicipioPage` (`/selecionar-municipio`) — escolha de
    tenant para usuários com 2+ municípios.
  - `DashboardPage` (`/`) — placeholder com cards de atalhos.
  - `EmConstrucaoPage` — placeholder reutilizado em
    `/servidores`, `/cargos`, `/lotacoes`, `/rubricas`, `/relatorios`.
  - `<RequireAuth>` wrapper para rotas autenticadas.

- **test(frontend):** 8 testes novos.
  - `auth-storage.test.ts` (5): tokens round-trip, tenant ativo,
    clear total, comportamento sem storage.
  - `LoginPage.test.tsx` (3): render, submit chama `login()` com
    payload correto, mensagem de erro aparece em falha.
  - `test/utils.tsx` com helpers `renderWithProviders` e
    `renderWithAuth`.

#### Modificado

- **chore(frontend/deps):** instalado `openapi-typescript` (dev),
  `@testing-library/user-event` (dev). 11 primitivos shadcn trazem
  Radix + sonner + react-hook-form + next-themes.
- **chore(frontend):** `main.tsx` envolve `<App />` em `<AuthProvider>`
  + `<Toaster>` (sonner). `App.tsx` reescrito com rotas autenticadas.
- **chore(.gitignore):** já incluía `*.tsbuildinfo` (commit anterior).

#### Validações

- `npx tsc --noEmit` — limpo.
- `npm run lint` — 3 warnings (fast-refresh em arquivos shadcn padrão
  e em `auth-context.tsx` que exporta hook + provider — aceitável).
- `npm run format` — verde.
- `npm run build` — 451 KB / 141 KB gzip.
- `npm test` — **10/10 passando** (5 storage + 3 login + 2 HomePage
  legado).
- Backend: 193 testes mantidos verdes, 97% cobertura.

#### Próximos passos

- **Onda 1.3b** (~1 sem): Servidor (lista + detalhe + admissão),
  Cargo CRUD, Lotação CRUD, Rubrica esqueleto.
  Hooks de API tipados consumindo `components["schemas"][...]`.
  Endpoint `@extend_schema` no backend para tipar `UserMe` e
  `HistoricoServidorEntry` (eliminar tipagem manual).
- Adicionar `@extend_schema` no `MeView` para que o `gen:types` tipe
  o response de `/api/auth/me/`.

---

### Bloco 1.2 — Onda 3 (hotfix): admin do Django + cobertura HTML · 2026-04-29

> ⚠ Bug identificado por **navegação manual do usuário** que minha
> bateria automatizada anterior não pegou. Documentando aqui com
> transparência sobre o gap.

#### Fix

- **fix(core/middleware):** `TenantHeaderOrHostMiddleware` parou de
  setar `request.tenant = None` em rotas públicas. Agora o atributo
  simplesmente **não é definido** quando estamos no schema `public`.
  - **Sintoma:** `GET /admin/` retornava HTTP 500 com
    `AttributeError: 'NoneType' object has no attribute 'schema_name'`
    em `django_tenants/templatetags/tenant.py:61` (template tag
    `is_public_schema`, usada pelo template do admin via
    `{% load tenant %}`).
  - **Causa:** a template tag faz `hasattr(request, 'tenant')` antes
    de acessar `.schema_name`. Atributo presente porém None passa pelo
    `hasattr` e quebra na linha seguinte.
  - **Fix:** não setar o atributo. `hasattr(...)` retorna False; a
    template tag interpreta como "schema public" — o que está correto.
  - **Arquivo:** `apps/core/middleware/tenant.py`.
  - **Impacto:** `/admin/` e demais rotas públicas voltam a renderizar
    normalmente. Endpoints API (`/api/people/...`) seguem inalterados:
    o middleware continua setando `request.tenant` quando o header
    `X-Tenant` é resolvido.

#### Adicionado (cobertura)

- **test(core):** `apps/core/tests/test_admin_smoke.py` — 12 testes
  novos cobrindo:
  - 8 páginas do admin do Django (`/admin/`, `/admin/login/`,
    `/admin/auth/group/`, `/admin/core/{user,municipio,domain,
    usuariomunicipiopapel,configuracaoglobal}/`).
  - 3 páginas do drf-spectacular (`/api/schema/`, `/api/docs/`,
    `/api/redoc/`).
  - 1 teste explicito do invariante "request.tenant não existe em
    rota pública" para evitar regressão.
  - **Por que faltava:** minha bateria anterior usava `APIClient` do
    DRF para testar JSON. Templates HTML do admin (que carregam
    `{% load tenant %}` do `django-tenants`) **nunca eram renderizados
    durante os testes**. Bug histórico ficou invisível até o usuário
    abrir o `/admin/` no browser.

#### Validações

- `pytest` — **193/193 passando** em ~39s (12 novos sobre 181 anteriores).
- `pytest --cov` — **97% de cobertura** mantida.
- `ruff format` + `ruff check` — verdes.
- `python manage.py check` — sem warnings.
- Smoke manual via curl: 11 páginas (admin + swagger + redoc + schema)
  todas retornam 200/302 sem mensagem de erro no body.

---

### Bloco 1.2 — Onda 3: Services + Rubrica + criar_usuario · 2026-04-29

> Camada de services (regras de negócio) finalmente entra em ação:
> admissão, desligamento e transferência saem do `serializer.save()`
> ingênuo e passam a executar invariantes de domínio em transação atômica.
> Bloco 1.2 está agora 75% completo (Ondas 1+2+3 de 4).

#### Adicionado

- **feat(people/services):** Camada de regras de negócio em
  `apps/people/services/`.
  - `exceptions.py` com `DomainError`, `AdmissaoInvalidaError`,
    `DesligamentoInvalidoError`, `TransferenciaInvalidaError`. Cada uma
    carrega `code` estável.
  - `admissao.admitir_servidor(DadosAdmissao)` — cria Servidor +
    VinculoFuncional em uma transação atômica, com 13 invariantes
    validadas.
  - `desligamento.desligar_servidor(DadosDesligamento)` — encerra todos
    os vínculos ativos + marca servidor inativo. 5 codes de erro.
  - `transferencia.transferir_lotacao(DadosTransferencia)` — encerra
    vínculo atual e cria novo na nova lotação preservando atributos.
    5 codes de erro.
  - Todos com `@transaction.atomic` + `select_for_update()` onde
    necessário.

- **feat(people/views):** Endpoints `@action` orquestrando services.
  - `POST /api/people/servidores/admitir/`
  - `POST /api/people/servidores/<id>/desligar/`
  - `POST /api/people/vinculos/<id>/transferir/`
  - `_domain_error_to_validation_error()` traduz `DomainError` em
    HTTP 400 com `code` estável.

- **feat(payroll):** CRUD de **Rubrica** (esqueleto — DSL no Bloco 2).
  - Pattern triplo de serializers, `/api/payroll/rubricas/` com filtros
    e busca, RBAC dedicado: leitura aberta, escrita exige
    `IsFinanceiroMunicipio` (RH não cria rubrica).

- **feat(core):** Management command **`criar_usuario`** (resolve gap
  do Bloco 1.1: hoje não tínhamos como atribuir papel via CLI).
  - Cria User + UsuarioMunicipioPapel opcional. Suporta
    `--staff-arminda`, `--superuser`, `--precisa-trocar-senha`.
  - Senha via `--password` ou `--senha-stdin` (evita histórico shell).

- **test:** 55 testes novos.
  - 18 admissão (caminho feliz + cada um dos 15 codes incluindo
    `CPF_INVALIDO` e `PIS_INVALIDO` + atomicidade)
  - 6 desligamento, 6 transferência
  - 8 endpoints @action (HTTP + RBAC + propagação de code)
  - 5 Rubrica CRUD + RBAC + isolamento
  - 12 criar_usuario (cobre todos os flags)

#### Fix

- **fix(people/services):** `admitir_servidor` agora captura
  `django.core.exceptions.ValidationError` de `validar_cpf` e
  `validar_pis_pasep` e re-levanta como `AdmissaoInvalidaError` com
  `code=CPF_INVALIDO` ou `PIS_INVALIDO`. **Antes:** CPF/PIS inválidos
  retornavam HTTP 500. **Detectado em:** smoke E2E manual via curl.
  Cobertura de teste adicionada (`test_cpf_invalido`, `test_pis_invalido`).

#### Validações

- `pytest` — **179/179 passando** em ~36s.
- `pytest --cov` — **97% de cobertura** geral.
- `ruff format` + `ruff check` — verdes.
- `python manage.py check` — sem warnings.

#### Próximos passos

- **Bloco 1.2 — Onda 4** (~2 dias): hardening final, OpenAPI revisado,
  `docs/BLOCO_1.2_RESUMO.md`, validação manual end-to-end.
- **Bloco 1.3** (~2 sem): frontend autenticado consumindo a API.

---

### Bloco 1.2 — Onda 2: CRUD Servidor + Vínculo + Dependente + Documento · 2026-04-29

> Cadastros centrais de RH via API REST. Reaproveita o pattern da Onda 1
> (3 serializers, ViewSet, permissions, filtros, isolamento) e adiciona
> validação de domínio brasileiro, histórico funcional via simple-history
> e upload de arquivos (Documento). **Performance baseline atingida**:
> 100 servidores criados em ~5s (gate ROADMAP era < 30s).

#### Adicionado

- **feat(people):** CRUD de **Servidor**, **VinculoFuncional**,
  **Dependente** e **Documento**.
  - Endpoints: `/api/people/{servidores,vinculos,dependentes,documentos}/`.
  - **3 serializers por modelo** (List/Detail/Write) — pattern.
  - `ServidorDetailSerializer` embute dependentes + vínculos resumidos
    (cargo_nome, lotacao_nome, regime_display) — evita N+1 com
    `prefetch_related`.
  - `VinculoListSerializer` traz resumo do servidor (matricula, nome) e
    cargo (nome) — UX de listagem direta.
  - `DocumentoViewSet` aceita upload via `MultiPartParser` (`arquivo`).

- **feat(people):** Endpoint **GET /api/people/servidores/{id}/historico/**
  consultando `simple_history`. Retorna registros paginados com
  `history_id`, `history_date`, `history_type` (+/~/-),
  `history_user_email` (capturado pelo `HistoryRequestMiddleware`) e
  snapshot dos campos do modelo no momento da mudança.
  - Permission: leitura (`IsLeituraMunicipio`) — qualquer papel pode ver.

- **feat(people):** Validações de domínio nos `Write` serializers.
  - **CPF** (Servidor + Dependente): aceita máscara, normaliza para
    dígitos, valida via `apps.core.validators.validar_cpf`.
  - **PIS/PASEP** (Servidor): opcional; se preenchido, valida e
    normaliza.
  - **Data de nascimento**: não pode ser futura; idade mínima 14 anos.
  - **Carga horária** (Vínculo): entre 1 e 60 horas semanais.
  - **Datas de admissão/demissão** (Vínculo): admissão não futura,
    demissão >= admissão.
  - Códigos (Cargo/Lotação): `upper().strip()`.
  - Erros HTTP 400 com `code` estável (`CPF_INVALIDO`, `PIS_INVALIDO`,
    `DATA_FUTURA`, `IDADE_MINIMA`, etc.).

- **feat(people/filters):** FilterSets para todos os novos viewsets.
  - `ServidorFilter`: filtros por `vinculos__cargo`, `vinculos__lotacao`,
    `vinculos__regime`, `ativo`, `sexo`.
  - `VinculoFilter`: `admitido_apos`/`admitido_ate` (range de datas) +
    servidor/cargo/lotacao/regime/ativo.
  - `DependenteFilter`: servidor, parentesco, ir, salario_familia.
  - `DocumentoFilter`: servidor, tipo.

- **test(people):** 36 testes novos.
  - `test_views_servidor.py` (15): CRUD, RBAC, isolamento, validação CPF,
    PIS, data, idade mínima, matrícula duplicada, histórico via
    `simple-history` (autor capturado pelo middleware).
  - `test_views_vinculo.py` (6): CRUD, validação de carga horária,
    coerência de datas, filtro por servidor.
  - `test_views_dependente_documento.py` (5): CRUD básico, upload de
    arquivo via multipart, leitura por papel.
  - `test_perf.py` (1, marker `@pytest.mark.perf`): **100 servidores
    criados em ~5s**, bem abaixo do gate de 30s.

#### Modificado

- **chore(pytest):** marker `perf` adicionado em `pyproject.toml`. Suíte
  default exclui (`-m "not perf"`); rodar com `pytest -m perf`.

#### Validações realizadas

- `pytest` — **126/126 passando** em ~30s (1 deselected: o teste perf).
- `pytest -m perf` — 1 passando em ~5s (100 servidores via API).
- `pytest --cov` — **96% de cobertura** geral.
- `ruff format` + `ruff check` — verdes.
- `python manage.py check` — sem warnings.

#### Próximos passos

- **Bloco 1.2 — Onda 3** (~4 dias): Services em `apps.people.services/`
  (admissão, desligamento, transferência) + endpoints `@action` para
  fluxos. CRUD de Rubrica esqueleto. Management command
  `criar_usuario` (resolve gap do Bloco 1.1).

---

### Bloco 1.2 — Onda 1: Validators + CRUD Cargo/Lotação · 2026-04-29

> Primeira onda de cadastros via API REST. Valida o pattern (3 serializers,
> ViewSet, permissions por papel, filtros, isolamento) que vai se repetir
> nas ondas 2–4 com Servidor/Vínculo/Dependente/Documento/Rubrica.

#### Adicionado

- **feat(core/validators):** `apps/core/validators.py` com `validar_cpf`,
  `validar_pis_pasep`, `validar_codigo_ibge`. Aceitam string com ou sem
  máscara, retornam dígitos normalizados, levantam `ValidationError` com
  `code` estável (`CPF_INVALIDO`, `PIS_INVALIDO`, `IBGE_INVALIDO`).
  - **Por quê:** dados brasileiros aparecem em vários models (Servidor,
    Dependente, Município) — centralizar evita reimplementação.
  - **Decisão:** ficam **só na fronteira HTTP (serializer)** + camada de
    service. Não em Django field validators (que ignoram retorno e não
    normalizam). Pattern: `def validate_cpf(self, value): return validar_cpf(value)`.
  - 27 testes (`apps/core/tests/test_validators.py`).

- **feat(people):** CRUD de **Cargo** e **Lotação** via API REST.
  - Endpoints: `/api/people/cargos/` e `/api/people/lotacoes/` (GET list,
    POST, GET detail, PATCH, PUT, DELETE).
  - **3 serializers por modelo** (List/Detail/Write) — pattern do
    `backend/apps/CONTEXT.md`.
  - **`_PapelPorAcaoMixin`** em `apps/people/views.py`: leitura exige
    `IsLeituraMunicipio`, escrita exige `IsRHMunicipio`.
  - **FilterSets** (`apps/people/filters.py`): `?codigo=X`, `?nome__icontains=X`,
    `?nivel_escolaridade=X`, `?ativo=true`, `?raiz=true` (Lotação).
  - **Search e ordering** globais via `SearchFilter` + `OrderingFilter`
    adicionados em `REST_FRAMEWORK.DEFAULT_FILTER_BACKENDS`.
  - **Detail enriquecido**: `nivel_escolaridade_display`, `lotacao_pai_nome`.
  - **Validação de ciclo** em LotaçãoWriteSerializer: lotação não pode ser
    pai de si mesma.
  - **Normalização**: `codigo` automaticamente upper + strip.

- **test:** 25 testes HTTP (18 Cargo + 7 Lotação) cobrindo:
  - CRUD completo (list/retrieve/create/update/partial/destroy).
  - RBAC: leitura permite GET, bloqueia POST/PATCH/DELETE; staff_arminda
    passa em qualquer tenant.
  - Isolamento entre tenants (criar em A não aparece em B; mesmo
    `codigo` em A e B é permitido).
  - Filtros (`?nivel_escolaridade=`, `?raiz=true`) e search (`?search=`).
  - Erros: 401 sem auth, 400 sem tenant, 403 sem papel, 400 código vazio
    ou duplicado, 400 ciclo de hierarquia.

#### Modificado

- **chore(settings):** `DEFAULT_FILTER_BACKENDS` ganha `SearchFilter` e
  `OrderingFilter` para ativar `search_fields`/`ordering_fields` nos viewsets.

- **fix(test):** `test_x_tenant_com_codigo_ibge_resolve` e
  `test_x_tenant_inexistente_retorna_400` agora batem em
  `/api/people/cargos/` (era `/api/people/`, que virou root do router).

#### Removido

- **chore(settings):** `backend/arminda/settings/local.py` — incompatível
  com `django-tenants` (multi-tenant exige PostgreSQL; SQLite não tem
  schemas). Bloco 1+ não suporta mais "rodar sem Postgres".

#### Validações realizadas

- `pytest` — **100/100 passando** em ~30s.
- `pytest --cov` — **96% de cobertura** geral.
- `ruff format` + `ruff check` — verdes.
- `python manage.py check` — sem warnings.

#### Próximos passos

- **Bloco 1.2 — Onda 2** (5 dias): CRUD de Servidor + VinculoFuncional
  + Dependente + Documento, com validação de CPF/PIS via
  `apps.core.validators`, endpoint de histórico (`simple_history`),
  perf baseline (100 servidores < 30s).

---

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
