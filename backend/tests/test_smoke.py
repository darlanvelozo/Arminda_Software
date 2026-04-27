"""
Smoke test — garante que o projeto Django sobe e o endpoint de health responde.
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
