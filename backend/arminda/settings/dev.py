"""
Configurações de desenvolvimento local.
"""

from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Console backend para email em dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# CORS aberto em dev (front roda em localhost:5173)
CORS_ALLOW_ALL_ORIGINS = True

# Logging mais verboso
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
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "arminda": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
