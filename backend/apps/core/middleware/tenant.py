"""
Middleware de resolucao de tenant (ADR-0006).

Estrategia hibrida:
- DEV / integracoes: header HTTP `X-Tenant: <schema_name | codigo_ibge>`
- PROD: hostname / subdominio (delegado ao TenantMainMiddleware do django-tenants)

Rotas publicas (em PUBLIC_PATH_PREFIXES) rodam no schema `public`.
"""

from __future__ import annotations

from django.db import connection
from django.http import HttpRequest, JsonResponse
from django_tenants.middleware.main import TenantMainMiddleware
from django_tenants.utils import get_tenant_model


class TenantHeaderOrHostMiddleware(TenantMainMiddleware):
    """Resolve tenant por header (dev) ou hostname (prod)."""

    PUBLIC_PATH_PREFIXES: tuple[str, ...] = (
        "/admin/",
        "/health/",
        "/status/",
        "/api/auth/",
        "/api/schema/",
        "/api/docs/",
        "/api/redoc/",
        "/static/",
        "/media/",
    )

    def process_request(self, request: HttpRequest):
        # Rotas publicas: forca schema public e segue o pipeline normal.
        # IMPORTANTE: nao setar request.tenant = None — a template tag
        # `is_public_schema` do django-tenants faz `hasattr(request, 'tenant')`
        # antes de acessar `.schema_name`. Atributo presente porem None quebra.
        # Solucao: deixar o atributo nao existir; a template tag entao retorna
        # True corretamente (nao tem tenant -> e public).
        if any(request.path.startswith(p) for p in self.PUBLIC_PATH_PREFIXES):
            connection.set_schema_to_public()
            return None

        # Tentativa 1: header X-Tenant
        tenant_header = request.headers.get("X-Tenant")
        if tenant_header:
            tenant = self._resolve_by_header(tenant_header)
            if tenant is None:
                return JsonResponse(
                    {
                        "detail": f"Tenant '{tenant_header}' nao encontrado",
                        "code": "TENANT_NAO_ENCONTRADO",
                    },
                    status=400,
                )
            request.tenant = tenant
            connection.set_tenant(tenant)
            return None

        # Tentativa 2: hostname (comportamento padrao do django-tenants)
        try:
            return super().process_request(request)
        except Exception:
            return JsonResponse(
                {
                    "detail": (
                        "Tenant nao resolvido. Envie o header X-Tenant ou use "
                        "subdominio configurado."
                    ),
                    "code": "TENANT_NAO_RESOLVIDO",
                },
                status=400,
            )

    @staticmethod
    def _resolve_by_header(header: str):
        """Aceita schema_name OU codigo_ibge no header."""
        Tenant = get_tenant_model()
        try:
            return Tenant.objects.get(schema_name=header)
        except Tenant.DoesNotExist:
            try:
                return Tenant.objects.get(codigo_ibge=header)
            except Tenant.DoesNotExist:
                return None
