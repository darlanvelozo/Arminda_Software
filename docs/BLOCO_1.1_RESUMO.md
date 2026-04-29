# Bloco 1.1 — Fundação técnica (resumo)

> Snapshot do que foi entregue. Espelho do `BLOCO_0_RESUMO.md`.

## Status

✅ **Concluído** — 2026-04-29.

## Objetivo do sub-bloco

Acertar as três decisões estruturais que destravam o restante do Bloco 1:
1. User customizado (impossível trocar depois).
2. Multi-tenant **ativo** (Bloco 0 deixou comentado).
3. Auth JWT + RBAC, com fixtures de teste para usar nos sub-blocos seguintes.

## O que foi entregue

### Documentação (3 ADRs novas)
- `docs/adr/0005-custom-user.md` — User com login por e-mail
- `docs/adr/0006-multi-tenant-implementacao.md` — refina ADR-0004 com a implementação concreta (sem FK redundante para Município)
- `docs/adr/0007-jwt-rbac.md` — JWT + RBAC escopado por município

### Backend
- **`apps.core.User`** — `AbstractUser` customizado, login por e-mail, sem `username`, com `nome_completo`, `precisa_trocar_senha`. Manager dedicado.
- **`apps.core.Municipio`** com `TenantMixin` (`django-tenants`).
- **`apps.core.Domain`** (DomainMixin) para roteamento por hostname em prod.
- **`apps.core.UsuarioMunicipioPapel`** — RBAC escopado por município.
- **`apps.core.middleware.tenant.TenantHeaderOrHostMiddleware`** — header `X-Tenant` com fallback para hostname.
- **`apps.core.permissions`** — `IsStaffArminda`, `IsAdminMunicipio`, `IsRHMunicipio`, `IsFinanceiroMunicipio`, `IsLeituraMunicipio`. `staff_arminda` é override global.
- **`apps.core.auth`** — endpoints `/api/auth/{login,refresh,logout,me}/` com JWT.
- **`apps.core.management.commands`** — `criar_municipio`, `listar_tenants`.
- **Data migration** `apps/core/migrations/0002_seed_grupos_papeis.py` — seed dos 5 grupos-base.
- **Models tenant refatorados** — `apps/{people,payroll,reports}/models.py` sem FK para `Municipio`. `unique_together` simplificado.
- **`simple_history`** ativo nos models críticos (`Cargo`, `Lotacao`, `Servidor`, `VinculoFuncional`).
- **Settings** com split `SHARED_APPS` / `TENANT_APPS`, engine `django_tenants.postgresql_backend`, `SIMPLE_JWT`, `HistoryRequestMiddleware`.

### Testes
- **`backend/conftest.py`** com fixtures multi-tenant (session: `tenant_a`, `tenant_b`; function: `usuario_factory` + papéis pré-configurados, `api_client`, `api_client_factory`, `in_tenant`).
- **`apps/core/tests/test_user.py`** — 8 testes do User.
- **`apps/core/tests/test_multi_tenant.py`** — 4 testes de isolamento real por schema.
- **`apps/core/tests/test_middleware_tenant.py`** — 6 testes do middleware.
- **`apps/core/tests/test_auth_jwt.py`** — 9 testes (login/refresh/logout/me/claims).
- **`apps/core/tests/test_permissions.py`** — 11 testes de RBAC.
- **`apps/core/tests/test_management_commands.py`** — 5 testes (criar_municipio, listar_tenants).
- **`apps/people/tests/test_history.py`** — 3 testes de simple-history (create/update/delete).
- **`tests/test_smoke.py`** — 2 testes de healthcheck atualizados.

**Total:** 48 testes. **95% de cobertura geral.**

## Validações realizadas

| Check | Resultado |
|-------|-----------|
| `python manage.py check` | ✓ sem warnings |
| `python manage.py makemigrations --dry-run` | ✓ sem migrations pendentes |
| `python manage.py migrate_schemas --shared` | ✓ aplicou todas |
| `python manage.py criar_municipio --schema=mun_sao_raimundo --domain=...` | ✓ schema criado, 16 tabelas TENANT |
| `python manage.py criar_municipio --schema=mun_teresina` | ✓ idem |
| `python manage.py listar_tenants` | ✓ ambos listados |
| `pytest` | ✓ 48/48 passando em ~22s |
| `pytest --cov` | ✓ 95% cobertura |
| `ruff format` | ✓ verde |
| `ruff check` | ✓ verde |
| Cross-tenant isolation (teste programático) | ✓ Servidor criado em A não aparece em B |
| Cross-tenant unique constraints | ✓ Mesmo `Cargo.codigo` em A e B sem conflito |

## Como rodar localmente

### 1. Pré-requisitos
- PostgreSQL 16 rodando (`sudo service postgresql start` em WSL/Linux)
- Role `arminda` com `SUPERUSER` (ou `CREATEDB` + permissão de criar schemas)
- Database `arminda` criada e vazia
- venv em `backend/.venv` com `requirements.txt` instalado

### 2. Configurar `.env` na raiz do repo
```bash
cp .env.example .env
# ajustar se necessario
```

### 3. Criar schemas
```bash
cd backend
.venv/bin/python manage.py migrate_schemas --shared
```

### 4. Criar tenants de teste
```bash
.venv/bin/python manage.py criar_municipio \
  --nome "Sao Raimundo do Doca Bezerra" \
  --uf MA --codigo-ibge 2110005 \
  --schema mun_sao_raimundo \
  --domain mun-sao-raimundo.localhost

.venv/bin/python manage.py criar_municipio \
  --nome "Teresina" --uf PI --codigo-ibge 2211001 \
  --schema mun_teresina
```

### 5. Criar superusuário
```bash
.venv/bin/python manage.py createsuperuser
# pede email + password (NAO username)
```

### 6. Validar
```bash
.venv/bin/python manage.py runserver
# em outro terminal:
curl http://localhost:8000/health/
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"<seu-email>","password":"<sua-senha>"}'
```

### 7. Rodar testes
```bash
.venv/bin/pytest --cov
```

## Decisões e gotchas registrados

- **`auto_drop_schema = False`** em `Municipio` — proteção contra DROP acidental. Para dropar schema em dev: `python manage.py shell` + `municipio.delete()` + manual `DROP SCHEMA`.
- **`staff_arminda`** é Group no `User.groups` (não em `UsuarioMunicipioPapel`) — funciona como override global.
- **`token_blacklist.blacklistedtoken`** vive no schema `public` — refresh tokens são globais ao usuário, não ao tenant.
- **`drf-spectacular`** está em `SHARED_APPS` (Swagger acessível sem tenant).
- **`HistoryRequestMiddleware`** captura o autor automaticamente — services não precisam setar `criado_por`/`atualizado_por` manualmente desde que tenham acesso ao request.

## Próximo sub-bloco

**Bloco 1.2 — Cadastros core via API REST** (estimativa: ~2 semanas).

### Escopo
- Serializers (`List`/`Detail`/`Write`) para Cargo, Lotação, Servidor, Vínculo, Dependente, Documento, Rubrica esqueleto.
- ViewSets com filtros, busca, paginação, permissions corretas.
- `apps/people/services/`: `admitir_servidor`, `desligar_servidor`, `transferir_lotacao`.
- Validações: CPF (algoritmo de dígito), PIS/PASEP, datas coerentes.
- Histórico funcional consultável via endpoint.
- Cobertura ≥ 80% em `apps/people` e `apps/core` (atual já está em 92%+).
- Performance: 100 servidores criados via API < 30s.

Ver [docs/ROADMAP.md](ROADMAP.md) e [CHANGELOG.md](../CHANGELOG.md).
