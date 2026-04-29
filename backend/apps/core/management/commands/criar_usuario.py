"""
Management command: cria um User + opcionalmente associa papel a um Municipio.

Uso (usuario operacional de um municipio):
    python manage.py criar_usuario \\
        --email ana@prefeitura.ma.gov.br \\
        --password senha-segura-123 \\
        --nome "Ana Souza" \\
        --tenant mun_sao_raimundo \\
        --papel rh_municipio

Uso (membro da equipe Arminda — cross-tenant):
    python manage.py criar_usuario \\
        --email suporte@arminda.app \\
        --password senha-segura-456 \\
        --nome "Suporte Arminda" \\
        --staff-arminda

Senha pode vir de stdin com --senha-stdin (evita historico de shell).
"""

from __future__ import annotations

import sys
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models import Municipio, UsuarioMunicipioPapel
from apps.core.permissions import GRUPO_STAFF_ARMINDA, GRUPOS_BASE

User = get_user_model()

PAPEIS_MUNICIPIO = tuple(g for g in GRUPOS_BASE if g != GRUPO_STAFF_ARMINDA)


class Command(BaseCommand):
    help = "Cria um usuario do sistema. Associa papel a um municipio (opcional)."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="E-mail (login)")
        parser.add_argument(
            "--password",
            required=False,
            help="Senha. Se ausente, use --senha-stdin para ler do stdin.",
        )
        parser.add_argument(
            "--senha-stdin",
            action="store_true",
            help="Le a senha do stdin (evita expor em historico de shell).",
        )
        parser.add_argument("--nome", default="", help="Nome completo")
        parser.add_argument(
            "--tenant",
            default=None,
            help=("schema_name do municipio. Obrigatorio se --papel for " "informado."),
        )
        parser.add_argument(
            "--papel",
            default=None,
            choices=list(PAPEIS_MUNICIPIO),
            help="Papel no municipio (rh_municipio, etc.)",
        )
        parser.add_argument(
            "--staff-arminda",
            action="store_true",
            help="Marca como membro do time Arminda (cross-tenant).",
        )
        parser.add_argument(
            "--superuser",
            action="store_true",
            help="Marca como superuser do Django (acesso total ao admin).",
        )
        parser.add_argument(
            "--precisa-trocar-senha",
            action="store_true",
            help="Forca o usuario a trocar senha no proximo login.",
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:  # noqa: C901
        email: str = options["email"].strip().lower()
        nome: str = (options["nome"] or "").strip()
        tenant_schema: str | None = options["tenant"]
        papel: str | None = options["papel"]
        staff_arminda: bool = options["staff_arminda"]
        superuser: bool = options["superuser"]
        precisa_trocar_senha: bool = options["precisa_trocar_senha"]

        if papel and not tenant_schema:
            raise CommandError("--papel exige --tenant <schema_name>.")
        if tenant_schema and not papel:
            raise CommandError("--tenant exige --papel <grupo>.")

        password = self._resolver_senha(options)

        if User.objects.filter(email=email).exists():
            raise CommandError(f"Ja existe usuario com e-mail '{email}'.")

        # Resolve tenant (fora do bloco de criacao, para falhar cedo)
        municipio = None
        if tenant_schema:
            municipio = Municipio.objects.filter(schema_name=tenant_schema).first()
            if not municipio:
                raise CommandError(f"Tenant '{tenant_schema}' nao encontrado.")

        if superuser:
            user = User.objects.create_superuser(
                email=email,
                password=password,
                nome_completo=nome,
                precisa_trocar_senha=precisa_trocar_senha,
            )
        else:
            user = User.objects.create_user(
                email=email,
                password=password,
                nome_completo=nome,
                precisa_trocar_senha=precisa_trocar_senha,
            )

        if staff_arminda:
            grupo_staff, _ = Group.objects.get_or_create(name=GRUPO_STAFF_ARMINDA)
            user.groups.add(grupo_staff)

        if municipio and papel:
            grupo = Group.objects.get(name=papel)
            UsuarioMunicipioPapel.objects.create(usuario=user, municipio=municipio, grupo=grupo)

        self.stdout.write(self.style.SUCCESS(f"Usuario criado: {user.email}"))
        if staff_arminda:
            self.stdout.write("  - staff Arminda (cross-tenant)")
        if municipio and papel:
            self.stdout.write(f"  - papel '{papel}' em '{municipio.schema_name}'")

    def _resolver_senha(self, options: dict) -> str:
        if options["senha_stdin"]:
            self.stdout.write("Digite a senha (nao sera ecoada): ", ending="")
            self.stdout.flush()
            password = sys.stdin.readline().rstrip("\n")
        else:
            password = options.get("password") or ""
        if len(password) < 8:
            raise CommandError("Senha deve ter ao menos 8 caracteres.")
        return password
