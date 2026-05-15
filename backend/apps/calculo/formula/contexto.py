"""
ContextoFolha — namespace de variáveis disponível em cada fórmula (Bloco 2.1).

Toda fórmula consulta variáveis de um contexto fechado: SALARIO_BASE,
IDADE, CARGA_HORARIA, DEPENDENTES, etc. O contexto NÃO permite acesso
a globals do Python, módulos, ou qualquer coisa fora da lista
explicitamente fornecida no momento da avaliação.

Por convenção, todos os valores de contexto vão para `Decimal` (mesmo
inteiros) antes de entrarem no namespace, exceto strings de tabela
(ano, código de rubrica) — para evitar surpresas de tipo durante a
avaliação.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class ContextoFolha:
    """
    Variáveis disponíveis para uma fórmula DSL.

    Args:
        variaveis: dict de variáveis disponíveis (SALARIO_BASE, IDADE, ...).
        rubricas_calculadas: rubricas já avaliadas nesta competência —
            acessadas via função `RUBRICA("codigo")`.
    """

    variaveis: dict[str, Any] = field(default_factory=dict)
    rubricas_calculadas: dict[str, Decimal] = field(default_factory=dict)

    def como_namespace(self) -> dict[str, Any]:
        """Retorna um dict pronto para servir de namespace local em `eval`."""
        # Cópia defensiva — evita que avaliação modifique o contexto original
        return dict(self.variaveis)


# Lista de variáveis padrão esperadas em cada cálculo de folha.
# Não é uma whitelist (o contexto pode ter outras); é só um contrato
# documentado das variáveis "primárias" que toda implementação de cálculo
# vai prover ao engine. Bloco 2.2 (cálculo mensal) vai preencher todas.
VARIAVEIS_PADRAO = (
    "SALARIO_BASE",         # Decimal — salário-base do vínculo
    "CARGA_HORARIA",        # Decimal — horas semanais
    "HORAS_TRABALHADAS",    # Decimal — horas efetivamente trabalhadas no mês
    "HORAS_PADRAO",         # Decimal — horas-mês contratual
    "IDADE",                # Decimal — idade do servidor na competência
    "DEPENDENTES",          # Decimal — número de dependentes (IR)
    "DEPENDENTES_SALFAM",   # Decimal — número de dependentes salário-família
    "TEMPO_SERVICO_ANOS",   # Decimal — anos de serviço (para licença-prêmio etc.)
    "DIAS_TRABALHADOS",     # Decimal — dias com remuneração no mês
    "FALTAS",               # Decimal — dias de falta injustificada
    "SALARIO_MINIMO",       # Decimal — valor do salário-mínimo no exercício
    "COMPETENCIA_ANO",      # int — ano da competência (uso em FAIXA_*)
    "COMPETENCIA_MES",      # int — mês da competência (1-12)
)
