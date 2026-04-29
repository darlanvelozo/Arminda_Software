"""
Configuracoes para rodar localmente sem Docker/PostgreSQL/Redis.
Usa SQLite e desativa Celery.
"""

from pathlib import Path

from .dev import *  # noqa: F401, F403

# SQLite em vez de PostgreSQL
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(__file__).resolve().parent.parent.parent / "db.sqlite3",
    }
}

# Desativa Celery (nao precisa de Redis para dev local)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
