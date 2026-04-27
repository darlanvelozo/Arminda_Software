"""
Fixtures globais para os testes do Arminda.
"""

import pytest


@pytest.fixture
def api_client():
    """Cliente de API DRF reutilizável."""
    from rest_framework.test import APIClient

    return APIClient()
