"""URLs do app payroll (rotas tenant — exigem header X-Tenant)."""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.payroll.views import RubricaViewSet

app_name = "payroll"

router = DefaultRouter()
router.register("rubricas", RubricaViewSet, basename="rubrica")

urlpatterns = [path("", include(router.urls))]
