# ADR-0005 — User customizado em `apps.core.User`

**Status:** Aceito
**Data:** 2026-04-28
**Bloco:** 1.1 (Fundação técnica)

## Contexto

O Bloco 0 deixou os models `apps.people.*` e `apps.payroll.*` referenciando `settings.AUTH_USER_MODEL` (Django default `auth.User`) através do `TimeStampedModel.criado_por` e `atualizado_por`. Trocar o User depois que houver dados em produção é doloroso: o Django **não permite** trocar `AUTH_USER_MODEL` após a primeira migração ter sido aplicada com o User default sem reset completo de migrations.

Como ainda **não há produção** e o Bloco 1.1 vai reescrever as migrations de qualquer jeito (multi-tenant exige), este é o momento certo para introduzir um User customizado, evitando uma dor previsível.

Requisitos para o User do Arminda que o `auth.User` padrão não atende sem extensão:

1. **E-mail como identificador principal** (não `username`). Servidores e administradores são identificados por e-mail; pedir um `username` separado é UX ruim para um SaaS B2G.
2. **Vínculo com Municípios** via M2M (a partir do Bloco 1.2). Um usuário pode operar em mais de uma prefeitura (ex: contador que atende 3 municípios da rede; suporte interno do Arminda).
3. **Papel principal por município**, materializado a partir de `Group` (ver ADR-0007).
4. **Auditoria mais rica:** `last_login_ip`, `mfa_enabled` (futuro), `precisa_trocar_senha` (importação inicial).
5. **Soft delete** (`ativo=False`) ao invés de delete hard, para preservar histórico.

## Decisão

Criar `apps.core.User` herdando de **`AbstractUser`** (não `AbstractBaseUser`), no schema **`SHARED_APPS`** (compartilhado entre tenants).

### Justificativa: `AbstractUser` e não `AbstractBaseUser`
- `AbstractUser` herda toda a infraestrutura útil (`first_name`, `last_name`, `is_staff`, `is_superuser`, `is_active`, grupos, permissões, manager, password validation).
- Customizamos o necessário (e-mail unique, opção de remover `username`, campos extras).
- `AbstractBaseUser` daria controle total mas exigiria reimplementar o que já temos.
- Migração para `AbstractBaseUser` no futuro é possível se aparecer requisito que `AbstractUser` não cubra.

### Forma concreta

```python
# apps/core/models.py

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("E-mail e obrigatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True or extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser exige is_staff=True e is_superuser=True")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Usuario do sistema.

    Identificacao por e-mail, vinculo opcional com municipios via M2M.
    Papeis (Group) sao escopados por municipio (ver ADR-0007).
    """

    username = None  # remove o campo herdado
    email = models.EmailField("e-mail", unique=True)
    nome_completo = models.CharField("nome completo", max_length=200, blank=True)
    municipios = models.ManyToManyField(
        "Municipio",
        related_name="usuarios",
        blank=True,
        help_text="Municipios em que o usuario opera (vazio = somente staff Arminda)",
    )
    precisa_trocar_senha = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []  # email + password ja sao obrigatorios

    objects = UserManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self) -> str:
        return self.email
```

### Settings
```python
AUTH_USER_MODEL = "core.User"
```

Setado **antes** de qualquer makemigrations.

### Tenant ou shared?
Shared (`SHARED_APPS`). Usuário precisa autenticar antes do middleware resolver tenant; e o mesmo e-mail pode operar em múltiplos municípios.

### Permissões e papéis
- Usar `django.contrib.auth.Group` + `Permission` (não inventar tabela própria).
- Papéis-base seedados via **data migration**: `admin_municipio`, `rh_municipio`, `financeiro_municipio`, `leitura_municipio`, `staff_arminda`.
- Escopo por município: tabela através (`UsuarioMunicipioPapel`) entre `User` × `Municipio` × `Group`. Definição final em ADR-0007.

## Consequências

**Positivas**
- Login por e-mail (UX SaaS).
- Decisão de auth não bloqueia mais o resto do Bloco 1.
- Reset de migrations é uma única dor — não vai se repetir.
- Espaço para crescer (MFA, SSO via SAML/OIDC) sem trocar a base.

**Negativas / mitigações**
- `createsuperuser` agora pede e-mail, não username — atualizar `setup.sh` e docs.
- Códigos de terceiros que assumem `auth.User` precisam usar `get_user_model()`. Mitigação: nosso código novo já adota; libs externas (DRF, simple-jwt, simple-history, django-tenants) suportam `AUTH_USER_MODEL` corretamente.
- Migration inicial passa a depender de `core.User` em vez de `auth.User`. Reset completo no Bloco 1.1.

## Alternativas consideradas

- **Manter `auth.User` e estender via OneToOne `Profile`** — caminho clássico mas dobra cada query (`select_related("profile")` em todo lugar). Sem ganho real e com fricção permanente.
- **`AbstractBaseUser` puro** — mais flexível, mas reescreve manager, password helpers, e-mail confirmation. Custo desproporcional para o que precisamos hoje.

## Implicações para o desenvolvimento

- Reset de migrations dos apps `core`, `people`, `payroll`, `reports` (tarefa do Bloco 1.1).
- `tests/conftest.py` provê fixture `usuario_admin`, `usuario_rh`, `usuario_leitura` usando `User.objects.create_user(email=..., password=...)`.
- Backend usa `from django.contrib.auth import get_user_model; User = get_user_model()` em **toda referência** ao User. **Nunca** importar `from apps.core.models import User` em service ou view (acopla forte).
- Endpoints de auth (ADR-0007) operam sobre `email`/`password`, **não** `username`/`password`.

## Referências

- [Django: Substituting a custom User model](https://docs.djangoproject.com/en/5.1/topics/auth/customizing/#substituting-a-custom-user-model)
- [Django: AbstractUser vs AbstractBaseUser](https://docs.djangoproject.com/en/5.1/topics/auth/customizing/#specifying-a-custom-user-model)
