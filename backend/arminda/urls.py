"""
URLs principais do Arminda.

Cada app tem seu próprio urls.py incluído aqui sob um prefixo.
"""

import time

from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

_start_time = time.time()


def health_check(_request):
    """Endpoint simples de healthcheck."""
    return JsonResponse({"status": "ok", "service": "arminda"})


def status_page(_request):
    """Status page com verificação de serviços."""
    checks = {}

    # Check do banco de dados
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = {"status": "ok", "detail": "PostgreSQL respondendo"}
    except Exception as exc:
        checks["database"] = {"status": "error", "detail": str(exc)}

    # Uptime
    uptime_seconds = int(time.time() - _start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    all_ok = all(c["status"] == "ok" for c in checks.values())

    return JsonResponse(
        {
            "status": "ok" if all_ok else "degraded",
            "service": "arminda",
            "version": "0.1.0",
            "uptime": f"{hours}h {minutes}m {seconds}s",
            "uptime_seconds": uptime_seconds,
            "checks": checks,
        }
    )


urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Healthcheck & Status
    path("health/", health_check, name="health"),
    path("status/", status_page, name="status"),
    # API
    path("api/core/", include("apps.core.urls")),
    path("api/people/", include("apps.people.urls")),
    path("api/payroll/", include("apps.payroll.urls")),
    path("api/reports/", include("apps.reports.urls")),
    # OpenAPI / Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
