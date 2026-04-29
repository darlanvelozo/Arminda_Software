"""Testes dos validators de dominio brasileiro."""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError

from apps.core.validators import validar_codigo_ibge, validar_cpf, validar_pis_pasep


class TestValidarCpf:
    @pytest.mark.parametrize(
        "entrada",
        [
            "529.982.247-25",  # CPF valido conhecido
            "52998224725",
            "111.444.777-35",
            "11144477735",
        ],
    )
    def test_aceita_cpf_valido_com_e_sem_mascara(self, entrada):
        assert validar_cpf(entrada) == "".join(c for c in entrada if c.isdigit())

    @pytest.mark.parametrize(
        "entrada",
        [
            "111.111.111-11",  # todos digitos iguais
            "000.000.000-00",
            "123.456.789-00",  # digito errado
            "11144477734",  # digito 2 errado
        ],
    )
    def test_rejeita_cpf_invalido(self, entrada):
        with pytest.raises(ValidationError) as exc:
            validar_cpf(entrada)
        assert exc.value.code == "CPF_INVALIDO"

    @pytest.mark.parametrize("entrada", ["", "12345", "1234567890123"])
    def test_rejeita_tamanho_errado(self, entrada):
        with pytest.raises(ValidationError) as exc:
            validar_cpf(entrada)
        assert exc.value.code == "CPF_INVALIDO"


class TestValidarPisPasep:
    @pytest.mark.parametrize(
        "entrada",
        [
            "123.45678.90-0",  # sufixo 0 (resto < 2 -> digito = 0)
            "12345678900",
            "120.66566.55-3",  # outro caso valido
            "12066566553",
        ],
    )
    def test_aceita_pis_valido_com_e_sem_mascara(self, entrada):
        digitos_esperados = "".join(c for c in entrada if c.isdigit())
        assert validar_pis_pasep(entrada) == digitos_esperados

    @pytest.mark.parametrize(
        "entrada",
        [
            "111.11111.11-1",  # repetidos
            "12066566550",  # digito errado
            "12345678901",  # digito errado
        ],
    )
    def test_rejeita_pis_invalido(self, entrada):
        with pytest.raises(ValidationError) as exc:
            validar_pis_pasep(entrada)
        assert exc.value.code == "PIS_INVALIDO"

    @pytest.mark.parametrize("entrada", ["", "12345", "12345678901234"])
    def test_rejeita_tamanho_errado(self, entrada):
        with pytest.raises(ValidationError) as exc:
            validar_pis_pasep(entrada)
        assert exc.value.code == "PIS_INVALIDO"


class TestValidarCodigoIbge:
    @pytest.mark.parametrize("entrada", ["2110005", "2211001", "3550308"])
    def test_aceita_codigo_valido(self, entrada):
        assert validar_codigo_ibge(entrada) == entrada

    @pytest.mark.parametrize("entrada", ["", "123", "12345678"])
    def test_rejeita_tamanho_errado(self, entrada):
        with pytest.raises(ValidationError) as exc:
            validar_codigo_ibge(entrada)
        assert exc.value.code == "IBGE_INVALIDO"
