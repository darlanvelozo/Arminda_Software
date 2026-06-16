"""URLs do app payroll (rotas tenant — exigem header X-Tenant)."""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.payroll.views import (
    ComplementarItemViewSet,
    FeriasItemViewSet,
    FolhaViewSet,
    LancamentoViewSet,
    LicencaPremioItemViewSet,
    RegimePrevidenciarioViewSet,
    RubricaViewSet,
)

app_name = "payroll"

router = DefaultRouter()
router.register("rubricas", RubricaViewSet, basename="rubrica")
router.register("folhas", FolhaViewSet, basename="folha")
router.register("lancamentos", LancamentoViewSet, basename="lancamento")
router.register(
    "regimes-previdenciarios", RegimePrevidenciarioViewSet, basename="regime-previdenciario"
)
router.register("ferias-itens", FeriasItemViewSet, basename="ferias-item")
router.register("licenca-premio-itens", LicencaPremioItemViewSet, basename="licenca-premio-item")
router.register("complementar-itens", ComplementarItemViewSet, basename="complementar-item")

urlpatterns = [path("", include(router.urls))]
