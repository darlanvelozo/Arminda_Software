"""
Configurações da DEMO (branch `demo`).

Diferente de `prod.py`:
- DEBUG=False (esconde stacks pro cliente).
- SECURE_SSL_REDIRECT=False (a demo expõe pelo Cloudflare Tunnel, que
  termina TLS por fora; o tráfego interno Vite preview → gunicorn é HTTP
  local sem redirect).
- ALLOWED_HOSTS=* (cloudflared usa hostname dinâmico).
- CORS permissivo (mesmo motivo).
- Logging mais verboso que prod para diagnosticar problemas na demo.

Esta configuração é exclusiva da branch `demo` — não vai pra main.
"""

from .base import *  # noqa: F401, F403
from .base import env

DEBUG = False

# Cloudflared usa hostname dinâmico ".trycloudflare.com" — aceitamos qualquer
ALLOWED_HOSTS = ["*"]

# ============================================================
# HTTPS — desligado no servidor interno
# ============================================================
# O cliente final acessa via HTTPS (Cloudflare termina TLS), mas internamente
# o vite preview faz proxy HTTP → gunicorn HTTP. Sem redirect, sem HSTS.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Confia no header X-Forwarded-Proto se vier (Cloudflare sempre envia).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# CSRF aceita qualquer origem trycloudflare.com
CSRF_TRUSTED_ORIGINS = [
    "https://*.trycloudflare.com",
    "http://localhost:4173",
    "http://localhost:5173",
    "http://localhost:8000",
]

# ============================================================
# CORS — permissivo para a demo (token só vale na hora)
# ============================================================
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ============================================================
# Database — usa DATABASE_URL da venv (setado pelo start-demo.sh)
# ============================================================
# DATABASES já vem de base.py via django-environ

# ============================================================
# Logging
# ============================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
