"""
URLs principais do Arminda.

Cada app tem seu próprio urls.py incluído aqui sob um prefixo.
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


def health_check(_request):
    """Endpoint simples de healthcheck."""
    return JsonResponse({"status": "ok", "service": "arminda"})


urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Healthcheck
    path("health/", health_check, name="health"),
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
