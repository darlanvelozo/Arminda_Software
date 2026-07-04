"""
Assinatura digital de eventos eSocial (Onda 4.2 — ADR-0022).

Assina o XML do evento com XML-DSig **enveloped**, no padrão do eSocial:
`Reference URI=""` (documento inteiro), transformas enveloped-signature + C14N,
`RSA-SHA256`/`SHA256`. A `<Signature>` entra como último filho de `<eSocial>`.
O material do certificado vem do cofre (decifrado só em memória).
"""

from __future__ import annotations

from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)
from lxml import etree
from signxml import CanonicalizationMethod, DigestAlgorithm, SignatureMethod, XMLSigner, methods

from apps.esocial.models import EventoESocial, StatusEvento
from apps.esocial.services.cofre import MaterialCertificado, carregar_material
from apps.esocial.services.validacao import validar_xml


class SemCertificado(Exception):
    """O órgão não tem certificado no cofre."""


def _signer() -> XMLSigner:
    return XMLSigner(
        method=methods.enveloped,
        signature_algorithm=SignatureMethod.RSA_SHA256,
        digest_algorithm=DigestAlgorithm.SHA256,
        c14n_algorithm=CanonicalizationMethod.CANONICAL_XML_1_0,
    )


def assinar_xml(xml: str | bytes, material: MaterialCertificado) -> bytes:
    """Assina um XML de evento eSocial e devolve os bytes assinados."""
    root = etree.fromstring(xml.encode("utf-8") if isinstance(xml, str) else xml)
    key_pem = material.chave_privada.private_bytes(
        Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
    )
    cert_pem = material.certificado.public_bytes(Encoding.PEM)
    # Sem reference_uri → assina o documento inteiro com Reference URI="" (padrão eSocial).
    assinado = _signer().sign(root, key=key_pem, cert=cert_pem)
    return etree.tostring(assinado, xml_declaration=True, encoding="UTF-8")


def assinar_evento(evento: EventoESocial) -> EventoESocial:
    """Assina o evento com o certificado do órgão e revalida contra o XSD."""
    cert = getattr(evento.orgao_emissor, "certificado", None)
    if cert is None:
        raise SemCertificado("Órgão emissor não tem certificado no cofre.")
    material = carregar_material(cert)
    xml_assinado = assinar_xml(evento.xml, material)
    # Agora o documento tem a assinatura; valida contra o XSD (que a exige).
    validar_xml(xml_assinado, evento.tipo)
    evento.xml = xml_assinado.decode("utf-8")
    evento.status = StatusEvento.ASSINADO
    evento.save(update_fields=["xml", "status", "atualizado_em"])
    return evento
