"""URLs de gestão de usuários do município (escopo tenant — exige X-Tenant)."""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.core.users.views import UsuarioMunicipioPapelViewSet

app_name = "users"

router = DefaultRouter()
router.register("usuarios", UsuarioMunicipioPapelViewSet, basename="usuario")

urlpatterns = [path("", include(router.urls))]
