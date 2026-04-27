# Bloco 0 — Resumo da entrega

> Snapshot do que foi entregue na fundação do projeto.

## Status

✅ **Concluído.** Repositório pronto para `git push` e início do Bloco 1.

## O que foi entregue

### Documentação fundacional
- `README.md` — porta de entrada, contexto, setup, documentação
- `docs/ROADMAP.md` — 7 blocos com critério de aceitação
- `docs/ARCHITECTURE.md` — visão técnica + DSL de rubricas
- `docs/CONTRIBUTING.md` — Conventional Commits, branches, PRs
- `docs/adr/0001-monorepo.md` — decisão sobre estrutura de repo
- `docs/adr/0002-django-backend.md` — decisão sobre Django + DRF
- `docs/adr/0003-vite-react-frontend.md` — decisão sobre Vite + React
- `docs/adr/0004-multi-tenant-schema.md` — decisão sobre isolamento por schema

### Infraestrutura local
- `docker-compose.yml` — Postgres 16 + Redis 7 com healthchecks
- `.env.example` — template de variáveis
- `.editorconfig` — padronização de editores
- `.gitignore` — Python + Node + IDEs + dados sensíveis
- `scripts/setup.sh` — automação de setup local

### Backend Django
- Estrutura `backend/arminda/` com settings split (base/dev/prod)
- 4 apps esqueletadas: `core`, `people`, `payroll`, `reports`
- Endpoint `/health/` operacional
- OpenAPI (Swagger UI em `/api/docs/`, Redoc em `/api/redoc/`)
- Smoke test passando ✓
- Ruff: lint + format passando ✓
- `requirements.txt`: Django 5.1, DRF, Celery, django-tenants, simple-history, pytest

### Frontend Vite + React
- Vite 6 + React 18 + TypeScript 5
- Tailwind 3 + tokens CSS shadcn-ready
- TanStack Query + React Router 7 + axios
- 3 páginas: Home, Health (testa conexão com backend), 404
- Vitest + Testing Library configurados
- ESLint flat config + Prettier
- Proxy `/api → :8000` em dev

### CI (GitHub Actions)
- `backend-ci.yml` — ruff + django check + pytest com Postgres e Redis
- `frontend-ci.yml` — eslint + prettier + tsc + vitest + build
- `pull_request_template.md`

## Como usar

### 1. Clonar e configurar

```bash
git clone https://github.com/darlanvelozo/Arminda_Software.git
cd Arminda_Software
cp .env.example .env
```

### 2. Setup automático

```bash
./scripts/setup.sh
```

### 3. Ou setup manual

**Backend:**
```bash
docker compose up -d
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Validações realizadas

- ✓ `python manage.py check` sem warnings
- ✓ `ruff check` e `ruff format --check` verdes
- ✓ Smoke test (`tests/test_smoke.py`) passando
- ✓ Endpoint `/health/` retorna `{"status": "ok", "service": "arminda"}`
- ✓ Estrutura sintaticamente válida em todos os arquivos Python
- ✓ Configuração TypeScript / Vite / Tailwind coerente

## Próximo bloco

**Bloco 1 — Fundação multi-tenant e cadastros (meses 1–2)**

Escopo: ativar `django-tenants`, modelar `Tenant`, `Servidor`, `Cargo`, `Lotação`, `VínculoFuncional`, `Rubrica` (esqueleto), implementar JWT auth + RBAC, importador v1 do Firebird → PostgreSQL, telas iniciais de cadastro.

Ver `docs/ROADMAP.md` para detalhes.
