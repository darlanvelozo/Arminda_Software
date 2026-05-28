"""URLs do app people (rotas tenant — exigem header X-Tenant)."""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.people.views import (
    CargoViewSet,
    DependenteViewSet,
    DocumentoViewSet,
    LotacaoViewSet,
    OrgaoEmissorViewSet,
    ServidorViewSet,
    SindicatoViewSet,
    VinculoFuncionalViewSet,
)

app_name = "people"

router = DefaultRouter()
router.register("cargos", CargoViewSet, basename="cargo")
router.register("lotacoes", LotacaoViewSet, basename="lotacao")
router.register("servidores", ServidorViewSet, basename="servidor")
router.register("vinculos", VinculoFuncionalViewSet, basename="vinculo")
router.register("dependentes", DependenteViewSet, basename="dependente")
router.register("documentos", DocumentoViewSet, basename="documento")
router.register("orgaos-emissores", OrgaoEmissorViewSet, basename="orgao-emissor")
router.register("sindicatos", SindicatoViewSet, basename="sindicato")

urlpatterns = [path("", include(router.urls))]
