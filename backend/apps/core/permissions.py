"""
Permissions DRF base (ADR-0007).

`HasPapelInTenant` checa, no tenant resolvido pelo middleware (request.tenant),
se o usuario tem PELO MENOS UM dos papeis listados em `papeis`.

Subclasses concretas representam os papeis-base do produto.
`staff_arminda` e incluido em todas as subclasses como override global.
"""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from apps.core.models import UsuarioMunicipioPapel

GRUPO_STAFF_ARMINDA = "staff_arminda"
GRUPO_ADMIN_MUNICIPIO = "admin_municipio"
GRUPO_RH_MUNICIPIO = "rh_municipio"
GRUPO_FINANCEIRO_MUNICIPIO = "financeiro_municipio"
GRUPO_LEITURA_MUNICIPIO = "leitura_municipio"

GRUPOS_BASE = (
    GRUPO_STAFF_ARMINDA,
    GRUPO_ADMIN_MUNICIPIO,
    GRUPO_RH_MUNICIPIO,
    GRUPO_FINANCEIRO_MUNICIPIO,
    GRUPO_LEITURA_MUNICIPIO,
)


class IsStaffArminda(BasePermission):
    """Membro da equipe Arminda — superuser logico (cross-tenant via commands)."""

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            return False
        return user.groups.filter(name=GRUPO_STAFF_ARMINDA).exists()


class HasPapelInTenant(BasePermission):
    """Exige PELO MENOS UM dos papeis listados, no tenant atual.

    `staff_arminda` (Group no User, nao por municipio) e um override global:
    se o usuario tem esse Group no proprio User.groups, passa em qualquer tenant.
    """

    papeis: tuple[str, ...] = ()

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            return False
        # Override global: staff_arminda passa em qualquer tenant
        if user.groups.filter(name=GRUPO_STAFF_ARMINDA).exists():
            return True
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return False
        return UsuarioMunicipioPapel.objects.filter(
            usuario=user,
            municipio=tenant,
            grupo__name__in=self.papeis,
        ).exists()


class IsAdminMunicipio(HasPapelInTenant):
    papeis = (GRUPO_ADMIN_MUNICIPIO, GRUPO_STAFF_ARMINDA)


class IsRHMunicipio(HasPapelInTenant):
    papeis = (
        GRUPO_RH_MUNICIPIO,
        GRUPO_ADMIN_MUNICIPIO,
        GRUPO_STAFF_ARMINDA,
    )


class IsFinanceiroMunicipio(HasPapelInTenant):
    papeis = (
        GRUPO_FINANCEIRO_MUNICIPIO,
        GRUPO_ADMIN_MUNICIPIO,
        GRUPO_STAFF_ARMINDA,
    )


class IsLeituraMunicipio(HasPapelInTenant):
    papeis = (
        GRUPO_LEITURA_MUNICIPIO,
        GRUPO_RH_MUNICIPIO,
        GRUPO_FINANCEIRO_MUNICIPIO,
        GRUPO_ADMIN_MUNICIPIO,
        GRUPO_STAFF_ARMINDA,
    )
