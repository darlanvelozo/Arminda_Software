# ADR-0012 — DSL de fórmulas via subset seguro de Python (AST whitelist)

**Status:** Aceita · 2026-05-12 · Vigora para Bloco 2

## Contexto

Cada rubrica da folha de pagamento (campo `apps.payroll.Rubrica.formula`,
já existente) precisa de uma **expressão calculável**. Exemplos do
mundo real, observados no Fiorilli SIP do município-piloto e em
MANADs analisados:

```
SALARIO_BASE * (HORAS_TRABALHADAS / HORAS_PADRAO)
MAX(SALARIO_BASE, SALARIO_MINIMO)
SE(IDADE >= 65, INSS_FAIXA_REDUZIDA, INSS_PADRAO)
FAIXA_IRRF(BASE_IRRF, "2026")
RUBRICA("SAL_BASE") * 0.20 - DEPENDENTES * 189.59
```

Características do problema:

- **Operadores aritméticos** (`+`, `-`, `*`, `/`, `%`).
- **Comparações** (`>`, `<`, `==`, `!=`, `>=`, `<=`).
- **Lógicos** (`and`, `or`, `not`).
- **Condicional** ternário (`SE(cond, sim, nao)`).
- **Funções de domínio** (MAX, MIN, ABS, ARRED, SE, FAIXA_IRRF, FAIXA_INSS, etc.).
- **Acesso a variáveis** do contexto (SALARIO_BASE, IDADE, DEPENDENTES, etc.).
- **Acesso a outras rubricas** já calculadas (`RUBRICA("X")`).
- **Tudo em decimal exato** (Decimal, não float) — dinheiro não admite arredondamento implícito.

Requisitos não-funcionais:

- **Segurança:** uma fórmula maliciosa não pode acessar filesystem,
  socket, módulos arbitrários, ou consumir CPU/memória sem limite.
- **Performance:** calcular folha de 5 mil servidores × 50 rubricas =
  250 mil avaliações — precisa ser rápido (compile uma vez, executa
  N vezes).
- **Mensagens de erro claras:** o operador vê "RUBRICA 'XYZ' não
  existe na linha 3" e não "TypeError: NoneType object is not callable".
- **Testabilidade:** parser e avaliador são funções puras.

### Opções avaliadas

#### Opção A — DSL própria com parser (Lark/PLY)

Gramática completa em arquivo `.lark`, parser dedicado, AST customizada.

- **Prós:** controle total da gramática, mensagens de erro 100% custom, sem surpresas de Python.
- **Contras:** custo alto (~3-5 dias só pra ter algo funcional, sem contar funções), risco de bugs sutis, exige manutenção de gramática.

#### Opção B — Subset seguro de Python via `ast` whitelist

Usar `ast.parse(source, mode="eval")` + walker que rejeita qualquer
nó AST não-permitido. Funções de domínio injetadas via namespace
no `eval()` controlado.

- **Prós:** rapidez de implementação (~1 dia), aproveita parser de
  Python (que é maduro, testado, tem mensagens de erro decentes
  para sintaxe), zero deps externas.
- **Contras:** sintaxe "parece Python" (pode confundir operadores
  não-técnicos), tem que manter a whitelist atualizada com cuidado
  para não vazar capacidade.

#### Opção C — Biblioteca externa (`asteval`, `simpleeval`)

Pegar uma solução pronta.

- **Prós:** ainda mais rápido (~2h).
- **Contras:** dependência externa não-essencial, perda de controle
  sobre funções de domínio, manutenção delegada.

## Decisão

**Opção B — Subset seguro de Python via AST whitelist.**

### Justificativa

1. **Velocidade vence o resto.** Bloco 2 é grande (~5 semanas) e a DSL é só a primeira onda. Gastar 5 dias no parser tira tempo do que importa: implementar bem o cálculo da folha. Opção B entrega em 1 dia o que Opção A entrega em 5.
2. **Os operadores não vão escrever fórmulas raw.** A UI de Bloco 2.6 vai ter helpers (autocompletar nomes de rubricas, picker de função, validador inline). A sintaxe "Python-like" fica escondida.
3. **A whitelist é pequena e testável.** Cabe em uma página: `BinOp`, `Compare`, `BoolOp`, `UnaryOp`, `IfExp`, `Call`, `Name`, `Constant`. Bloqueia explicitamente `Attribute`, `Subscript`, `Import`, `Lambda`, `ListComp`, etc.
4. **Decimal exato é fácil em Python.** Toda constante numérica vira `Decimal`; operações reusam o tipo nativo.

### O que está dentro da whitelist (permitido)

```python
ALLOWED_NODES = {
    ast.Expression,    # raiz para mode="eval"
    ast.Constant,      # números, strings literais
    ast.Name,          # SALARIO_BASE, IDADE, ...
    ast.Load,          # contexto de leitura (não Store)
    ast.BinOp,         # +, -, *, /, %, ** (** veta-se à parte)
    ast.UnaryOp,       # -x, +x
    ast.Compare,       # a > b, a == b
    ast.BoolOp,        # and, or
    ast.IfExp,         # x if cond else y  (suporta SE() também)
    ast.Call,          # funções de domínio
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod,
    ast.USub, ast.UAdd, ast.Not,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.And, ast.Or,
}
```

### O que está fora (bloqueia)

```python
# Tudo que não está acima, em particular:
# - ast.Attribute (a.b — bloqueia introspecção)
# - ast.Subscript (a[b] — bloqueia acesso a dict/list externos)
# - ast.Lambda, ast.FunctionDef, ast.ClassDef
# - ast.Import, ast.ImportFrom
# - ast.Try, ast.With, ast.For, ast.While
# - ast.ListComp, ast.SetComp, ast.GeneratorExp
# - ast.Pow (**) — DoS via 10**10**10
```

### Funções de domínio permitidas (whitelist por nome)

```python
ALLOWED_FUNCTIONS = {
    # Numéricas
    "MAX", "MIN", "ABS", "ARRED",  # ARRED = round
    # Condicionais
    "SE",                          # SE(cond, sim, nao)
    # Acesso a contexto
    "RUBRICA",                     # RUBRICA("codigo") → Decimal já calculado
    # Tabelas legais (lazy — injetadas conforme blocos avançam)
    "FAIXA_IRRF", "FAIXA_INSS",    # progressivas, recebem (base, ano)
}
```

A lista cresce conforme o Bloco 2 avança. A regra: **toda função
nova passa por revisão e teste explícito** — não é só "adiciono na
lista".

### Decimal exato

```python
# Toda constante numérica vira Decimal antes de avaliar:
expr = "SALARIO_BASE * 0.10"  →  AST com Constant(0.10) → após walk,
                                  Constant(Decimal("0.10"))
```

`from decimal import Decimal, ROUND_HALF_UP, getcontext` —
precisão padrão 28 dígitos, suficiente para folha.

### Cache de compilação

Cada `Rubrica.formula` é compilada **uma vez** por processo
(`functools.lru_cache` keyed pela tupla `(formula_text, version_id)`).
Reavaliação é apenas `eval(compiled_code, namespace)` — milissegundos.

### Tratamento de erros

Todo erro de fórmula vira `apps.calculo.errors.FormulaError` com
`code` estável traduzido para HTTP 400 quando a fórmula é avaliada
via API:

```
FORMULA_SINTAXE        — ast.parse falhou
FORMULA_NAO_PERMITIDA  — AST tem nó proibido
FORMULA_FUNCAO_DESCONHECIDA — Call para função fora da whitelist
FORMULA_VARIAVEL_AUSENTE    — Name acessa variável fora do contexto
FORMULA_RUBRICA_NAO_EXISTE  — RUBRICA("X") com X inexistente
FORMULA_DIV_POR_ZERO        — DivisionByZero
FORMULA_TIPO_INVALIDO       — operação entre tipos incompatíveis
```

### Onde mora

App novo **`apps.calculo`** em `TENANT_APPS` (cada município pode
ter suas próprias regras de cálculo customizadas via rubricas
configuráveis). Estrutura inicial:

```
apps/calculo/
├── __init__.py
├── apps.py
├── CONTEXT.md
├── formula/
│   ├── __init__.py
│   ├── parser.py      # compila + valida (AST walker)
│   ├── funcoes.py     # builtins (SE, MAX, MIN, ARRED, FAIXA_*)
│   ├── contexto.py    # ContextoFolha — variáveis disponíveis
│   ├── avaliador.py   # orquestra compile + eval
│   └── errors.py      # FormulaError + códigos
└── tests/
    ├── test_parser.py
    ├── test_avaliador.py
    └── test_funcoes.py
```

## Consequências

### Positivas

- **Implementação em ~1 dia** vs. 3-5 dias da Opção A.
- Sintaxe que casa com mental model de operadores que já viram
  fórmula em planilha (`SE`, `MAX`, `MIN`, parêntese, comparação).
- **Performance excelente:** Python compila o AST e executa direto;
  benchmark estimado: 1 µs por avaliação (depois de compilada),
  250 ms para folha de 5k servidores × 50 rubricas.
- Mensagens de erro decentes "de graça" para sintaxe (mensagem
  nativa do parser do Python).
- Zero dependências externas.

### Negativas / trade-offs

- **Sintaxe "parece Python".** Quem escrever fórmula complexa pode
  cair em pegadinha — ex.: divisão inteira vs. real (`5 / 2` em
  Python 3 é `2.5`, mas `5 // 2` é `2`; bloqueamos `//`).
- **Operadores avançados ficam fora.** Sem list comprehension, sem
  lambda. Isso é intencional, mas algum dia alguém vai querer
  "fórmula com loop sobre dependentes". Solução: oferecer função
  de domínio dedicada (ex.: `SOMA_DEPENDENTES(idade_min, idade_max)`)
  em vez de abrir a gramática.
- **Pow `**` desligado.** Se algum dia precisar de potência,
  oferecer função explícita `POW(base, expoente)` em vez de
  reativar o operador (risco de DoS).

## Implementação na Onda 2.1

1. Criar app `apps.calculo` registrado em `TENANT_APPS`.
2. Implementar `parser.py` + `funcoes.py` + `contexto.py` +
   `avaliador.py` + `errors.py` conforme estrutura acima.
3. Funções iniciais: `SE`, `MAX`, `MIN`, `ABS`, `ARRED`, `RUBRICA`.
   `FAIXA_IRRF` e `FAIXA_INSS` ficam para Onda 2.3 (tabelas legais).
4. Suite de testes cobrindo:
   - Aritmética básica
   - Operadores de comparação e lógicos
   - Funções builtin (cada uma)
   - Erros de domínio (cada `code`)
   - Decimal exato
5. Endpoint `POST /api/payroll/rubricas/{id}/avaliar/`:
   - Body: `{"contexto": {"SALARIO_BASE": "1320.00", "IDADE": 35, ...}}`
   - Resposta: `{"valor": "132.00", "passos": [...]}` (passos
     são opcionais — útil para debug futuro)
6. Backend testes: ≥ 95% de cobertura no app `apps.calculo`.

## Histórico

- 2026-05-12 — Aceita. Versão `v0.6.0` ao final da Onda 2.1.
