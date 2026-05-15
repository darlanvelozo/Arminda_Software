# MANAD — Manual Normativo de Arquivos Digitais

> **Fonte legal:** IN SRP nº 86/2003 (Ministério da Previdência Social) e
> atualizações posteriores (IN RFB 1.252/2012 e seguintes).
>
> **Status atual:** ainda exigido em fiscalizações pontuais da Receita
> Federal e do INSS, embora o uso rotineiro tenha sido em grande parte
> substituído por eSocial + EFD-Reinf + DCTFWeb. Continua sendo
> obrigatório que sistemas de folha de pagamento brasileiros **saibam
> gerar** o arquivo, porque a Receita pode solicitar a qualquer momento.

---

## Quem é obrigado a gerar

Toda pessoa jurídica com folha de pagamento que seja **alvo de
fiscalização**. No setor público:

- **Por CNPJ** (não pelo município inteiro): cada órgão emissor
  (Prefeitura matriz, Fundo Municipal de Saúde, Fundo Municipal de
  Assistência Social, Câmara, etc.) gera seu **próprio MANAD** com seu
  CNPJ.
- **Por competência**: 1 arquivo por mês. Quando a fiscalização pede
  "ano de 2020", o sistema entrega 12 arquivos (jan a dez).

## Formato do arquivo

- Texto **pipe-delimitado** (`|` como separador de campos).
- Charset: **Windows-1252** (Latin-1) — não UTF-8.
- Quebra de linha: CRLF.
- Cada linha é um **registro** identificado pelos 4 primeiros caracteres.

## Estrutura geral

```
0000  Cabeçalho: entidade + CNPJ + UF + período + versão
0001  Abertura do bloco 0 (info)
0050  Tabela de outras inscrições (filiais, etc.)
0100  Representante legal
0990  Fechamento do bloco 0 com contagem
─── Bloco K — Folha de Pagamento ───
K001  Abertura do bloco K
K050  Cadastro de pessoas (CPF, PIS, nome, datas, sexo, salário)
K100  Estabelecimento/lotação
K150  Rubricas/eventos (códigos e nomes)
K200  Fatos da folha (eventos por competência)
K250  Vínculos (pessoa × estabelecimento × período)
K300  Lançamentos por evento (valor por rubrica × pessoa × competência)
K990  Fechamento do bloco K
─── Bloco 9 — Controle ───
9001  Abertura
9900  Tabela de contagem por tipo de registro
9990  Fechamento do bloco 9
9999  Fim de arquivo
```

> **Observação:** o exemplo que analisamos em maio/2026 (Fundo Municipal
> de Assistência Social de Canindé de São Francisco/SE — referência de
> aprendizado, não persistida no repositório) continha apenas os blocos
> de **cadastros** (`K050`/`K100`/`K150`) e não os blocos de
> **movimentação** (`K200`/`K250`/`K300`). Isso pode ocorrer em
> fiscalizações que pedem só cadastros, ou em arquivos parciais — para
> uma auditoria completa, todos os blocos K acima são exigidos.

## Detalhamento dos registros principais

### `0000` — Cabeçalho

```
0000|<nome_entidade>|<cnpj>|<ie>|<im>|<cnaef>|<uf>|<municipio>|<bairro>|...|<dt_inicio>|<dt_fim>|<versao>|<codigo_finalidade>|<id_arq>
```

Exemplo (anonimizado):
```
0000|FUNDO MUN DE ASSISTENCIA SOCIAL DE XXX|99999999000199||||XX|||||0|01012020|31012020|003|61|11
```

| Campo | Conteúdo |
|---|---|
| Nome | Razão social da entidade |
| CNPJ | 14 dígitos sem máscara |
| UF | Unidade federativa |
| Data início / fim | DDMMAAAA (período da competência) |
| Versão | `003` = MANAD versão 3 |
| Código finalidade | `61` ou outro código da Receita |

### `K050` — Cadastro de pessoa

```
K050|<cnpj>|<dt_inicio>|<matricula>|<cpf>|<pis>|<tipo_inscricao>|<nome>|<dt_nasc>|<dt_admissao>|<dt_rescisao>|<sexo>|<tipo_vinculo>|<categoria>|<salario>|<dt_situacao>
```

| Campo | Conteúdo |
|---|---|
| CNPJ | Da entidade emissora |
| dt_inicio | DDMMAAAA do registro |
| matricula | Numérico do sistema de folha de origem |
| cpf | 11 dígitos sem máscara |
| pis | 11 dígitos PIS/PASEP |
| tipo_inscricao | `4` = CPF (usual) |
| nome | Nome completo (até 60 chars usual) |
| dt_nasc | DDMMAAAA |
| dt_admissao | DDMMAAAA |
| dt_rescisao | DDMMAAAA ou vazio se ativo |
| sexo | `1` = masc, `2` = fem (varia por versão) |
| tipo_vinculo | Código numérico |
| categoria | Código (efetivo, comissionado, etc.) |
| salario | Numérico com 2 decimais (`123456` = 1234,56) |
| dt_situacao | DDMMAAAA da última situação |

### `K100` — Lotação/Estabelecimento

```
K100|<dt_inicio>|<seq>|<cnpj>|<descricao>|<info_adicional>
```

Exemplo:
```
K100|02012016|1|99999999000199|00214 - S.M.DE INC.TRAB.E DES.SOCIAL|
```

Mapeia para o **órgão emissor** + **lotação física** no Arminda.

### `K150` — Rubrica/Evento

```
K150|<cnpj>|<dt_inicio>|<codigo>|<nome_rubrica>
```

Exemplos:
```
K150|99999999000199|02012016|160|INSS S/ 13: SALARIO
K150|99999999000199|02012016|8|FERIAS
K150|99999999000199|02012016|1038|CONSIGNADO BB
```

| Campo | Conteúdo |
|---|---|
| Código | Numérico do sistema de origem |
| Nome | Descrição livre (até 60 chars) |

> **Nota técnica:** códigos de rubrica **não são padronizados** entre
> sistemas de folha. Cada sistema/município tem seu próprio mapeamento.
> Por isso o Arminda armazena o nome E o código original do legado em
> `Rubrica.codigo` (texto livre) e usa a `Rubrica.formula` (DSL) para a
> lógica de cálculo.

### `9999` — Fim de arquivo

```
9999|<total_linhas>
```

## Implementação no Arminda

### Bloco 4 (Out-Nov/2026)

**Gerador MANAD** (`apps.reports.adapters.manad`):
- `gerar_manad(orgao_emissor, competencia)` → produz arquivo TXT
- Cobertura de blocos: `0000`/`0001`/`0050`/`0100`/`0990` (cabeçalho) +
  bloco `K` completo (`K001`–`K990`) + bloco `9` (`9001`–`9999`).
- Encoding: **WIN1252** (não UTF-8); CRLF.
- Validador de estrutura antes do envio.

**Pré-requisitos:**
- Modelo `OrgaoEmissor` (apps.people) — cada CNPJ que emite folha.
- Engine de cálculo do Bloco 2 já ter rodado uma competência completa
  (sem isso, não há `K200`/`K250`/`K300` para gerar).

### Configuração

Cada município ativa o MANAD no admin via `IntegracaoExterna(tipo="manad")`
conforme ADR-0011. Como o MANAD é **gerado** mas não **enviado**
automaticamente (a Receita pede sob demanda), a configuração só precisa
guardar o caminho de exportação preferido.

## Material de referência

- IN SRP 86/2003 — [Diário Oficial da União, 2003](#)
- IN RFB 1.252/2012 — atualização do leiaute
- [Leiaute oficial MANAD v3](https://www.gov.br/receitafederal/) — buscar
  na seção de fiscalização

> **Os arquivos `.txt` originais** que serviram de aprendizado (Fundo
> Municipal de Assistência Social de Canindé de São Francisco/SE, 2020,
> 159 servidores reais) **NÃO** foram commitados — contêm CPF, PIS e
> nomes pessoais. O entendimento do leiaute foi documentado neste README
> sem incluir nenhum dado individual.
