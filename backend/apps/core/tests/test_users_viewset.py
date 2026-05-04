"""
Testes do CRUD de usuários do município — /api/core/usuarios/ (Onda 1.5).

Apenas admin_municipio + staff_arminda podem operar. Cada item da listagem
representa um par (User × papel) no tenant ativo.
"""

from __future__ import annotations

import pytest


@pytest.mark.django_db
class TestListagem:
    def test_admin_lista_papeis_do_seu_tenant(
        self,
        api_client_factory,
        usuario_factory,
        usuario_admin_a,
        tenant_a,
        tenant_b,
    ):
        # Cria 2 usuários no tenant_a + 1 no tenant_b
        usuario_factory(
            email="rh-a-1@arminda.test", papeis=[(tenant_a, "rh_municipio")]
        )
        usuario_factory(
            email="leitura-a-1@arminda.test",
            papeis=[(tenant_a, "leitura_municipio")],
        )
        usuario_factory(
            email="rh-b-1@arminda.test", papeis=[(tenant_b, "rh_municipio")]
        )

        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        response = client.get("/api/core/usuarios/")
        assert response.status_code == 200
        data = response.json()
        emails = {item["usuario"]["email"] for item in data["results"]}
        # Apenas papéis do tenant_a (incluindo o próprio admin)
        assert "rh-a-1@arminda.test" in emails
        assert "leitura-a-1@arminda.test" in emails
        assert "rh-b-1@arminda.test" not in emails

    def test_rh_nao_pode_listar(
        self, api_client_factory, usuario_rh_a, tenant_a
    ):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        response = client.get("/api/core/usuarios/")
        assert response.status_code == 403

    def test_sem_auth_falha(self, api_client, tenant_a):
        api_client.defaults["HTTP_X_TENANT"] = tenant_a.schema_name
        response = api_client.get("/api/core/usuarios/")
        assert response.status_code == 401


@pytest.mark.django_db
class TestCriacao:
    def test_admin_cria_user_com_papel(
        self, api_client_factory, usuario_admin_a, tenant_a
    ):
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        response = client.post(
            "/api/core/usuarios/",
            {
                "email": "novinha@arminda.test",
                "nome_completo": "Maria Nova",
                "papel": "rh_municipio",
                "senha_temporaria": "senha-segura-456",
            },
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["usuario"]["email"] == "novinha@arminda.test"
        assert data["papel"] == "rh_municipio"
        assert data["usuario"]["precisa_trocar_senha"] is True

    def test_email_existente_reaproveita_user_e_atribui_novo_papel(
        self,
        api_client_factory,
        usuario_admin_a,
        usuario_admin_b,
        usuario_factory,
        tenant_a,
        tenant_b,
    ):
        # User já existe com papel no tenant_b
        usuario_factory(
            email="ja-existe@arminda.test",
            papeis=[(tenant_b, "rh_municipio")],
        )
        # Admin de tenant_a o adiciona ao seu tenant
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        response = client.post(
            "/api/core/usuarios/",
            {
                "email": "ja-existe@arminda.test",
                "nome_completo": "Já Existe",
                "papel": "leitura_municipio",
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.json()["papel"] == "leitura_municipio"

    def test_nao_permite_atribuir_staff_arminda(
        self, api_client_factory, usuario_admin_a, tenant_a
    ):
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        response = client.post(
            "/api/core/usuarios/",
            {
                "email": "x@x.test",
                "nome_completo": "X",
                "papel": "staff_arminda",
            },
            format="json",
        )
        assert response.status_code == 400

    def test_papel_invalido_falha(
        self, api_client_factory, usuario_admin_a, tenant_a
    ):
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        response = client.post(
            "/api/core/usuarios/",
            {
                "email": "x@x.test",
                "nome_completo": "X",
                "papel": "papel_inexistente",
            },
            format="json",
        )
        assert response.status_code == 400

    def test_rh_nao_pode_criar(
        self, api_client_factory, usuario_rh_a, tenant_a
    ):
        client = api_client_factory(user=usuario_rh_a, tenant=tenant_a)
        response = client.post(
            "/api/core/usuarios/",
            {
                "email": "novo@x.test",
                "nome_completo": "Novo",
                "papel": "leitura_municipio",
            },
            format="json",
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestEdicao:
    def test_admin_troca_papel(
        self,
        api_client_factory,
        usuario_admin_a,
        usuario_factory,
        tenant_a,
    ):
        user = usuario_factory(
            email="alguem@arminda.test", papeis=[(tenant_a, "leitura_municipio")]
        )
        from apps.core.models import UsuarioMunicipioPapel

        papel_id = UsuarioMunicipioPapel.objects.get(
            usuario=user, municipio=tenant_a
        ).id
        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        response = client.patch(
            f"/api/core/usuarios/{papel_id}/",
            {"papel": "rh_municipio"},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["papel"] == "rh_municipio"


@pytest.mark.django_db
class TestRemocao:
    def test_admin_remove_papel_mas_nao_deleta_user(
        self,
        api_client_factory,
        usuario_admin_a,
        usuario_factory,
        tenant_a,
        tenant_b,
    ):
        from apps.core.models import User, UsuarioMunicipioPapel

        # User existe em 2 tenants
        user = usuario_factory(
            email="bi-tenant@arminda.test",
            papeis=[
                (tenant_a, "leitura_municipio"),
                (tenant_b, "rh_municipio"),
            ],
        )
        papel_a_id = UsuarioMunicipioPapel.objects.get(
            usuario=user, municipio=tenant_a
        ).id

        client = api_client_factory(user=usuario_admin_a, tenant=tenant_a)
        response = client.delete(f"/api/core/usuarios/{papel_a_id}/")
        assert response.status_code == 204

        # User não foi deletado
        assert User.objects.filter(email="bi-tenant@arminda.test").exists()
        # Papel no tenant_a sumiu
        assert not UsuarioMunicipioPapel.objects.filter(
            usuario=user, municipio=tenant_a
        ).exists()
        # Papel no tenant_b continua
        assert UsuarioMunicipioPapel.objects.filter(
            usuario=user, municipio=tenant_b
        ).exists()
