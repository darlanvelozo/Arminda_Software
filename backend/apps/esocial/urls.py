"""URLs do app esocial (rotas tenant — exigem header X-Tenant)."""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.esocial.views import (
    CertificadoDigitalViewSet,
    EventoESocialViewSet,
    LoteESocialViewSet,
)

app_name = "esocial"

router = DefaultRouter()
router.register("eventos", EventoESocialViewSet, basename="evento-esocial")
router.register("certificados", CertificadoDigitalViewSet, basename="certificado-digital")
router.register("lotes", LoteESocialViewSet, basename="lote-esocial")

urlpatterns = [path("", include(router.urls))]
