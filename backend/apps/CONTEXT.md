# backend/apps/CONTEXT.md — Estrutura padrão de app Django

> Como cada app Django deve estar organizado internamente.
> **Antes de criar um app novo ou mexer em estrutura, ler este arquivo + [`backend/CONTEXT.md`](../CONTEXT.md).**

---

## 1. Apps existentes

| App | Responsabilidade | Status no Bloco 0 |
|-----|------------------|-------------------|
| `core` | Tenant (`Municipio`), modelo base (`TimeStampedModel`), config global, autenticação, RBAC, middleware multi-tenant | Models prontos; auth/RBAC/middleware no Bloco 1 |
| `people` | Servidor, Cargo, Lotação, Vínculo Funcional, Dependente, Documento | Models prontos; serializers/views/services no Bloco 1 |
| `payroll` | Rubrica, Folha, Lançamento, DSL de cálculo, incidências | Models básicos prontos; engine no Bloco 2 |
| `reports` | Relatórios gerados, exportações, holerite, ficha financeira | Model `RelatorioGerado` pronto; geração no Bloco 2 |

**Apps futuros possíveis:** `esocial` (Bloco 4), `tce` (Bloco 5), `portal_servidor` (Bloco 7), `bi` (Bloco 7), `imports` (se importadores ficarem grandes).

---

## 2. Estrutura interna de um app

```
apps/<nome>/
├── __init__.py                    ← vazio
├── apps.py                        ← AppConfig (default_auto_field, name="apps.<nome>")
├── admin.py                       ← admin do Django (se aplicável)
├── models.py                      ← modelos (ver CONTEXT_MODELS.md)
├── serializers.py                 ← DRF serializers (a partir do Bloco 1)
├── views.py                       ← viewsets/APIViews (orquestração HTTP)
├── urls.py                        ← rotas do app, com app_name
├── permissions.py                 ← permissões DRF customizadas (se necessário)
├── filters.py                     ← FilterSets do django-filter (se necessário)
├── services/                      ← regras de negócio (ver CONTEXT_SERVICES.md)
│   ├── __init__.py
│   ├── exceptions.py
│   └── <operacao>.py
├── tasks.py                       ← Celery tasks (Bloco 2+)
├── management/
│   └── commands/                  ← management commands (importadores, jobs admin)
│       └── <comando>.py
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py
└── tests/
    ├── __init__.py
    ├── conftest.py                ← fixtures locais do app
    ├── test_models.py
    ├── test_services_<x>.py
    └── test_views.py
```

---

## 3. Regras por arquivo

### `apps.py`
```python
from django.apps import AppConfig

class PeopleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.people"
    verbose_name = "Servidores e estrutura organizacional"
```

- `name` **sempre** com prefixo `apps.` — combina com o `LOCAL_APPS` em `settings/base.py`.
- `verbose_name` em português, descritivo, aparece no admin.

### `models.py`
- Ver [`backend/CONTEXT_MODELS.md`](../CONTEXT_MODELS.md).
- Um arquivo por app. Se ficar > 500 linhas, considerar quebrar (`models/__init__.py` + módulos), mas não antecipar.

### `views.py` (viewsets, APIViews)
- **Orquestração apenas.** Sem regra de negócio.
- Padrão para CRUD: `ModelViewSet` com `serializer_class`, `queryset`, `permission_classes`, `filterset_fields`.
- Ações customizadas via `@action` chamando service:

```python
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from apps.people.models import Servidor
from apps.people.serializers import ServidorListSerializer, ServidorDetailSerializer, AdmissaoSerializer
from apps.people.services.admissao import admitir_servidor, DadosAdmissao
from apps.people.services.exceptions import DomainError


class ServidorViewSet(viewsets.ModelViewSet):
    """CRUD de servidores e ações de RH (admissão, desligamento, transferência)."""

    queryset = Servidor.objects.select_related("municipio").prefetch_related("vinculos__cargo", "vinculos__lotacao")
    filterset_fields = ["municipio", "ativo"]
    search_fields = ["nome", "matricula", "cpf"]

    def get_serializer_class(self):
        if self.action == "list":
            return ServidorListSerializer
        return ServidorDetailSerializer

    @action(detail=False, methods=["post"], url_path="admitir")
    def admitir(self, request):
        """POST /api/people/servidores/admitir/ — admite novo servidor."""
        serializer = AdmissaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            servidor = admitir_servidor(
                municipio=request.tenant,                          # provido pelo middleware
                dados=DadosAdmissao(**serializer.validated_data),
            )
        except DomainError as exc:
            raise ValidationError({"detail": str(exc), "code": exc.code})
        return Response(ServidorDetailSerializer(servidor).data, status=201)
```

### `serializers.py`
- **Um serializer por contexto:**
  - `<Model>ListSerializer` — campos enxutos para listagem.
  - `<Model>DetailSerializer` — completo, para `retrieve`.
  - `<Model>WriteSerializer` — para `create`/`update` (se diferir do detail).
  - Serializers de ação (`AdmissaoSerializer`, `DesligamentoSerializer`) — espelham `DadosAdmissao`/etc.
- **Não** colocar regra de negócio em `validate()` — só validação de **forma**.
- `to_representation` só para shape de saída (data masking de CPF, formatação de moeda).

### `urls.py`
```python
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.people.views import ServidorViewSet, CargoViewSet, LotacaoViewSet

app_name = "people"

router = DefaultRouter()
router.register("servidores", ServidorViewSet, basename="servidor")
router.register("cargos", CargoViewSet, basename="cargo")
router.register("lotacoes", LotacaoViewSet, basename="lotacao")

urlpatterns = [path("", include(router.urls))]
```

- `app_name` obrigatório.
- Roteamento via `DefaultRouter` para CRUD; `path()` solto só para endpoints especiais.

### `services/`
- Ver [`backend/CONTEXT_SERVICES.md`](../CONTEXT_SERVICES.md).
- Criar a pasta no primeiro service do app.

### `tasks.py`
```python
from celery import shared_task

@shared_task(name="payroll.calcular_folha", bind=True, max_retries=3)
def calcular_folha_task(self, folha_id: int) -> dict:
    from apps.payroll.services.folha import calcular_folha
    resumo = calcular_folha(folha_id)
    return {
        "folha_id": folha_id,
        "total_liquido": str(resumo.total_liquido),
        "qtd_servidores": resumo.qtd_servidores,
    }
```

- `name` explícito (`<app>.<acao>`) — facilita inspeção em produção.
- `max_retries` definido.
- Task é **fina**: chama service, traduz retorno. Lógica fica no service.

### `admin.py`
- Cadastros de domínio devem ter admin para suporte e investigação de bugs.
- Mínimo: `list_display`, `search_fields`, `list_filter`, `readonly_fields` para campos auditados.

```python
from django.contrib import admin
from apps.people.models import Servidor

@admin.register(Servidor)
class ServidorAdmin(admin.ModelAdmin):
    list_display = ["matricula", "nome", "cpf", "municipio", "ativo"]
    list_filter = ["municipio", "ativo", "sexo"]
    search_fields = ["matricula", "nome", "cpf"]
    readonly_fields = ["criado_em", "atualizado_em", "criado_por", "atualizado_por"]
```

### `permissions.py`
- Permissões DRF customizadas. RBAC concreto entra no Bloco 1.
- Naming: `Pode<Acao><Recurso>` (`PodeEditarFolha`, `PodeFecharFolha`).

### `filters.py`
- FilterSets quando `filterset_fields` simples não basta (filtros customizados, ranges).

### `tests/`
- Um arquivo por área: `test_models.py`, `test_services_<operacao>.py`, `test_views.py`.
- Ver padrão completo em `CONTEXT_SERVICES.md` §9.

---

## 4. Como criar um app novo

```bash
cd backend
python manage.py startapp <nome> apps/<nome>
```

Depois:

1. Editar `apps/<nome>/apps.py`: `name = "apps.<nome>"`.
2. Adicionar em `arminda/settings/base.py` → `LOCAL_APPS`.
3. Criar `apps/<nome>/urls.py` com `app_name`.
4. Incluir em `arminda/urls.py`: `path("api/<nome>/", include("apps.<nome>.urls"))`.
5. Definir tenant vs shared:
   - **Tenant** (vai para schema do município) — adicionar em `TENANT_APPS` no settings (a partir do Bloco 1).
   - **Shared** (fica no schema `public`) — adicionar em `SHARED_APPS`.
6. Criar primeira migration: `python manage.py makemigrations <nome> --name initial`.
7. Adicionar entrada no `CHANGELOG.md` e atualizar este arquivo (§1).

---

## 5. Tenant vs Shared — guia rápido

| Vai para `SHARED_APPS` (schema public) | Vai para `TENANT_APPS` (schema do município) |
|----------------------------------------|----------------------------------------------|
| `apps.core` (Município, ConfigGlobal, User) | `apps.people` |
| `django.contrib.auth` (a depender da estratégia) | `apps.payroll` |
| `simple_history` (ambos podem ser necessários) | `apps.reports` |
| Tabelas legais nacionais (INSS, IRRF) | `apps.esocial` (futuro) |

**Decisão final** sobre cada app sai do ADR específico que vier no Bloco 1.

---

## 6. Padrão de import entre apps

- `apps.payroll` pode importar de `apps.people` e `apps.core`.
- `apps.people` pode importar de `apps.core`.
- `apps.core` **não** importa de outros apps de domínio (é fundação).
- `apps.reports` importa de qualquer um.
- **Nunca** import circular. Se aparecer, **a regra de negócio está no lugar errado** — extrair para um service neutro ou para `core`.

```
core ◀── people ◀── payroll
  ◀──────  reports ────────
```

---

## 7. Quando um app deve ter seu próprio `CONTEXT.md`

Crie `apps/<nome>/CONTEXT.md` quando:
- O app tiver **regras específicas** que não cabem nos contextos genéricos (ex: `payroll/CONTEXT.md` vai descrever a DSL no Bloco 2).
- O app tiver **invariantes críticas** (ex: `payroll`: "nunca recalcular folha fechada sem snapshot").
- O app tiver **integração externa** com regras próprias (`esocial/CONTEXT.md` vai listar todos os eventos S-* e seus gates).

Apps simples (CRUD direto) **não** precisam — as regras gerais bastam.

---

## 8. Checklist ao mexer em um app

- [ ] Estrutura interna conforme §2.
- [ ] `apps.py` com `name="apps.<nome>"`.
- [ ] `urls.py` com `app_name`.
- [ ] Models aderentes a [`CONTEXT_MODELS.md`](../CONTEXT_MODELS.md).
- [ ] Regras de negócio em `services/` aderentes a [`CONTEXT_SERVICES.md`](../CONTEXT_SERVICES.md).
- [ ] Views/serializers magrinhos.
- [ ] Admin minimamente útil.
- [ ] Testes nos pontos críticos.
- [ ] Migration nomeada.
- [ ] Entrada no `CHANGELOG.md`.
