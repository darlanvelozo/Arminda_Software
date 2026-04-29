"""
Testes das permissions DRF base (ADR-0007).

HasPapelInTenant olha o tenant resolvido pelo middleware (request.tenant) e
checa UsuarioMunicipioPapel.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from apps.core.permissions import (
    HasPapelInTenant,
    IsAdminMunicipio,
    IsFinanceiroMunicipio,
    IsLeituraMunicipio,
    IsRHMunicipio,
    IsStaffArminda,
)


def _request(user, tenant):
    """Constroi um request mockado com user e tenant."""
    req = Mock()
    req.user = user
    req.tenant = tenant
    return req


@pytest.mark.django_db
class TestIsStaffArminda:
    def test_staff_arminda_passa(self, usuario_staff_arminda):
        perm = IsStaffArminda()
        assert perm.has_permission(_request(usuario_staff_arminda, None), None)

    def test_usuario_comum_falha(self, usuario_admin_a):
        perm = IsStaffArminda()
        assert not perm.has_permission(_request(usuario_admin_a, None), None)

    def test_anonimo_falha(self):
        perm = IsStaffArminda()
        anon = Mock(is_authenticated=False)
        assert not perm.has_permission(_request(anon, None), None)


@pytest.mark.django_db
class TestHasPapelInTenant:
    def test_admin_a_tem_admin_em_a(self, usuario_admin_a, tenant_a):
        perm = IsAdminMunicipio()
        assert perm.has_permission(_request(usuario_admin_a, tenant_a), None)

    def test_admin_a_nao_tem_admin_em_b(self, usuario_admin_a, tenant_b):
        """Admin de A nao tem papel em B — isolamento real."""
        perm = IsAdminMunicipio()
        assert not perm.has_permission(_request(usuario_admin_a, tenant_b), None)

    def test_staff_arminda_passa_em_qualquer_tenant(
        self, usuario_staff_arminda, tenant_a, tenant_b
    ):
        perm = IsAdminMunicipio()
        assert perm.has_permission(_request(usuario_staff_arminda, tenant_a), None)
        assert perm.has_permission(_request(usuario_staff_arminda, tenant_b), None)

    def test_rh_acessa_endpoint_de_rh(self, usuario_rh_a, tenant_a):
        perm = IsRHMunicipio()
        assert perm.has_permission(_request(usuario_rh_a, tenant_a), None)

    def test_leitura_nao_acessa_endpoint_rh(self, usuario_leitura_a, tenant_a):
        perm = IsRHMunicipio()
        assert not perm.has_permission(_request(usuario_leitura_a, tenant_a), None)

    def test_leitura_acessa_endpoint_de_leitura(self, usuario_leitura_a, tenant_a):
        perm = IsLeituraMunicipio()
        assert perm.has_permission(_request(usuario_leitura_a, tenant_a), None)

    def test_admin_acessa_endpoints_de_grupos_inferiores(self, usuario_admin_a, tenant_a):
        """admin_municipio passa em todas as permissions de menor privilegio."""
        for perm_class in [
            IsRHMunicipio,
            IsFinanceiroMunicipio,
            IsLeituraMunicipio,
        ]:
            assert perm_class().has_permission(
                _request(usuario_admin_a, tenant_a), None
            ), f"admin_municipio deveria passar em {perm_class.__name__}"

    def test_falta_de_tenant_falha(self, usuario_admin_a):
        perm = IsAdminMunicipio()
        assert not perm.has_permission(_request(usuario_admin_a, None), None)


@pytest.mark.django_db
class TestSubclassExigePapeisDefinidos:
    def test_subclass_sem_papeis_nao_passa(self, usuario_admin_a, tenant_a):
        class SemPapeis(HasPapelInTenant):
            papeis = ()

        perm = SemPapeis()
        assert not perm.has_permission(_request(usuario_admin_a, tenant_a), None)
