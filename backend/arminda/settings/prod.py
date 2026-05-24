"""
Configurações de produção.

Pontos de atenção:
- DEBUG sempre False
- ALLOWED_HOSTS deve ser configurado via variável de ambiente
- SECRET_KEY deve vir do ambiente, nunca hardcoded
- HTTPS obrigatório (SECURE_SSL_REDIRECT)
"""

from .base import *  # noqa: F401, F403
from .base import env

DEBUG = False

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

# ============================================================
# Segurança HTTPS
# ============================================================
# Quando o tráfego chega via proxy reverso (Nginx) que termina TLS,
# o Django vê o request como HTTP. O header X-Forwarded-Proto avisa
# que o cliente externo veio via HTTPS. SECURE_SSL_REDIRECT continua
# fazendo redirect 80 → 443 sob esse header.
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# ============================================================
# CSRF — origens confiáveis (via env, com fallback aceitando os
# domínios do Arminda em produção)
# ============================================================
CSRF_TRUSTED_ORIGINS = env.list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    default=[
        "https://arminda.site",
        "https://www.arminda.site",
    ],
)

# ============================================================
# CORS — só origens explicitamente permitidas
# ============================================================
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "https://arminda.site",
        "https://www.arminda.site",
    ],
)
CORS_ALLOW_CREDENTIALS = True

# ============================================================
# Logging para produção
# ============================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
