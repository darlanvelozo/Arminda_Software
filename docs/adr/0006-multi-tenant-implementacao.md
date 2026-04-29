# ADR-0006 — Multi-tenant: implementação concreta

**Status:** Aceito
**Data:** 2026-04-28
**Bloco:** 1.1 (Fundação técnica)
**Refina:** [ADR-0004](0004-multi-tenant-schema.md) — que decidiu *isolamento por schema*; este aqui decide *como exatamente*.

## Contexto

A ADR-0004 fixou a estratégia: **um schema PostgreSQL por município**, via `django-tenants`. O Bloco 0 deixou o pacote no `requirements.txt` mas comentado em `INSTALLED_APPS`, e os models já criados de `apps.people`, `apps.payroll`, `apps.reports` **carregam um FK redundante para `Municipio`** em todas as entidades de domínio.

Com `django-tenants` ativo, o tenant é resolvido pelo `search_path` do PostgreSQL — manter o FK explícito quebra a premissa de isolamento (cria a possibilidade de cross-tenant por bug em filtragem). Este ADR registra a decisão de **remover** os FKs redundantes e os detalhes operacionais que vão guiar o resto do Bloco 1.

## Decisão

### 1. `Municipio` herda de `TenantMixin`

```python
# apps/core/models.py
from django_tenants.models import TenantMixin, DomainMixin

class Municipio(TenantMixin, TimeStampedModel):
    nome = models.CharField(max_length=200)
    codigo_ibge = models.CharField(max_length=7, unique=True)
    uf = models.CharField(max_length=2)
    ativo = models.BooleanField(default=True)
    data_adesao = models.DateField(null=True, blank=True)

    # TenantMixin contribui:
    #   schema_name (CharField unique) — o nome do schema Postgres
    #   auto_create_schema = True (default) — cria schema ao salvar
    #   auto_drop_schema = False — protege contra DROP acidental

    auto_drop_schema = False  # explicito; nunca queremos drop em prod

    class Meta:
        ordering = ["nome"]
        verbose_name = "municipio"
        verbose_name_plural = "municipios"

    def __str__(self) -> str:
        return f"{self.nome}/{self.uf}"
```

### 2. `Domain` (modelo de roteamento por subdomínio/host)

```python
class Domain(DomainMixin):
    """Mapeia hostname/subdominio para um Municipio.

    Em dev usaremos header X-Tenant; o Domain fica para producao.
    """
    pass
```

### 3. Settings split SHARED / TENANT

```python
# arminda/settings/base.py

SHARED_APPS = [
    "django_tenants",                  # OBRIGATORIAMENTE primeiro
    "apps.core",                       # Municipio, Domain, User, ConfiguracaoGlobal
    # Django built-ins compartilhados:
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    # Terceiros que precisam estar no public:
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]

TENANT_APPS = [
    "django.contrib.contenttypes",     # repetido em ambos por exigencia da lib
    "apps.people",
    "apps.payroll",
    "apps.reports",
    "simple_history",
]

INSTALLED_APPS = list({*SHARED_APPS, *TENANT_APPS})

TENANT_MODEL = "core.Municipio"
TENANT_DOMAIN_MODEL = "core.Domain"

DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        # ...resto igual
    }
}

DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

MIDDLEWARE = [
    "apps.core.middleware.tenant.TenantHeaderOrHostMiddleware",   # ANTES de tudo
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # ...
]
```

### 4. Resolução de tenant em dev e prod

**Dev:** header HTTP `X-Tenant: <codigo_ibge>` (ou `<schema_name>`). Permite testar com um único host (`localhost:8000`).

**Prod:** subdomínio `<municipio>.arminda.app` resolvido por `django_tenants.middleware.main.TenantMainMiddleware`.

Nosso middleware customizado **`TenantHeaderOrHostMiddleware`** tenta primeiro o header (dev/integrações), depois o host (prod). Se nada bater e a rota for tenant-only, retorna 400 com payload claro.

```python
# apps/core/middleware/tenant.py
from django.db import connection
from django.http import JsonResponse
from django_tenants.middleware.main import TenantMainMiddleware
from django_tenants.utils import get_public_schema_name, get_tenant_model

class TenantHeaderOrHostMiddleware(TenantMainMiddleware):
    """Resolve tenant por header X-Tenant (dev) ou hostname (prod)."""

    PUBLIC_PATH_PREFIXES = ("/admin/", "/health/", "/status/", "/api/auth/", "/api/schema/", "/api/docs/", "/api/redoc/")

    def process_request(self, request):
        if any(request.path.startswith(p) for p in self.PUBLIC_PATH_PREFIXES):
            connection.set_schema_to_public()
            return None

        tenant_header = request.headers.get("X-Tenant")
        if tenant_header:
            Tenant = get_tenant_model()
            try:
                tenant = Tenant.objects.get(schema_name=tenant_header)
            except Tenant.DoesNotExist:
                try:
                    tenant = Tenant.objects.get(codigo_ibge=tenant_header)
                except Tenant.DoesNotExist:
                    return JsonResponse(
                        {"detail": "Tenant nao encontrado", "code": "TENANT_NAO_ENCONTRADO"},
                        status=400,
                    )
            request.tenant = tenant
            connection.set_tenant(tenant)
            return None

        # Fallback: comportamento padrao do TenantMainMiddleware (subdominio)
        return super().process_request(request)
```

### 5. Models tenant — **sem FK para `Municipio`**

```python
# apps/people/models.py — DEPOIS do refactor
class Cargo(TimeStampedModel):
    # municipio = REMOVIDO (tenant implicito via schema)
    codigo = models.CharField(max_length=20, unique=True)  # unique no escopo do schema
    nome = models.CharField(max_length=200)
    cbo = models.CharField("CBO", max_length=10, blank=True)
    nivel_escolaridade = models.CharField(max_length=30, choices=NivelEscolaridade.choices, default=NivelEscolaridade.MEDIO)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "cargo"
        verbose_name_plural = "cargos"
```

`unique_together = [("municipio", "codigo")]` vira `unique=True` em `codigo` (escopo do schema = município).

### 6. Migrations: comandos próprios

```bash
# Schema public (SHARED_APPS):
python manage.py migrate_schemas --shared

# Schema de cada tenant (TENANT_APPS, em todos os municipios):
python manage.py migrate_schemas

# Schema de um tenant especifico:
python manage.py migrate_schemas --schema=mun_sao_raimundo
```

`makemigrations` continua o mesmo. `migrate` original é **substituído** por `migrate_schemas`.

### 7. Schema name e segurança

- **Naming:** `mun_<codigo_ibge>` ou `mun_<slug_do_nome>` — definido no momento da criação do `Municipio`. Slug ASCII, sem hífen, máx 32 chars (limite Postgres é 63, deixamos margem).
- **Reservados:** Postgres trata `public` como o schema compartilhado. `django-tenants` adiciona `pg_*` e o próprio `public` à lista de reservados.
- **Role da aplicação:** em dev usa `SUPERUSER` (cria schema na hora). Em prod, `arminda_app` com `CREATEDB` + `CREATE` em `template1` (a planejar no Bloco 6, junto com infra).

### 8. Comandos administrativos

Management commands em `apps.core.management.commands`:

- `criar_municipio.py` — cria `Municipio` + `Domain` + roda `migrate_schemas --schema=...`. Usa transação atômica.
- `listar_tenants.py` — `Municipio.objects.all()` formatado.
- `tenant_shell.py` — abre `shell` com `connection.set_tenant(tenant)` aplicado.

Cross-tenant (manutenção) **só** via management commands explícitos. Código de aplicação **nunca** deve setar tenant manualmente.

## Consequências

**Positivas**
- Isolamento real e enforced pelo Postgres — bug em queryset não vaza dados entre municípios.
- Models mais limpos (sem `municipio = ForeignKey(...)` repetido em toda entidade).
- `unique_together` simplifica para `unique=True` em campos naturais.
- Backup/restore por município é `pg_dump --schema=mun_xxx`.

**Negativas / mitigações**
- **Migrations rodam N vezes** (uma por tenant). Mitigação: `django-tenants` paraleliza com `--parallel`.
- **`auth_user` no schema public:** todos os usuários ficam visíveis a todos os schemas. Isolamento é por papel + município, não por tabela. Aceitável e desejado (login antes de tenant).
- **Fixtures de teste exigem 2 tenants** mínimo. Mitigação: `conftest.py` provê `tenant_a`/`tenant_b` automaticamente.
- **Deploy precisa rodar `migrate_schemas`** sempre. Mitigação: pipeline CI/CD chama os dois comandos em sequência.
- **`pg_dump` full do banco fica grande** com muitos tenants. Mitigação: backup por tenant + retenção diferenciada (fica para Bloco 6).

## Alternativas consideradas

- **`django-tenant-schemas`** (predecessor do `django-tenants`) — descartado, sem manutenção.
- **`django-tenants` com `domain_url`** apenas (sem header) — menos prático em dev (precisaria de subdomínios locais via `/etc/hosts`). Adotado o middleware híbrido.
- **`django-pgschemas`** — concorrente; sólido, mas comunidade e ecossistema do `django-tenants` são maiores. ADR-0004 já fixou; sem motivo para reverter.

## Implicações para o desenvolvimento

- **Reset de migrations** em `core`, `people`, `payroll`, `reports` (tarefa do Bloco 1.1, junto com User custom — ADR-0005).
- Testes de domínio **sempre** em fixture com tenant ativo. `pytest-django` com `databases` configurado para `default` apenas — `django-tenants` cuida do switch.
- Endpoints públicos (lista em `PUBLIC_PATH_PREFIXES`) rodam no schema `public`. Tudo o resto exige tenant.
- Admin do Django roda no schema `public` por padrão; para administrar dados de um tenant, usar `tenant_shell` + admin "tenanted" futuro (parking — Bloco 1.5+).
- Documentação operacional vai em **`docs/MULTI_TENANT_PLAYBOOK.md`** (próxima entrega do 1.1).

## Referências

- [django-tenants documentation](https://django-tenants.readthedocs.io/)
- [PostgreSQL: search_path](https://www.postgresql.org/docs/current/runtime-config-client.html#GUC-SEARCH-PATH)
- ADR-0004 — multi-tenant por schema (decisão pai)
