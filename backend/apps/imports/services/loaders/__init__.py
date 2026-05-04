"""
Loaders — uma função por entidade que recebe rows brutos do SIP e persiste
no Arminda usando `update_or_create` (idempotente).

Cada loader retorna `LoaderStats` com contagens (lidos, criados, atualizados,
erros) para o relatório final do command.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from apps.imports.models import SipImportRecord, StatusImportacao


@dataclass
class LoaderStats:
    """Contadores e erros de uma execução de loader."""

    tipo: str
    lidos: int = 0
    criados: int = 0
    atualizados: int = 0
    inalterados: int = 0
    erros: int = 0
    mensagens_erro: list[str] = field(default_factory=list)

    @property
    def ok(self) -> int:
        return self.criados + self.atualizados + self.inalterados

    def log_erro(self, msg: str) -> None:
        self.erros += 1
        self.mensagens_erro.append(msg)

    def resumo(self) -> str:
        return (
            f"{self.tipo}: {self.lidos} lidos · "
            f"{self.ok} ok ({self.criados} novos, {self.atualizados} atualizados, "
            f"{self.inalterados} sem mudança) · {self.erros} erros"
        )


def grava_sucesso(tipo: str, chave: str, arminda_id: int, payload_hash_str: str) -> None:
    """Registra (ou atualiza) um SipImportRecord com status OK."""
    SipImportRecord.objects.update_or_create(
        tipo=tipo,
        chave_sip=chave,
        defaults={
            "arminda_id": arminda_id,
            "payload_sip_hash": payload_hash_str,
            "status": StatusImportacao.OK,
            "erro_mensagem": "",
        },
    )


def grava_erro(tipo: str, chave: str, mensagem: str) -> None:
    """Registra (ou atualiza) um SipImportRecord com status ERRO."""
    SipImportRecord.objects.update_or_create(
        tipo=tipo,
        chave_sip=chave,
        defaults={
            "arminda_id": None,
            "status": StatusImportacao.ERRO,
            "erro_mensagem": mensagem[:2000],
        },
    )
