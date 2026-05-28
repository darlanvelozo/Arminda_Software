"""
Bulk update de Servidores e Vínculos (Onda 1.6b).

Usado para preencher em lote campos pré-eSocial — tipicamente após o
operador filtrar "cadastro incompleto", seleciona N servidores e aplica
uma única alteração (ex.: "todos da SEMSA passam a ter Sindicato X").

Regras:
- Só campos da whitelist são aceitos. Tentar atualizar `cpf`, `matricula`,
  `data_nascimento` etc. via bulk levanta DomainError (esses campos são
  individuais e devem passar pelo CRUD normal com validação completa).
- IDs inexistentes são ignorados, mas reportados no resultado.
- Roda dentro de transação atômica — ou aplica tudo, ou nada.
- Histórico (simple-history) é preservado: usamos `save()` por instância,
  não `update()` em queryset.
"""

from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.people.models import OrgaoEmissor, Servidor, Sindicato, VinculoFuncional
from apps.people.services.exceptions import DomainError

CAMPOS_SERVIDOR_BULK_PERMITIDOS: frozenset[str] = frozenset({
    "tipo_logradouro",
    "logradouro",
    "numero",
    "complemento",
    "bairro",
    "cidade",
    "uf",
    "cep",
    "nacionalidade",
    "raca",
    "estado_civil",
    "instrucao",
    "nome_pai",
    "nome_mae",
    "ativo",
})

CAMPOS_VINCULO_BULK_PERMITIDOS: frozenset[str] = frozenset({
    "orgao_emissor",
    "sindicato",
    "lotacao",
    "unidade_orcamentaria",
    "carga_horaria",
})

# Campos que carregam FK — aceitam id no payload e resolvem aqui.
FKS_VINCULO: dict[str, type] = {
    "orgao_emissor": OrgaoEmissor,
    "sindicato": Sindicato,
}


def _validar_whitelist(updates: dict[str, Any], permitidos: frozenset[str]) -> None:
    forbidden = set(updates.keys()) - permitidos
    if forbidden:
        raise DomainError(
            f"Campos não permitidos em bulk-update: {', '.join(sorted(forbidden))}",
            code="CAMPO_NAO_PERMITIDO",
        )


@transaction.atomic
def aplicar_bulk_update_servidores(*, ids: list[int], updates: dict[str, Any]) -> dict[str, Any]:
    """Aplica `updates` em cada Servidor referenciado por `ids`."""
    _validar_whitelist(updates, CAMPOS_SERVIDOR_BULK_PERMITIDOS)
    servidores = list(Servidor.objects.filter(id__in=ids))
    encontrados = {s.id for s in servidores}
    nao_encontrados = sorted(set(ids) - encontrados)
    atualizados = 0
    for servidor in servidores:
        mudou = False
        for campo, valor in updates.items():
            atual = getattr(servidor, campo)
            normalizado = valor.strip() if isinstance(valor, str) else valor
            if campo == "uf" and isinstance(normalizado, str):
                normalizado = normalizado.upper()
            if atual != normalizado:
                setattr(servidor, campo, normalizado)
                mudou = True
        if mudou:
            servidor.save()
            atualizados += 1
    return {
        "atualizados": atualizados,
        "ids_nao_encontrados": nao_encontrados,
        "total_solicitado": len(ids),
    }


@transaction.atomic
def aplicar_bulk_update_vinculos(  # noqa: C901 — fluxo linear de FK→atualização não vale extrair
    *, ids: list[int], updates: dict[str, Any]
) -> dict[str, Any]:
    """Aplica `updates` em cada VinculoFuncional referenciado por `ids`."""
    _validar_whitelist(updates, CAMPOS_VINCULO_BULK_PERMITIDOS)
    # Resolve FKs antes — se id de FK não existe, falha em tudo (atômico).
    fk_resolvidas: dict[str, Any] = {}
    for campo, model in FKS_VINCULO.items():
        if campo in updates:
            valor = updates[campo]
            if valor is None or valor == "":
                fk_resolvidas[campo] = None
                continue
            try:
                fk_resolvidas[campo] = model.objects.get(pk=int(valor))
            except (model.DoesNotExist, ValueError, TypeError) as exc:
                raise DomainError(
                    f"{campo} id={valor} não encontrado.",
                    code="FK_INVALIDA",
                ) from exc

    vinculos = list(VinculoFuncional.objects.filter(id__in=ids))
    encontrados = {v.id for v in vinculos}
    nao_encontrados = sorted(set(ids) - encontrados)
    atualizados = 0
    for vinculo in vinculos:
        mudou = False
        for campo, valor in updates.items():
            if campo in fk_resolvidas:
                novo = fk_resolvidas[campo]
                atual_id = getattr(vinculo, f"{campo}_id")
                novo_id = novo.id if novo is not None else None
                if atual_id != novo_id:
                    setattr(vinculo, campo, novo)
                    mudou = True
            else:
                atual = getattr(vinculo, campo)
                if atual != valor:
                    setattr(vinculo, campo, valor)
                    mudou = True
        if mudou:
            vinculo.save()
            atualizados += 1
    return {
        "atualizados": atualizados,
        "ids_nao_encontrados": nao_encontrados,
        "total_solicitado": len(ids),
    }
