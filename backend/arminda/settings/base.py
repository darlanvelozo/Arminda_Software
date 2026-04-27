"""
Configurações base do Arminda.

Este arquivo contém configurações compartilhadas entre todos os ambientes.
Configurações específicas de cada ambiente vivem em:
- arminda.settings.dev
- arminda.settings.prod

A escolha do arquivo é feita pela variável de ambiente DJANGO_SETTINGS_MODULE.
"""

from pathlib import Path

import environ

# ============================================================
# Paths
# ============================================================
# BASE_DIR aponta para a pasta backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ============================================================
# Carregar variáveis de ambiente
# ============================================================
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)

# Lê o .env na raiz do repositório (subindo um nível a partir de backend/)
environ.Env.read_env(BASE_DIR.parent / ".env")

# ============================================================
# Segurança
# ============================================================
SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-only-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# ============================================================
# Apps
# ============================================================
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    # "django_tenants",      # ativar no Bloco 1
    # "simple_history",      # ativar no Bloco 1
]

LOCAL_APPS = [
    "apps.core",
    "apps.people",
    "apps.payroll",
    "apps.reports",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ============================================================
# Middleware
# ============================================================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # "simple_history.middleware.HistoryRequestMiddleware",  # ativar no Bloco 1
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
# Banco de dados
# ============================================================
# No Bloco 1 vamos trocar o ENGINE para django_tenants.postgresql_backend
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="arminda"),
        "USER": env("POSTGRES_USER", default="arminda"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="arminda_dev_password"),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5432"),
    }
}

# ============================================================
# Validação de senha
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ============================================================
# Internacionalização
# ============================================================
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Fortaleza"
USE_I18N = True
USE_TZ = True

# ============================================================
# Arquivos estáticos
# ============================================================
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static_collected"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ============================================================
# Default primary key field type
# ============================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ============================================================
# Django REST Framework
# ============================================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        # "rest_framework_simplejwt.authentication.JWTAuthentication",  # Bloco 1
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# ============================================================
# OpenAPI / drf-spectacular
# ============================================================
SPECTACULAR_SETTINGS = {
    "TITLE": "Arminda API",
    "DESCRIPTION": "API do sistema Arminda — folha de pagamento e gestão de pessoal municipal.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ============================================================
# CORS (frontend dev)
# ============================================================
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173", "http://127.0.0.1:5173"],
)

# ============================================================
# Celery
# ============================================================
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/2")
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
