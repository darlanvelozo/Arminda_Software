"""
Excecoes de dominio do app people (Bloco 1.2 — Onda 3).

Todas carregam:
- mensagem em PT-BR (vai para usuario final)
- code estavel (vai para logs e clients que precisam tratar)

ViewSets traduzem para `rest_framework.exceptions.ValidationError(detail=str, code=...)`.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base para erros de dominio do app people.

    Convencao:
        raise SubError("mensagem em pt-br", code="CODIGO_ESTAVEL")

    Ou, mais comum, com `code` definido na subclasse:
        class MinhaErr(DomainError): code = "MEU_ERRO"
        raise MinhaErr("mensagem")
    """

    code: str = "ERRO_DOMINIO"

    def __init__(self, mensagem: str, *, code: str | None = None):
        super().__init__(mensagem)
        if code:
            self.code = code


# ============================================================
# Admissao
# ============================================================


class AdmissaoInvalidaError(DomainError):
    code = "ADMISSAO_INVALIDA"


# ============================================================
# Desligamento
# ============================================================


class DesligamentoInvalidoError(DomainError):
    code = "DESLIGAMENTO_INVALIDO"


# ============================================================
# Transferencia
# ============================================================


class TransferenciaInvalidaError(DomainError):
    code = "TRANSFERENCIA_INVALIDA"
