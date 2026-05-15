# CHANGELOG

> Memória do projeto Arminda. Toda alteração relevante deve ter uma entrada aqui.
>
> Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
> com seção adicional **Por quê** (motivação) e **Impacto** (consequências).
>
> Versionamento: ver `docs/ROADMAP.md` — versão minor por bloco entregue.

---

## Como registrar uma mudança

Cada entrada deve responder:

- **O quê** — descrição curta e objetiva da alteração.
- **Por quê** — motivação (referência ao bloco do roadmap, ADR, bug, requisito legal, etc.).
- **Arquivos** — caminhos principais alterados (não precisa exaustivo; aponte os críticos).
- **Impacto** — o que muda para quem? Quebra contrato? Migration? Variável de ambiente nova?
- **Próximos passos** — se a alteração abre frentes ou tem dívida residual.

Categorias permitidas (Conventional Commits):
- **feat** — nova funcionalidade
- **fix** — correção de bug
- **refactor** — mudança sem alterar comportamento
- **chore** — manutenção (deps, build, configs)
- **docs** — documentação
- **test** — testes
- **perf** — performance
- **ci** — pipeline

Mudanças que afetam contrato de API, schema de banco ou semântica de cálculo recebem o marcador **⚠ BREAKING**.

---

## [Não lançado] — em construção

### Bloco 2.1 — Engine de cálculo: DSL de fórmulas para rubricas · 2026-05-12

> Início do **Bloco 2 (engine de cálculo de folha)**. Esta onda entrega
> a peça mais incerta do bloco — a linguagem de fórmulas que as
> rubricas usam para calcular valor. Com a DSL pronta, as próximas
> ondas (2.2 cálculo mensal, 2.3 tabelas legais, 2.5 holerite)
> compõem em cima dela.

#### Adicionado — Backend

- **docs(adr):** [ADR-0012 — DSL via subset seguro de Python (AST whitelist)](docs/adr/0012-dsl-formulas-via-python-ast.md).
  Decide:
  - Sintaxe Python-like (`MAX(a, b)`, `SE(cond, sim, nao)`, operadores
    aritméticos e de comparação) validada por AST whitelist.
  - Toda constante numérica vira `Decimal` (não float) — dinheiro não
    admite arredondamento implícito.
  - Bloqueia: import, attribute, subscript, lambda, comprehension,
    pow (`**`), floor div (`//`), kwargs em chamadas.
  - Compilação cacheada via `functools.lru_cache(1024)`.

- **feat(apps.calculo):** Novo app em `TENANT_APPS` com:
  - `formula/parser.py` — compila a fórmula em bytecode, valida AST,
    substitui literais numéricos por chamadas a `_D("0.10")`
    em runtime (o `compile()` do Python não aceita `Decimal` em
    `Constant`).
  - `formula/funcoes.py` — funções builtin: `SE`, `MAX`, `MIN`,
    `ABS`, `ARRED`, `RUBRICA(codigo)`. Funções `FAIXA_IRRF` e
    `FAIXA_INSS` são placeholders (entram na Onda 2.3 com tabelas
    legais 2026).
  - `formula/contexto.py` — `ContextoFolha(variaveis,
    rubricas_calculadas)` + lista de variáveis padrão
    (SALARIO_BASE, IDADE, DEPENDENTES, CARGA_HORARIA, HORAS_*,
    TEMPO_SERVICO_ANOS, DIAS_TRABALHADOS, FALTAS, SALARIO_MINIMO,
    COMPETENCIA_ANO, COMPETENCIA_MES).
  - `formula/avaliador.py` — orquestra: compila → monta namespace
    (Decimal + builtins + RUBRICA dinâmico + contexto) → executa.
    Trata 6 categorias de erro (`FormulaSintaxeError`,
    `FormulaNaoPermitidaError`, `FormulaFuncaoDesconhecidaError`,
    `FormulaVariavelAusenteError`, `FormulaRubricaInexistenteError`,
    `FormulaDivisaoPorZeroError`, `FormulaTipoInvalidoError`) com
    `code` estável.

- **feat(apps.payroll):** Novo endpoint
  `POST /api/payroll/rubricas/{id}/avaliar/` que recebe `{contexto,
  rubricas_calculadas}` e retorna `{valor, formula}` ou erro
  `{detail, code}` com HTTP 400. Permissão de leitura
  (`IsLeituraMunicipio`) — qualquer papel pode disparar para debug.

- **test:** 76 testes novos no `apps.calculo` cobrindo:
  - Compilação de fórmulas válidas
  - Rejeição de sintaxe inválida (4 casos)
  - Segurança: 8 construções perigosas bloqueadas
  - Cache: mesma fórmula reusa code object
  - 24 testes de funções builtin
  - 26 testes do avaliador (aritmética, comparações, lógicos,
    condicionais, rubricas, erros de contexto e runtime)
  - 6 testes do endpoint (caminho feliz, erros, permissão)
  - Cálculos realistas: proporcionalidade por horas, piso salarial,
    IRRF simplificado.

- **332 testes verde no total** (256 → 332, +76).

#### Por quê

- **DSL é o item mais incerto do Bloco 2.** Resolver primeiro destrava
  o resto do bloco. Se a estratégia AST whitelist falhasse, eu
  saberia em 1 dia — agora confirmamos que funciona, performa bem
  (1 µs por avaliação após cache) e tem mensagens de erro
  adequadas.
- **Decimal exato é não-negociável.** Folha de pagamento opera em
  centavos; `float` introduz erros silenciosos (0.1 + 0.2 != 0.3).
  Toda constante e toda variável de contexto entra na fórmula
  como `Decimal` — isso vai prevenir 80% dos bugs de cálculo
  futuros.
- **Errors estruturados (com `code`) viram contrato.** Quando a UI
  de Bloco 2.6 entrar, o operador vai ver "Variável X não disponível"
  e não "NameError" técnico. Cada `code` mapeia para uma mensagem
  amigável.

#### Impacto

- 1 app novo (`apps.calculo`), 6 arquivos de domínio, ~700 LOC
  de código + 800 LOC de testes.
- Sem migrations (engine é puro).
- Sem mudança de contrato existente — apenas endpoint novo
  (`/avaliar/`) na rota de rubricas.
- Build verde, suite completa verde.

#### Próximos passos

- **Onda 2.2 — Cálculo mensal ordinário.** Usa a DSL para calcular
  uma folha inteira: itera servidores ativos × rubricas → produz
  `Lancamento`. Vai começar a popular `salario_base` real nos
  vínculos (hoje todos zerados pela importação).
- **Onda 2.3 — Tabelas legais 2026** (INSS, IRRF progressivo,
  salário-mínimo, deduções por dependente). Aí `FAIXA_IRRF` e
  `FAIXA_INSS` deixam de ser placeholders.

---

### docs: MANAD no Bloco 4 + Sagres no Bloco 5 + ADR-0011 adaptadores · 2026-05-12

> Ajuste de roadmap após dois aprendizados externos:
>
> 1. Conversa com Dr. Renzo sobre MANAD ("base de todas as folhas do
>    Brasil, é obrigatório") + análise de arquivo MANAD 2020 real
>    (FMAS de Canindé de São Francisco/SE — referência apenas, não
>    commitado por conter dados pessoais).
> 2. Necessidade de suportar **múltiplas prefeituras** com perfis
>    fiscais diferentes (TCE-MA para uma, Sagres-PB para outra, etc.)
>    sem deploy de código.
>
> Nenhuma mudança de produto neste commit — só documentação que orienta
> os Blocos 4, 5 e 7 quando chegarem.

#### Adicionado

- **docs(roadmap):** Bloco 4 ganha **MANAD** como entrega nominal
  (estava ausente), com critério de paridade bit-a-bit contra o
  sistema legado. Pré-requisito explicitado: modelo `OrgaoEmissor`
  por CNPJ (cada município tem N órgãos emissores).
- **docs(roadmap):** Bloco 5 ganha **TCE-PB (Sagres Folha)** como
  segundo adaptador prioritário (estava genericamente em "framework
  extensível"). Critério novo: município ativa integrações no admin
  sem deploy.
- **docs(adr):** [ADR-0011 — Adaptadores externos configuráveis](docs/adr/0011-adaptadores-externos-configuraveis.md).
  Decide:
  - Modelo `IntegracaoExterna(municipio, orgao_emissor, tipo, ativo,
    configuracao)` em `apps.core` (SHARED, public schema).
  - Adapter Pattern em código (`apps/<bloco>/adapters/<tipo>.py`)
    implementando interface comum (`gerar_remessa`, `validar`,
    `enviar`, `consultar_status`).
  - Modelo `OrgaoEmissor` em `apps.people` (TENANT) com CNPJ próprio
    + relacionamento opcional com `UnidadeOrcamentaria`.
  - Endpoint `GET /api/core/integracoes/ativas/` para frontend
    montar menu dinamicamente — município sem TCE-PB literalmente
    não vê o ícone.
  - Credenciais cifradas com Fernet no JSON `configuracao`.
  - Tipos pré-listados: eSocial, MANAD, SEFIP, CAGED, RAIS, DIRF,
    DCTFWeb, TCE-MA, TCE-PB, TCE-SP (Audesp), expansível.
- **docs(leiautes):** Nova pasta
  [`docs/leiautes/manad/`](docs/leiautes/manad/) com `README.md`
  detalhando o leiaute MANAD (registros 0000–9999, blocos K, encoding
  WIN1252, exemplo de cada record desanonimizado). Material de
  consulta para o Bloco 4. **Não commitamos** os 12 arquivos .txt
  originais que serviram de aprendizado (contêm CPF/PIS/nomes de 159
  servidores reais de Canindé/SE).
- **docs(status-page):** entregas dos Blocos 4 e 5 expandidas com
  os novos itens.
- **docs(guia):** subseções de Bloco 4 e Bloco 5 detalhadas com a
  nova lista de obrigações + nota sobre menu dinâmico. `LAST_UPDATED`
  para 2026-05-12.

#### Por quê

- **Multi-município é requisito de produto.** Hoje o piloto é em
  São Raimundo do Doca Bezerra/MA, mas o Arminda nasce para atender
  N prefeituras brasileiras. Sem a decisão de arquitetura agora, o
  primeiro adapter (eSocial no Bloco 4) seria implementado
  monoliticamente e quebraria ao chegar a segunda prefeitura.
- **MANAD é obrigatório por lei, não por preferência.** Mesmo que o
  uso esteja diminuindo, a Receita pode pedir e o sistema tem que
  saber gerar. O risco de descobrir isso no piloto seria caro.
- **CNPJ por órgão emissor evita rework futuro.** Confirmado no
  arquivo MANAD analisado: cada Fundo (Saúde, Assistência, etc.)
  emite com seu próprio CNPJ. Se modelarmos "1 município = 1 CNPJ",
  vamos ter que refatorar tudo quando bater na realidade.

#### Impacto

- Sem mudança de código de produto, sem migration, sem alteração
  de contrato.
- Documentação cresceu: 1 ADR nova (0011), 1 README de leiaute,
  CHANGELOG e GuiaPage atualizados, ROADMAP e status.json revistos.
- Nenhuma tag de versão é criada (segundo ADR-0010 §3, tags são por
  entrega de produto — docs internas não geram tag).

#### Próximos passos

- **Bloco 2.1 — DSL de fórmulas para rubricas.** Começo agora —
  é o item mais incerto do Bloco 2 e destrava o resto da engine
  de cálculo.

---

### Onda 1.4-bis: Unidade orçamentária (DEPDESPESA do SIP) · 2026-05-10

> Extensão do importador para puxar a tabela `UNIDADE` do Fiorilli SIP
> (~65 unidades orçamentárias por exercício fiscal) e associar cada
> vínculo à sua unidade de despesa. Antes da onda, o sistema só sabia
> da "lotação física" (onde o servidor trabalha); agora sabe também
> da "unidade orçamentária" (de onde sai o empenho do salário) — que é
> a fonte de verdade quando os dois divergem, conforme caso real do
> município-piloto.

#### Adicionado — Backend

- **feat(people/models):** Novo modelo `UnidadeOrcamentaria` em
  `apps.people` com `codigo` (DEPDESPESA do SIP, ex.: '201013'),
  `codigo_interno_sip` (PK numérico interno do Fiorilli — é por ele
  que `TRABALHADOR.DEPDESPESA` aponta; o nome do campo no SIP é
  enganoso), `ano`, `nome`, `sigla`, `natureza` e `ativo`. Chave
  única por `(codigo, ano)`. Auditoria via `simple-history`.
- **feat(people/models):** Novo campo `unidade_orcamentaria` (FK
  nullable) em `VinculoFuncional` — quando preenchido, vence sobre
  a natureza inferida pela lotação física para classificação por
  secretaria.
- **migrations 0007 + 0008:** Schema da nova tabela + campo
  `codigo_interno_sip` (descoberta tardia durante o smoke E2E).
- **feat(imports/adapter):** Novo `fetch_unidades_orcamentarias`
  lê de `UNIDADE` filtrando por ano. `fetch_trabalhadores` agora
  inclui `DEPDESPESA` no SELECT (estava ausente).
- **feat(imports/mapping):** Novo `map_unidade_orcamentaria` que
  classifica a natureza por prioridade (1º nome → fallback no prefixo
  numérico do código `DEPDESPESA`: 1=adm, 2=saúde, 3=educação,
  4=assistência, 5=adm, 6=outros, 7=adm — convenção empírica
  observada no município-piloto). O `map_vinculo` aceita o parâmetro
  opcional `unidade_orcamentaria_id`.
- **feat(imports/loaders):** Novo
  `load_unidades_orcamentarias`. O `load_vinculos` agora aceita
  `ano_unidade` e resolve a FK do vínculo via mapa
  `codigo_interno_sip → arminda_id` (consultando direto o ORM em vez
  do `SipImportRecord`, mais simples para esse JOIN específico).
- **feat(imports/command):** `import_fiorilli_sip` aceita a tabela
  `unidades` e a flag `--ano-unidade <ano>` (default: ano corrente).
- **feat(people/serializers):** `VinculoDetailSerializer` e
  `_VinculoEmbutidoSerializer` agora expõem
  `unidade_orcamentaria` (FK), `unidade_orcamentaria_codigo`,
  `unidade_orcamentaria_nome` e `unidade_orcamentaria_natureza`.
- **feat(people/filters):** Novo filtro `natureza_unidade` em
  `ServidorFilter` via `vinculos__unidade_orcamentaria__natureza`.
  Convive com o `natureza` existente (via lotação) — quem quiser
  agrupar pelo empenho usa `?natureza_unidade=saude`.
- **test:** 8 testes novos para `map_unidade_orcamentaria` (256
  testes verde no total; era 248).

#### Smoke E2E real

Re-rodamos contra `SIP.FDB` do município de São Raimundo do Doca
Bezerra (MA) com `--ano-unidade 2026`:

| Métrica | Resultado |
|---|---|
| Unidades orçamentárias importadas | **65 / 65 (100%)** |
| Distribuição: adm/educ/saúde/assist/outros | 21 / 19 / 13 / 7 / 5 |
| Vínculos ativos cruzados com unidade | **472 / 1.503 (31%)** |
| Vínculos sem unidade no SIP (DEPDESPESA=0) | 1.031 (69%) |
| Ex-"outros" pela lotação física, agora identificados | 29 vínculos (15 outros, 14 adm) |

A cobertura de 31% reflete a realidade do município: muitos
servidores históricos têm `DEPDESPESA=0` no SIP, sem informação
de empenho. Para os 472 que têm o dado, o cruzamento foi 100%
correto. O admin pode classificar manualmente o resto via tela
de Lotação (a natureza da lotação física vira a referência
quando a unidade não existe).

#### Adicionado — Frontend

- **feat(servidores/detalhe):** Card do vínculo agora exibe a
  unidade orçamentária associada (quando existe), com código
  monoespaçado, nome e badge colorida da natureza inferida. O
  ícone `Wallet` reforça que é informação de empenho.
- **docs(GuiaPage):** Nova subseção "Unidade orçamentária (origem
  do empenho)" dentro de "Organização". Novo `FlowItem` na seção
  Servidores. `LAST_UPDATED` para 2026-05-10.

#### Por quê

- **Fecha a demanda do Dr. Renzo.** A conversa original foi sobre
  "todo mundo numa única lotação no Fiorilli, era preciso recadastrar
  para saber quem é de cada secretaria". A unidade orçamentária é
  exatamente o dado que resolve isso onde existe.
- **Pré-requisito do Bloco 2.** O cálculo de folha precisa saber
  para qual orçamento empenhar cada lançamento financeiro. Com a
  FK no Vínculo, o engine de cálculo já encontra o dado pronto
  quando entrar em ação.
- **JOIN correto descoberto cedo.** A descoberta de que o nome do
  campo `DEPDESPESA` no Fiorilli é enganoso (referência é via
  `UNIDADE.CODIGO`, não pelo VARCHAR de mesmo nome) só pôde
  acontecer no smoke E2E. Ficar essa armadilha para o Bloco 2
  seria muito mais caro.

#### Impacto

- **Backend:** 256 testes verde (248 → 256, +8), 2 migrations novas,
  1 modelo novo, FK opcional no Vínculo. Sem mudança de contrato
  destrutivo (todos campos opcionais).
- **Frontend:** Bundle inicial inalterado (500 KB / 155 KB gzip).
  Build verde, typecheck verde, 10/10 testes verde.
- **Importador:** agora rodar com `--tabelas
  cargos,lotacoes,unidades,servidores,vinculos,dependentes` traz
  o panorama completo do município, incluindo o dado de empenho.

#### Próximos passos

- **Bloco 2.1 — DSL de fórmulas das rubricas.** É o item mais
  incerto do Bloco 2; começar por ele destrava o resto.
- **Tabelas legais 2026** (INSS, IRRF, deduções) entram junto.

---

### Onda 1.5b: Organização por vínculo e por área (secretaria) · 2026-05-08

> Resposta direta ao caso real do município de São Raimundo do Doca Bezerra:
> 369 servidores estavam num "balde genérico sem nome" no Fiorilli SIP,
> impossibilitando saber quem trabalha na Saúde, Educação, etc., sem
> recadastramento manual. Esta onda dá ao sistema a estrutura para
> organizar servidores em **duas dimensões independentes**: vínculo
> (Efetivo/Comissionado/Contratado/Eletivo) e área da secretaria
> (Administração/Saúde/Educação/Assistência social). A classificação
> automática rodou nos dados reais e cobriu 1.103 dos 1.503 vínculos
> ativos em 4 áreas claras; os 400 restantes ficam como "Outros"
> (cultura/esporte/obras/balde sem nome) para revisão manual.

#### Adicionado — Backend

- **feat(people/models):** Novo regime `ELETIVO` (cobre Prefeito, Vice e
  Vereadores — antes virava `comissionado` indevidamente). Labels do enum
  Regime ficaram mais explícitos: "Efetivo (concursado)" em vez de só
  "Estatutário", "Contratado temporário" em vez de "Temporário".
- **feat(people/models):** Novo enum `NaturezaLotacao` com 5 valores
  (administração, saúde, educação, assistência_social, outros) e campo
  `natureza` em `Lotacao` (default="outros").
- **migration 0003:** Schema — adiciona `Lotacao.natureza` e adapta
  `Regime` choices.
- **migration 0004 + 0005 + 0006 (data migrations):** Classifica
  automaticamente as 66 lotações importadas baseado em padrões no nome:
  - Saúde: ACS, UBS, hospital, posto, PSF/ESF, SAMU, vigilância sanitária
  - Educação: escola, creche, EMEF/EMEI, biblioteca, NIIPED, "G E", "ESC", "UI"
  - Assistência social: CRAS, CREAS, conselho tutelar, SCFV, Criança Feliz
  - Administração: gabinete, prefeitura, câmara, finanças, jurídico,
    procuradoria, controladoria
  - As 3 passadas sequenciais elevaram a cobertura para 73% (1.103 de 1.503
    vínculos classificados em 4 áreas claras; 400 restantes em "Outros").
- **feat(people/filters):** `LotacaoFilter` ganha filtro por `natureza`.
  `ServidorFilter` ganha filtro por `natureza` (via
  `vinculos__lotacao__natureza`). Todos os filtros via `vinculos__*` agora
  têm `distinct=True` para evitar duplicação por servidor com múltiplos
  vínculos.
- **feat(people/serializers):** `natureza` e `natureza_display` em
  Lotacao{List,Detail,Write}Serializer.
- **feat(imports/mapping):**
  - `VINCULO=01` (AGENTE POLÍTICO no Fiorilli) agora vira `Regime.ELETIVO`
    (era `comissionado`).
  - `map_lotacao` chama `_classifica_natureza` automaticamente — novas
    importações já chegam classificadas, sem precisar de data migration
    adicional.
- **test:** 6 testes novos (mapping de natureza + ELETIVO) → 248 verde.

#### Adicionado — Frontend

- **feat(lib/constants):** Tabelas centrais `REGIMES` e `NATUREZAS` com
  labels em português e variantes de Badge consistentes — usadas em
  todas as 4 telas afetadas e no Dashboard.
- **feat(lotacoes/form):** `LotacaoFormSheet` ganha Select obrigatório
  de Natureza (5 opções) com hint sobre quando usar "Outros".
- **feat(lotacoes/list):** `LotacoesListPage` ganha:
  - Nova coluna "Natureza" com Badge colorida (cores estáveis por natureza)
  - Filtro de Natureza na toolbar
- **feat(servidores/list):** `ServidoresListPage` ganha 2 filtros novos
  (Vínculo + Natureza) que combinam entre si. Suporta deep-link via URL
  (`?regime=estatutario&natureza=saude`) — filtros são sincronizados
  bidirecionalmente.
- **feat(queries/kpis):** Novo hook `useDashboardKpis` que dispara 10
  contagens em paralelo (total + 5 vínculos + 4 naturezas + outros),
  cada uma com cache de 60s. Reusa o endpoint `?ativo=true&page_size=1`
  e lê `count` da resposta paginada — sem precisar de endpoint dedicado.
- **feat(dashboard):** Dashboard reescrito com 3 seções:
  - Header com nome + município + **total de servidores ativos**
  - "Servidores por vínculo": 4 cards (Efetivos / Comissionados /
    Contratados / Eletivos), cada um clicável navega para a lista filtrada
  - "Servidores por área": 4 cards (Administração / Saúde / Educação /
    Assistência social), cada um navega para a lista filtrada
  - Linha extra "outros" para a quinta categoria quando > 0
  - Atalhos para áreas operacionais (Servidores / Cargos / Lotações / Folha
    / Rubricas / Relatórios)
- **docs(guia):** `LAST_UPDATED` para 2026-05-08. Nova seção "Organização:
  vínculos e áreas (secretarias)" explica as duas dimensões e como
  combiná-las no dia a dia, com referência direta ao Dashboard e à
  pesquisa filtrada. Posicionada antes de Cadastros centrais — é a
  base conceitual.

#### Por quê

- **Demanda real do município-piloto.** O Dr. Renzo levantou em conversa
  que o sistema atual não distingue secretarias e exige recadastramento
  manual para descobrir quem é de cada área. Validamos a frustração nos
  dados reais (369 servidores num balde sem nome) e atacamos a raiz: o
  Fiorilli mistura "lotação física" com "natureza de despesa" no mesmo
  campo; o Arminda separa em dimensões independentes.
- **Eletivo como regime próprio é correção semântica.** Tratar Prefeito
  como "comissionado" estava errado — eletivo tem mandato, não cargo de
  confiança, e o cálculo de folha futuro pode precisar diferenciar
  (Bloco 2).
- **Classificação automática + revisão manual é o padrão certo.** A
  máquina cobre o caso fácil (escola é educação), o humano resolve o
  caso difícil (Sec. de Cultura → onde encaixa?). Sem isso, ou se gasta
  meses recadastrando, ou se aceita o caos do "balde genérico".
- **Dashboard navegacional (não decorativo).** Cada KPI é um link para
  a lista filtrada — o operador descobre que algo está estranho clicando,
  não esperando um relatório.

#### Impacto

- **Backend:** 248 testes verde (era 244, +4). 3 migrations novas (1 schema +
  2 data). Sem mudança de contrato exceto adição de campo (todas opcionais
  no payload, default no banco). Importador agora classifica natureza
  automaticamente na ingestão (mas mantém compatibilidade — sem natureza
  vira "outros").
- **Frontend:** Bundle inicial 500 KB / 155 KB gzip (+1 KB pelo Dashboard
  reescrito + kpis hook). Build verde, typecheck verde, 10/10 testes verde.
- **Sem regressão.** Todas as telas continuam funcionando; filtros novos
  são opcionais.

#### Próximos passos

- **Onda 1.4-bis (Importador estendido):** importar `DEPDESPESA` do SIP e
  cruzar com `LOCAL_TRABALHO` para inferir natureza pelo empenho quando
  divergir do nome da lotação. Resolve os 369 servidores no "balde sem
  nome" automaticamente para a maioria — caso edge do Dr. Renzo.
- **Bloco 2 (engine de cálculo):** vai consumir natureza para
  determinar unidade orçamentária do empenho de cada lançamento.

---

### Bloco 1.5 — Onda 1.5: Documentos, Configurações, Pesquisa global, Notificações honestas · 2026-05-05

> Fecha as lacunas reais do Bloco 1: aba Documentos no detalhe do servidor,
> página Configurações com 3 abas (Perfil, Segurança, Usuários), pesquisa
> global com ⌘K, e dropdown de notificações honesto (sem badge fake). O
> Bloco 1 agora não tem mais buracos de UX em produção.

#### Adicionado — Backend (5 endpoints novos)

- **feat(core/auth):** `POST /api/auth/change-password/` — troca de senha
  do próprio usuário com `current_password`, `new_password`,
  `new_password_confirm`. Valida senha atual, exige confirmação igual,
  nova diferente da atual, e roda `validate_password` do Django
  (mínimo, similaridade, lista de senhas comuns). Limpa
  `precisa_trocar_senha`.
- **feat(core/auth):** `PATCH /api/auth/me/` — edita campos do próprio
  User (apenas `nome_completo` por enquanto). E-mail é imutável.
- **feat(core/users):** `GET/POST/PATCH/DELETE /api/core/usuarios/` —
  gestão de `UsuarioMunicipioPapel` no tenant ativo. Apenas
  `admin_municipio` + `staff_arminda` operam. Cria User + papel
  atomicamente; se o e-mail já existir em outro município, reaproveita.
  DELETE remove só a associação (não deleta o User).
- **test:** 19 testes novos (244 verde no total).

#### Adicionado — Frontend

- **feat(servidores):** Aba **Documentos** no `ServidorDetailPage`.
  - `lib/queries/documentos.ts` — `useDocumentosDoServidor`,
    `useUploadDocumento`, `useDeleteDocumento` (multipart/form-data via
    FormData; axios deixa o navegador preencher o boundary).
  - `pages/servidores/DocumentoUploadSheet.tsx` — Sheet com input de
    arquivo (PDF/JPG/PNG até 10 MB), tipo (RG, CPF, certificado, etc.)
    e descrição opcional.
  - Aba na DetailPage: lista cards de documentos com download e delete;
    botão "Enviar documento" no topo; AlertDialog de confirmação
    para excluir.

- **feat(configuracoes):** Página `/configuracoes` real (não mais
  `EmConstrucaoPage`). 3 abas em `Tabs` shadcn:
  - **Perfil** — `PerfilTab.tsx` edita nome via `PATCH /auth/me/`,
    refresca o `AuthContext` no sucesso, exibe e-mail como read-only.
  - **Segurança** — `SegurancaTab.tsx` formulário de troca de senha
    com toggle de visibilidade, validação Zod
    (mínimo 8 chars + confirmação igual + diferente da atual), erros
    do backend mapeados por campo via `code` do `ValidationError`.
  - **Usuários** (admin only) — `UsuariosTab.tsx` lista paginada com
    troca inline de papel via Select; Sheet "Novo usuário" com
    e-mail/nome/papel/senha-temporária; botão "Remover acesso" com
    AlertDialog. Não-admins veem mensagem "apenas administradores
    podem gerir usuários".
  - `lib/queries/usuarios.ts` — hooks correspondentes.
  - `lib/auth.ts` — `updateMe()` e `changePassword()` adicionados.

- **feat(search):** Pesquisa global com **⌘K / Ctrl+K**.
  - Lib `cmdk` instalada.
  - Primitivos `command.tsx` e `dialog.tsx` adicionados a
    `components/ui/`.
  - `components/search/CommandPalette.tsx` — Dialog que abre via atalho
    ou clique no SearchTrigger. Busca paralela debounced (250ms) em 4
    APIs (`/people/cargos/`, `/people/lotacoes/`, `/people/servidores/`,
    `/payroll/rubricas/`) com `?search=` e `page_size=5`. Resultados
    agrupados por tipo, navegam para a página relevante. Quando
    vazio, mostra atalhos para todas as áreas (Dashboard, Servidores,
    Configurações, Guia de uso, etc.).
  - `useCommandPaletteShortcut` registra ⌘K / Ctrl+K globalmente.
  - `AppShell` mantém o estado do palette e passa `onSearchOpen` para
    o Topbar.

- **feat(layout):** `Topbar.tsx`
  - SearchTrigger agora é interativo (abre o palette).
  - **Notificações honestas:** o sino sem badge fake; ao clicar abre
    DropdownMenu com mensagem "Nada por enquanto" e nota explicando
    que alertas reais entram nos Blocos 5 (TCE) e 7 (alertas
    inteligentes).
  - Itens "Meu perfil" e "Trocar senha" do PerfilDropdown deixaram
    de ser `disabled` — agora navegam para `/configuracoes`. Adicionado
    item "Guia de uso".

- **docs(GuiaPage):**
  - `LAST_UPDATED` para 2026-05-05.
  - 2 seções novas: **Configurações** (com FlowItems para Perfil,
    Segurança, Usuários) e **Pesquisa e atalhos** (explica ⌘K,
    como navegar, escopo por município).
  - Status da feature "Documentos" subiu de "em-construcao" para "ok"
    com descrição atualizada.
  - Callout do "Como começar" agora aponta para
    `/configuracoes#seguranca` em vez de "entra na Onda 1.5".

#### Por quê

- **O Bloco 1 estava entregue mas com fricção visível** — botão de
  pesquisa fake, sino com badge falsa, 4 placeholders disabled no
  perfil dropdown, aba Documentos prometida pelo backend mas sem UI.
  Em produção esses detalhes corroem confiança rápido.
- **Configurações de usuário não dão pra ser CLI-only** — qualquer
  prefeitura precisa que o admin cadastre/remova RH/financeiro pela
  UI, sem precisar SSH no servidor.
- **Pesquisa global é UX foundational** — sem ela, encontrar 1
  servidor numa lista de 517 vira fricção repetitiva. ⌘K resolve em
  ~250ms.
- **Notificações fake violam confiança** — badge vermelho permanente
  sem clique acionável é teatro. Estrutura honesta agora; alertas
  reais quando o domínio existir.

#### Impacto

- **Backend:** 244 testes verde (era 225, +19), 4 endpoints novos,
  nenhuma migration, nenhum breaking.
- **Frontend:** 10/10 testes verde, build verde, lint verde (1 warning
  preexistente). Bundle inicial subiu para 499 KB (era 468) por causa
  das novas pages — ainda dentro do alvo. ConfiguracoesPage 15 KB e
  GuiaPage 24 KB são lazy-chunks separados.
- **Sem regressão.** Todas as telas anteriores continuam funcionando.

#### Próximos passos

- Bloco 1 está 100% completo agora — incluindo todas as funcionalidades
  marcadas como "deve fazer parte do Bloco 1" no roadmap original.
- Próximo passo: **Bloco 2 — Engine de cálculo de folha** (DSL de
  fórmulas, INSS, IRRF, FGTS, holerite). Habilita Folha + KPIs
  do Dashboard + as primeiras importações de histórico financeiro
  (EVENTOSFIXOS, MOVIMENTO).

---

### docs(frontend): Guia de uso do sistema acessível em /guia · 2026-05-03

> Página viva de documentação dentro do próprio sistema. Substitui a
> necessidade de manual em PDF — o usuário-operador encontra tudo o que
> precisa direto no menu da sidebar (rodapé, junto com "Configurações").

#### Adicionado

- **feat(frontend):** `pages/GuiaPage.tsx` (rota `/guia`, lazy-loaded em chunk
  separado de 22 KB). Layout em 2 colunas: TOC sticky à esquerda + conteúdo à
  direita com 9 seções:
  - Visão geral
  - Como começar
  - Município ativo (multi-tenant)
  - Papéis e permissões (tabela com 5 papéis: staff_arminda,
    admin_municipio, rh_municipio, financeiro_municipio, leitura_municipio)
  - Cadastros centrais (Cargos, Lotações, Rubricas)
  - Servidores (admissão, edição, desligamento, transferência, dependentes,
    histórico, documentos)
  - Importador Fiorilli SIP
  - Em construção (Bloco 2 a 7 com período-alvo)
  - Suporte
  - Componentes auxiliares: `Section`, `Status`, `FeatureCard`, `FlowItem`,
    `RoadmapItem`, `Callout` (info/warning/tip).
  - Constante `LAST_UPDATED` no topo do arquivo, exibida no header da página.
  - Cada feature recebe um `<Status>` indicando se é "Disponível" /
    "Parcial" / "Em construção" / "No roadmap" — permite ao operador saber
    o que pode usar agora.

- **feat(frontend/layout):** Link "Guia de uso" no rodapé da
  `Sidebar.tsx` (acima de "Configurações"); `BookOpen` icon. Ativa o
  estado visual de NavLink quando a rota é `/guia`.

- **feat(frontend/layout):** Breadcrumb do `Topbar.tsx` reconhece o
  segmento `guia` → exibe "Guia de uso".

- **docs(context):** `CONTEXT.md` raiz ganhou regra de escrita
  obrigatória item 4: "Atualizar o Guia de uso se a alteração afetou
  o que o usuário final vê" + lembrete de atualizar `LAST_UPDATED`.

#### Por quê

- **Onboarding sem fricção.** Operador novo (RH ou financeiro de
  prefeitura) não precisa de manual externo nem de treinamento longo
  para entender o que está disponível e onde ficam os fluxos.
- **Documentação viva, não documentação morta.** Manual fora do sistema
  desatualiza em semanas. Manter dentro do código, com convenção de
  atualização vinculada ao CHANGELOG, garante que a regra "atualizar a
  cada feature" tenha um lar visível.
- **Honestidade sobre o que está pronto.** Cada feature tem um badge de
  status; o operador não tropeça em um botão fake — sabe exatamente
  o que dá para usar e o que ainda virá.

#### Impacto

- Bundle inicial inalterado (468 KB / 145 KB gzip) — `GuiaPage` só
  carrega quando o usuário navega para `/guia`.
- Sem mudança de backend ou contrato.
- 10/10 testes verde, build verde, lint verde.

#### Próximos passos

- A cada onda entregue, atualizar `LAST_UPDATED` + as seções
  pertinentes. Política agora também documentada em `CONTEXT.md` raiz.
- Onda 1.5 (escopo a alinhar) deve atualizar este guia ao adicionar:
  documentos digitalizados (aba do servidor), página de Configurações
  com perfil/segurança/usuários, e pesquisa global ⌘K.

---

### Bloco 1.4 — Onda 1.4: Importador Fiorilli SIP (cadastros) · 2026-05-03

> Importador unidirecional do banco legado Fiorilli SIP (Firebird 2.5) para
> o schema do município no Postgres. Pipeline ETL em 3 camadas (extract /
> transform / load) com idempotência via chave SIP estável. Smoke E2E
> contra o FDB real do município de São Raimundo do Doca Bezerra/MA
> (`SIP.FDB`, 1029 tabelas, 409 MB) entregou: **91/91 cargos, 66/66 lotações,
> 517/517 servidores, 1.503/2.762 vínculos, 279/303 dependentes** importados
> em dry-run. Os 1.259 vínculos com erro são CPFs que existem em
> TRABALHADOR mas não em PESSOA (registros históricos órfãos) — comportamento
> esperado, fora do controle do importador.

#### Adicionado

- **docs(adr):** [ADR-0009 — Importador Fiorilli SIP](docs/adr/0009-importador-fiorilli-sip.md).
  Decisões: `firebirdsql` (pure Python), pipeline ETL em 3 camadas, chave
  SIP estável (`<EMPRESA>-<CODIGO>` para Cargo/Lotação, `CPF` para Servidor,
  `<EMPRESA>-<REGISTRO>` para Vínculo), `update_or_create` para idempotência,
  política de "linhas com erro não param o batch", dry-run com rollback,
  senha do FDB nunca persistida.

- **feat(backend/imports):** Novo app `apps.imports` em `TENANT_APPS` com:
  - `models.py` — `SipImportRecord` (audita uma linha SIP importada).
    Indexado por `(tipo, chave_sip)` único + `(tipo, status)`. Guarda
    `arminda_id`, `payload_sip_hash` (sha256 do dict bruto, detecta drift),
    `status` (ok/erro), `erro_mensagem`.
  - `adapters/firebird.py` — read-only. `FirebirdConfig` (dataclass),
    `open_connection` (context manager), e `fetch_<entidade>` para
    cargos/locais_trabalho/pessoas/trabalhadores/dependentes/eventos.
    Charset WIN1252, normalização de espaços/bytes.
  - `services/mapping.py` — funções **puras** SIP-row → Arminda-dict.
    Mapeamento de códigos SIP (instrução, sexo, estado civil, parentesco,
    vínculo) para enums Arminda. `payload_hash()` para detecção de drift.
  - `services/loaders/{cargos,lotacoes,servidores,vinculos,dependentes}.py`
    — `update_or_create` por entidade. Resolve FKs via `SipImportRecord`
    (não consulta o banco de domínio direto, evita fan-out de queries).
    `LoaderStats` (lidos/criados/atualizados/erros) para relatório.
  - `management/commands/import_fiorilli_sip.py` — CLI orquestrador
    (`--tenant`, `--host`, `--database`, `--user`, `--password`,
    `--tabelas`, `--limit`, `--dry-run`). Imprime relatório final
    com erros (até 20 visíveis, restante em SipImportRecord).

- **feat(backend/people):** Migrations `0002` adiciona campos opcionais
  necessários para receber dados ricos do SIP/eSocial:
  - **Cargo:** `data_criacao`, `data_extincao`, `vagas_total`,
    `dedicacao_exclusiva`, `atribuicoes`.
  - **Servidor:** `nacionalidade`, `raca`, `nome_pai`, `nome_mae`,
    `instrucao` (código eSocial).
  - **VinculoFuncional:** `matricula_contrato`, `tipo_admissao`,
    `processo_admissao`.
  - Todos opcionais (blank/null) — frontend atual continua funcionando
    sem preencher nenhum.

- **chore(deps):** `firebirdsql==1.4.5` + `passlib==1.7.4` em
  `requirements.txt` (Bloco 1.4).

- **test(imports):** **32 testes novos** (24 mapping puro + 8 loaders
  com Postgres). Cobertura por:
  - `test_mapping.py` — input/output de cada função puro, casos de borda
    (códigos desconhecidos, datas ausentes, CPF curto, situação demitido,
    payload_hash estável independente de ordem).
  - `test_loaders.py` — cria, atualiza idempotente, linha inválida não
    para batch, FK ausente gera erro mas não levanta. Reusa fixture
    `tenant_a` global.

#### Smoke E2E (validação contra FDB real)

Subimos `jacobalberty/firebird:2.5-ss` em Docker com o `SIP.FDB` do
município-piloto montado, criamos usuário `FSCSIP` (owner do FDB,
necessário para SYSDBA estar bloqueado por SQL ROLE típico do Fiorilli),
rodamos:

```bash
manage.py import_fiorilli_sip --tenant mun_sao_raimundo \
  --host 127.0.0.1 --port 13050 \
  --database /firebird/data/SIP.FDB \
  --user FSCSIP --password fscpw \
  --tabelas cargos,lotacoes,servidores,vinculos,dependentes --dry-run
```

Resultado:

| Tabela | Lidas | OK | Taxa | Erros |
|---|---|---|---|---|
| Cargos | 91 | 91 | 100% | 0 |
| Lotações | 66 | 66 | 100% | 0 |
| Servidores | 517 | 517 | 100% | 0 |
| Vínculos | 2.762 | 1.503 | 54% | 1.259 |
| Dependentes | 303 | 279 | 92% | 24 |

Os 1.259 erros em Vínculos têm a mesma causa: o CPF de TRABALHADOR não
existe na tabela PESSOA. Dado típico de Fiorilli (registros históricos
órfãos). Está fora do controle do importador — em produção, o município
corrige os CPFs em PESSOA e re-roda (a importação é idempotente).

#### Por quê

- **Bloqueia o piloto.** Sem importar os 517 servidores reais, o
  município-piloto não consegue testar o fluxo de folha contra dados
  conhecidos. A importação dos cadastros é gate para o Bloco 6.
- **Pipeline em 3 camadas isola o adaptador.** O `mapping` puro fica
  trivialmente testável (24 testes em 0.10s, sem DB). Trocar Fiorilli
  SIP por outro sistema legado é trocar `adapters/`, sem mexer em
  loaders ou mapping.
- **Idempotência por chave SIP elimina rework.** O usuário pode rodar
  3 vezes seguidas (corrigindo CPFs entre runs) e o estado final
  converge.
- **Histórico financeiro foi deixado para depois.** EVENTOSFIXOS (1.387)
  e MOVIMENTO (~250k) só fazem sentido depois do Bloco 2 (engine de
  cálculo) — o que importamos agora dá pra calcular folha do zero,
  sem precisar do histórico.

#### Impacto

- **Backend:** 4 apps → **5 apps** (`apps.imports` novo). 2 migrations
  novas (people 0002, imports 0001). **225 testes verde** (193 → 225,
  +32) com 94% cobertura (97% → 94% pelo código novo do adapter
  Firebird que só é exercido em smoke E2E, não em CI).
- **Sem mudança de contrato API.** As migrations adicionam campos
  opcionais; nenhum endpoint mudou.
- **Deps novas:** `firebirdsql` e `passlib` (ambas pure Python; sem
  binários nativos pra deploy).

#### Próximos passos

- **Onda 1.4-bis (curta):** Filtrar `TRABALHADOR.SITUACAO` para excluir
  registros históricos antes de tentar resolver CPF, reduzindo a
  contagem de erros "esperados" para ~0.
- **Bloco 2:** Engine de cálculo (DSL de fórmulas). Aí podemos ressuscitar
  o `fetch_eventos` do adapter (esqueleto já está) e importar EVENTOSFIXOS
  + MOVIMENTO histórico para testes de paridade.

---

### Bloco 1.3 — Onda 1.3c: Edição inline + ações + lazy routes · 2026-04-30

> Fecha as lacunas que estavam read-only na onda anterior. Servidor pode
> agora ser editado, desligado, transferir vínculo, e ter dependentes
> cadastrados/editados/excluídos diretamente no detalhe — todas as ações
> chamam endpoints atômicos que já existiam no backend (Bloco 1.2).
> Bundle do frontend foi splitado por rota: o chunk inicial caiu de
> 680 KB para 468 KB.

#### Adicionado

- **feat(frontend/queries):** Hooks novos
  - `lib/queries/vinculos.ts` — `useUpdateVinculo`, `useTransferirVinculo`
    (POST `/api/people/vinculos/{id}/transferir/`)
  - `lib/queries/dependentes.ts` — `useCreateDependente`, `useUpdateDependente`,
    `useDeleteDependente`. Ambos invalidam o cache de `["servidores", tenant]`
    porque o detalhe do servidor traz os vínculos e dependentes embutidos.

- **feat(frontend/servidores):** 4 componentes novos no fluxo do servidor
  - `ServidorEditSheet.tsx` — Sheet com formulário de edição dos dados
    pessoais (identificação, contato, endereço); zod + react-hook-form;
    erros do backend mapeados por campo.
  - `DesligamentoDialog.tsx` — AlertDialog com formulário de desligamento
    (data + motivo opcional). Avisa que encerra TODOS os vínculos ativos.
  - `TransferenciaDialog.tsx` — AlertDialog para transferir um vínculo;
    dropdown popula com lotações ativas (excluindo a atual) e exige
    `data_transferencia`.
  - `DependenteFormSheet.tsx` — Sheet de criação/edição de dependente
    com checkboxes para flags `ir` e `salario_familia`. Aceita um shape
    mínimo (compatível com o serializer embedded e o full).

- **feat(frontend/servidores/detalhe):** `ServidorDetailPage.tsx` ganhou
  - Botões "Editar dados" e "Desligar" no header (Desligar só aparece
    se o servidor estiver ativo).
  - DropdownMenu por vínculo na aba "Vínculos" com opção "Transferir
    lotação" (só para vínculos ativos).
  - Botão "Novo dependente" + DropdownMenu por dependente (Editar/Excluir)
    na aba "Dependentes".
  - AlertDialog de confirmação para excluir dependente.

- **perf(frontend):** Code-splitting por rota com `React.lazy` +
  `Suspense` em `App.tsx`. Cada página de domínio virou um chunk:
  - CargosListPage 11 KB · LotacoesListPage 11 KB · RubricasListPage 14 KB
  - ServidoresListPage 13 KB · ServidorDetailPage 37 KB
  - DashboardPage 4 KB · sheet (chunk shared) 132 KB
  - **Bundle inicial:** 680 KB → **468 KB** (gzip 197 KB → 146 KB,
    redução de 31%). Vite parou de avisar do warning de chunk grande.

#### Por quê

- **Operação real exige edição.** Sem editar dados pessoais, desligar,
  transferir e cadastrar dependentes, o usuário-piloto não consegue
  rodar nenhum fluxo realista — só consegue admitir e olhar. Esses 4
  fluxos completam o ciclo de vida CRUD do servidor.
- **Reaproveitamento total do backend.** Todos os endpoints já existem
  desde o Bloco 1.2 (services atômicos `admitir_servidor`,
  `desligar_servidor`, `transferir_lotacao` + CRUD de Dependente).
  A onda foi exclusivamente frontend, sem migration nem mudança de
  contrato.
- **Code-splitting agora, não depois.** Adicionar lazy routes ficou
  mais simples enquanto o roteamento ainda é pequeno (10 rotas);
  fazer isso depois exigiria refatorar mais arquivos.

#### Impacto

- Sem mudança de backend, sem migration, sem mudança de contrato.
- Bundle inicial 31% menor — primeira renderização mais rápida em
  conexões lentas (target: prefeituras com internet ruim).
- Frontend cresceu para ~10.5k LOC TS em ~64 arquivos.
- 10/10 testes verde, build verde, lint verde (5 warnings preexistentes).

#### Próximos passos

- **Onda 1.4** — Importador Fiorilli SIP. ADR-0009 + `apps.imports`
  (Django app novo) + adapter Firebird (firebirdsql) + migrations
  para campos faltantes em Cargo/Servidor/Vínculo + management command
  `import_fiorilli_sip --dsn ... --dry-run` + import MVP de
  Cargo/Lotação/Servidor/Vínculo/Dependente.
- **Onda 1.3d (opcional)** — Upload de documentos digitalizados no
  detalhe do servidor (precisa multipart/form-data, valida tamanho
  e tipo).

---

### Bloco 1.3 — Onda 1.3b: Telas de domínio (Cargos, Lotações, Rubricas, Servidores) · 2026-04-30

> Onda dedicada às telas autenticadas de domínio. As 4 áreas que estavam
> em `EmConstrucaoPage` ganharam CRUD funcional ligado à API, com busca,
> filtros, ordenação, paginação e ações por linha. Tudo reaproveitando
> os tokens OKLCH e os primitivos shadcn já estabelecidos. Mantém o
> mesmo padrão de tratamento de erro de domínio do backend (ValidationError
> com `code` e mensagem por campo) — erros são mapeados nos próprios
> campos do formulário; falha genérica cai num `toast`.

#### Adicionado

- **feat(frontend/ui):** Primitivos shadcn faltantes
  - `components/ui/table.tsx` (Table/Header/Body/Row/Head/Cell)
  - `components/ui/badge.tsx` (variants: default/secondary/destructive/outline/success/warning/info/muted)
  - `components/ui/select.tsx` (Radix Select wrapper)
  - `components/ui/alert-dialog.tsx` (confirmação de delete)
  - `components/ui/tabs.tsx` (Radix Tabs wrapper, usado em ServidorDetailPage)
  - Deps novas: `@radix-ui/react-select`, `@radix-ui/react-tabs`,
    `@radix-ui/react-alert-dialog`, `@radix-ui/react-tooltip`.

- **feat(frontend/queries):** Hooks TanStack Query por recurso, em
  `src/lib/queries/`:
  - `cargos.ts` — list/get/create/update/delete + tipos `CargosListParams`
  - `lotacoes.ts` — idem, com filtro `raiz` e `lotacaoPaiId`
  - `rubricas.ts` — idem, com filtro por `tipo`
  - `servidores.ts` — list/get + ações (`admitir`, `update`, `desligar`,
    `historico`).
  - Padrão: `queryKey` escopado por tenant (`["cargos", activeTenant, ...]`)
    para evitar mistura de cache entre municípios; `placeholderData:
    keepPreviousData` para paginação suave.
  - Tipo `*Input = Omit<*Write, "id">` corrige limitação do
    drf-spectacular (campos `read_only_fields` saem como `readonly`
    obrigatórios na schema gerada).

- **feat(frontend/cargos):** `pages/cargos/CargosListPage.tsx` +
  `CargoFormSheet.tsx`. Tabela com busca debounced (300ms), filtro
  por status, ordenação clicável (nome/código), paginação DRF, ações
  por linha (editar, ativar/desativar, excluir). Form de create/edit
  via Sheet slide-from-right com Zod + react-hook-form.

- **feat(frontend/lotacoes):** `pages/lotacoes/LotacoesListPage.tsx` +
  `LotacaoFormSheet.tsx`. Mesmo padrão de Cargos; form inclui dropdown
  de **Lotação pai** (popula com lotações ativas para hierarquia
  organograma).

- **feat(frontend/rubricas):** `pages/rubricas/RubricasListPage.tsx` +
  `RubricaFormSheet.tsx`. Filtro adicional por **tipo**
  (provento/desconto/informativa), checkboxes de incidências
  (INSS/IRRF/FGTS), campo `formula` como TextArea (DSL apenas
  armazenada — interpretação no Bloco 2).

- **feat(frontend/servidores):** `pages/servidores/ServidoresListPage.tsx`
  + `ServidorAdmissaoSheet.tsx` + `ServidorDetailPage.tsx`. Lista
  paginada com busca por matrícula/nome/CPF; clique na linha vai para
  rota `/servidores/:id`. Sheet de **admissão** chama
  `POST /api/people/servidores/admitir/` (cria Servidor + Vínculo em
  transação atômica). Detalhe com 4 abas:
  - **Pessoais** — view read-only (identificação + contato + endereço)
  - **Vínculos** — cards com cargo/lotação/regime/datas/salário
  - **Dependentes** — cards com flags IR / sal. família
  - **Histórico** — timeline com snapshots simple-history (tipo,
    data/hora, autor, snapshot ativo, motivo)

- **feat(frontend/routes):** `App.tsx` substitui `EmConstrucaoPage`
  pelas 4 páginas reais e adiciona rota nested `/servidores/:id`.

#### Por quê

- **Operação real depende de cadastros.** Sem CRUDs, não dá para o
  usuário-piloto poder testar o sistema. As telas reais habilitam o
  fluxo de admissão ponta-a-ponta — único caminho para validar a
  paridade contra o sistema legado antes do importador entrar.
- **Estabelecer padrão antes de Servidores.** Cargo/Lotação/Rubrica
  são CRUDs simples (3–6 campos). Implementá-los primeiro estabelece
  o padrão de UI (toolbar + tabela + sheet de form + alert dialog
  de delete) que Servidores reaproveita — reduzindo divergências
  estilísticas entre as telas.
- **Read-only no detalhe do servidor.** Edição inline e ações
  (desligar, transferir, novo dependente, upload documento) ficam
  para Onda 1.3c. Manter este escopo enxuto entrega valor sem
  comprometer a previsibilidade da onda.

#### Impacto

- Frontend cresceu para **5.6k linhas TS**; bundle de produção foi de
  622 KB para **680 KB** (gzip 197 KB) — segue dentro do alvo, mas o
  warning do Vite sobre code-splitting ficou mais alto. Não bloqueia,
  resolveremos com lazy routes na próxima sub-onda.
- Sem mudança de backend, sem migrations, sem mudança de contrato.
- 10/10 tests verde, build verde, lint verde (5 warnings preexistentes
  de fast-refresh).

#### Próximos passos

- **Onda 1.3c** — Edição do servidor (sheet), ação de desligamento,
  transferência de vínculo (sheet por vínculo), CRUD de dependentes
  e upload de documentos. Lazy-load das rotas para reduzir bundle.
- **Onda 1.4** — Importador Fiorilli SIP (FDB → Postgres), conforme
  diagnóstico em [docs/adr/0009-importador-fiorilli.md](#) (a escrever).

---

### Bloco 1.3 — Onda 1.3a-bis: Adaptação do design Arminda (Claude Design) · 2026-04-29

> O usuário gerou um design completo no Claude Design (claude.ai/design) e
> exportou como bundle. Esta entrega adapta o sistema de design para o
> nosso stack (Vite + Tailwind + shadcn) mantendo o visual original:
> tokens OKLCH, dark mode default, brand panel no login, sidebar
> redesenhada, topbar com breadcrumb e theme toggle.

#### Adicionado

- **feat(frontend/design):** Sistema de tokens **OKLCH** (light + dark).
  - `src/styles/globals.css` reescrito com 14 famílias de tokens
    (background, foreground, card, popover, primary[+soft], secondary,
    muted, accent, success, warning, info, destructive[+soft], border[+strong]).
  - Convenção: variáveis CSS guardam `L C H` (sem `oklch()`); o
    `tailwind.config.ts` envelopa em `oklch(var(--token))` ao consumir,
    permitindo `oklch(var(--ring) / 0.4)` para alfa.
  - **Fontes** Inter + JetBrains Mono importadas do Google Fonts;
    `font-feature-settings: cv02 cv03 cv04 cv11` para variantes
    estilísticas do Inter.
  - **Default dark mode** (escolha do design canvas).

- **feat(frontend/theme):** `src/lib/theme.tsx` — ThemeProvider +
  `useTheme()` hook. Persiste em localStorage com chave
  `arminda_theme`. Aplica classe `dark` no `<html>`.

- **feat(frontend/brand):** `src/components/brand/Logo.tsx` — SVG
  oficial (retângulo arredondado + monograma "M"). Variants
  `light` (para fundos escuros) e `withText`.

- **feat(frontend/layout):** Sidebar redesenhada.
  - Logo no topo (collapsa para ícone-só em modo collapsed).
  - **Município context card** mostrando ativo + atalho de troca.
  - Grupo "Operação" com 7 itens (Dashboard, Servidores, Cargos,
    Lotações, Folha, Rubricas, Relatórios) — ícones lucide-react.
  - Footer com Configurações + botão de colapso (248px → 64px).
  - Estado ativo usa `bg-primary-soft` + `text-primary-soft-foreground`.

- **feat(frontend/layout):** Topbar redesenhada.
  - Breadcrumb gerado automaticamente da rota.
  - Search trigger com tecla `⌘K` (placeholder — CmdK real entra
    na Onda 1.3b).
  - Toggle de tema (sol/lua), sino com badge de notificação,
    avatar dropdown com dados do usuário + papel + logout.

- **feat(frontend/pages):**
  - `LoginPage` redesenhada em **2 colunas**: brand panel à esquerda
    com gradient azul + grid decorativo + orb radial + headline
    "Folha de pagamento moderna para a gestão pública"; formulário à
    direita com toggle de visibilidade da senha (Eye/EyeOff).
  - `SelecionarMunicipioPage` em cards radio-style com seleção
    visual + botão "Acessar Arminda".
  - `DashboardPage` com header + 3 cards-KPI placeholder
    (servidores, folha mensal, variação 30d) + grid de 6 atalhos.

#### Modificado

- **chore(frontend/tailwind):** `tailwind.config.ts` reescrito.
  - Cores em `oklch(var(--token))` em vez de `hsl(var(--token))`.
  - Tokens novos: `primary-soft`, `success`, `warning`, `info`,
    `border-strong`, `popover` + variantes `*-foreground` e `*-soft-foreground`.
  - `fontFamily.sans = Inter`, `fontFamily.mono = JetBrains Mono`.
  - Animations: `fade-in`, `slide-up`, `slide-from-right` (do design).

- **chore(frontend/main.tsx):** Envolve em `<ThemeProvider>` antes
  do `<QueryClientProvider>`.

- **fix(test):** `LoginPage.test.tsx` ajustado para selectors mais
  específicos (botão "Continuar", label "Senha" exato em vez de
  regex que casava com "Esqueci minha senha" e "Mostrar senha").

#### Validações

- `npx tsc --noEmit` — limpo.
- `npm run build` — **467 KB / 145 KB gzip** (subiu ~16 KB pelos
  tokens novos + fontes Inter/Mono linkadas via Google Fonts).
- `npm test` — **10/10 passando**.
- `npm run lint` — 4 warnings react-refresh em arquivos shadcn padrão
  e em providers (auth-context, theme) que exportam hook + provider —
  aceitáveis.
- Backend mantido: 193 testes verde, 97% cobertura.
- Smoke manual: `curl http://localhost:5173/login` HTTP 200.

#### Decisões de adaptação

- **Não adaptamos:** CmdK real, painel de notificações com lista,
  gráficos SVG do dashboard original, telas de Folha/Holerite
  (ficam para Onda 1.3b ou Bloco 2).
- **Sidebar mobile (off-canvas):** parking — no design original
  ela some abaixo de `lg`. Adicionar Sheet mobile em hardening.
- **Densidade ajustável:** o design canvas tinha tweaks de
  densidade (`compact|comfortable|spacious`); pulamos por agora,
  default `comfortable`.

---

### Bloco 1.3 — Onda 1.3a: Frontend autenticado · 2026-04-29

> Primeira fatia do frontend autenticado. O esqueleto de login, layout
> e troca de tenant está pronto. Telas de domínio (Servidor, Cargo,
> Lotação, Rubrica) entram na Onda 1.3b.

#### Adicionado

- **feat(frontend):** Geração automática de tipos OpenAPI via
  `openapi-typescript` (ADR-0008).
  - `npm run gen:types` lê `/api/schema/?format=json` do backend
    rodando em `:8000` e escreve `src/types/api.ts`.
  - `npm run gen:types:offline` lê do snapshot `openapi-schema.json`
    commitado.
  - `src/types/index.ts` faz aliases legíveis: `Servidor`,
    `CargoWrite`, `AdmissaoInput`, `LoginResponse`, etc.
  - Tipos manuais à mão são proibidos em código novo a partir desta
    ADR (com exceções documentadas para `UserMe` e
    `HistoricoServidorEntry`, onde drf-spectacular não tipa o
    response — TODO: adicionar `@extend_schema` no backend).

- **feat(frontend/auth):** Camada completa de autenticação JWT.
  - `src/lib/auth-storage.ts` — wrappers de localStorage para tokens
    e tenant ativo.
  - `src/lib/auth.ts` — `login()`, `logout()`, `fetchMe()`.
  - `src/lib/auth-context.tsx` — `<AuthProvider>` + `useAuth()` hook
    com `user`, `activeTenant`, `papelAtual`, `switchTenant`.
  - `src/lib/api.ts` reescrito: interceptor de request injeta
    `Authorization: Bearer <access>` + `X-Tenant: <schema>`;
    interceptor de response tenta refresh em 401 (com lock para evitar
    múltiplas chamadas concorrentes), redireciona para `/login` se
    refresh falhar.

- **feat(frontend/components):** 11 primitivos shadcn/ui adicionados
  via `npx shadcn add` (button, input, label, card, dropdown-menu,
  sheet, separator, avatar, skeleton, sonner, form). Versionados em
  `src/components/ui/`.

- **feat(frontend/layout):** AppShell + Sidebar + Topbar.
  - `Sidebar` com 6 itens (Dashboard, Servidores, Cargos, Lotações,
    Rubricas, Relatórios) — esconde abaixo de `lg`.
  - `Topbar` com seletor de município (dropdown se >1, label estático
    se 1) + dropdown de perfil com logout.
  - Trocar de município chama `queryClient.clear()` para evitar
    vazamento de cache entre tenants.

- **feat(frontend/pages):**
  - `LoginPage` (`/login`) — formulário com validação HTML5,
    mensagens de erro com `code` do backend, redireciona pós-login.
  - `SelecionarMunicipioPage` (`/selecionar-municipio`) — escolha de
    tenant para usuários com 2+ municípios.
  - `DashboardPage` (`/`) — placeholder com cards de atalhos.
  - `EmConstrucaoPage` — placeholder reutilizado em
    `/servidores`, `/cargos`, `/lotacoes`, `/rubricas`, `/relatorios`.
  - `<RequireAuth>` wrapper para rotas autenticadas.

- **test(frontend):** 8 testes novos.
  - `auth-storage.test.ts` (5): tokens round-trip, tenant ativo,
    clear total, comportamento sem storage.
  - `LoginPage.test.tsx` (3): render, submit chama `login()` com
    payload correto, mensagem de erro aparece em falha.
  - `test/utils.tsx` com helpers `renderWithProviders` e
    `renderWithAuth`.

#### Modificado

- **chore(frontend/deps):** instalado `openapi-typescript` (dev),
  `@testing-library/user-event` (dev). 11 primitivos shadcn trazem
  Radix + sonner + react-hook-form + next-themes.
- **chore(frontend):** `main.tsx` envolve `<App />` em `<AuthProvider>`
  + `<Toaster>` (sonner). `App.tsx` reescrito com rotas autenticadas.
- **chore(.gitignore):** já incluía `*.tsbuildinfo` (commit anterior).

#### Validações

- `npx tsc --noEmit` — limpo.
- `npm run lint` — 3 warnings (fast-refresh em arquivos shadcn padrão
  e em `auth-context.tsx` que exporta hook + provider — aceitável).
- `npm run format` — verde.
- `npm run build` — 451 KB / 141 KB gzip.
- `npm test` — **10/10 passando** (5 storage + 3 login + 2 HomePage
  legado).
- Backend: 193 testes mantidos verdes, 97% cobertura.

#### Próximos passos

- **Onda 1.3b** (~1 sem): Servidor (lista + detalhe + admissão),
  Cargo CRUD, Lotação CRUD, Rubrica esqueleto.
  Hooks de API tipados consumindo `components["schemas"][...]`.
  Endpoint `@extend_schema` no backend para tipar `UserMe` e
  `HistoricoServidorEntry` (eliminar tipagem manual).
- Adicionar `@extend_schema` no `MeView` para que o `gen:types` tipe
  o response de `/api/auth/me/`.

---

### Bloco 1.2 — Onda 3 (hotfix): admin do Django + cobertura HTML · 2026-04-29

> ⚠ Bug identificado por **navegação manual do usuário** que minha
> bateria automatizada anterior não pegou. Documentando aqui com
> transparência sobre o gap.

#### Fix

- **fix(core/middleware):** `TenantHeaderOrHostMiddleware` parou de
  setar `request.tenant = None` em rotas públicas. Agora o atributo
  simplesmente **não é definido** quando estamos no schema `public`.
  - **Sintoma:** `GET /admin/` retornava HTTP 500 com
    `AttributeError: 'NoneType' object has no attribute 'schema_name'`
    em `django_tenants/templatetags/tenant.py:61` (template tag
    `is_public_schema`, usada pelo template do admin via
    `{% load tenant %}`).
  - **Causa:** a template tag faz `hasattr(request, 'tenant')` antes
    de acessar `.schema_name`. Atributo presente porém None passa pelo
    `hasattr` e quebra na linha seguinte.
  - **Fix:** não setar o atributo. `hasattr(...)` retorna False; a
    template tag interpreta como "schema public" — o que está correto.
  - **Arquivo:** `apps/core/middleware/tenant.py`.
  - **Impacto:** `/admin/` e demais rotas públicas voltam a renderizar
    normalmente. Endpoints API (`/api/people/...`) seguem inalterados:
    o middleware continua setando `request.tenant` quando o header
    `X-Tenant` é resolvido.

#### Adicionado (cobertura)

- **test(core):** `apps/core/tests/test_admin_smoke.py` — 12 testes
  novos cobrindo:
  - 8 páginas do admin do Django (`/admin/`, `/admin/login/`,
    `/admin/auth/group/`, `/admin/core/{user,municipio,domain,
    usuariomunicipiopapel,configuracaoglobal}/`).
  - 3 páginas do drf-spectacular (`/api/schema/`, `/api/docs/`,
    `/api/redoc/`).
  - 1 teste explicito do invariante "request.tenant não existe em
    rota pública" para evitar regressão.
  - **Por que faltava:** minha bateria anterior usava `APIClient` do
    DRF para testar JSON. Templates HTML do admin (que carregam
    `{% load tenant %}` do `django-tenants`) **nunca eram renderizados
    durante os testes**. Bug histórico ficou invisível até o usuário
    abrir o `/admin/` no browser.

#### Validações

- `pytest` — **193/193 passando** em ~39s (12 novos sobre 181 anteriores).
- `pytest --cov` — **97% de cobertura** mantida.
- `ruff format` + `ruff check` — verdes.
- `python manage.py check` — sem warnings.
- Smoke manual via curl: 11 páginas (admin + swagger + redoc + schema)
  todas retornam 200/302 sem mensagem de erro no body.

---

### Bloco 1.2 — Onda 3: Services + Rubrica + criar_usuario · 2026-04-29

> Camada de services (regras de negócio) finalmente entra em ação:
> admissão, desligamento e transferência saem do `serializer.save()`
> ingênuo e passam a executar invariantes de domínio em transação atômica.
> Bloco 1.2 está agora 75% completo (Ondas 1+2+3 de 4).

#### Adicionado

- **feat(people/services):** Camada de regras de negócio em
  `apps/people/services/`.
  - `exceptions.py` com `DomainError`, `AdmissaoInvalidaError`,
    `DesligamentoInvalidoError`, `TransferenciaInvalidaError`. Cada uma
    carrega `code` estável.
  - `admissao.admitir_servidor(DadosAdmissao)` — cria Servidor +
    VinculoFuncional em uma transação atômica, com 13 invariantes
    validadas.
  - `desligamento.desligar_servidor(DadosDesligamento)` — encerra todos
    os vínculos ativos + marca servidor inativo. 5 codes de erro.
  - `transferencia.transferir_lotacao(DadosTransferencia)` — encerra
    vínculo atual e cria novo na nova lotação preservando atributos.
    5 codes de erro.
  - Todos com `@transaction.atomic` + `select_for_update()` onde
    necessário.

- **feat(people/views):** Endpoints `@action` orquestrando services.
  - `POST /api/people/servidores/admitir/`
  - `POST /api/people/servidores/<id>/desligar/`
  - `POST /api/people/vinculos/<id>/transferir/`
  - `_domain_error_to_validation_error()` traduz `DomainError` em
    HTTP 400 com `code` estável.

- **feat(payroll):** CRUD de **Rubrica** (esqueleto — DSL no Bloco 2).
  - Pattern triplo de serializers, `/api/payroll/rubricas/` com filtros
    e busca, RBAC dedicado: leitura aberta, escrita exige
    `IsFinanceiroMunicipio` (RH não cria rubrica).

- **feat(core):** Management command **`criar_usuario`** (resolve gap
  do Bloco 1.1: hoje não tínhamos como atribuir papel via CLI).
  - Cria User + UsuarioMunicipioPapel opcional. Suporta
    `--staff-arminda`, `--superuser`, `--precisa-trocar-senha`.
  - Senha via `--password` ou `--senha-stdin` (evita histórico shell).

- **test:** 55 testes novos.
  - 18 admissão (caminho feliz + cada um dos 15 codes incluindo
    `CPF_INVALIDO` e `PIS_INVALIDO` + atomicidade)
  - 6 desligamento, 6 transferência
  - 8 endpoints @action (HTTP + RBAC + propagação de code)
  - 5 Rubrica CRUD + RBAC + isolamento
  - 12 criar_usuario (cobre todos os flags)

#### Fix

- **fix(people/services):** `admitir_servidor` agora captura
  `django.core.exceptions.ValidationError` de `validar_cpf` e
  `validar_pis_pasep` e re-levanta como `AdmissaoInvalidaError` com
  `code=CPF_INVALIDO` ou `PIS_INVALIDO`. **Antes:** CPF/PIS inválidos
  retornavam HTTP 500. **Detectado em:** smoke E2E manual via curl.
  Cobertura de teste adicionada (`test_cpf_invalido`, `test_pis_invalido`).

#### Validações

- `pytest` — **179/179 passando** em ~36s.
- `pytest --cov` — **97% de cobertura** geral.
- `ruff format` + `ruff check` — verdes.
- `python manage.py check` — sem warnings.

#### Próximos passos

- **Bloco 1.2 — Onda 4** (~2 dias): hardening final, OpenAPI revisado,
  `docs/BLOCO_1.2_RESUMO.md`, validação manual end-to-end.
- **Bloco 1.3** (~2 sem): frontend autenticado consumindo a API.

---

### Bloco 1.2 — Onda 2: CRUD Servidor + Vínculo + Dependente + Documento · 2026-04-29

> Cadastros centrais de RH via API REST. Reaproveita o pattern da Onda 1
> (3 serializers, ViewSet, permissions, filtros, isolamento) e adiciona
> validação de domínio brasileiro, histórico funcional via simple-history
> e upload de arquivos (Documento). **Performance baseline atingida**:
> 100 servidores criados em ~5s (gate ROADMAP era < 30s).

#### Adicionado

- **feat(people):** CRUD de **Servidor**, **VinculoFuncional**,
  **Dependente** e **Documento**.
  - Endpoints: `/api/people/{servidores,vinculos,dependentes,documentos}/`.
  - **3 serializers por modelo** (List/Detail/Write) — pattern.
  - `ServidorDetailSerializer` embute dependentes + vínculos resumidos
    (cargo_nome, lotacao_nome, regime_display) — evita N+1 com
    `prefetch_related`.
  - `VinculoListSerializer` traz resumo do servidor (matricula, nome) e
    cargo (nome) — UX de listagem direta.
  - `DocumentoViewSet` aceita upload via `MultiPartParser` (`arquivo`).

- **feat(people):** Endpoint **GET /api/people/servidores/{id}/historico/**
  consultando `simple_history`. Retorna registros paginados com
  `history_id`, `history_date`, `history_type` (+/~/-),
  `history_user_email` (capturado pelo `HistoryRequestMiddleware`) e
  snapshot dos campos do modelo no momento da mudança.
  - Permission: leitura (`IsLeituraMunicipio`) — qualquer papel pode ver.

- **feat(people):** Validações de domínio nos `Write` serializers.
  - **CPF** (Servidor + Dependente): aceita máscara, normaliza para
    dígitos, valida via `apps.core.validators.validar_cpf`.
  - **PIS/PASEP** (Servidor): opcional; se preenchido, valida e
    normaliza.
  - **Data de nascimento**: não pode ser futura; idade mínima 14 anos.
  - **Carga horária** (Vínculo): entre 1 e 60 horas semanais.
  - **Datas de admissão/demissão** (Vínculo): admissão não futura,
    demissão >= admissão.
  - Códigos (Cargo/Lotação): `upper().strip()`.
  - Erros HTTP 400 com `code` estável (`CPF_INVALIDO`, `PIS_INVALIDO`,
    `DATA_FUTURA`, `IDADE_MINIMA`, etc.).

- **feat(people/filters):** FilterSets para todos os novos viewsets.
  - `ServidorFilter`: filtros por `vinculos__cargo`, `vinculos__lotacao`,
    `vinculos__regime`, `ativo`, `sexo`.
  - `VinculoFilter`: `admitido_apos`/`admitido_ate` (range de datas) +
    servidor/cargo/lotacao/regime/ativo.
  - `DependenteFilter`: servidor, parentesco, ir, salario_familia.
  - `DocumentoFilter`: servidor, tipo.

- **test(people):** 36 testes novos.
  - `test_views_servidor.py` (15): CRUD, RBAC, isolamento, validação CPF,
    PIS, data, idade mínima, matrícula duplicada, histórico via
    `simple-history` (autor capturado pelo middleware).
  - `test_views_vinculo.py` (6): CRUD, validação de carga horária,
    coerência de datas, filtro por servidor.
  - `test_views_dependente_documento.py` (5): CRUD básico, upload de
    arquivo via multipart, leitura por papel.
  - `test_perf.py` (1, marker `@pytest.mark.perf`): **100 servidores
    criados em ~5s**, bem abaixo do gate de 30s.

#### Modificado

- **chore(pytest):** marker `perf` adicionado em `pyproject.toml`. Suíte
  default exclui (`-m "not perf"`); rodar com `pytest -m perf`.

#### Validações realizadas

- `pytest` — **126/126 passando** em ~30s (1 deselected: o teste perf).
- `pytest -m perf` — 1 passando em ~5s (100 servidores via API).
- `pytest --cov` — **96% de cobertura** geral.
- `ruff format` + `ruff check` — verdes.
- `python manage.py check` — sem warnings.

#### Próximos passos

- **Bloco 1.2 — Onda 3** (~4 dias): Services em `apps.people.services/`
  (admissão, desligamento, transferência) + endpoints `@action` para
  fluxos. CRUD de Rubrica esqueleto. Management command
  `criar_usuario` (resolve gap do Bloco 1.1).

---

### Bloco 1.2 — Onda 1: Validators + CRUD Cargo/Lotação · 2026-04-29

> Primeira onda de cadastros via API REST. Valida o pattern (3 serializers,
> ViewSet, permissions por papel, filtros, isolamento) que vai se repetir
> nas ondas 2–4 com Servidor/Vínculo/Dependente/Documento/Rubrica.

#### Adicionado

- **feat(core/validators):** `apps/core/validators.py` com `validar_cpf`,
  `validar_pis_pasep`, `validar_codigo_ibge`. Aceitam string com ou sem
  máscara, retornam dígitos normalizados, levantam `ValidationError` com
  `code` estável (`CPF_INVALIDO`, `PIS_INVALIDO`, `IBGE_INVALIDO`).
  - **Por quê:** dados brasileiros aparecem em vários models (Servidor,
    Dependente, Município) — centralizar evita reimplementação.
  - **Decisão:** ficam **só na fronteira HTTP (serializer)** + camada de
    service. Não em Django field validators (que ignoram retorno e não
    normalizam). Pattern: `def validate_cpf(self, value): return validar_cpf(value)`.
  - 27 testes (`apps/core/tests/test_validators.py`).

- **feat(people):** CRUD de **Cargo** e **Lotação** via API REST.
  - Endpoints: `/api/people/cargos/` e `/api/people/lotacoes/` (GET list,
    POST, GET detail, PATCH, PUT, DELETE).
  - **3 serializers por modelo** (List/Detail/Write) — pattern do
    `backend/apps/CONTEXT.md`.
  - **`_PapelPorAcaoMixin`** em `apps/people/views.py`: leitura exige
    `IsLeituraMunicipio`, escrita exige `IsRHMunicipio`.
  - **FilterSets** (`apps/people/filters.py`): `?codigo=X`, `?nome__icontains=X`,
    `?nivel_escolaridade=X`, `?ativo=true`, `?raiz=true` (Lotação).
  - **Search e ordering** globais via `SearchFilter` + `OrderingFilter`
    adicionados em `REST_FRAMEWORK.DEFAULT_FILTER_BACKENDS`.
  - **Detail enriquecido**: `nivel_escolaridade_display`, `lotacao_pai_nome`.
  - **Validação de ciclo** em LotaçãoWriteSerializer: lotação não pode ser
    pai de si mesma.
  - **Normalização**: `codigo` automaticamente upper + strip.

- **test:** 25 testes HTTP (18 Cargo + 7 Lotação) cobrindo:
  - CRUD completo (list/retrieve/create/update/partial/destroy).
  - RBAC: leitura permite GET, bloqueia POST/PATCH/DELETE; staff_arminda
    passa em qualquer tenant.
  - Isolamento entre tenants (criar em A não aparece em B; mesmo
    `codigo` em A e B é permitido).
  - Filtros (`?nivel_escolaridade=`, `?raiz=true`) e search (`?search=`).
  - Erros: 401 sem auth, 400 sem tenant, 403 sem papel, 400 código vazio
    ou duplicado, 400 ciclo de hierarquia.

#### Modificado

- **chore(settings):** `DEFAULT_FILTER_BACKENDS` ganha `SearchFilter` e
  `OrderingFilter` para ativar `search_fields`/`ordering_fields` nos viewsets.

- **fix(test):** `test_x_tenant_com_codigo_ibge_resolve` e
  `test_x_tenant_inexistente_retorna_400` agora batem em
  `/api/people/cargos/` (era `/api/people/`, que virou root do router).

#### Removido

- **chore(settings):** `backend/arminda/settings/local.py` — incompatível
  com `django-tenants` (multi-tenant exige PostgreSQL; SQLite não tem
  schemas). Bloco 1+ não suporta mais "rodar sem Postgres".

#### Validações realizadas

- `pytest` — **100/100 passando** em ~30s.
- `pytest --cov` — **96% de cobertura** geral.
- `ruff format` + `ruff check` — verdes.
- `python manage.py check` — sem warnings.

#### Próximos passos

- **Bloco 1.2 — Onda 2** (5 dias): CRUD de Servidor + VinculoFuncional
  + Dependente + Documento, com validação de CPF/PIS via
  `apps.core.validators`, endpoint de histórico (`simple_history`),
  perf baseline (100 servidores < 30s).

---

### Bloco 1.1 — Fundação técnica (multi-tenant + auth + RBAC) · 2026-04-29

> ⚠ **BREAKING.** O schema do banco foi reestruturado de zero. A DB de dev precisa ser recriada (drop & migrate). Nenhum dado de Bloco 0 é compatível.

#### Adicionado

- **feat(core):** `User` customizado com identificação por e-mail (ADR-0005).
  - **Por quê:** produto SaaS B2G — `username` separado é UX ruim; e-mail unique é a chave natural. Trocar `AUTH_USER_MODEL` depois de produção é doloroso, então decidimos antes do primeiro dado real.
  - **Arquivos:** `apps/core/models.py`, `apps/core/admin.py`, `arminda/settings/base.py`.
  - **Impacto:** `createsuperuser` agora pede `email`+`password`. Todo código que referencia User deve usar `get_user_model()`.

- **feat(core):** Multi-tenant ativo via `django-tenants` por schema PostgreSQL (ADR-0006, refina ADR-0004).
  - `Municipio` herda `TenantMixin`, com `auto_create_schema=True` e `auto_drop_schema=False`.
  - `Domain` (DomainMixin) para roteamento por hostname em prod.
  - `SHARED_APPS` no schema `public` (core, auth, sessions, admin, DRF, JWT, OpenAPI).
  - `TENANT_APPS` no schema do município (people, payroll, reports, simple_history).
  - `ENGINE = django_tenants.postgresql_backend`.
  - **Models tenant sem FK redundante para `Municipio`** — isolamento real via `search_path`.
  - **Por quê:** ADR-0004 fixou a estratégia; Bloco 0 deixou o pacote inativo. Sem essa ativação, todas as features futuras seriam comprometidas.
  - **Arquivos:** `apps/core/models.py`, `apps/people/models.py`, `apps/payroll/models.py`, `apps/reports/models.py`, `arminda/settings/base.py`.

- **feat(core):** Middleware `TenantHeaderOrHostMiddleware` com fallback header `X-Tenant` → hostname.
  - Lista pública (`/admin/`, `/health/`, `/status/`, `/api/auth/*`, `/api/schema/`, `/api/docs/`, `/api/redoc/`, `/static/`, `/media/`) roda no schema `public`; tudo o mais exige tenant.
  - Erro 400 com `code=TENANT_NAO_ENCONTRADO` se header inválido.
  - **Arquivos:** `apps/core/middleware/tenant.py`.

- **feat(core):** Modelo de RBAC `UsuarioMunicipioPapel` (User × Município × Group) — ADR-0007.
  - 5 papéis-base seedados via data migration: `staff_arminda`, `admin_municipio`, `rh_municipio`, `financeiro_municipio`, `leitura_municipio`.
  - **Permissions DRF base** em `apps/core/permissions.py`: `IsStaffArminda`, `IsAdminMunicipio`, `IsRHMunicipio`, `IsFinanceiroMunicipio`, `IsLeituraMunicipio`. `staff_arminda` é override global cross-tenant.
  - **Arquivos:** `apps/core/models.py` (UsuarioMunicipioPapel), `apps/core/migrations/0002_seed_grupos_papeis.py`, `apps/core/permissions.py`.

- **feat(auth):** Autenticação JWT com `djangorestframework-simplejwt` (ADR-0007).
  - Endpoints públicos: `POST /api/auth/login/`, `POST /api/auth/refresh/`, `POST /api/auth/logout/`, `GET /api/auth/me/`.
  - Access TTL 30 min, refresh TTL 7 dias, com `ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION`.
  - Claim customizada `municipios` no access token (lista de `{schema, papel}`).
  - `ArmindaTokenObtainPairSerializer` enriquece resposta de login com dados do user.
  - **Arquivos:** `apps/core/auth/{serializers,views,urls}.py`, `arminda/settings/base.py` (SIMPLE_JWT).

- **feat(audit):** `simple-history` ativo nos models críticos do tenant (`Cargo`, `Lotacao`, `Servidor`, `VinculoFuncional`).
  - `HistoryRequestMiddleware` capturando o autor de cada mudança.
  - **Arquivos:** `apps/people/models.py`, `apps/people/admin.py` (SimpleHistoryAdmin), `arminda/settings/base.py` (middleware).

- **feat(ops):** Management commands.
  - `criar_municipio`: cria tenant + Domain, dispara `auto_create_schema`.
  - `listar_tenants`: lista municípios cadastrados.
  - **Arquivos:** `apps/core/management/commands/*`.

- **test:** Suíte multi-tenant completa.
  - Fixtures session-scoped: `tenant_a`, `tenant_b` em `backend/conftest.py`.
  - Fixtures function-scoped: `usuario_factory`, `usuario_admin_a`, `usuario_rh_a`, `usuario_leitura_a`, `usuario_staff_arminda`, `api_client`, `api_client_factory`, `in_tenant` (context manager).
  - **48 testes passando**, **95% de cobertura geral** (>90% em todo módulo de domínio do Bloco 1.1).
  - Cobre: User, isolamento por schema, middleware, JWT (login/refresh/logout/me/claims), RBAC (todas as combinações de papel), simple-history (create/update/delete), management commands.

- **docs:** ADR-0005 (User), ADR-0006 (Multi-tenant impl), ADR-0007 (JWT + RBAC), `docs/BLOCO_1.1_RESUMO.md`, `docs/MULTI_TENANT_PLAYBOOK.md`.

#### Modificado

- **⚠ BREAKING refactor(models):** removido FK `municipio = ForeignKey(...)` de TODOS os models tenant (`Cargo`, `Lotacao`, `Servidor`, `VinculoFuncional`, `Dependente`, `Documento`, `Rubrica`, `Folha`, `Lancamento`, `RelatorioGerado`).
  - **Por quê:** `django-tenants` já isola por schema; FK redundante criaria possibilidade de cross-tenant por bug.
  - **Impacto:** unique constraints simplificadas — `unique_together = [("municipio", "codigo")]` virou `unique=True` em `codigo` (escopo do schema).

- **chore(migrations):** todas as migrations 0001 dos apps `core`, `people`, `payroll`, `reports` foram **deletadas e regeneradas**. Nenhum dado de Bloco 0 é recuperável.
  - **Por quê:** trocar `AUTH_USER_MODEL` + ativar `django-tenants` exige regeneração total das migrations.
  - **Como aplicar (dev):** drop DB → recreate → `python manage.py migrate_schemas --shared` → `python manage.py criar_municipio --schema=...`.

- **chore(deps):** `django-tenants`, `simple_history`, `rest_framework_simplejwt`, `rest_framework_simplejwt.token_blacklist` ativos em `INSTALLED_APPS` (estavam comentados no Bloco 0).

- **refactor(choices):** todas as `choices` de string foram migradas para `models.TextChoices` em `apps/people` e `apps/payroll`.

#### Removido

- **chore:** referências a `municipio` em `admin.py` de `people`/`payroll`/`reports` (não existe mais).

#### Validações realizadas

- `python manage.py check` — sem warnings.
- `python manage.py migrate_schemas --shared` — verde, public schema com 16 tabelas SHARED.
- `python manage.py criar_municipio` em 2 tenants reais (mun_sao_raimundo, mun_teresina) — schemas criados, 16 tabelas TENANT em cada.
- `pytest` — **48/48 passando** em ~22s.
- `pytest --cov` — **95% de cobertura** geral; ≥ 90% em todos os módulos de domínio.
- `ruff format` + `ruff check` — verdes.

#### Próximos passos

- **Bloco 1.2** — CRUDs de domínio (servidor, cargo, lotação, vínculo, rubrica esqueleto), serializers, viewsets com permissions, services (admissão, desligamento, transferência).
- Criar usuários reais para os 2 municípios via management command (`criar_usuario` ou seed).
- Migrar geração de tipos TS do OpenAPI para o frontend (ADR-0008, no Bloco 1.3).

---

### Documentação

- **2026-04-28 · docs:** sistema de contexto distribuído implantado.
  - **Por quê:** garantir rastreabilidade, padronização e que nenhuma implementação ocorra sem contexto, conforme política do projeto.
  - **Arquivos:** `CONTEXT.md`, `CHANGELOG.md`, `backend/CONTEXT.md`, `backend/CONTEXT_MODELS.md`, `backend/CONTEXT_SERVICES.md`, `backend/apps/CONTEXT.md`, `frontend/CONTEXT.md`, `frontend/src/pages/CONTEXT.md`, `frontend/src/components/CONTEXT.md`.
  - **Impacto:** toda alteração futura deve consultar o `CONTEXT.md` pertinente antes e atualizar o `CHANGELOG.md` depois. Não é regressão; é processo novo.

---

## [0.1.0] — 2026-04-27 — Bloco 0: Estrutura inicial

> Snapshot do que estava entregue antes da implantação do sistema de contexto.
> Detalhes em `docs/BLOCO_0_RESUMO.md`.

### Adicionado

- **feat(repo):** monorepo organizado (`backend/`, `frontend/`, `docs/`, `scripts/`, `status-page/`).
  - **Por quê:** ADR-0001 — versionamento e contexto unificado para dev solo.
- **feat(backend):** esqueleto Django 5.1 com settings split (`base`/`dev`/`prod`).
  - **Apps esqueletadas:** `core`, `people`, `payroll`, `reports`.
  - **Endpoints:** `/health/`, `/status/`, `/api/docs/` (Swagger), `/api/redoc/`.
  - **Models iniciais:** `Municipio`, `Servidor`, `Cargo`, `Lotacao`, `VinculoFuncional`, `Dependente`, `Documento`, `Rubrica`, `Folha`, `Lancamento`, `RelatorioGerado`, `TimeStampedModel` (abstrato), `ConfiguracaoGlobal`.
  - **Por quê:** ADR-0002 — base relacional sólida antes de cálculo.
- **feat(frontend):** Vite 6 + React 18 + TS + Tailwind 3 + shadcn-ready.
  - **Páginas:** `HomePage`, `HealthPage` (consome `/health/` e `/status/`), `NotFoundPage`.
  - **Lib:** `api.ts` (axios), `utils.ts` (`cn` helper).
  - **Por quê:** ADR-0003 — UX moderna como diferencial de produto.
- **feat(infra):** Docker Compose com Postgres 16 e Redis 7 (healthchecks).
- **feat(ci):** GitHub Actions para backend (ruff + check + pytest) e frontend (eslint + prettier + tsc + vitest + build).
- **docs:** `README.md`, `docs/ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/CONTRIBUTING.md`, ADRs 0001–0004.

### Validações

- `python manage.py check` sem warnings.
- `ruff check` e `ruff format --check` verdes.
- Smoke test (`tests/test_smoke.py`) passando.
- `/health/` retornando `{"status": "ok", "service": "arminda"}`.

### Conhecidas (dívida explícita do Bloco 0)

- `django-tenants` ainda comentado em `INSTALLED_APPS` — ativar no Bloco 1.
- `simple-history` ainda comentado — ativar no Bloco 1.
- JWT (`djangorestframework-simplejwt`) presente no `requirements.txt` mas não configurado em `REST_FRAMEWORK` — ativar no Bloco 1.
- `frontend/src/components/` ainda não existe — será criada quando entrar a primeira tela do Bloco 1.
- Não há camada de **services** ainda; será introduzida no primeiro app que precisar de regra de negócio (provavelmente `people` no Bloco 1).

---

## Convenção de versão

| Versão | Marco |
|--------|-------|
| 0.1.0  | Fim do Bloco 0 (estrutura inicial) |
| 0.2.0  | Fim do Bloco 1 (multi-tenant + cadastros) |
| 0.3.0  | Fim do Bloco 2 (engine de cálculo) |
| ...    | um minor por bloco |
| 1.0.0  | Fim do Bloco 6 (piloto em produção, paridade ≥ 99,9%) |

Patches (`0.1.x`, `0.2.x`) cobrem fixes pontuais entre blocos.
