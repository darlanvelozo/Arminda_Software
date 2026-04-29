"""
Modelos do app core (SHARED_APPS).

Vivem no schema `public`:
- User: usuario customizado, identificacao por e-mail (ADR-0005)
- Municipio: tenant (ADR-0004 + ADR-0006), herda de TenantMixin
- Domain: roteamento por hostname/subdominio em prod
- UsuarioMunicipioPapel: associacao ternaria User x Municipio x Group (ADR-0007)
- ConfiguracaoGlobal: chave-valor compartilhado entre tenants
- TimeStampedModel: abstrato com auditoria de quem criou/atualizou
"""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin


class TimeStampedModel(models.Model):
    """Modelo abstrato com campos de auditoria de quem criou/atualizou."""

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_criados",
    )
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_atualizados",
    )

    class Meta:
        abstract = True


# ============================================================
# User customizado (ADR-0005)
# ============================================================


class UserManager(BaseUserManager):
    """Manager para User com identificacao por e-mail."""

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("E-mail e obrigatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser exige is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser exige is_superuser=True")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Usuario do sistema. Identificacao por e-mail."""

    # Remove o campo username herdado do AbstractUser
    username = None

    email = models.EmailField("e-mail", unique=True)
    nome_completo = models.CharField("nome completo", max_length=200, blank=True)
    precisa_trocar_senha = models.BooleanField(
        "precisa trocar senha no proximo login",
        default=False,
        help_text="Setado para usuarios criados via importacao",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()  # type: ignore[assignment]

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["email"]

    def __str__(self) -> str:
        return self.email


# ============================================================
# Municipio (Tenant) e Domain (ADR-0006)
# ============================================================


class Municipio(TenantMixin):
    """Municipio/Prefeitura — cada um vira um schema isolado.

    `schema_name` (CharField unique) e contribuido por TenantMixin.
    """

    nome = models.CharField(max_length=200)
    codigo_ibge = models.CharField("codigo IBGE", max_length=7, unique=True)
    uf = models.CharField("UF", max_length=2)
    ativo = models.BooleanField(default=True)
    data_adesao = models.DateField(null=True, blank=True)

    # TimeStamped (sem TimeStampedModel para evitar ciclo: TenantMixin precisa
    # estar disponivel antes de qualquer migracao envolvendo AUTH_USER_MODEL)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    # django-tenants:
    auto_create_schema = True  # cria schema automaticamente ao salvar
    auto_drop_schema = False  # NUNCA dropar schema automaticamente

    class Meta:
        ordering = ["nome"]
        verbose_name = "municipio"
        verbose_name_plural = "municipios"

    def __str__(self) -> str:
        return f"{self.nome}/{self.uf}"


class Domain(DomainMixin):
    """Mapeia hostname/subdominio para um Municipio (uso em producao).

    Em dev usamos header X-Tenant (ver TenantHeaderOrHostMiddleware).
    """

    pass


# ============================================================
# RBAC: associacao User x Municipio x Group (ADR-0007)
# ============================================================


class UsuarioMunicipioPapel(models.Model):
    """Papel de um usuario em um municipio especifico.

    Um mesmo usuario pode ter papeis diferentes em municipios diferentes.
    """

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="papeis",
    )
    municipio = models.ForeignKey(
        Municipio,
        on_delete=models.CASCADE,
        related_name="papeis",
    )
    grupo = models.ForeignKey(
        "auth.Group",
        on_delete=models.PROTECT,
        related_name="papeis",
        help_text="Grupo Django (admin_municipio, rh_municipio, etc.)",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "municipio", "grupo"],
                name="papel_unico_por_usuario_municipio_grupo",
            ),
        ]
        verbose_name = "papel de usuario em municipio"
        verbose_name_plural = "papeis de usuarios em municipios"

    def __str__(self) -> str:
        return f"{self.usuario.email} @ {self.municipio.schema_name} ({self.grupo.name})"


# ============================================================
# Configuracao global (chave-valor)
# ============================================================


class ConfiguracaoGlobal(models.Model):
    """Configuracoes do sistema por chave-valor (ex: tabelas legais nacionais)."""

    chave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    descricao = models.TextField(blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["chave"]
        verbose_name = "configuracao global"
        verbose_name_plural = "configuracoes globais"

    def __str__(self) -> str:
        return self.chave
