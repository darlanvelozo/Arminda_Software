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


# ============================================================
# Tabelas legais (Onda 2.3)
# ============================================================


class TipoTabelaLegal(models.TextChoices):
    """Tipos de tabela legal nacional usados no cálculo de folha."""

    SALARIO_MINIMO = "salario_minimo", "Salário mínimo"
    INSS = "inss", "Faixas INSS"
    IRRF = "irrf", "Faixas IRRF"
    DEDUCAO_DEPENDENTE_IRRF = "deducao_dependente_irrf", "Dedução por dependente (IRRF)"


class TabelaLegal(models.Model):
    """
    Tabelas legais nacionais com vigência (Onda 2.3).

    Vive em SHARED (public) porque salário mínimo, INSS e IRRF são
    federais — uma fonte de verdade para todos os municípios. Cada
    município pode ter, eventualmente, tabelas próprias (previdência
    municipal) no Bloco 2.4 — essas vão para um modelo TENANT separado.

    Campo `valores` é JSON com estrutura específica por tipo:

    - `salario_minimo`: `{"valor": "1518.00"}`
    - `deducao_dependente_irrf`: `{"valor": "189.59"}`
    - `inss`: `{"faixas": [
          {"ate": "1518.00", "aliquota": "0.075"},
          {"ate": "2793.88", "aliquota": "0.09"},
          {"ate": "4190.83", "aliquota": "0.12"},
          {"ate": "8157.41", "aliquota": "0.14"}
      ], "teto": "8157.41"}`
    - `irrf`: `{"faixas": [
          {"ate": "2428.80", "aliquota": "0",      "deducao": "0"},
          {"ate": "2826.65", "aliquota": "0.075",  "deducao": "182.16"},
          {"ate": "3751.05", "aliquota": "0.15",   "deducao": "394.16"},
          {"ate": "4664.68", "aliquota": "0.225",  "deducao": "675.49"},
          {"ate": null,      "aliquota": "0.275",  "deducao": "908.73"}
      ]}`

    Vigência:
    - `vigencia_inicio` é obrigatório.
    - `vigencia_fim` é opcional; quando null, a tabela continua valendo
      até ser substituída por uma versão mais nova.

    Resolução por competência: pega a tabela do mesmo `tipo` com
    `vigencia_inicio <= competencia` e (`vigencia_fim is null` ou
    `vigencia_fim >= competencia`).
    """

    tipo = models.CharField(max_length=40, choices=TipoTabelaLegal.choices)
    vigencia_inicio = models.DateField(help_text="Primeiro dia em que a tabela vigora.")
    vigencia_fim = models.DateField(
        null=True,
        blank=True,
        help_text="Último dia de vigência (null = continua valendo).",
    )
    valores = models.JSONField(help_text="Estrutura específica por tipo — ver TabelaLegal.")
    referencia_legal = models.CharField(
        max_length=200,
        blank=True,
        help_text="Lei/Decreto/Portaria de origem (ex.: 'Lei 14.663/2023').",
    )
    observacoes = models.TextField(blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["tipo", "-vigencia_inicio"]
        constraints = [
            models.UniqueConstraint(
                fields=["tipo", "vigencia_inicio"],
                name="tabela_legal_unica_por_tipo_e_vigencia",
            ),
        ]
        verbose_name = "tabela legal"
        verbose_name_plural = "tabelas legais"

    def __str__(self) -> str:
        fim = self.vigencia_fim.isoformat() if self.vigencia_fim else "atual"
        return f"{self.get_tipo_display()} · {self.vigencia_inicio.isoformat()} → {fim}"
