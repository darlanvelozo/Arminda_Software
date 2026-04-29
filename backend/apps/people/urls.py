"""URLs do app people (rotas tenant — exigem header X-Tenant)."""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.people.views import CargoViewSet, LotacaoViewSet

app_name = "people"

router = DefaultRouter()
router.register("cargos", CargoViewSet, basename="cargo")
router.register("lotacoes", LotacaoViewSet, basename="lotacao")

urlpatterns = [path("", include(router.urls))]
