"""
Loader de Vínculo — TRABALHADOR (SIP) → apps.people.VinculoFuncional.

Resolve as FKs (servidor, cargo, lotação) lendo `SipImportRecord`
das entidades já importadas. Linhas que apontam para entidades
ausentes viram erros (sem interromper o batch).
"""

from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.imports.models import SipImportRecord, TipoEntidadeSip
from apps.imports.services.loaders import LoaderStats, grava_erro, grava_sucesso
from apps.imports.services.mapping import map_vinculo, payload_hash
from apps.people.models import UnidadeOrcamentaria, VinculoFuncional


def _resolver_unidade_orcamentaria(
    row: dict[str, Any], unidades_internas_map: dict[int, int]
) -> int | None:
    """Resolve a FK de unidade orçamentária via TRABALHADOR.DEPDESPESA."""
    dep_raw = row.get("depdespesa")
    try:
        dep_int = int(dep_raw) if dep_raw is not None else 0
    except (TypeError, ValueError):
        dep_int = 0
    return unidades_internas_map.get(dep_int)


def _resolver_fks_vinculo(
    row: dict[str, Any],
    *,
    chave_sip: str,
    cargos_map: dict,
    lotacoes_map: dict,
    servidores_map: dict,
    stats: LoaderStats,
) -> tuple[int, int, int] | None:
    """Resolve cargo_id, lotacao_id, servidor_id ou registra erro e devolve None."""
    empresa = str(row.get("empresa", "")).strip()
    cargo_codigo_sip = f"{empresa}-{str(row.get('cargoatual', '')).strip()}"
    lotacao_codigo_sip = f"{empresa}-LT-{str(row.get('local_trabalho', '')).strip()}"
    cpf_servidor = str(row.get("cpf", "")).strip()

    cargo_id = cargos_map.get(cargo_codigo_sip)
    lotacao_id = lotacoes_map.get(lotacao_codigo_sip)
    servidor_id = servidores_map.get(cpf_servidor)

    if cargo_id is None:
        msg = f"Cargo SIP '{cargo_codigo_sip}' não encontrado para vínculo {chave_sip}"
        stats.log_erro(msg)
        grava_erro(TipoEntidadeSip.VINCULO, chave_sip, msg)
        return None
    if lotacao_id is None:
        msg = f"Lotação SIP '{lotacao_codigo_sip}' não encontrada para vínculo {chave_sip}"
        stats.log_erro(msg)
        grava_erro(TipoEntidadeSip.VINCULO, chave_sip, msg)
        return None
    if servidor_id is None:
        msg = f"Servidor com CPF '{cpf_servidor}' não importado (vínculo {chave_sip})"
        stats.log_erro(msg)
        grava_erro(TipoEntidadeSip.VINCULO, chave_sip, msg)
        return None

    return cargo_id, lotacao_id, servidor_id


def load_vinculos(rows: list[dict[str, Any]], *, ano_unidade: int | None = None) -> LoaderStats:
    """
    Persiste TRABALHADORes como VínculosFuncionais.

    Pré-requisito: cargos e lotações já importados (via SipImportRecord).
    Pessoas devem estar importadas como Servidores via CPF.

    Se `ano_unidade` for informado e as unidades orçamentárias desse ano
    estiverem importadas, o vínculo recebe FK para a unidade correspondente
    (TRABALHADOR.DEPDESPESA → UnidadeOrcamentaria(codigo, ano)). Quando a
    unidade não existe (ex.: DEPDESPESA='000000'), o vínculo fica com a
    FK nula — sem erro.
    """
    stats = LoaderStats(tipo="vinculo")

    # Carrega os mapas (chave_sip → arminda_id) uma vez por batch.
    cargos_map = _build_id_map(TipoEntidadeSip.CARGO)
    lotacoes_map = _build_id_map(TipoEntidadeSip.LOTACAO)
    servidores_map = _build_id_map(TipoEntidadeSip.SERVIDOR)
    # Para vinculo → unidade orçamentária, o JOIN é TRABALHADOR.DEPDESPESA
    # (int) = UnidadeOrcamentaria.codigo_interno_sip (PK interno do Fiorilli),
    # NÃO o codigo VARCHAR. Construímos um mapa direto pelo banco — mais simples
    # que usar SipImportRecord.chave_sip neste caso.
    unidades_internas_map: dict[int, int] = {}
    if ano_unidade:
        unidades_internas_map = {
            u.codigo_interno_sip: u.id
            for u in UnidadeOrcamentaria.objects.filter(ano=ano_unidade)
            .exclude(codigo_interno_sip=None)
            .only("id", "codigo_interno_sip")
        }

    for row in rows:
        stats.lidos += 1
        empresa = str(row.get("empresa", "")).strip()
        registro = str(row.get("registro", "")).strip()
        chave_sip = f"{empresa}-{registro}"

        fks = _resolver_fks_vinculo(
            row,
            chave_sip=chave_sip,
            cargos_map=cargos_map,
            lotacoes_map=lotacoes_map,
            servidores_map=servidores_map,
            stats=stats,
        )
        if fks is None:
            continue
        cargo_id, lotacao_id, servidor_id = fks

        unidade_orcamentaria_id: int | None = None
        if ano_unidade and unidades_internas_map:
            unidade_orcamentaria_id = _resolver_unidade_orcamentaria(row, unidades_internas_map)

        try:
            chave_sip, defaults = map_vinculo(
                row,
                servidor_id=servidor_id,
                cargo_id=cargo_id,
                lotacao_id=lotacao_id,
                unidade_orcamentaria_id=unidade_orcamentaria_id,
            )
        except Exception as exc:
            stats.log_erro(f"map_vinculo falhou: {exc} (chave={chave_sip})")
            grava_erro(TipoEntidadeSip.VINCULO, chave_sip, str(exc))
            continue

        try:
            with transaction.atomic():
                vinculo, created = VinculoFuncional.objects.update_or_create(
                    matricula_contrato=defaults["matricula_contrato"],
                    servidor_id=servidor_id,
                    defaults=defaults,
                )
                grava_sucesso(
                    TipoEntidadeSip.VINCULO,
                    chave_sip,
                    vinculo.id,
                    payload_hash(defaults),
                )
                if created:
                    stats.criados += 1
                else:
                    stats.atualizados += 1
        except Exception as exc:
            stats.log_erro(f"persistência de vínculo {chave_sip} falhou: {exc}")
            grava_erro(TipoEntidadeSip.VINCULO, chave_sip, str(exc))

    return stats


def _build_id_map(tipo: str) -> dict[str, int]:
    """
    Mapa chave_sip → arminda_id para uma entidade já importada.

    Para SERVIDOR a chave é o CPF (já é exatamente o que map_servidor usa).
    Para CARGO/LOTACAO a chave é '<EMPRESA>-<CODIGO>'.
    """
    qs = SipImportRecord.objects.filter(tipo=tipo, status="ok").exclude(arminda_id=None)
    return {r.chave_sip: r.arminda_id for r in qs}
