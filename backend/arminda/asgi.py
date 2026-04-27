"""
ASGI config para o projeto Arminda.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "arminda.settings.prod")

application = get_asgi_application()
