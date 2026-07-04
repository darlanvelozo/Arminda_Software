"""
Cofre de certificados digitais (Onda 4.2 — ADR-0022).

Guarda o `.pfx` (e a senha) **cifrados com Fernet** no banco, por órgão. Extrai
metadados em claro para operação. `carregar_material` é uso interno (assinatura)
— nunca expor o PFX/senha por API nem em log.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import pkcs12
from django.conf import settings
from django.utils import timezone

from apps.esocial.models import CertificadoDigital
from apps.people.models import OrgaoEmissor


class CertificadoInvalido(Exception):
    """O PFX não abre com a senha, ou está expirado/malformado."""


@dataclass
class MaterialCertificado:
    chave_privada: object
    certificado: object
    cadeia: list


def _fernet() -> Fernet:
    return Fernet(settings.ESOCIAL_CERT_KEY.encode())


def _cnpj_do_certificado(cert) -> str:
    """Extrai o CNPJ do CN do e-CNPJ (formato NOME:CNPJ14)."""
    cn = cert.subject.rfc4514_string()
    m = re.search(r":(\d{14})", cn)
    if not m:
        return ""
    d = m.group(1)
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"


def _cn(nome) -> str:
    from cryptography.x509.oid import NameOID
    attrs = nome.get_attributes_for_oid(NameOID.COMMON_NAME)
    return attrs[0].value if attrs else nome.rfc4514_string()[:200]


def guardar_certificado(orgao: OrgaoEmissor, pfx_bytes: bytes, senha: str) -> CertificadoDigital:
    """Valida o PFX, extrai metadados, cifra e guarda (upsert por órgão)."""
    try:
        chave, cert, cadeia = pkcs12.load_key_and_certificates(pfx_bytes, senha.encode())
    except Exception as exc:  # noqa: BLE001 - erro de PFX/senha vira erro de domínio
        raise CertificadoInvalido("PFX não abre com a senha informada.") from exc
    if chave is None or cert is None:
        raise CertificadoInvalido("PFX sem chave privada ou certificado.")

    fim = cert.not_valid_after_utc
    if fim < timezone.now():
        raise CertificadoInvalido(f"Certificado expirado em {fim:%d/%m/%Y}.")

    f = _fernet()
    defaults = {
        "arquivo_cifrado": f.encrypt(pfx_bytes).decode(),
        "senha_cifrada": f.encrypt(senha.encode()).decode(),
        "titular": _cn(cert.subject),
        "cnpj": _cnpj_do_certificado(cert),
        "emissor": _cn(cert.issuer),
        "validade_inicio": cert.not_valid_before_utc,
        "validade_fim": fim,
        "thumbprint": cert.fingerprint(hashes.SHA1()).hex(),
    }
    obj, _ = CertificadoDigital.objects.update_or_create(
        orgao_emissor=orgao, defaults=defaults
    )
    return obj


def carregar_material(cert: CertificadoDigital) -> MaterialCertificado:
    """Decifra o PFX e devolve o material para assinatura (uso interno)."""
    f = _fernet()
    pfx = f.decrypt(cert.arquivo_cifrado.encode())
    senha = f.decrypt(cert.senha_cifrada.encode())
    chave, x509, cadeia = pkcs12.load_key_and_certificates(pfx, senha)
    return MaterialCertificado(chave_privada=chave, certificado=x509, cadeia=list(cadeia or []))
