"""
Teste de performance baseline (Bloco 1.2 — Onda 2).

Gate: 100 servidores criados via API < 30 segundos.
Roda apenas com -m perf para nao penalizar a CI normal.
"""

from __future__ import annotations

import time

import pytest


@pytest.mark.perf
@pytest.mark.django_db
def test_cria_100_servidores_em_menos_de_30s(api_client_factory, usuario_rh_a, tenant_a):
    """Garante que o pipeline serializer+view+models suporta carga inicial.

    Limite definido no ROADMAP do Bloco 1: importacao real do Fiorilli SIP
    (~16k servidores) deve completar em < 30 minutos. 100 em < 30s e o
    smoke equivalente deste pipeline.
    """
    client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
    inicio = time.perf_counter()

    for i in range(100):
        # CPFs sinteticos validos sao raros sem gerador; usamos o mesmo CPF
        # valido em payloads diferentes — model nao tem unique no CPF.
        response = client.post(
            "/api/people/servidores/",
            {
                "matricula": f"M{i:04d}",
                "nome": f"Servidor de Teste {i}",
                "cpf": "111.444.777-35",
                "data_nascimento": "1990-01-01",
                "sexo": "M",
                "ativo": True,
            },
            format="json",
        )
        assert response.status_code == 201, f"falha na iter {i}: {response.json()}"

    duracao = time.perf_counter() - inicio
    assert duracao < 30.0, (
        f"100 servidores levaram {duracao:.1f}s (limite 30s). "
        f"Vai estourar o gate de 30 min para 16k servidores no Bloco 1.4."
    )
