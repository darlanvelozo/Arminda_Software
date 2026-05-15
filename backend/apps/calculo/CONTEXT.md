# apps/calculo — Contexto

> App do engine de cálculo de folha (Bloco 2). Vive em **TENANT_APPS**:
> cada município pode customizar fórmulas, tabelas legais municipais
> e configurações próprias.

## O que está aqui

- `formula/parser.py` — compila fórmula DSL (Python AST whitelist) em
  bytecode. Validação estrutural pré-execução. Cacheado.
- `formula/funcoes.py` — funções builtin disponíveis dentro de uma
  fórmula (SE, MAX, MIN, ABS, ARRED, RUBRICA, FAIXA_IRRF, FAIXA_INSS).
- `formula/contexto.py` — `ContextoFolha`, namespace de variáveis
  disponível em cada avaliação (SALARIO_BASE, IDADE, DEPENDENTES,
  etc.) + cache de rubricas já calculadas.
- `formula/avaliador.py` — orquestra: compila, monta namespace,
  executa. Retorna `Decimal`.
- `formula/errors.py` — `FormulaError(code, message)` com códigos
  estáveis traduzidos para HTTP 400.

## Decisão arquitetural

A DSL é um **subset seguro de Python** validado via AST whitelist —
ver ADR-0012. Detalhes:
- Sintaxe parecida com planilha: `SE(cond, sim, nao)`, `MAX(a, b)`,
  operadores aritméticos e de comparação.
- Tudo em `Decimal` (não `float`) — dinheiro não admite
  arredondamento implícito.
- Bloqueia: import, attribute, subscript, lambda, comprehension,
  pow (`**`).

## Padrão de uso

```python
from apps.calculo.formula.avaliador import avaliar
from apps.calculo.formula.contexto import ContextoFolha
from decimal import Decimal

ctx = ContextoFolha(variaveis={
    "SALARIO_BASE": Decimal("1320.00"),
    "IDADE": 35,
    "DEPENDENTES": 2,
})

resultado = avaliar("SALARIO_BASE * 0.10 - DEPENDENTES * 189.59", ctx)
# Decimal("-247.18")
```

## O que NÃO está aqui

- Modelos de domínio (Rubrica, Folha, Lancamento) — esses vivem em
  `apps.payroll`. Este app é puro engine, sem persistência própria
  além de cache.
- Tabelas legais (IRRF, INSS, salário mínimo) — Bloco 2.3, ficarão
  em `apps.core.ConfiguracaoGlobal` (compartilhadas) ou
  `apps.payroll.TabelaLegal` (sobrescrevíveis por município).

## Como testar

```bash
.venv/bin/pytest apps/calculo/tests/ -v
```

Cobertura alvo: ≥ 95% no `apps.calculo` (engine é coração do produto).

## Não fazer

- Adicionar função builtin sem atualizar a whitelist em
  `funcoes.py` + teste explícito.
- Permitir nó AST novo na whitelist sem entender a implicação de
  segurança.
- Usar `float` em qualquer cálculo — sempre `Decimal`.
- Trabalhar com fórmulas em texto durante o cálculo de produção;
  sempre compilar uma vez e reusar via cache.
