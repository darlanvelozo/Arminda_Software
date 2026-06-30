# ADR-0020 — eSocial: arquitetura de eventos (geração XML + validação XSD)

**Status:** Aceita · 2026-06-15 · Vigora para Bloco 4 (Onda 4.1)

## Contexto

Bloco 4 — obrigações legais federais. O eSocial é a espinha dorsal: eventos
XML enviados ao ambiente do governo. O fluxo completo tem três camadas:

1. **Gerar** o XML do evento (a partir dos dados do tenant).
2. **Assinar** digitalmente (XML-DSig, certificado ICP-Brasil A1/A3).
3. **Transmitir** ao web service do eSocial (ambiente restrito/produção),
   em lotes, com reconciliação de retornos.

As camadas 2 e 3 dependem de **certificado digital** e **credenciais de
acesso** que não temos em desenvolvimento. A Onda 4.1 entrega só a camada 1
(geração + validação contra XSD oficial) — desbloqueada e 100% testável
offline. Assinatura e transmissão entram em ondas seguintes.

## Decisão

1. **App novo `apps/esocial`** (schema do tenant). Eventos são gerados **por
   órgão emissor** (`people.OrgaoEmissor`, com CNPJ próprio — ADR-0011), não
   por município: uma prefeitura tem N órgãos (Prefeitura, Fundo de Saúde,
   Câmara), cada um com seu eSocial.

2. **Modelo genérico `EventoESocial`** — uma linha por evento gerado:
   `tipo` (S-1000, S-1005, …), `orgao_emissor` (FK), `id_evento` (ID único do
   eSocial, 36 chars), `versao_layout`, `xml` (texto), `status`
   (`gerado` → `validado` → `assinado` → `enviado` → `processado`/`rejeitado`),
   `lote`, `retorno`, auditado via `simple-history`. Não há um model por tipo
   de evento — o tipo discrimina e o serviço sabe montar cada um. Isso escala
   para as dezenas de eventos sem explosão de tabelas.

3. **Geração de XML** com `lxml`, montando a árvore conforme o leiaute. O ID
   do evento segue o padrão eSocial:
   `ID + tpInsc(1) + nrInsc(14, zero-pad) + AAAAMMDDHHMMSS + sequencial(5)`.

4. **Validação contra XSD oficial** (`lxml.etree.XMLSchema`). Os schemas da
   versão vigente (**S-1.3**, `v_S_01_03_00`) ficam **versionados no repo** em
   `apps/esocial/schemas/<versao>/` (evtInfoEmpregador, evtTabEstab, tipos,
   xmldsig-core). Validar é um passo do serviço, não opcional: um evento só
   passa a `validado` se bate no XSD.

5. **Onda 4.1** cobre os dois eventos de tabela que tudo depende:
   - **S-1000** (`evtInfoEmpregador`) — informações do empregador (órgão).
   - **S-1005** (`evtTabEstab`) — tabela de estabelecimentos.

## Consequências

### Positivas
- Camada 1 desbloqueada e testável sem certificado/governo.
- Modelo genérico de evento escala para todos os eventos do Bloco 4.
- XSD oficial versionado → validação real, regressão garantida.

### Custos / dívidas
- Assinatura (XML-DSig) e transmissão (web service, lotes, reconciliação)
  ficam para ondas seguintes — exigem certificado ICP-Brasil e acesso ao
  ambiente do governo.
- Os XSDs vêm de mirror confiável (`nfephp-org/sped-esocial`, padrão de fato
  em software fiscal BR); ao obter o pacote oficial direto do gov.br, conferir
  paridade.

## Alternativas descartadas

- **Um model por tipo de evento:** explode em dezenas de tabelas quase
  idênticas; o discriminador `tipo` + serviço por tipo é mais enxuto.
- **Gerar XML por template de string:** frágil e sujeito a XML malformado;
  `lxml` + validação XSD é seguro.
- **Incluir assinatura/transmissão já na 4.1:** bloqueado por certificado e
  acesso ao governo; fora do escopo desta onda.
