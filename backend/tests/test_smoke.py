"""
Smoke test — garante que o projeto Django sobe e os endpoints de health/status respondem.
"""

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
    """O endpoint /status/ retorna status 200 com checks de servicos."""
    url = reverse("status")
    response = api_client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "arminda"
    assert data["version"] == "0.1.0"
    assert "checks" in data
    assert "database" in data["checks"]
    assert data["checks"]["database"]["status"] == "ok"
    assert "uptime" in data
    assert "uptime_seconds" in data
