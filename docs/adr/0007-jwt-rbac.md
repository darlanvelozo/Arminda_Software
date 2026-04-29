# ADR-0007 — Autenticação JWT + RBAC escopado por município

**Status:** Aceito
**Data:** 2026-04-28
**Bloco:** 1.1 (Fundação técnica)
**Depende de:** [ADR-0005](0005-custom-user.md), [ADR-0006](0006-multi-tenant-implementacao.md)

## Contexto

Com User customizado (ADR-0005) e multi-tenant por schema (ADR-0006), falta decidir:

1. Como o frontend autentica.
2. Como expressar **papéis** (admin do município, RH, financeiro, leitura, staff Arminda).
3. Como esses papéis funcionam em um modelo onde **um mesmo usuário pode operar em múltiplos municípios** com papéis diferentes em cada.

## Decisão

### 1. Autenticação por JWT (access + refresh)

`djangorestframework-simplejwt` 5.3 — já no `requirements.txt`.

**Endpoints (no schema `public`, sem tenant):**

| Verbo | Path | Função |
|-------|------|--------|
| POST | `/api/auth/login/` | recebe `{ email, password }`, retorna `{ access, refresh, user }` |
| POST | `/api/auth/refresh/` | recebe `{ refresh }`, retorna `{ access }` |
| POST | `/api/auth/logout/` | recebe `{ refresh }`, blacklist (opcional, Bloco 1.2) |
| GET | `/api/auth/me/` | retorna o usuário autenticado + papéis nos municípios |

**Tokens:**
- `access` — TTL **30 min** (config `ACCESS_TOKEN_LIFETIME`).
- `refresh` — TTL **7 dias** (config `REFRESH_TOKEN_LIFETIME`).
- Algoritmo: **HS256** com `SIGNING_KEY = SECRET_KEY` em dev. Em prod, **chave dedicada** lida de `JWT_SIGNING_KEY` (a configurar no Bloco 6).

**Claims customizadas no payload:**
```json
{
  "user_id": 42,
  "email": "ana@prefeitura.ma.gov.br",
  "is_staff_arminda": false,
  "municipios": [
    { "schema": "mun_sao_raimundo", "papel": "rh_municipio" },
    { "schema": "mun_teresina", "papel": "leitura_municipio" }
  ],
  "exp": 1745251200,
  "iat": 1745249400
}
```

A claim `municipios` é populada por um serializer customizado em `apps.core.auth.serializers.ArmindaTokenObtainPairSerializer`.

### 2. RBAC: `Group` do Django escopado por município

**Modelo de associação ternária** (User × Município × Group):

```python
# apps/core/models.py

class UsuarioMunicipioPapel(TimeStampedModel):
    """Papel de um usuario em um municipio especifico."""

    usuario = models.ForeignKey("User", on_delete=models.CASCADE, related_name="papeis")
    municipio = models.ForeignKey("Municipio", on_delete=models.CASCADE, related_name="papeis")
    grupo = models.ForeignKey(
        "auth.Group",
        on_delete=models.PROTECT,
        related_name="papeis",
        help_text="Grupo Django (admin_municipio, rh_municipio, etc.)",
    )

    class Meta:
        unique_together = [("usuario", "municipio", "grupo")]
        verbose_name = "papel de usuario em municipio"
        verbose_name_plural = "papeis de usuarios em municipios"
```

### 3. Papéis-base (seedados via data migration)

| Group | Permissões iniciais (Bloco 1.1) | Escopo final (Bloco 1.2+) |
|-------|--------------------------------|---------------------------|
| `staff_arminda` | superuser-like, cross-tenant via management commands | infra do produto |
| `admin_municipio` | tudo do município | RH + financeiro + config |
| `rh_municipio` | CRUD de servidor/cargo/lotação/vínculo | + admissão, desligamento |
| `financeiro_municipio` | leitura RH + CRUD payroll | + cálculo, fechamento |
| `leitura_municipio` | só leitura | dashboards, relatórios |

Permissões granulares (model-level Django + viewset-level DRF) entram no Bloco 1.2 quando os endpoints CRUD aparecerem. **Bloco 1.1 cria os Groups e o vínculo `UsuarioMunicipioPapel`**, mas as permissions efetivas vêm depois.

### 4. Permissions DRF base (em `apps.core.permissions`)

```python
class IsAuthenticated(BaseIsAuthenticated):
    """Mesmo do DRF, mas explicito como import central."""

class IsStaffArminda(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.groups.filter(name="staff_arminda").exists())

class HasPapelInTenant(BasePermission):
    """Exige que o usuario tenha PELO MENOS UM dos papeis informados no tenant atual."""

    papeis: list[str] = []  # subclasse define

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return False
        return UsuarioMunicipioPapel.objects.filter(
            usuario=request.user,
            municipio=tenant,
            grupo__name__in=self.papeis,
        ).exists()


class IsAdminMunicipio(HasPapelInTenant):
    papeis = ["admin_municipio", "staff_arminda"]


class IsRHMunicipio(HasPapelInTenant):
    papeis = ["rh_municipio", "admin_municipio", "staff_arminda"]


class IsFinanceiroMunicipio(HasPapelInTenant):
    papeis = ["financeiro_municipio", "admin_municipio", "staff_arminda"]


class IsLeituraMunicipio(HasPapelInTenant):
    papeis = ["leitura_municipio", "rh_municipio", "financeiro_municipio", "admin_municipio", "staff_arminda"]
```

`staff_arminda` é incluído em todas — é um override global para suporte interno.

### 5. Fluxo end-to-end

```
1. Frontend POST /api/auth/login/ {email, password}
   → backend valida credenciais (público, sem tenant)
   → retorna {access, refresh, user, municipios:[...]}

2. Frontend escolhe município (se >1) → guarda schema_name

3. Frontend chama API com:
   Authorization: Bearer <access>
   X-Tenant: mun_sao_raimundo

4. Middleware:
   - JWT auth: resolve request.user
   - TenantHeaderOrHostMiddleware: resolve request.tenant a partir do X-Tenant

5. Permission class no viewset:
   - IsRHMunicipio.has_permission(request, view)
   - True se request.user tem papel rh/admin/staff em request.tenant
```

### 6. Settings

```python
# arminda/settings/base.py

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",  # mantem admin Django
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # ...
}

from datetime import timedelta
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,    # exige rest_framework_simplejwt.token_blacklist em SHARED_APPS
    "ALGORITHM": "HS256",
    "SIGNING_KEY": env("JWT_SIGNING_KEY", default=SECRET_KEY),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "TOKEN_OBTAIN_SERIALIZER": "apps.core.auth.serializers.ArmindaTokenObtainPairSerializer",
}
```

### 7. Senhas

- Hashing default do Django (PBKDF2-SHA256 / Argon2 — manter default).
- Validação de senha: 4 validators padrão Django + mínimo 10 caracteres em prod (a refinar no Bloco 6).
- `precisa_trocar_senha=True` em usuários importados → endpoint `/api/auth/me/` retorna a flag e o frontend força fluxo de troca antes de qualquer outra ação.

## Consequências

**Positivas**
- Stateless: não precisa session store por request — escala horizontalmente.
- Frontend SPA + mobile (PWA, Bloco 7) compartilham o mesmo modelo de auth.
- RBAC fica simples: papéis em Groups Django, escopo via tabela ternária.
- Token carrega claim `municipios` — frontend não precisa buscar de novo a cada navegação.

**Negativas / mitigações**
- JWT é stateless → revogação imediata exige blacklist. Mitigação: ativamos `BLACKLIST_AFTER_ROTATION` desde já. Logout marca refresh como blacklisted.
- TTL de access curto (30 min) gera refresh frequente. Mitigação: rotação automática + interceptor axios no frontend.
- Mais um lugar para manter sincronizado se papéis mudarem (claim do token versus DB). Mitigação: `/api/auth/me/` é canônico; frontend re-busca em momentos-chave (login, troca de tenant, mudança de papel).
- Senha exposta no client em login — usar HTTPS em prod, óbvio. Em dev, `localhost` aceitável.

## Alternativas consideradas

- **Sessions baseadas em cookie** (Django default) — mais simples, mas atrelado ao mesmo domínio e mais difícil de usar com mobile. Mantemos `SessionAuthentication` apenas para o admin do Django.
- **OAuth2/OIDC com provider externo** (Keycloak) — overkill no Bloco 1; pode ser plugado no Bloco 6/7 se demanda surgir.
- **API key por servidor** — descartado, não cobre o caso humano.
- **Permission por endpoint** ao invés de papel — descartado: gera matriz enorme e difícil de auditar. Papéis primeiro, permissions granulares como complemento (Bloco 1.2+).

## Implicações para o desenvolvimento

- Header `X-Tenant` obrigatório em chamadas tenant (todas exceto as de `PUBLIC_PATH_PREFIXES`).
- Frontend axios interceptor adiciona `Authorization: Bearer ...` e `X-Tenant: ...` automaticamente.
- Ao trocar de município no frontend, **invalidar todo o cache do TanStack Query** (`queryClient.clear()`) — dados de tenant A não devem aparecer em tenant B nem por cache.
- Testes precisam de **2 usuários × 2 tenants × papéis variados** para cobrir matriz mínima de RBAC. Fixtures em `tests/conftest.py`.
- ADR sobre permissões granulares por endpoint vai sair do Bloco 1.2 (quando os CRUDs forem implementados).

## Referências

- [djangorestframework-simplejwt](https://django-rest-framework-simplejwt.readthedocs.io/)
- [Django: Groups & Permissions](https://docs.djangoproject.com/en/5.1/topics/auth/default/#groups)
- ADR-0005, ADR-0006
