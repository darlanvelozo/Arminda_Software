"""
Validators de dominio brasileiro (Bloco 1.2).

Implementacao manual (sem dep externa) — algoritmos sao publicos e estaveis.
Cada validador:
- Aceita string com ou sem mascara/separadores.
- Levanta `django.core.exceptions.ValidationError` com mensagem em PT-BR
  e `code` estavel para clients tratarem.
- Tem teste cobrindo dois casos validos, dois invalidos e um edge.

Referencia matematica:
- CPF: https://www.macoratti.net/alg_cpf.htm
- PIS/PASEP: https://www.macoratti.net/alg_pis.htm
- Codigo IBGE: 7 digitos numericos (sem digito verificador formal aqui).
"""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError

# ============================================================
# CPF
# ============================================================


def _so_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def _cpf_digito(parcial: str, peso_inicial: int) -> int:
    """Calcula um digito verificador de CPF a partir do prefixo `parcial`."""
    soma = sum(int(d) * (peso_inicial - i) for i, d in enumerate(parcial))
    resto = (soma * 10) % 11
    return 0 if resto == 10 else resto


def validar_cpf(valor: str) -> str:
    """Valida CPF e retorna apenas digitos.

    Aceita '123.456.789-09' ou '12345678909'. Retorna '12345678909'.
    Levanta ValidationError com code=CPF_INVALIDO se invalido.
    """
    digitos = _so_digitos(valor)

    if len(digitos) != 11:
        raise ValidationError("CPF deve ter 11 digitos.", code="CPF_INVALIDO")

    if digitos == digitos[0] * 11:
        # CPFs com todos os digitos iguais sao matematicamente validos mas invalidos legalmente
        raise ValidationError("CPF invalido.", code="CPF_INVALIDO")

    d1 = _cpf_digito(digitos[:9], peso_inicial=10)
    d2 = _cpf_digito(digitos[:10], peso_inicial=11)

    if int(digitos[9]) != d1 or int(digitos[10]) != d2:
        raise ValidationError("CPF invalido.", code="CPF_INVALIDO")

    return digitos


# ============================================================
# PIS/PASEP/NIS/NIT
# ============================================================

_PESOS_PIS = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]


def validar_pis_pasep(valor: str) -> str:
    """Valida PIS/PASEP/NIS/NIT (mesmo algoritmo).

    Aceita '123.45678.90-1' ou '12345678901'. Retorna 11 digitos.
    Levanta ValidationError com code=PIS_INVALIDO se invalido.
    """
    digitos = _so_digitos(valor)

    if len(digitos) != 11:
        raise ValidationError("PIS/PASEP deve ter 11 digitos.", code="PIS_INVALIDO")

    if digitos == digitos[0] * 11:
        raise ValidationError("PIS/PASEP invalido.", code="PIS_INVALIDO")

    soma = sum(int(d) * peso for d, peso in zip(digitos[:10], _PESOS_PIS, strict=True))
    resto = soma % 11
    digito_esperado = 0 if resto < 2 else 11 - resto

    if int(digitos[10]) != digito_esperado:
        raise ValidationError("PIS/PASEP invalido.", code="PIS_INVALIDO")

    return digitos


# ============================================================
# Codigo IBGE
# ============================================================


def validar_codigo_ibge(valor: str) -> str:
    """Valida codigo IBGE de municipio (7 digitos numericos).

    O IBGE nao publica algoritmo de digito verificador padronizado para
    o codigo de municipio; validamos formato e UF coerente em camadas
    superiores (Bloco 4 quando precisar enviar eSocial).
    """
    digitos = _so_digitos(valor)

    if len(digitos) != 7:
        raise ValidationError("Codigo IBGE deve ter 7 digitos.", code="IBGE_INVALIDO")

    return digitos
