"""URLs do app imports (tenant — exigem X-Tenant)."""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.imports.views import ImportadorCsvViewSet

app_name = "imports"

router = DefaultRouter()
router.register("csv", ImportadorCsvViewSet, basename="csv")

urlpatterns = [path("", include(router.urls))]
