"""
Management command — Paridade Fiorilli (Onda 2.7, fecha o Bloco 2).

Compara o cálculo tributário do Arminda contra a folha real publicada
pelo SIP (tabela BASES), competência a competência. Só leitura do
Firebird; nada é persistido. O relatório é agregado e sem PII.

Uso:
  python manage.py paridade_fiorilli \\
    --host 127.0.0.1 --port 3050 \\
    --database /var/lib/firebird/3.0/data/sjb.fdb \\
    --user paridade --password ... \\
    --auth-plugin Legacy_Auth --no-wire-crypt \\
    --listar                 # lista competências disponíveis
    # ou
    --referencia 232         # compara a competência de CODIGO 232

Veja docs/adr/0021-licoes-base-fiorilli.md e a Onda 2.7 no ROADMAP.
"""

from __future__ import annotations

import os
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from apps.imports.adapters.firebird import (
    FirebirdConfig,
    fetch_bases_competencia,
    fetch_referencias,
    open_connection,
)
from apps.imports.services.paridade import RelatorioParidade, comparar_competencia


class Command(BaseCommand):
    help = "Compara o cálculo tributário do Arminda contra a folha real do SIP (BASES)."

    def add_arguments(self, parser):
        parser.add_argument("--host", default="127.0.0.1")
        parser.add_argument("--port", type=int, default=3050)
        parser.add_argument("--database", required=True, help="caminho do .FDB")
        parser.add_argument("--user", default="SYSDBA")
        parser.add_argument("--password", default=None, help="senha (ou env SIP_PASSWORD)")
        parser.add_argument("--auth-plugin", default=None)
        parser.add_argument("--no-wire-crypt", action="store_true")
        parser.add_argument(
            "--listar", action="store_true", help="lista competências (REFERENCIA) e sai"
        )
        parser.add_argument(
            "--referencia", type=int, default=None, help="CODIGO da competência a comparar"
        )
        parser.add_argument(
            "--ano", type=int, default=None, help="filtra --listar por ano"
        )

    def handle(self, *args, **opts):
        password = opts["password"] or os.environ.get("SIP_PASSWORD")
        if not password:
            raise CommandError("Senha obrigatória — passe --password ou env SIP_PASSWORD.")

        config = FirebirdConfig(
            host=opts["host"],
            port=opts["port"],
            database=opts["database"],
            user=opts["user"],
            password=password,
            auth_plugin_name=opts.get("auth_plugin"),
            wire_crypt=not opts.get("no_wire_crypt"),
        )

        with open_connection(config) as conn:
            if opts["listar"] or not opts.get("referencia"):
                self._listar(conn, ano=opts.get("ano"))
                if not opts.get("referencia"):
                    return

            referencia = opts["referencia"]
            refs = {str(r["codigo"]): r for r in fetch_referencias(conn)}
            ref = refs.get(str(referencia))
            if ref is None:
                raise CommandError(f"REFERENCIA {referencia} não existe.")
            competencia = date(int(ref["ano"]), int(ref["mes"]), 1)

            self.stdout.write(
                self.style.NOTICE(
                    f"\nComparando competência {ref['ano']}-{int(ref['mes']):02d} "
                    f"(REFERENCIA {referencia})..."
                )
            )
            bases = fetch_bases_competencia(conn, referencia)

        rel = comparar_competencia(competencia=competencia, bases=bases)
        self._imprimir_relatorio(rel)

    def _listar(self, conn, *, ano: int | None) -> None:
        self.stdout.write(self.style.NOTICE("Competências disponíveis (mensais):"))
        for r in fetch_referencias(conn):
            if str(r.get("tipo", "")).strip() != "1":
                continue
            if ano and int(r["ano"]) != ano:
                continue
            self.stdout.write(
                f"  cod={r['codigo']:>4}  {r['ano']}-{int(r['mes']):02d}  "
                f"({r['qtd_bases']} servidores)"
            )

    def _imprimir_relatorio(self, rel: RelatorioParidade) -> None:
        w = self.stdout.write
        w("")
        w(self.style.NOTICE("=" * 60))
        w(self.style.NOTICE(f"  PARIDADE FIORILLI — {rel.competencia.strftime('%m/%Y')}"))
        w(self.style.NOTICE("=" * 60))
        w(f"Servidores na competência: {rel.total_servidores}")
        w("Regime previdenciário: " + ", ".join(
            f"{k}={v}" for k, v in sorted(rel.regimes.items())
        ))
        w("")

        for nome, t in rel.tributos.items():
            cor = self.style.SUCCESS if t.taxa_acerto >= 95 else (
                self.style.WARNING if t.taxa_acerto >= 50 else self.style.ERROR
            )
            w(cor(f"[{nome}]"))
            w(f"  comparados: {t.comparados}")
            w(cor(f"  exatos (≤1¢): {t.exatos}  ({t.taxa_acerto:.1f}%)"))
            if t.divergentes:
                media = (t.soma_abs_divergencia / t.divergentes) if t.divergentes else 0
                w(f"  divergentes: {t.divergentes}  "
                  f"(média R${media:.2f}, máx R${t.maior_divergencia:.2f})")
                w("  faixas: " + ", ".join(
                    f"{k}={v}" for k, v in sorted(t.faixas.items())
                ))
            w("")

        if rel.residuo_rpps:
            w(self.style.NOTICE("[Resíduo previdência — casos RPPS (config do tenant)]"))
            for cat, n in sorted(rel.residuo_rpps.items(), key=lambda kv: -kv[1]):
                w(f"  {cat}: {n}")
            w("")

        if rel.rpps_aliquotas:
            w(self.style.NOTICE("[Previdência — alíquota efetiva observada (SIP)]"))
            top = sorted(rel.rpps_aliquotas.items(), key=lambda kv: -kv[1])[:8]
            for aliq, n in top:
                w(f"  {float(aliq) * 100:.2f}%  →  {n} servidores")
            w("")
