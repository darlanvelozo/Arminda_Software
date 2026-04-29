"""
URLs principais do Arminda.

Rotas publicas (rodam no schema `public`, sem tenant):
    /admin/                      Admin do Django
    /health/                     Healthcheck simples
    /status/                     Status detalhado
    /api/auth/*                  Login, refresh, logout, me
    /api/schema/                 OpenAPI schema
    /api/docs/                   Swagger UI
    /api/redoc/                  Redoc

Rotas tenant (exigem header X-Tenant ou subdominio):
    /api/core/*                  Operacoes administrativas do tenant
    /api/people/*                Servidores, cargos, lotacoes, vinculos
    /api/payroll/*               Rubricas, folhas, lancamentos
    /api/reports/*               Relatorios

A resolucao do tenant e feita pelo TenantHeaderOrHostMiddleware (ADR-0006).
"""

from __future__ import annotations

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
    """Endpoint simples de healthcheck (rota publica)."""
    return JsonResponse({"status": "ok", "service": "arminda"})


def status_page(_request):
    """Status com checks de servicos (rota publica)."""
    checks = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = {"status": "ok", "detail": "PostgreSQL respondendo"}
    except Exception as exc:
        checks["database"] = {"status": "error", "detail": str(exc)}

    uptime_seconds = int(time.time() - _start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    all_ok = all(c["status"] == "ok" for c in checks.values())

    return JsonResponse(
        {
            "status": "ok" if all_ok else "degraded",
            "service": "arminda",
            "version": "0.2.0-dev",
            "uptime": f"{hours}h {minutes}m {seconds}s",
            "uptime_seconds": uptime_seconds,
            "checks": checks,
        }
    )


urlpatterns = [
    # Public
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health"),
    path("status/", status_page, name="status"),
    # Auth (publica — login)
    path("api/auth/", include("apps.core.auth.urls")),
    # OpenAPI / Swagger (publica)
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
    # Tenant (exigem X-Tenant)
    path("api/core/", include("apps.core.urls")),
    path("api/people/", include("apps.people.urls")),
    path("api/payroll/", include("apps.payroll.urls")),
    path("api/reports/", include("apps.reports.urls")),
]
