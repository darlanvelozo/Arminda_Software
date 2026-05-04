"""
Management command — Importa cadastros do Fiorilli SIP (Firebird → Postgres).

Uso típico:
  python manage.py import_fiorilli_sip \\
    --tenant mun_sao_raimundo \\
    --host 127.0.0.1 --port 13050 \\
    --database /firebird/data/SIP.FDB \\
    --user FSCSIP --password fscpw \\
    --tabelas cargos,lotacoes,servidores,vinculos,dependentes \\
    --dry-run

Depende: Firebird 2.5 server rodando em $host:$port com $database montado.
Veja docs/adr/0009-importador-fiorilli-sip.md para o procedimento completo.
"""

from __future__ import annotations

import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django_tenants.utils import schema_context

from apps.core.models import Municipio
from apps.imports.adapters.firebird import (
    FirebirdConfig,
    fetch_cargos,
    fetch_dependentes,
    fetch_locais_trabalho,
    fetch_pessoas,
    fetch_trabalhadores,
    open_connection,
)
from apps.imports.services.loaders import LoaderStats
from apps.imports.services.loaders.cargos import load_cargos
from apps.imports.services.loaders.dependentes import load_dependentes
from apps.imports.services.loaders.lotacoes import load_lotacoes
from apps.imports.services.loaders.servidores import load_servidores
from apps.imports.services.loaders.vinculos import load_vinculos

# Ordem de importação respeita dependências de FK:
#   cargos e lotacoes não dependem de nada
#   servidores não depende
#   vinculos depende de cargos + lotacoes + servidores
#   dependentes depende de servidores
TABELAS_VALIDAS = ("cargos", "lotacoes", "servidores", "vinculos", "dependentes")


class Command(BaseCommand):
    help = "Importa cadastros do Fiorilli SIP (Firebird) para o schema tenant."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", required=True, help="schema_name do município destino")
        parser.add_argument("--host", default="127.0.0.1")
        parser.add_argument("--port", type=int, default=3050)
        parser.add_argument("--database", required=True, help="caminho do .FDB no servidor FB")
        parser.add_argument("--user", default="SYSDBA")
        parser.add_argument(
            "--password",
            default=None,
            help="senha do usuário FB (ou env SIP_PASSWORD)",
        )
        parser.add_argument(
            "--tabelas",
            default=",".join(TABELAS_VALIDAS),
            help=(
                "lista separada por vírgula. Padrão: todas em ordem de FK. "
                f"Opções: {', '.join(TABELAS_VALIDAS)}"
            ),
        )
        parser.add_argument(
            "--limit", type=int, default=None, help="processa apenas as N primeiras linhas (debug)"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="executa o pipeline mas faz rollback no fim",
        )

    def handle(self, *args, **opts):
        tenant_schema = opts["tenant"]
        try:
            municipio = Municipio.objects.get(schema_name=tenant_schema)
        except Municipio.DoesNotExist:
            raise CommandError(
                f"Tenant '{tenant_schema}' não existe. Crie o município antes de importar."
            )

        password = opts["password"] or os.environ.get("SIP_PASSWORD")
        if not password:
            raise CommandError(
                "Senha do FDB obrigatória — passe --password ou defina env SIP_PASSWORD."
            )

        config = FirebirdConfig(
            host=opts["host"],
            port=opts["port"],
            database=opts["database"],
            user=opts["user"],
            password=password,
        )

        tabelas_pedidas = [t.strip() for t in opts["tabelas"].split(",") if t.strip()]
        invalidas = [t for t in tabelas_pedidas if t not in TABELAS_VALIDAS]
        if invalidas:
            raise CommandError(
                f"Tabela(s) inválida(s): {invalidas}. Use: {TABELAS_VALIDAS}"
            )

        # Reordena para respeitar dependências, sem perder seleção do usuário
        tabelas = [t for t in TABELAS_VALIDAS if t in tabelas_pedidas]

        self.stdout.write(
            self.style.NOTICE(
                f"Importador Fiorilli SIP → {municipio.nome}/{municipio.uf} "
                f"(schema={tenant_schema})"
            )
        )
        self.stdout.write(f"Tabelas: {', '.join(tabelas)}")
        if opts["dry_run"]:
            self.stdout.write(self.style.WARNING("DRY-RUN: nada será persistido."))
        self.stdout.write("")

        all_stats: list[LoaderStats] = []

        class _DryRunRollback(Exception):
            """Exceção interna para forçar rollback do `transaction.atomic` em dry-run."""

        with open_connection(config) as conn:
            with schema_context(tenant_schema):
                if opts["dry_run"]:
                    # Wrap em atomic + raise no fim → o rollback é garantido,
                    # diferente de `savepoint_rollback` solto (que é no-op
                    # fora de bloco atômico, em autocommit).
                    try:
                        with transaction.atomic():
                            all_stats = self._executar(conn, tabelas, limit=opts["limit"])
                            raise _DryRunRollback()
                    except _DryRunRollback:
                        pass
                else:
                    all_stats = self._executar(conn, tabelas, limit=opts["limit"])

        self._imprime_relatorio(all_stats, dry_run=opts["dry_run"])

    def _executar(self, conn, tabelas: list[str], *, limit: int | None) -> list[LoaderStats]:
        stats: list[LoaderStats] = []

        for tabela in tabelas:
            self.stdout.write(f"-> Importando {tabela}...")
            if tabela == "cargos":
                rows = fetch_cargos(conn, limit=limit)
                stats.append(load_cargos(rows))
            elif tabela == "lotacoes":
                rows = fetch_locais_trabalho(conn, limit=limit)
                stats.append(load_lotacoes(rows))
            elif tabela == "servidores":
                rows = fetch_pessoas(conn, limit=limit)
                stats.append(load_servidores(rows))
            elif tabela == "vinculos":
                rows = fetch_trabalhadores(conn, limit=limit)
                stats.append(load_vinculos(rows))
            elif tabela == "dependentes":
                rows = fetch_dependentes(conn, limit=limit)
                stats.append(load_dependentes(rows))

        return stats

    def _imprime_relatorio(self, stats: list[LoaderStats], *, dry_run: bool) -> None:
        self.stdout.write("")
        self.stdout.write(self.style.NOTICE("=== Relatório ==="))
        total_erros = 0
        for s in stats:
            line = s.resumo()
            style = self.style.ERROR if s.erros > 0 else self.style.SUCCESS
            self.stdout.write(style(line))
            total_erros += s.erros

        if total_erros > 0:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING(f"Erros detalhados (até 20):"))
            mostrados = 0
            for s in stats:
                for msg in s.mensagens_erro:
                    if mostrados >= 20:
                        break
                    self.stdout.write(f"  - [{s.tipo}] {msg}")
                    mostrados += 1
                if mostrados >= 20:
                    break
            if total_erros > 20:
                self.stdout.write(
                    f"  ... e mais {total_erros - 20} erro(s) — consulte SipImportRecord."
                )

        self.stdout.write("")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN: rollback aplicado, nada persistiu."))
        elif total_erros == 0:
            self.stdout.write(self.style.SUCCESS("Importação concluída sem erros."))
        else:
            self.stdout.write(
                self.style.WARNING(f"Importação concluída com {total_erros} erro(s).")
            )
