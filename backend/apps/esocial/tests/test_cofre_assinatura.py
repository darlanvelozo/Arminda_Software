"""
Testes do cofre de certificados + assinatura — Onda 4.2 (ADR-0022).

Usa um certificado **sintético** gerado no próprio teste (nunca um certificado
real — a senha não pode ir para o git).
"""

from __future__ import annotations

import datetime

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from django_tenants.utils import schema_context
from signxml import XMLVerifier

from apps.esocial.models import StatusEvento, TipoEvento
from apps.esocial.services.assinatura import SemCertificado, assinar_evento
from apps.esocial.services.cofre import (
    CertificadoInvalido,
    carregar_material,
    guardar_certificado,
)
from apps.esocial.services.geracao import gerar_evento
from apps.esocial.services.validacao import validar_xml
from apps.people.models import OrgaoEmissor

SENHA = "test1234"


def _pfx_teste(senha: str = SENHA) -> bytes:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nome = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "MUNICIPIO DE TESTE:12345678000190"),
    ])
    agora = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(nome).issuer_name(nome)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(agora - datetime.timedelta(days=1))
        .not_valid_after(agora + datetime.timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    return pkcs12.serialize_key_and_certificates(
        b"teste", key, cert, None, serialization.BestAvailableEncryption(senha.encode())
    )


def _orgao():
    return OrgaoEmissor.objects.create(
        nome="Prefeitura de Teste", cnpj="12.345.678/0001-90", cnae_principal="8411600",
    )


@pytest.mark.django_db
class TestCofre:
    def test_guarda_cifrado_e_extrai_metadados(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            orgao = _orgao()
            pfx = _pfx_teste()
            cert = guardar_certificado(orgao, pfx, SENHA)
            assert cert.cnpj == "12.345.678/0001-90"
            assert cert.validade_fim > cert.validade_inicio
            # cifrado: o conteúdo guardado NÃO é o PFX cru nem a senha em claro
            assert cert.arquivo_cifrado.encode() != pfx
            assert SENHA not in cert.senha_cifrada
            # e volta a decifrar corretamente
            material = carregar_material(cert)
            assert material.chave_privada is not None

    def test_senha_errada_falha(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            orgao = _orgao()
            with pytest.raises(CertificadoInvalido):
                guardar_certificado(orgao, _pfx_teste(), "senha-errada")


@pytest.mark.django_db
class TestAssinatura:
    def test_assina_evento_e_valida(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            orgao = _orgao()
            guardar_certificado(orgao, _pfx_teste(), SENHA)
            evento = gerar_evento(orgao, TipoEvento.S_1000)
            assinado = assinar_evento(evento)
            assert assinado.status == StatusEvento.ASSINADO
            assert "Signature" in assinado.xml
            # XSD (com assinatura) + verificação criptográfica
            validar_xml(assinado.xml, TipoEvento.S_1000)
            material = carregar_material(orgao.certificado)
            XMLVerifier().verify(
                assinado.xml.encode(),
                x509_cert=material.certificado.public_bytes(serialization.Encoding.PEM),
            )

    def test_assinar_sem_certificado_falha(self, tenant_a):
        with schema_context(tenant_a.schema_name):
            orgao = _orgao()
            evento = gerar_evento(orgao, TipoEvento.S_1000)
            with pytest.raises(SemCertificado):
                assinar_evento(evento)

    def test_api_upload_e_assinar(self, api_client_factory, usuario_factory, tenant_a):
        from django.core.files.uploadedfile import SimpleUploadedFile
        usuario = usuario_factory(
            email="fin@arminda.test", papeis=[(tenant_a, "financeiro_municipio")]
        )
        with schema_context(tenant_a.schema_name):
            orgao = _orgao()
            evento = gerar_evento(orgao, TipoEvento.S_1000)
        client = api_client_factory(user=usuario, tenant=tenant_a)
        arquivo = SimpleUploadedFile("cert.pfx", _pfx_teste(), content_type="application/x-pkcs12")
        r = client.post(
            "/api/esocial/certificados/upload/",
            {"orgao_emissor": orgao.id, "arquivo": arquivo, "senha": SENHA},
            format="multipart",
        )
        assert r.status_code == 201, r.json()
        # o cifrado nunca aparece na resposta
        assert "arquivo_cifrado" not in r.json() and "senha" not in r.json()
        r2 = client.post(f"/api/esocial/eventos/{evento.id}/assinar/")
        assert r2.status_code == 200, r2.json()
        assert r2.json()["status"] == "assinado"
