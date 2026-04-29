# backend/CONTEXT.md — Regras do Backend

> Contexto e regras de implementação do backend Django.
> **Antes de qualquer alteração, consulte também o [`CONTEXT.md`](../CONTEXT.md) raiz.**

---

## 1. Stack e versões fixadas

- **Python 3.12**
- **Django 5.1.4**
- **Django REST Framework 3.15.2**
- **PostgreSQL 16** (driver `psycopg[binary] 3.2.3`)
- **django-tenants 3.7** ✅ ativo desde Bloco 1.1 (multi-tenant por schema)
- **Celery 5.4 + Redis 5.2** (cálculo assíncrono — uso real no Bloco 2)
- **djangorestframework-simplejwt 5.3** ✅ ativo desde Bloco 1.1 (JWT)
- **django-simple-history 3.7** ✅ ativo desde Bloco 1.1 (auditoria)
- **drf-spectacular 0.27** (OpenAPI)
- **ruff 0.8** (lint + format)
- **pytest 8.3 + pytest-django 4.9 + pytest-cov 6 + factory-boy 3.3 + faker 33**

Mudança de versão: **só via PR específico de upgrade**, com nota no `CHANGELOG.md` e teste da suíte.

---

## 2. Arquitetura em camadas

```
┌──────────────────────────────────────────────┐
│ HTTP layer                                   │
│   urls.py → views/viewsets → serializers     │  ← orquestração
├──────────────────────────────────────────────┤
│ Service layer (apps/<app>/services/)         │
│   regras de negócio, transações, validações  │  ← lógica
├──────────────────────────────────────────────┤
│ Domain layer (apps/<app>/models.py)          │
│   modelos, queryset/manager customizados     │  ← dados
├──────────────────────────────────────────────┤
│ Persistence (PostgreSQL via ORM)             │
└──────────────────────────────────────────────┘
```

**Regra de ouro:**
- **Views/viewsets:** parsing de input, autorização, chamada de service, serialização do output. Sem lógica.
- **Services:** toda regra de negócio, qualquer escrita relevante, transações. **Sem Django HTTP** (nada de `request`, `Response`, `HttpResponse` aqui).
- **Models:** estrutura de dados + querysets customizados + métodos triviais derivados (ex: `nome_completo`). **Sem regra de processo** (nada de "envia eSocial" no model).

Detalhamento das camadas:
- Models → [`CONTEXT_MODELS.md`](CONTEXT_MODELS.md)
- Services → [`CONTEXT_SERVICES.md`](CONTEXT_SERVICES.md)
- Estrutura interna de cada app → [`apps/CONTEXT.md`](apps/CONTEXT.md)

---

## 3. Estrutura de pastas

```
backend/
├── arminda/
│   ├── settings/
│   │   ├── base.py            ← config compartilhada
│   │   ├── dev.py             ← override para dev local
│   │   ├── prod.py            ← override para produção
│   │   └── local.py           ← (gitignored) override pessoal opcional
│   ├── urls.py                ← rotas raiz (/admin, /health, /status, /api/*)
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py              ← (a criar no Bloco 2) instância Celery
├── apps/
│   ├── core/                  ← Tenant, auth, RBAC, modelo base
│   ├── people/                ← Servidor, Cargo, Lotação, Vínculo
│   ├── payroll/               ← Rubrica, Folha, Lançamento (DSL no Bloco 2)
│   └── reports/               ← Relatórios e exportações
├── tests/                     ← testes globais e fixtures
├── manage.py
├── requirements.txt
└── pyproject.toml             ← config ruff + pytest + coverage
```

---

## 4. Convenções obrigatórias

### Idioma
- **Comentários, docstrings, mensagens de UI:** português.
- **Código (variáveis, classes, funções, módulos):** inglês.
- **Exceção viva:** termos de domínio brasileiro (`Servidor`, `Lotacao`, `pis_pasep`, `cpf`, `competencia`) ficam em português — já adotado em `apps/people/models.py` e `apps/payroll/models.py`. **Manter consistência com o que já existe.**

### Type hints
- Obrigatórios em **funções públicas** e **métodos de service**.
- Recomendado em métodos de model que retornem algo derivado.
- `from __future__ import annotations` permitido se simplificar imports circulares.

```python
# bom
def calcular_inss(salario: Decimal, competencia: date) -> Decimal: ...

# ruim
def calcular_inss(salario, competencia): ...
```

### Imports
- Ordem (ruff aplica): stdlib → third-party → local.
- **Absolute imports** sempre: `from apps.people.models import Servidor`. Nada de `from .models`.
- Modelos cross-app: importar via `apps.<outroapp>.models`. **Não** usar `apps.get_model` em código de domínio (só em migrations).

### Lint/format
```bash
cd backend
ruff format .          # antes
ruff check . --fix     # depois
ruff check .           # confirma
```
PR não passa sem ruff verde. CI roda automaticamente.

---

## 5. Settings — regras

- **`base.py`** é a única fonte da verdade. `dev.py` e `prod.py` só **estendem**.
- **Toda variável sensível** vem de `.env` via `django-environ`. Nada de string hardcoded.
- Nenhum settings importa de `apps.*` (evita import circular).
- `DJANGO_SETTINGS_MODULE` default em dev: `arminda.settings.dev`.
- Adicionar app nova: editar `LOCAL_APPS` em `base.py` + criar `apps/<nome>/CONTEXT.md` se for grande.

---

## 6. URLs — regras

- Cada app tem seu `urls.py` com `app_name` definido.
- Roteamento raiz só em `arminda/urls.py`, prefixando `/api/<app>/`.
- Endpoints de infraestrutura (`/health/`, `/status/`, `/admin/`, `/api/docs/`, `/api/redoc/`, `/api/schema/`) ficam fora de `/api/<app>/`.
- Naming de URL pattern: `<app>:<recurso>-<acao>` (ex: `people:servidor-list`).

---

## 7. API REST — DRF

### Padrões
- **ViewSets** sempre que houver CRUD; `APIView` só em endpoints especiais (cálculo, importação, exportação).
- **Serializers** dedicados por contexto: `ServidorListSerializer` (lista, campos enxutos), `ServidorDetailSerializer` (detalhe, completo), `ServidorWriteSerializer` (create/update). Não reusar o mesmo serializer em todos os contextos.
- **Permissões** por viewset, não globais. `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` é piso.
- **Filtros** via `django-filter`. Listar campos pesquisáveis em `filterset_fields`.
- **Paginação** padrão (`PageNumberPagination`, `PAGE_SIZE = 25`). Endpoints que retornam lista grande têm que paginar.

### Resposta de erro
- Erros de domínio levantam `ValidationError` (DRF) ou `services.exceptions.<DomainError>` (a definir no Bloco 1).
- Estrutura de resposta de erro em PT-BR sempre que possível: `{"detail": "Servidor não encontrado", "code": "SERVIDOR_NAO_ENCONTRADO"}`.
- 4xx para erros de cliente, 5xx só para falha real do servidor (e o stacktrace **não** vai para o cliente em prod).

### Documentação
- Toda viewset/APIView tem **docstring** descrevendo o endpoint.
- `@extend_schema` (drf-spectacular) usado quando o schema gerado automaticamente não for suficiente.
- Swagger em `/api/docs/`, Redoc em `/api/redoc/`. **Não removê-los.**

---

## 8. Multi-tenant (a partir do Bloco 1)

Decisão registrada em [ADR-0004](../docs/adr/0004-multi-tenant-schema.md).

### Regras
- **Tenant apps** (`people`, `payroll`, `reports`): tabelas vivem nos schemas de cada município.
- **Shared apps** (`core`): tabelas no schema `public` — `Municipio`, `User`, `ConfiguracaoGlobal`, configurações legais nacionais (tabela INSS, IRRF), layouts TCE.
- Toda query em código de domínio roda no contexto do tenant resolvido pelo middleware. **Nunca** queries cross-tenant em código de aplicação.
- Operações administrativas cross-tenant (relatório agregado da plataforma, manutenção) ficam em **management commands** dedicados, com flag explícita.

### Resolução de tenant
- Por **header HTTP** `X-Tenant: <codigo_ibge>` em chamadas de API.
- Por **subdomínio** `<municipio>.arminda.app` em produção.
- Middleware customizado em `apps/core/middleware/tenant.py` (a criar).

### Testes
- Toda suíte que testa tenant app deve montar **pelo menos 2 tenants** e validar isolamento.
- Fixture base em `tests/conftest.py` provê `tenant_a` e `tenant_b`.

---

## 9. Migrations

- Sempre revisar a migration gerada antes de commitar.
- Nomes descritivos: `python manage.py makemigrations people --name adiciona_campo_cbo_em_cargo`.
- **Migrations destrutivas** (drop column, drop table, rename) exigem:
  - Plano de rollback documentado no PR.
  - Backfill em migration **separada** (data migration), não acoplada à structural migration.
  - Aviso no `CHANGELOG.md` com marcador **⚠ BREAKING** se quebra contrato externo.
- Nunca editar migration já aplicada em produção.
- `migrations/0001_initial.py` de cada app já está commitada — referência do Bloco 0.

---

## 10. Celery (a partir do Bloco 2)

- Toda tarefa pesada (cálculo de folha, geração de eSocial, importação) **assíncrona**.
- Tasks em `apps/<app>/tasks.py`.
- Filas separadas por tipo: `payroll`, `esocial`, `reports`, `imports`. Configurar no `celery.py`.
- Tasks são **idempotentes** sempre que possível (mesma input → mesmo output, retry seguro).
- Resultados longos persistem em modelo (`Folha.status`, `RelatorioGerado.arquivo`), não no result backend Redis.

---

## 11. Testes

### Estrutura
```
backend/
├── tests/                        ← testes integrados, smoke, fixtures globais
│   ├── conftest.py               ← fixtures (tenants, usuários, factories)
│   └── test_smoke.py
└── apps/
    └── <app>/
        └── tests/
            ├── test_models.py
            ├── test_services.py
            └── test_views.py     ← integração HTTP
```

### Regras
- **pytest**, não `manage.py test`.
- `factory-boy + faker` para fixtures; **nada hardcoded** em fixture de domínio.
- **Cobertura mínima 80%** em apps de domínio (`people`, `payroll`, `reports`).
- Bug fix sempre vem com teste de regressão.
- Nome de teste: `test_<o_que_testa>_<condicao>_<resultado_esperado>`. Ex: `test_calcular_inss_com_salario_zero_retorna_zero`.

### Comandos
```bash
pytest                       # roda tudo
pytest apps/people           # roda só o app
pytest -k calculo_inss       # filtra por nome
pytest --cov                 # cobertura
```

---

## 12. Logging e auditoria

- Logger por módulo: `logger = logging.getLogger(__name__)`.
- **Níveis:**
  - `DEBUG` — fluxo interno detalhado (off em prod)
  - `INFO` — eventos relevantes (folha calculada, eSocial enviado)
  - `WARNING` — condições anormais que não param fluxo
  - `ERROR` — falha em fluxo de domínio
  - `CRITICAL` — falha que exige atenção humana imediata
- **Nunca** logar dados sensíveis (CPF completo, conta bancária, senha). Mascarar.
- Auditoria de escritas via `simple-history` (ativar no Bloco 1) — registra **quem/quando/o quê/antes/depois**.

---

## 13. O que NUNCA fazer no backend

- ❌ Lógica de negócio em view/viewset.
- ❌ `eval`, `exec` em qualquer hipótese (DSL de rubricas tem sandbox próprio).
- ❌ String concatenation em SQL — sempre ORM ou parametrizado.
- ❌ `print` em código de produção — usar logger.
- ❌ Commit com `--no-verify`.
- ❌ Migration que renomeia coluna sem etapa intermediária (deploy em duas fases).
- ❌ Importar `from apps.<x>.views import ...` em outro app (acoplamento errado).
- ❌ Mock de banco em teste de integração (banco real via fixture pytest-django).
- ❌ Deletar dados em migration sem plano de backup.
- ❌ Adicionar dependência sem nota no `CHANGELOG.md`.

---

## 14. O que SEMPRE fazer no backend

- ✅ Ler este arquivo + o `CONTEXT.md` específico (models/services/apps) antes de codar.
- ✅ Atualizar `CHANGELOG.md` ao final.
- ✅ Atualizar este arquivo se o padrão mudar.
- ✅ Type hints em funções públicas e services.
- ✅ Docstring em viewset, service e model não-trivial.
- ✅ `select_related`/`prefetch_related` em querysets que atravessam FK.
- ✅ Transações explícitas (`transaction.atomic()`) em qualquer escrita multi-tabela.
- ✅ Teste cobrindo a feature/fix.
- ✅ ruff verde.

---

## 15. Comandos de referência

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Migrations
python manage.py makemigrations <app> --name descritivo
python manage.py migrate

# Run
python manage.py runserver
celery -A arminda worker --loglevel=info     # Bloco 2+
celery -A arminda beat --loglevel=info       # jobs agendados

# Qualidade
ruff format .
ruff check . --fix
pytest --cov

# Inspeção
python manage.py shell
python manage.py show_urls                   # via django-extensions
python manage.py dbshell
```
