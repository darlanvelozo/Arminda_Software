"""
Análise estática de dependências entre rubricas (Bloco 2.2).

Cada rubrica pode referenciar outras via `RUBRICA('codigo')` em sua
fórmula. Antes de calcular a folha, precisamos:

1. Descobrir as dependências por análise estática da AST (sem
   executar a fórmula).
2. Ordenar topologicamente o conjunto de rubricas a calcular.
3. Detectar ciclos (`A → RUBRICA('B')`, `B → RUBRICA('A')`).

Tudo isso é puro — funções deterministas que recebem strings/listas e
retornam estruturas de dados. Sem dependência de modelo Django.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

from apps.calculo.formula.errors import FormulaError, FormulaSintaxeError


class DependenciaCiclicaError(FormulaError):
    """Ciclo detectado no grafo de dependências de rubricas."""

    code = "DEPENDENCIA_CICLICA"


class DependenciaInexistenteError(FormulaError):
    """Rubrica referencia outra que não está na lista de rubricas conhecidas."""

    code = "DEPENDENCIA_INEXISTENTE"


def extrair_dependencias(formula: str) -> set[str]:
    """
    Devolve o conjunto de códigos de rubrica referenciados via
    RUBRICA('codigo') na fórmula. Análise estática — não executa nada.

    Aceita tanto aspas simples quanto duplas. Ignora chamadas a
    RUBRICA com argumentos não-literais (ex.: `RUBRICA(codigo_var)` —
    seria erro em tempo de avaliação, mas aqui não temos como saber o
    valor estaticamente, então ignoramos da análise).
    """
    if not formula or not formula.strip():
        return set()
    try:
        tree = ast.parse(formula, mode="eval")
    except SyntaxError as exc:
        raise FormulaSintaxeError(
            f"Sintaxe inválida ao analisar dependências: {exc.msg}"
        ) from exc

    deps: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name):
            continue
        if node.func.id != "RUBRICA":
            continue
        if len(node.args) != 1:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            deps.add(arg.value)
        # Outros casos (expressão dinâmica, variável) silenciosamente
        # ignorados — avaliador detecta em runtime.
    return deps


@dataclass(frozen=True)
class RubricaParaOrdenar:
    """Entrada mínima do toposort: código + fórmula."""

    codigo: str
    formula: str


def ordenar_topologicamente(rubricas: list[RubricaParaOrdenar]) -> list[str]:
    """
    Retorna lista de códigos de rubrica ordenada de modo que cada
    rubrica venha **depois** de todas as suas dependências (Kahn's
    algorithm).

    Args:
        rubricas: lista de (codigo, formula). Códigos repetidos não
            são permitidos.

    Returns:
        Lista de códigos na ordem de cálculo.

    Raises:
        DependenciaCiclicaError: se houver ciclo no grafo.
        DependenciaInexistenteError: se uma fórmula referenciar código
            que não está na lista.
    """
    codigos = {r.codigo for r in rubricas}
    if len(codigos) != len(rubricas):
        raise FormulaError("Códigos de rubrica duplicados na lista de ordenação.")

    # adjacencia[A] = conjunto de quem A depende
    adjacencia: dict[str, set[str]] = {}
    for r in rubricas:
        deps = extrair_dependencias(r.formula)
        invalidas = deps - codigos
        if invalidas:
            raise DependenciaInexistenteError(
                f"Rubrica '{r.codigo}' depende de "
                f"{sorted(invalidas)} que não está(ão) entre as rubricas a calcular."
            )
        adjacencia[r.codigo] = deps

    # Kahn: começa pelos que não dependem de nada
    indegree = {c: len(deps) for c, deps in adjacencia.items()}
    # reverso: para cada rubrica, quem depende dela?
    reverso: dict[str, set[str]] = {c: set() for c in codigos}
    for c, deps in adjacencia.items():
        for d in deps:
            reverso[d].add(c)

    # Fila estável: ordena alfabético para resultado determinístico
    livres = sorted([c for c, n in indegree.items() if n == 0])
    ordem: list[str] = []
    while livres:
        # pop do início (FIFO estável)
        atual = livres.pop(0)
        ordem.append(atual)
        # Para todos que dependiam de `atual`, decrementa indegree
        for filho in sorted(reverso[atual]):
            indegree[filho] -= 1
            if indegree[filho] == 0:
                # Insere mantendo ordem alfabética dos livres
                livres.append(filho)
                livres.sort()

    if len(ordem) != len(rubricas):
        nao_resolvidos = [c for c, n in indegree.items() if n > 0]
        raise DependenciaCiclicaError(
            f"Ciclo de dependência entre rubricas: {sorted(nao_resolvidos)}."
        )
    return ordem
