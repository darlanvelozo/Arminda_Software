"""
Views de autenticacao (ADR-0007).

Endpoints publicos (rodam no schema `public`):
- POST /api/auth/login/    — recebe email+password, retorna tokens + user
- POST /api/auth/refresh/  — recebe refresh, retorna novo access (rotaciona)
- POST /api/auth/logout/   — blacklist o refresh token informado
- GET  /api/auth/me/       — usuario autenticado + papeis
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from apps.core.auth.serializers import (
    ArmindaTokenObtainPairSerializer,
    ChangePasswordSerializer,
    UserMeSerializer,
    UserMeUpdateSerializer,
)


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ — autentica e retorna tokens."""

    serializer_class = ArmindaTokenObtainPairSerializer
    permission_classes = [AllowAny]


class RefreshView(TokenRefreshView):
    """POST /api/auth/refresh/ — gera novo access a partir do refresh."""

    permission_classes = [AllowAny]


class LogoutView(APIView):
    """POST /api/auth/logout/ — blacklist o refresh token informado."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        refresh = request.data.get("refresh")
        if not refresh:
            return Response(
                {"detail": "Campo 'refresh' obrigatorio", "code": "REFRESH_AUSENTE"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except TokenError as exc:
            return Response(
                {"detail": str(exc), "code": "TOKEN_INVALIDO"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """GET/PATCH /api/auth/me/ — retorna ou edita o usuário autenticado."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(UserMeSerializer(request.user).data)

    def patch(self, request: Request) -> Response:
        ser = UserMeUpdateSerializer(request.user, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(UserMeSerializer(request.user).data)


class ChangePasswordView(APIView):
    """POST /api/auth/change-password/ — troca a senha do próprio usuário."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        ser = ChangePasswordSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
