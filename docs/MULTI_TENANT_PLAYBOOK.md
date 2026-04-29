# Multi-tenant Playbook

> Manual operacional do multi-tenant do Arminda. Ler em conjunto com:
> - [ADR-0004](adr/0004-multi-tenant-schema.md) (decisão estratégica)
> - [ADR-0006](adr/0006-multi-tenant-implementacao.md) (implementação concreta)

---

## 1. Conceitos básicos

| Termo | Significado |
|-------|-------------|
| **Tenant** | Um município. Cada tenant = um schema PostgreSQL isolado. |
| **Public schema** | Schema `public` do Postgres. Compartilhado por TODOS os tenants. Guarda User, Municipio, Domain, configurações nacionais. |
| **Tenant schema** | `mun_<slug>` (ex: `mun_sao_raimundo`). Guarda servidores, folha, rubricas, etc. |
| **SHARED_APPS** | Apps cujos models vivem em `public`. |
| **TENANT_APPS** | Apps cujos models vivem em cada schema de tenant. |
| **search_path** | Variável do Postgres que diz em qual schema buscar tabelas. `django-tenants` muda isso por request. |

---

## 2. Comandos do dia a dia

### Aplicar migrations no schema public
```bash
python manage.py migrate_schemas --shared
```
Roda migrations dos `SHARED_APPS`. Use após mudar models de `apps.core` ou subir uma versão do Django/DRF/etc.

### Aplicar migrations em todos os tenants
```bash
python manage.py migrate_schemas
```
Roda migrations dos `TENANT_APPS` em **cada** schema cadastrado em `Municipio`. Use após mudar models de `apps.people`, `apps.payroll`, `apps.reports`.

### Aplicar em apenas um tenant
```bash
python manage.py migrate_schemas --schema=mun_sao_raimundo
```
Útil para depurar migrations problemáticas em um tenant antes de aplicar em todos.

### Criar um tenant novo
```bash
python manage.py criar_municipio \
  --nome "Caxias" \
  --uf MA \
  --codigo-ibge 2103000 \
  --schema mun_caxias \
  --domain caxias.arminda.app
```
- Cria a linha em `core_municipio`.
- Dispara `auto_create_schema=True` → Postgres cria o schema.
- `django-tenants` roda **todas** as migrations de `TENANT_APPS` no novo schema.
- Cria `core_domain` se `--domain` for passado.

### Listar tenants
```bash
python manage.py listar_tenants
```

### Abrir um shell no contexto de um tenant
```bash
python manage.py shell_plus  # ou shell
>>> from django.db import connection
>>> from apps.core.models import Municipio
>>> connection.set_tenant(Municipio.objects.get(schema_name="mun_sao_raimundo"))
>>> from apps.people.models import Servidor
>>> Servidor.objects.count()  # so do mun_sao_raimundo
```

---

## 3. Resolução de tenant em runtime

### Ordem de tentativa (`TenantHeaderOrHostMiddleware`)
1. Path está em `PUBLIC_PATH_PREFIXES`? → schema `public`, segue.
2. Header `X-Tenant: <schema_name | codigo_ibge>` presente? → resolve por header.
3. Hostname/subdomínio bate com `Domain.domain`? → resolve por host.
4. Nenhum? → 400 com `code: TENANT_NAO_RESOLVIDO`.

### Rotas públicas (sem tenant)
```
/admin/         /health/         /status/
/api/auth/*     /api/schema/     /api/docs/    /api/redoc/
/static/        /media/
```

### Rotas tenant (exigem `X-Tenant` ou subdomínio)
```
/api/core/      /api/people/     /api/payroll/    /api/reports/
```

### Como o frontend manda
```http
GET /api/people/servidores/ HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJ...
X-Tenant: mun_sao_raimundo
```

---

## 4. Boas práticas em código

### ✅ FAZER

```python
# Em código de aplicação, NUNCA setar tenant manualmente:
def view(request):
    servidores = Servidor.objects.all()  # filtra automaticamente pelo tenant atual
    ...
```

```python
# Em testes, usar a fixture in_tenant:
def test_algo(tenant_a, in_tenant):
    with in_tenant(tenant_a):
        Servidor.objects.create(...)
```

```python
# Em management command que precisa rodar em todos os tenants:
from django_tenants.utils import tenant_context

for municipio in Municipio.objects.all():
    with tenant_context(municipio):
        # codigo aqui roda com search_path do tenant
        ...
```

### ❌ NÃO FAZER

```python
# Cross-tenant em código de aplicação:
servidores = Servidor.objects.using("mun_outro").all()  # ERRADO
```

```python
# Setar schema manualmente em view/service:
connection.set_tenant(Municipio.objects.get(...))  # ERRADO em codigo de app
# Use o middleware. Manual so em management commands.
```

```python
# FK explicita para Municipio em model tenant:
class Servidor(models.Model):
    municipio = models.ForeignKey(Municipio, ...)  # ERRADO
    # O tenant ja e implicito via schema. FK redundante = bug em potencial.
```

---

## 5. Quando criar um novo app

### Decidir tenant vs shared

| Pergunta | Tenant | Shared |
|----------|--------|--------|
| Os dados pertencem a um único município? | ✅ | |
| Dois municípios poderiam ter mesmas linhas? (ex: tabela INSS) | | ✅ |
| O modelo é referenciado por User antes do tenant ser resolvido? | | ✅ |
| Afeta autenticação ou autorização? | | ✅ |

### Adicionar em settings
```python
# arminda/settings/base.py

SHARED_APPS = [
    ...,
    "apps.minha_nova_shared",   # se shared
]

TENANT_APPS = [
    ...,
    "apps.minha_nova_tenant",   # se tenant
]
```

### Aplicar
```bash
python manage.py makemigrations
python manage.py migrate_schemas --shared    # se shared
python manage.py migrate_schemas             # se tenant (em todos)
```

---

## 6. Migrations: regras críticas

1. **Sempre revisar** a migration gerada antes de commitar — `django-tenants` é estrito quanto ao que pode rodar em cada schema.
2. **Nomes descritivos** — `--name adiciona_campo_cbo_em_cargo`.
3. **Data migrations** que mudam dados de tenants devem usar `tenant_context`:
   ```python
   from django_tenants.utils import schema_context

   def forwards(apps, schema_editor):
       Municipio = apps.get_model("core", "Municipio")
       for m in Municipio.objects.all():
           with schema_context(m.schema_name):
               # mexer em dados do tenant
               ...
   ```
4. **Migrations destrutivas** (drop/rename) devem ter plano de rollback no PR.
5. **Nunca editar migration já aplicada em produção.**

---

## 7. Backup e restore

### Backup do banco inteiro
```bash
pg_dump -h localhost -U arminda arminda > backup-completo.sql
```

### Backup de um tenant específico (mais comum)
```bash
pg_dump -h localhost -U arminda \
  --schema=mun_sao_raimundo \
  arminda > backup-mun-sao-raimundo.sql
```

### Backup só do schema public (config + tenants)
```bash
pg_dump -h localhost -U arminda --schema=public arminda > backup-public.sql
```

### Restore de um tenant
```bash
psql -h localhost -U arminda arminda < backup-mun-sao-raimundo.sql
```

### Excluir um tenant
```python
# Em shell:
m = Municipio.objects.get(schema_name="mun_xxx")
m.auto_drop_schema = True   # override pontual; nao salvar
m.delete()                  # dropa schema + linha
```
**Em produção: NÃO usar. Fazer backup → desativar com `ativo=False` → arquivar dados → drop manual sob revisão.**

---

## 8. Troubleshooting

### "relation X does not exist"
- Faltou `migrate_schemas` (--shared se model é shared, sem flag se model é tenant em todos os tenants).

### "search_path errado"
- Em service/view: nunca setar manualmente. Confiar no middleware.
- Em management command: usar `tenant_context()`.

### "FK violado entre tabelas de schemas diferentes"
- Você criou FK de model tenant → model shared (ex: `Servidor.municipio = ForeignKey(Municipio)`). **Removê-la.** O tenant é implícito.

### "Tenant não resolvido em request de teste"
- Setar header: `client.defaults["HTTP_X_TENANT"] = tenant.schema_name`.
- Ou usar fixture `api_client_factory(user=..., tenant=...)` (já configurada em `backend/conftest.py`).

### "user.groups vs UsuarioMunicipioPapel"
- `user.groups` (Django padrão) — Groups globais. Use **só** para `staff_arminda`.
- `UsuarioMunicipioPapel` — papel **por município**. Use para todo o resto.
- Permissions DRF (`IsRHMunicipio` etc.) checam ambos.

### "Schema name muito longo"
- Postgres permite até 63 chars. `django-tenants` reserva alguns. Limite prático recomendado: **≤ 32 chars**.

---

## 9. Limites e capacity planning

- **Schemas por banco:** centenas a poucos milhares são ok. Acima disso, considerar particionamento por região.
- **Conexões:** `django-tenants` reusa conexão; o `search_path` é setado por sessão. PgBouncer **transaction mode** quebra isso — usar **session mode**.
- **Vacuum / autovacuum:** custo cresce linear com nº de schemas. Monitorar.
- **Backup full:** lento com muitos schemas. Backup por tenant é a estratégia padrão.

---

## 10. Referências

- [django-tenants docs](https://django-tenants.readthedocs.io/)
- [PostgreSQL: schemas](https://www.postgresql.org/docs/current/ddl-schemas.html)
- ADR-0004, ADR-0006 do Arminda.
