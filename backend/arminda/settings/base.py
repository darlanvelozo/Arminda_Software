"""
Configuracoes base do Arminda.

Compartilhadas entre todos os ambientes. Cada ambiente estende este arquivo:
- arminda.settings.dev
- arminda.settings.prod

DJANGO_SETTINGS_MODULE controla a escolha (default em dev: arminda.settings.dev).
"""

from datetime import timedelta
from pathlib import Path

import environ

# ============================================================
# Paths
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/

# ============================================================
# Variaveis de ambiente
# ============================================================
env = environ.Env(DJANGO_DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR.parent / ".env")

# ============================================================
# Seguranca
# ============================================================
SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-only-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# ============================================================
# Apps — split SHARED / TENANT (ADR-0006)
# ============================================================

SHARED_APPS = [
    # django-tenants OBRIGATORIAMENTE primeiro
    "django_tenants",
    # Nosso app shared (Municipio, Domain, User, ConfiguracaoGlobal, papeis)
    "apps.core",
    # Django built-ins compartilhados (auth/sessions/admin precisam estar no public)
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    # Terceiros que vivem no public
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]

TENANT_APPS = [
    # contenttypes precisa em ambos (limitacao do django-tenants)
    "django.contrib.contenttypes",
    # Auditoria por tenant
    "simple_history",
    # Apps de dominio (vivem no schema do municipio)
    "apps.people",
    "apps.payroll",
    "apps.reports",
]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

# django-tenants config
TENANT_MODEL = "core.Municipio"
TENANT_DOMAIN_MODEL = "core.Domain"
PUBLIC_SCHEMA_NAME = "public"

# Custom User (ADR-0005)
AUTH_USER_MODEL = "core.User"

# ============================================================
# Middleware (ADR-0006)
# ============================================================
MIDDLEWARE = [
    # Resolucao de tenant (header X-Tenant em dev / hostname em prod)
    "apps.core.middleware.tenant.TenantHeaderOrHostMiddleware",
    # CORS antes de tudo
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Auditoria de quem fez o request (simple-history)
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "arminda.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "arminda.wsgi.application"

# ============================================================
# Banco de dados — engine do django-tenants (ADR-0006)
# ============================================================
DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": env("POSTGRES_DB", default="arminda"),
        "USER": env("POSTGRES_USER", default="arminda"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="arminda_dev_password"),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5432"),
    }
}

DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

# ============================================================
# Validacao de senha
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ============================================================
# Internacionalizacao
# ============================================================
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Fortaleza"
USE_I18N = True
USE_TZ = True

# ============================================================
# Arquivos estaticos
# ============================================================
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static_collected"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ============================================================
# Default primary key
# ============================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ============================================================
# Django REST Framework
# ============================================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# ============================================================
# JWT (ADR-0007)
# ============================================================
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": env("JWT_SIGNING_KEY", default=SECRET_KEY),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_OBTAIN_SERIALIZER": "apps.core.auth.serializers.ArmindaTokenObtainPairSerializer",
}

# ============================================================
# OpenAPI / drf-spectacular
# ============================================================
SPECTACULAR_SETTINGS = {
    "TITLE": "Arminda API",
    "DESCRIPTION": "API do sistema Arminda — folha de pagamento e gestao de pessoal municipal.",
    "VERSION": "0.2.0-dev",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ============================================================
# CORS (frontend dev)
# ============================================================
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173", "http://127.0.0.1:5173"],
)
# Necessario para o frontend mandar X-Tenant + Authorization
CORS_ALLOW_HEADERS = list(
    [
        "accept",
        "accept-encoding",
        "authorization",
        "content-type",
        "dnt",
        "origin",
        "user-agent",
        "x-csrftoken",
        "x-requested-with",
        "x-tenant",
    ]
)

# ============================================================
# Celery
# ============================================================
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/2")
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
