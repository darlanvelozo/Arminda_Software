"""
URLs do app core (rotas tenant — exigem header X-Tenant).

Sub-rotas:
- usuarios/ — gestão de usuários do município (admin_municipio only)
"""

from __future__ import annotations

from django.urls import include, path

app_name = "core"

urlpatterns = [
    path("", include("apps.core.users.urls")),
]
