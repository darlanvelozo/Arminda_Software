"""
Views para gestão de usuários do município (Onda 1.5).

Apenas `admin_municipio` (e `staff_arminda` como override) podem operar.
Escopo é o tenant resolvido pelo middleware via cabeçalho `X-Tenant`.
"""

from __future__ import annotations

from django_tenants.utils import schema_context
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.models import UsuarioMunicipioPapel
from apps.core.permissions import IsAdminMunicipio
from apps.core.users.serializers import (
    UsuarioMunicipioPapelCreateSerializer,
    UsuarioMunicipioPapelListSerializer,
    UsuarioMunicipioPapelUpdateSerializer,
)


class UsuarioMunicipioPapelViewSet(viewsets.ModelViewSet):
    """
    CRUD de usuários do município ativo (associação User × Município × Group).

    GET    /api/core/usuarios/         lista papéis do tenant
    POST   /api/core/usuarios/         cria User + papel (atômico)
    PATCH  /api/core/usuarios/{id}/    troca papel
    DELETE /api/core/usuarios/{id}/    remove papel (não deleta o User)
    """

    permission_classes = [IsAuthenticated, IsAdminMunicipio]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        # Filtra por tenant resolvido pelo middleware
        tenant = getattr(self.request, "tenant", None)
        if tenant is None:
            return UsuarioMunicipioPapel.objects.none()
        return (
            UsuarioMunicipioPapel.objects.filter(municipio=tenant)
            .select_related("usuario", "grupo", "municipio")
            .order_by("usuario__nome_completo", "usuario__email")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return UsuarioMunicipioPapelCreateSerializer
        if self.action in ("update", "partial_update"):
            return UsuarioMunicipioPapelUpdateSerializer
        return UsuarioMunicipioPapelListSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        ser = self.get_serializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        papel = ser.save()
        # Re-serializa no shape de listagem para o cliente
        return Response(
            UsuarioMunicipioPapelListSerializer(papel).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        ser = self.get_serializer(instance, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        papel = ser.save()
        return Response(UsuarioMunicipioPapelListSerializer(papel).data)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        # Apenas remove o papel; não deleta User (pode ter papéis em outros tenants)
        with schema_context("public"):
            instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
