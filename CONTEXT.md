# CONTEXT.md — Contexto Global do Arminda

> **Documento mestre.** Toda implementação deve começar pela leitura deste arquivo.
> Última atualização: 2026-04-28 · Bloco corrente: **Bloco 0 → Bloco 1**

---

## 1. O que é o Arminda

**Arminda** é um SaaS multi-tenant de **folha de pagamento e gestão de pessoal para prefeituras brasileiras**. Substitui sistemas legados (Fiorilli SIP e similares) com paridade funcional (motor de cálculo, obrigações legais) e diferenciação em UX, mobile, BI, IA e WhatsApp.

**Cliente-alvo:** prefeituras de pequeno e médio porte (até ~16k servidores). Piloto previsto: município no MA.

**Princípios do produto:**
1. Paridade legal antes de diferenciação. Sem cálculo correto, qualquer "feature moderna" é teatro.
2. Risco crescente. Construir o crítico-simples antes do não-crítico-complexo.
3. Cada bloco do roadmap tem critério de aceitação objetivo.
4. Validação em mundo real é gate de qualidade (Bloco 6).

Ver detalhes em [docs/ROADMAP.md](docs/ROADMAP.md) e [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 2. Stack e arquitetura

### Backend
- **Python 3.12 + Django 5.1 + Django REST Framework**
- **PostgreSQL 16** com isolamento multi-tenant por schema (`django-tenants`)
- **Redis 7 + Celery** para cálculo assíncrono (folha não pode bloquear request HTTP)
- **JWT** para autenticação (`djangorestframework-simplejwt`)
- **simple-history** para auditoria de escritas
- **drf-spectacular** para OpenAPI/Swagger
- **pytest + pytest-django** para testes; **ruff** para lint+format

### Frontend
- **Vite 6 + React 18 + TypeScript 5**
- **TailwindCSS 3** + tokens CSS shadcn-ready
- **shadcn/ui** (componentes copiáveis, sem lock-in)
- **TanStack Query** para estado de servidor
- **React Router 7** para rotas
- **axios** para HTTP, **zod** para validação
- **vitest + testing-library** para testes; **eslint + prettier** para qualidade

### Infraestrutura
- **Docker Compose** (Postgres + Redis em dev local)
- **GitHub Actions** para CI (backend + frontend + status-page)
- Deploy alvo: Railway/Fly.io em staging; AWS/RDS em produção (decisão final no fim do Bloco 5)

### Diagrama de alto nível

```
React SPA  ──HTTPS──▶  Django + DRF  ──▶  PostgreSQL (schemas por município)
                            │
                            └──▶  Redis ──▶  Celery workers
```

---

## 3. Estrutura do repositório

```
Arminda_Software/
├── CONTEXT.md                  ← este arquivo (mestre)
├── CHANGELOG.md                ← memória do projeto (toda alteração registrada)
├── README.md                   ← porta de entrada
├── docker-compose.yml          ← infra dev
├── .env.example                ← template de variáveis
├── .github/workflows/          ← CI
├── backend/
│   ├── CONTEXT.md              ← regras de backend
│   ├── CONTEXT_MODELS.md       ← regras de modelagem
│   ├── CONTEXT_SERVICES.md     ← regras da camada de services
│   ├── arminda/                ← config Django (settings/urls/wsgi)
│   ├── apps/
│   │   ├── CONTEXT.md          ← estrutura padrão de app Django
│   │   ├── core/               ← Tenant, auth, RBAC, modelo base
│   │   ├── people/             ← Servidor, Cargo, Lotação, Vínculo
│   │   ├── payroll/            ← Rubrica, Folha, Lançamento (DSL no Bloco 2)
│   │   └── reports/            ← Relatórios e exportações
│   └── tests/                  ← testes globais e fixtures
├── frontend/
│   ├── CONTEXT.md              ← regras de frontend
│   └── src/
│       ├── components/         ← componentes reutilizáveis
│       │   └── CONTEXT.md
│       ├── pages/              ← páginas (rotas)
│       │   └── CONTEXT.md
│       ├── lib/                ← utilitários (api.ts, utils.ts)
│       ├── styles/             ← globals.css (tokens Tailwind/shadcn)
│       └── test/               ← setup e testes globais
├── docs/
│   ├── ROADMAP.md              ← plano em 7 blocos
│   ├── ARCHITECTURE.md         ← arquitetura técnica
│   ├── CONTRIBUTING.md         ← convenções de PR/commit/branch
│   ├── adr/                    ← Architecture Decision Records
│   └── relatorios/             ← entregáveis quinzenais
├── status-page/                ← painel público de progresso
└── scripts/                    ← setup.sh e utilitários
```

---

## 4. Sistema de contexto — como funciona

> O Arminda usa um sistema de **contexto distribuído**. Cada parte do sistema tem regras escritas. Toda implementação deve ler o contexto pertinente **antes** de tocar em código.

### Hierarquia de contextos

```
CONTEXT.md (raiz, este arquivo) ............ visão de produto e regras gerais
   ├── backend/CONTEXT.md ..................... regras Python/Django/DRF
   │   ├── backend/CONTEXT_MODELS.md ............ camada de models
   │   ├── backend/CONTEXT_SERVICES.md .......... camada de services
   │   └── backend/apps/CONTEXT.md .............. estrutura interna de cada app
   └── frontend/CONTEXT.md .................... regras React/TS/Tailwind
       ├── frontend/src/components/CONTEXT.md ... componentes
       └── frontend/src/pages/CONTEXT.md ........ páginas
```

### Regra de leitura obrigatória

Antes de qualquer alteração:

1. **Ler `CONTEXT.md` (raiz)** sempre.
2. **Ler o `CONTEXT.md` do escopo** (ex: mexer em backend → ler `backend/CONTEXT.md`).
3. **Ler o `CONTEXT.md` específico** se for arquivo crítico:
   - Mexendo em `models.py` → `backend/CONTEXT_MODELS.md`
   - Criando regra de negócio → `backend/CONTEXT_SERVICES.md`
   - Criando componente → `frontend/src/components/CONTEXT.md`
   - Criando página → `frontend/src/pages/CONTEXT.md`

### Regra de escrita obrigatória

Após qualquer alteração relevante:

1. **Atualizar `CHANGELOG.md`** com a entrada estruturada.
2. **Atualizar o `CONTEXT.md` pertinente** se a alteração mudou padrão, regra ou estrutura.
3. **Criar/atualizar ADR** se a decisão for difícil de reverter ou influencia futuras decisões (ver `docs/CONTRIBUTING.md`).

---

## 5. Padrões e convenções (resumo)

> Detalhes em cada `CONTEXT.md` específico. Aqui só o que é transversal.

### Idioma
- **Documentação, mensagens de UI, commits, comentários:** português.
- **Código (variáveis, classes, funções, branches):** inglês.
  - Exceção: domínio brasileiro intraduzível (ex: `Servidor`, `Lotacao`, `cpf`, `pis_pasep`) fica em português — já adotado nos models.
- **Nomes de campos no banco:** seguir o que já existe em `apps/people/models.py` (mistura: `nome`, `data_nascimento`, mas relações em inglês via `related_name="vinculos"`). **Manter consistência com o que já está.**

### Versionamento Git
- Conventional Commits em português imperativo: `feat(payroll): adiciona cálculo de INSS`
- Branches: `feature/`, `fix/`, `chore/`, `docs/`, `refactor/`, `test/`
- PRs sempre para `develop`. `main` é sagrada. Ver `docs/CONTRIBUTING.md`.

### Testes
- Backend: cobertura mínima **80%** em regras de domínio (`apps/people`, `apps/payroll`, `apps/reports`).
- Frontend: cobertura de **componentes críticos** e hooks de domínio.
- **Bug fix sem teste de regressão é proibido.** Cada fix traz teste que reproduz o bug.

### Segurança
- Sem `eval`, sem `exec`, sem string concatenation em SQL.
- Dados sensíveis (CPF, conta bancária) sempre criptografados em rest (a partir do Bloco 1).
- Multi-tenant: middleware do `django-tenants` rejeita requests sem tenant resolvido.
- Logs de auditoria via `simple-history` em toda escrita relevante (a partir do Bloco 1).

### LGPD
- Dados de teste: sempre Faker. **Nunca** commit de bases reais.
- Bases reais do Fiorilli vivem **fora do repo**, em volume Docker ou pasta ignorada.
- Toda exportação de dados pessoais deve passar por log auditado.

---

## 6. Decisões técnicas registradas (ADRs)

Decisões formais ficam em `docs/adr/`. Resumo do já decidido:

| ADR | Decisão | Status |
|-----|---------|--------|
| [0001](docs/adr/0001-monorepo.md) | Monorepo (backend + frontend juntos) | Aceito |
| [0002](docs/adr/0002-django-backend.md) | Django + DRF para backend | Aceito |
| [0003](docs/adr/0003-vite-react-frontend.md) | Vite + React + TS + Tailwind para frontend | Aceito |
| [0004](docs/adr/0004-multi-tenant-schema.md) | Multi-tenant por schema PostgreSQL via `django-tenants` | Aceito |

**Quando criar ADR:** sempre que a decisão **influencia futuras decisões** ou **é difícil de reverter**.

---

## 7. Roadmap — onde estamos

Plano completo em [docs/ROADMAP.md](docs/ROADMAP.md). Snapshot:

| Bloco | Tema | Status |
|-------|------|--------|
| 0 | Estrutura inicial | ✅ Concluído |
| 1 | Multi-tenant + cadastros + JWT/RBAC + importador Firebird | 🟡 Próximo |
| 2 | Engine de cálculo + DSL de rubricas | ⏳ |
| 3 | Folhas especiais (13º, férias, rescisão) | ⏳ |
| 4 | Obrigações legais federais (eSocial, SEFIP, RAIS, DIRF) | ⏳ |
| 5 | Integração TCE | ⏳ |
| 6 | MVP piloto em produção (gate crítico) | ⏳ |
| 7 | Diferenciação (PWA, WhatsApp, BI, IA) | ⏳ |

---

## 8. O que NÃO pode ser feito

- ❌ Lógica de negócio em views/viewsets (vai para `services/`).
- ❌ Query sem filtro de tenant em código que roda em contexto multi-tenant.
- ❌ Comparação de igualdade direta com `Decimal` sem `quantize` (use comparações com tolerância onde fizer sentido em domínio financeiro — mas valores armazenados são sempre `quantize`-ados).
- ❌ `eval`, `exec`, ou qualquer execução de string como código (DSL de rubricas tem sandbox próprio — Bloco 2).
- ❌ Commit de `.env` real, dump de banco real, base do Fiorilli, dados de produção.
- ❌ `--no-verify` em commits, force-push em `main`/`develop`.
- ❌ Criar componente shadcn/ui manualmente; usar a CLI `npx shadcn@latest add <componente>`.
- ❌ Imports relativos profundos (`../../../`); usar alias `@/` no frontend e absolute imports no backend.

## 9. O que SEMPRE deve ser feito

- ✅ Ler `CONTEXT.md` pertinente **antes** de implementar.
- ✅ Registrar mudança em `CHANGELOG.md` **depois** de implementar.
- ✅ Atualizar o `CONTEXT.md` pertinente quando o padrão muda.
- ✅ Escrever teste para todo fix e toda feature de domínio.
- ✅ Rodar `ruff check . && ruff format --check .` (backend) ou `npm run lint && npm run format:check` (frontend) antes de commitar.
- ✅ Tipar (Python type hints / TypeScript strict) em código de domínio.
- ✅ Usar `select_related`/`prefetch_related` em querysets que atravessam ForeignKey.

---

## 10. Em caso de erro / bug

Procedimento padrão:

1. Reproduzir localmente. Se não reproduz, escrever teste que reproduz.
2. Consultar `CHANGELOG.md` — o que mudou recentemente nessa área?
3. Consultar o `CONTEXT.md` específico — alguma regra foi violada?
4. Corrigir, escrever teste de regressão, atualizar `CHANGELOG.md`.
5. Se a causa raiz é falta de regra, **adicionar a regra** no `CONTEXT.md` correspondente.

---

## 11. Mudanças neste documento

Este arquivo é vivo. Toda alteração relevante de produto, stack, arquitetura ou padrão deve ser refletida aqui. Mudanças significativas geram entrada no `CHANGELOG.md`.
