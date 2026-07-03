<!--
  REFERÊNCIA INTERNA (Arminda). Engenharia reversa de bases reais do Fiorilli
  SIP_7 (Firebird). Contém apenas dados AGREGADOS — sem PII individual.
  A base bruta (.7z/.FDB, com PII real) NÃO fica no repositório: vive fora de
  qualquer checkout git (LGPD — CLAUDE.md §7). Decisões derivadas deste
  documento estão na ADR-0021. Não editar o corpo abaixo — é o material-fonte.
-->

# Base de Conhecimento — Sistemas de Folha de Pagamento Municipal (RH/eSocial)

> Documento gerado a partir da engenharia reversa de bancos de dados reais do
> **Fiorilli SIP_7** (sistema de RH/folha usado por centenas de prefeituras
> brasileiras), rodando em **Firebird**. O objetivo é servir de contexto/base
> de conhecimento para o desenvolvimento de um sistema próprio de folha de
> pagamento — não é documentação oficial da Fiorilli, é o que foi observado
> analisando bancos reais de duas prefeituras (Brejo-MA e São João Batista-MA).

---

## 1. Visão geral do domínio

Um sistema de folha de pagamento municipal brasileiro precisa lidar com:

1. **Cadastro civil e funcional** das pessoas (servidores, dependentes).
2. **Estrutura organizacional** do ente (secretarias, departamentos, cargos).
3. **Motor de cálculo de folha** (rubricas/verbas, fórmulas, incidências
   tributárias e previdenciárias).
4. **Regimes jurídicos distintos** coexistindo no mesmo ente: estatutário
   (RPPS — regime próprio de previdência) e celetista/temporário (RGPS — INSS).
5. **Obrigações legais federais**: eSocial, FGTS Digital, IRRF, RAIS, DIRF,
   SEFIP/CAGED (legado).
6. **Obrigações legais estaduais**: cada Tribunal de Contas Estadual (TCE) tem
   seu próprio layout de prestação de contas — é uma fonte enorme de
   complexidade "extra" que não tem relação com o cálculo da folha em si.
7. **Portal do servidor** (autoatendimento) e controle de ponto/frequência.

O banco analisado tem **1.033 tabelas** — mas isso é enganoso: boa parte é
"área de exportação" específica por estado (ver seção 8). O **núcleo real**
do domínio (cadastro + folha + eSocial + estrutura organizacional) é bem mais
enxuto — talvez 100–150 tabelas — e é nisso que este documento foca.

---

## 2. Arquitetura técnica observada (para contraste, não para copiar)

- **Banco:** Firebird 2.5 (ODS 11.2), single-tenant por arquivo `.FDB` — um
  arquivo de banco por prefeitura/ente. Não há multi-tenant dentro do mesmo
  banco (a tabela `EMPRESA` até suporta múltiplos registros, mas na prática
  cada backup tem 1 único ente).
- **Charset:** WIN1252 (Latin-1 estendido) em todo o banco — decisão antiga,
  hoje seria UTF-8. Se for construir do zero, use UTF-8.
- **Chaves primárias compostas:** o padrão do sistema é `(EMPRESA, CODIGO)` ou
  `(EMPRESA, REGISTRO)` em quase toda tabela — nunca um UUID/serial global.
  Isso é herança do desenho multi-empresa dentro de um único banco (mesmo que
  na prática só exista uma empresa por arquivo). Considere se isso faz sentido
  para o seu caso ou se um UUID/serial simples resolve melhor.
- **Volume de integridade referencial:** ~1.870 *foreign keys* e ~196
  *triggers* no schema. Vários campos "derivados" são mantidos por trigger
  (ex.: um campo de classificação que é recalculado automaticamente a partir
  de outro campo) — isso tem um custo real de manutenibilidade e depuração
  (times de fora não sabem por que um campo "não aceita" um valor direto).
  **Recomendação:** prefira colunas calculadas explícitas na camada de
  aplicação/serviço a triggers de banco escondidos, ou pelo menos documente-os
  MUITO bem — isso me custou tempo real ao tentar ajustar um campo de regime
  de trabalho que "voltava sozinho" por causa de um trigger.
- **Sem soft-constraints de obrigatoriedade real:** campos importantes como
  endereço, telefone e e-mail são `NULLABLE` e, na prática, ficam vazios para
  uma fração significativa dos registros (ver seção 9). Se o objetivo é um
  sistema mais robusto, vale definir claramente o que é obrigatório *no
  cadastro* vs. obrigatório *apenas para o envio ao eSocial*.

---

## 3. Entidades centrais do cadastro

### 3.1 `PESSOA` — dados civis (chave: `CPF`)
Uma pessoa física pode ser servidor, dependente, pensionista, autônomo etc. —
o cadastro civil é **desacoplado** do vínculo funcional. Campos principais:

- Identificação: `CPF`, `NOME`, `SEXO`, `RACA`, `NACIONALIDADE`, `DTNASCIMENTO`
- Filiação: `NOMEPAI`, `NOMEMAE`, `CPF_PAI`, `CPF_MAE`
- Endereço: `CEP`, `ENDERECO`, `NUMERO`, `BAIRRO`, `COMPL`, `CIDADE`, `UF`,
  `TIPO_LOGRADOURO` (FK para tabela `TIPO_LOGRADOURO` — código IBGE/DNE de
  tipo de logradouro: Rua, Avenida, Travessa etc.)
- Contato: `TELEFONE`, `CELULAR`, `EMAIL` — **na prática, extremamente
  esparsos** (ver seção 9).
- Documentos: `RG`, `PIS`, `CTPS`+`SERIE`, `CNH_*`, `ELEITOR`+`ZONAELEITORAL`,
  `RESERVISTA`
- Dados de saúde/biométricos: `TIPOSANGUE`, `DEFICIENCIAFISICA`, `PESO`,
  `ALTURA`, `ALERGIAMEDICAMENTOS`
- Portal do servidor: `USUARIO_WEB`, `SENHAWEB` (hash), `SIPWEB_ULTIMO_ACESSO`

### 3.2 `TRABALHADOR` — vínculo funcional (chave composta: `EMPRESA, REGISTRO`)
Um `TRABALHADOR` é um **vínculo empregatício/funcional específico** — não é a
pessoa. Uma mesma `PESSOA` (mesmo CPF) pode ter **múltiplos** registros em
`TRABALHADOR` (ex.: dois cargos acumuláveis, ou um vínculo antigo encerrado e
um novo). O link `TRABALHADOR.CPF → PESSOA.CPF` é a ponte.

Campos centrais (tabela tem ~389 colunas no total — é o "hub" do sistema):
- Identificação funcional: `REGISTRO` (matrícula técnica), `MATRICULA`
  (matrícula visível ao usuário), `CONTRATO`, `ADMISSAO`, `DEMISSAO`
- Vínculo: `VINCULO` (FK → `VINCULO`), `CARGO` (FK → `CARGOS`), `DIVISAO`,
  `SUBDIVISAO` (lotação)
- Regime de trabalho (⚠️ ver nota crítica abaixo): `REGIME_JURIDICO_TRAB`
- Endereço: réplica dos mesmos campos de `PESSOA` (`ENDERECO`, `BAIRRO`,
  `CIDADE`, `UF`, `CEP`, `TIPO_LOGRADOURO`) — **um vínculo pode ter endereço
  diferente do cadastro civil** (raro na prática, mas o campo existe e é
  independente).
- Jornada: `HORASMES`, `HORASEMANAL`, campos de banco de horas
- eSocial: `STATUS_ESOCIAL`, `STATUS_ESOCIAL_REND_TRAB`, `CODIGO_ESOCIAL`

> **Nota crítica aprendida na prática:** existe um campo legado
> `CLT_OU_ESTATUTO` (`'CLT'`/`'EST'`) que é **derivado por trigger a partir do
> vínculo** e **não é** o que a tela "Regime de Trabalho" (aba eSocial) exibe
> ao usuário. O campo que a tela realmente usa é **`REGIME_JURIDICO_TRAB`**
> (inteiro, padrão do próprio leiaute do eSocial: `1 = Celetista`,
> `2 = Estatutário/legislações específicas`). Isso é um ótimo exemplo de por
> que, num sistema próprio, vale a pena ter **um único campo de regime**,
> validado e sem duplicidade — não dois campos que podem divergir.

### 3.3 `DEPENDENTES` (chave: `EMPRESA, TRABALHADOR/REGISTRO, CODIGO`)
Dependentes para IRRF, salário-família, plano de saúde, pensão. Tem seus
próprios campos de endereço (podem divergir do titular).

### 3.4 `EMPRESA` — o ente empregador
Um registro por prefeitura/autarquia/fundo (CNPJ próprio). Guarda
identificação, endereço, e uma quantidade grande de **flags de qual layout de
prestação de contas usar** (por estado — ver seção 8) e de certificado
digital para assinatura de eSocial (`ESOCIAL_CERTIFICADO`,
`CERTIFICADO_DIGITAL`).

### 3.5 Estrutura organizacional: `DIVISAO` → `SUBDIVISAO`
- `DIVISAO` = secretaria/órgão (pode ter CNPJ e endereço próprios, quando é
  uma autarquia/fundo separado).
- `SUBDIVISAO` = departamento/setor dentro da divisão (`DIVISAO_CODIGO` como FK).
- Nem todo ente usa `SUBDIVISAO` (no banco analisado de SJB, a tabela estava
  **vazia** — a organização parava em "secretaria").

### 3.6 `CARGOS` — cargo/função (chave: `EMPRESA, CODIGO`)
Muito mais que um nome de cargo: tem `CBO` (Classificação Brasileira de
Ocupações — obrigatório no eSocial), regras de vaga (`VAGACARGO`,
`VAGAFUNCAO`, `VAGADEFICIENTE`, `VAGACOTA`), jornada padrão do cargo,
carreira/progressão, base legal de criação/extinção do cargo (lei, decreto),
e `CODIGO_ESOCIAL` (classificação do cargo conforme tabela do eSocial).

### 3.7 `VINCULO` — tipo de vínculo/regime (chave: `EMPRESA, CODIGO`)
Não confundir com "o vínculo de um trabalhador" — esta é a tabela **de
configuração** que define o comportamento de cada *tipo* de vínculo (ex.:
Efetivo, Comissionado, Contratado, Eletivo, Aposentado). É praticamente um
motor de regras à parte: define se incide INSS/FGTS/décimo terceiro, alíquotas
patronais (`TXEMPRESA`, `TXACIDENTES`, FAP), regras de licença-prêmio, regras
de férias, se está vinculado a RPPS (`ENVIAR_SIPRPPS`, `VINCULORPPS`),
`CODIGO_ESOCIAL` do vínculo. No banco analisado havia só **8 vínculos**
configurados (Efetivo, Contratados, Comissionado, Eletivo, Aposentados...) —
ou seja, é uma tabela pequena, mas de alto impacto em regras.

---

## 4. Motor de cálculo de folha

Esta é a parte mais valiosa para replicar corretamente. O fluxo observado:

```
EVENTOS (config da rubrica)
   │
   ├─► EVENTOSFIXOS   (lançamento recorrente por trabalhador — ex.: gratificação fixa, empréstimo)
   ├─► EVENTUAIS      (lançamento pontual/variável por trabalhador — ex.: hora extra do mês)
   │
   ▼ (processamento/cálculo do período)
MOVIMENTO   (linha calculada: trabalhador × evento × período, com valor final)
   │
   ▼ (agregação)
BASES       (totalizador por trabalhador × período: bases e valores de INSS/FGTS/IRRF/RAIS/DIRF, líquido etc.)
   │
   ▼ (contexto do período)
REFERENCIA  (o "mês de folha": ano/mês/tipo, datas de pagamento/fechamento, salário mínimo vigente, status de fechamento no eSocial)
```

### 4.1 `EVENTOS` — cadastro mestre de rubricas (o "plano de contas da folha")
Cada linha é uma rubrica (verba/desconto): salário-base, hora extra, INSS,
IRRF, vale-transporte, pensão alimentícia, etc. Estrutura riquíssima:
- Classificação: `TIPO`, `NATUREZA`, `VANTAGEM` (provento) vs desconto
- **Motor de fórmula:** `FORMULA`, `BASE`, `TIPOVALOR`, `PERCENTUAL`,
  `TIPO_FORMULA`, `FORMULA_TABELA` — o cálculo de cada rubrica pode ser fixo,
  percentual sobre outra base, ou uma fórmula livre.
- Incidências (booleanas): `INSS`, `FGTS`, `IRRF`, `RAIS`, `DIRF`, `SIPREV`
  (previdência própria), `FERIAS`, `SALARIO13`, `SALARIOFAMILIA` — cada uma
  controla se aquela rubrica entra na base de cálculo daquele encargo/benefício.
- **Classificação eSocial:** `CLASSIFICACAO_ESOCIAL`, `STATUS_ESOCIAL` — o
  "de-para" entre a rubrica interna e a natureza de rubrica oficial do eSocial
  (tabela 3 do leiaute — ver seção 5).
- Códigos por Tribunal de Contas estadual (`CODIGO_TCE`, `ID_TCEGO`, etc.).

No banco de SJB havia **137 eventos** cadastrados — um número administrável.

### 4.2 `EVENTOSFIXOS` — lançamentos recorrentes
Um trabalhador tem um evento "ligado" com valor/percentual/quantidade fixos,
válido entre `DATA_BASE` e `DATA_LIMITE` (ex.: uma gratificação de função
enquanto durar a designação, parcelas de empréstimo consignado).

### 4.3 `EVENTUAIS` — lançamentos pontuais
Um lançamento manual para um mês específico (`DTLANCTO`): horas extras do
mês, um desconto avulso, um adiantamento. Tem rastro de origem/controle
(`TIPOLEGAL`, `NUMDOC`, `DATADOC` — referência ao ato administrativo que
autoriza aquele lançamento — um detalhe importante para auditoria pública).

### 4.4 `MOVIMENTO` — o "holerite calculado", linha a linha
390 mil linhas no banco de SJB (14 anos de histórico). Cada linha é **um
evento, para um trabalhador, em um período**, já com o valor calculado
(`QTDE`, `VALOR`) e — ponto de design importante — uma **cópia (snapshot) das
flags de incidência da rubrica no momento do cálculo** (`INSS`, `FGTS`,
`IRRF` etc. replicadas de `EVENTOS`). Isso é proposital: **se a configuração
da rubrica mudar no futuro, o holerite histórico não muda retroativamente.**
Esse é um requisito de auditoria/legal (folha paga não pode "mudar sozinha"
quando alguém ajusta uma configuração meses depois) — **recomendo fortemente
replicar esse padrão** de "snapshot no momento do cálculo" em qualquer motor
de folha que for construído.

### 4.5 `BASES` — o resumo mensal por trabalhador (o "totalizador do holerite")
Uma linha por `(EMPRESA, REGISTRO, REFERENCIA)`. Consolida tudo que o
`MOVIMENTO` calculou naquele mês em bases e valores prontos para as
obrigações: `BASEPREVIDENCIAMES`/`VALORPREVIDENCIAMES`,
`BASEFGTSMES`/`VALORFGTSMES`, `BASEIRRFMES`/`VALORIRRFMES`, `BASERAIS`,
`BASEDIRFMES`, além de `TOTALPROVENTOS`, `TOTALDESCONTOS`, `LIQUIDO`, dados
bancários de pagamento (`BANCO`, `AGENCIA`, `CONTA`), e **flags de exclusão
por evento do eSocial** (`ESOCIAL_EXCLUSAO_S1200`, `_S1202`, `_S1207`,
`_S1210` — controla se aquele trabalhador/período deve ou não ser incluído em
cada evento periódico do eSocial, útil para retificações e casos especiais).
82 mil linhas no banco de SJB (~1.700 trabalhadores × ~50 meses médios de
histórico).

### 4.6 `REFERENCIA` — o período de folha ("competência")
Cada linha é **um fechamento de folha**: `ANO`, `MES`, `TIPO` (mensal,
complementar/13º, rescisão — o sistema usa múltiplos tipos no mesmo mês),
`DTPAGTO`, `DTFECHA`, `PRIMEIRO_DIA`/`ULTIMO_DIA` do período, salário mínimo
nacional e municipal **vigente naquele mês** (histórico, não um valor global —
importante porque o salário mínimo muda todo ano), `ENCERRADO` (flag de
fechamento — uma vez fechado, a folha não deveria mais ser recalculada sem um
processo de reabertura controlado), e **campos de status de envio ao
eSocial** (`STATUS_ESOCIAL_ENCERRAMENTO`, `STATUS_ESOCIAL_REABERTURA`,
`STATUS_ESOCIAL_DESONERACAO`).

No banco de SJB o histórico de `REFERENCIA` ia de **março/2012 a maio/2026**
— ou seja, o sistema mantém o histórico completo de competências, nunca
substitui/apaga um período antigo.

---

## 5. eSocial — o que realmente precisa ser implementado

O eSocial é o sistema unificado do governo federal para envio de eventos
trabalhistas, previdenciários e fiscais. Não é uma tabela — é um **protocolo de
eventos em lote**, e o schema reflete isso com um conjunto de tabelas de
controle:

| Tabela | Papel |
|---|---|
| `ESOCIAL_EVENTOS_LOTE` | Controle de lote enviado: `CODIGO_LOTE`, `ID_EVENTO`, `PK_EVENTO` (chave do evento gerado, ex. de um S-2200), `RECIBO_EVENTO` (protocolo devolvido pelo governo), `RECIBO_EXCLUSAO` |
| `ESOCIAL_OUTBOX` | Fila de envio (padrão outbox — desacopla geração do evento do envio efetivo) |
| `ESOCIAL_LOTES_ENVIADOS` | Histórico de lotes já transmitidos |
| `ESOCIAL_STATUS` | Domínio de status possíveis de um evento (pendente, enviado, aceito, rejeitado etc.) |
| `ESOCIAL_ARQUIVOS` | XML/arquivos gerados por evento (auditoria/reenvio) |
| `ESOCIAL_CERTIFICADO` | Certificado digital (A1/A3) usado para assinar/autenticar o envio |
| `ESOCIAL_QUALIFICADASTRAL` | Retorno da consulta de **qualificação cadastral** (CPF/PIS/Nome/DataNascimento conforme a base da Receita) — é o mecanismo oficial e **gratuito** de conferência de CPF+nome+data de nascimento antes de admitir/manter um vínculo. Ver observação prática abaixo. |
| `ESOCIAL_RUBRICA` / `ESOCIAL_CLASS_RUBRICA` | De-para entre a rubrica interna (`EVENTOS`) e a **Tabela 3 do eSocial** (natureza de rubrica oficial) — cada rubrica de folha precisa de um código oficial de natureza para ser aceita nos eventos periódicos (S-1200/S-1202/S-1210). |
| `ESOCIAL_FIELDS`, `ESOCIAL_VERSAO`, `ESOCIAL_DATA_MONITOR`, `ESOCIAL_LOG_INSTALL` | Metadados de versão do leiaute (o eSocial muda de versão periodicamente — o sistema precisa saber qual versão de schema está usando) |

### 5.1 Eventos do eSocial identificados no schema (via flags em `BASES`)
- **S-1200** — Remuneração do Trabalhador (regime geral/CLT/RGPS)
- **S-1202** — Remuneração de Servidor Vinculado a Regime Próprio de
  Previdência Social (RPPS) — **este é o evento específico do setor público**
  para servidores estatutários; a maioria dos sistemas privados nunca precisa
  implementá-lo.
- **S-1207** — Benefícios Previdenciários - RPPS (aposentadorias/pensões
  concedidas pelo próprio regime do ente, quando há instituto de previdência
  municipal)
- **S-1210** — Pagamentos de Rendimentos do Trabalho (o evento que efetivamente
  informa os valores pagos, DARF de IRRF retido, etc.)

Além desses (não vistos diretamente nas flags, mas implícitos pela estrutura
de cadastro): **S-2200/S-2206** (admissão/alteração contratual), **S-2299**
(desligamento), **S-1200/S-1202 + S-5001/S-5002/S-5003** (fechamento e
totalizadores), **S-1298/S-1299** (fechamento de eventos periódicos).

### 5.2 Qualificação cadastral e datas de nascimento (observação prática)
Na análise de um ente real, encontramos **221 servidores com data de
nascimento divergente** da base da Receita Federal, apontados justamente pela
rotina de qualificação cadastral do eSocial. **Aprendizados relevantes para o
seu sistema:**
- A **maioria (>60%) das divergências eram datas "placeholder"**
  (`01/01/AAAA`, dia=mês como `05/05`, `10/10`) — sinal de que o cadastro foi
  digitado sem a data real disponível. **Recomendação de design:** não
  permitir gravar uma data de nascimento sem confirmação, ou pelo menos
  marcar visualmente registros com padrões suspeitos (dia=mês, 01/01) para
  revisão futura.
- **Uma consulta pública de CPF por si só não resolve** — por LGPD, a maioria
  dos provedores comerciais só devolve o **ano** de nascimento a partir do
  CPF puro; a data completa exige convênio oficial (Serpro) ou o dado vem do
  próprio documento do servidor. Um sistema de RH deveria, no ato do
  cadastro, **exigir e guardar rastreabilidade do documento de origem** (RG,
  certidão) — não só o valor final.
- **Sem contato cadastrado, não há como notificar o servidor.** Nos dois
  bancos analisados, celular/telefone/e-mail estavam preenchidos em uma
  fração muito pequena dos cadastros (às vezes 0%). Se o objetivo do seu
  sistema inclui autoatendimento/notificações, **capturar e validar contato
  no onboarding é crítico** — hoje o Fiorilli tem os campos, mas nada força o
  preenchimento nem o mantém atualizado.

---

## 6. Segurança e usuários

- `USUARIOS` — login do sistema (não confundir com `PESSOA`/`TRABALHADOR`).
  Tem `SENHA_HASH`, expiração de senha (`SENHA_EXPIRA`, `SENHA_EXPIRA_DIAS`),
  bloqueio temporário, tema de interface, `ULTIMO_ACESSO`, e pode
  opcionalmente estar vinculado a um `TRABALHADOR` (`EMPRESA`+`REGISTRO`) —
  ou seja, um servidor pode logar no sistema com seu próprio vínculo, ou pode
  existir um usuário "técnico" sem vínculo funcional.
- `PERFIL_USUARIOS` — perfis de acesso (nome apenas na tabela raiz; as
  permissões finas ficam em tabelas relacionadas de permissão por
  evento/tela, ex. `PERMISSOES_PERFIL_EVENTOS`).
- Login separado para o **portal de documentos** (`ID_USER_FLOWDOCS`,
  `LOGIN_FLOWDOCS`) — sinal de integração com um segundo sistema
  (gestão de documentos/protocolo) fora do núcleo de folha.

---

## 7. Ponto e frequência

Módulo separado, mas fortemente acoplado à folha (falta gera desconto, hora
extra gera provento): `PONTO`, `PONTO_MES`, `PONTO_AFD_*` (importação do
Arquivo Fonte de Dados do REP — relógio de ponto eletrônico, padrão da
Portaria 1.510/671), `FALTAS` (com `EVENTO` associado — cada falta já nasce
ligada à rubrica que vai gerar o desconto/abono), férias (`FERIAS`,
`MOVTOFERIAS`) e licença-prêmio (regra municipal comum, não é CLT nacional —
`MOVTOLICENCAPREMIO`, com controle de dias por ano/carência).

---

## 8. Tabelas específicas por estado (Tribunal de Contas) — por que existem tantas

Cerca de **198 tabelas** seguem o padrão `SIP<UF>_...` (ex.: `SIPGO_*` para
Goiás, `SIPRN_*` para Rio Grande do Norte, `SIPMT_*`, `SIPRJ_*`, `SIPPR_*`,
`SIPBA_*` etc.). Cada Tribunal de Contas estadual exige um **layout próprio**
de prestação de contas de pessoal (estrutura de arquivo, nomenclatura de
campos, periodicidade) — não existe um padrão nacional único (o eSocial
tentou unificar a parte trabalhista/previdenciária, mas o TCE é sobre
controle orçamentário/fiscal e continua fragmentado por estado).

**Implicação prática para quem constrói um sistema do zero:** só é preciso
implementar o layout do(s) estado(s) onde seu cliente está. Não tente
generalizar para todos os 27 — é trabalho jogado fora; construa a
exportação de forma plugável (uma "camada de exportação" por estado) e
implemente sob demanda.

---

## 9. Qualidade de dados observada na prática (o que não confiar de "graça")

Dados de dois bancos reais de produção — úteis para calibrar expectativas de
"o quão sujo" um cadastro migrado costuma estar:

| Campo | Observado |
|---|---|
| Endereço completo (logradouro+número+bairro) | ~30–70% preenchido, variando muito por ente |
| CEP/Cidade/UF | Geralmente melhor preenchido que o logradouro específico |
| Telefone/celular/e-mail | Frequentemente **0%** preenchido para grupos inteiros de servidores |
| Tipo de logradouro (campo separado de "Rua/Av") | Comumente vazio mesmo quando o endereço existe |
| Data de nascimento | Existe quase sempre, mas pode estar **errada** (padrões "placeholder") sem nenhuma flag de "não confirmado" |
| Nomenclatura de bairro/cidade | Inconsistente (`CENTRO` vs `centro`, `Brejo` vs `BREJO`) — sem normalização |

**Recomendações de design para evitar isso no seu sistema:**
1. Separar claramente **obrigatório para operar** (nome, CPF, data de
   nascimento, cargo, lotação) de **obrigatório para eSocial/legal** (pode
   ser exigido só no momento de gerar o evento, com validação bloqueante ali).
2. Ter um **campo de confiança/proveniência** para dado sensível (ex.: "data
   de nascimento confirmada por documento" vs "herdada de importação") —
   evita repetir o problema de datas placeholder.
3. Normalizar texto livre de endereço/bairro (maiúsculas, trim) na gravação,
   não só na leitura.
4. Nunca deixar um sistema aceitar 100% dos campos como `NULL` só porque "o
   sistema legado também deixava" — isso se acumula por anos.

---

## 10. Sugestão de modelo de dados enxuto (para um sistema novo)

Baseado no que é essencial vs. acidental no schema estudado:

```
Pessoa (1) ───< Vinculo (N)                    -- CPF é a chave de pessoa; um
   │                                              CPF pode ter vários vínculos
   │                                              (cargos acumuláveis, etc.)
   ├───< Dependente (N)
   └───< Documento (N)                          -- RG, CTPS, PIS, título etc.
                                                    (normalizar em vez de colunas soltas)

Vinculo (Trabalhador)
   ├── Cargo (FK)
   ├── Lotacao (FK)  -- secretaria/departamento
   ├── TipoVinculo (FK)  -- motor de regras: regime, incidências, RPPS/RGPS
   └── RegimeTrabalho (enum único: CELETISTA | ESTATUTARIO)  -- não duplicar

RubricaFolha (Evento)
   ├── formula/incidências (INSS/FGTS/IRRF/RPPS/FGTS...)
   └── mapeamento_eSocial (natureza de rubrica oficial)

LancamentoFixo (por Vinculo × Rubrica, com vigência)
LancamentoEventual (por Vinculo × Rubrica × Competência)

Competencia (Referencia)
   ├── ano, mes, tipo (mensal/13º/rescisão)
   ├── salario_minimo_vigente
   └── status (aberta | fechada | enviada_esocial)

ItemFolhaCalculado (Movimento)
   -- Vinculo × Rubrica × Competência × valor, com SNAPSHOT das incidências
   -- no momento do cálculo (não referenciar a config "viva" da rubrica)

ResumoFolha (Bases)
   -- 1 linha por Vinculo × Competência: totais e bases por obrigação

EventoESocial
   ├── tipo (S-1200, S-1202, S-2200, ...)
   ├── competencia / vinculo (quando aplicável)
   ├── payload (XML/JSON gerado)
   ├── status (pendente | enviado | aceito | rejeitado | retificado)
   └── recibo_protocolo
```

Pontos de decisão de arquitetura a considerar (não copiados do legado, são
recomendações):
- **UUID/serial em vez de chave composta (empresa+código)** — mais simples de
  referenciar entre serviços, mais fácil de fazer sharding/particionamento se
  necessário.
- **Snapshot de incidências no cálculo é inegociável** — é o único jeito de
  garantir que a folha de um mês fechado nunca mude sozinha.
- **Separe geração do evento eSocial do envio** (padrão outbox, como o
  próprio Fiorilli faz) — evita acoplar o cálculo de folha à disponibilidade
  do webservice do governo.
- **Modele "competência" como entidade de primeira classe com estado**
  (aberta/fechada/enviada) — muita regra de negócio depende de "o período já
  fechou?" antes de permitir alterar um lançamento retroativo.
- **CBO, tipo de logradouro, natureza de rubrica eSocial** são todas tabelas
  de domínio **oficiais do governo** (atualizadas periodicamente) — trate como
  dados de referência versionados, não como enum fixo no código.

---

## 11. Escala de referência (para dimensionar banco/infra)

Números reais de um ente de porte médio (São João Batista-MA, ~2.900 vínculos
ativos/históricos):

| Tabela | Linhas |
|---|---:|
| PESSOA | 1.709 |
| TRABALHADOR (vínculos) | 2.896 |
| DEPENDENTES | 361 |
| MOVIMENTO (linhas de holerite, 14 anos) | 390.314 |
| BASES (resumo mensal por vínculo) | 82.701 |
| REFERENCIA (competências fechadas) | 158 |
| EVENTOS (rubricas cadastradas) | 137 |
| CARGOS | 194 |
| ESOCIAL_QUALIFICADASTRAL (histórico de consultas) | 1.115 |

Para um ente maior (dezenas de milhares de habitantes), espere esses números
multiplicarem proporcionalmente — o registro `MOVIMENTO` é o que mais cresce
(uma linha por rubrica por vínculo por mês).

---

## 12. Glossário rápido

| Termo | Significado |
|---|---|
| **RGPS** | Regime Geral de Previdência Social — INSS, trabalhadores celetistas/temporários |
| **RPPS** | Regime Próprio de Previdência Social — servidores estatutários, gerido pelo próprio ente (ou instituto próprio) |
| **CBO** | Classificação Brasileira de Ocupações — código oficial de profissão, obrigatório no eSocial |
| **FAP** | Fator Acidentário de Prevenção — multiplicador da alíquota de acidente de trabalho, definido anualmente pelo governo por CNAE |
| **SEFIP/CAGED/RAIS/DIRF/MANAD** | Obrigações legadas pré-eSocial — hoje majoritariamente substituídas, mas ainda mantidas por retrocompatibilidade/histórico |
| **TCE** | Tribunal de Contas Estadual — fiscaliza contas públicas; cada estado tem seu próprio leiaute de prestação de contas de pessoal |
| **Qualificação cadastral** | Rotina do eSocial que confere CPF+Nome+Data de Nascimento contra a base da Receita Federal antes de aceitar eventos daquele trabalhador |
| **Competência** | O "mês de referência" de uma folha (equivalente a `REFERENCIA` no schema estudado) |
| **Rubrica/Verba** | Um item de cálculo da folha (provento ou desconto) — salário, hora extra, INSS, vale-transporte etc. |

---

*Documento produzido a partir de engenharia reversa de backups reais (Firebird
2.5, formato de backup 9) de dois entes municipais do Maranhão, com apoio de
consultas SQL diretas ao schema (`RDB$RELATIONS`, `RDB$RELATION_FIELDS`,
`RDB$RELATION_CONSTRAINTS`) e inspeção de dados. Não reflete documentação
oficial da Fiorilli nem do eSocial — para os leiautes oficiais do eSocial,
consulte sempre o Manual de Orientação do eSocial (MOS) vigente no
portal-de-documentos do eSocial (gov.br).*
