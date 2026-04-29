"""
Smoke test — endpoints publicos respondem sem tenant.
"""

from __future__ import annotations

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_health_endpoint(api_client):
    """O endpoint /health/ retorna status 200 e payload conhecido."""
    url = reverse("health")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "arminda"}


@pytest.mark.django_db
def test_status_endpoint(api_client):
    """O endpoint /status/ retorna 200 com checks de servicos."""
    url = reverse("status")
    response = api_client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "arminda"
    assert data["version"].startswith("0.")
    assert data["checks"]["database"]["status"] == "ok"
