# ADR-0024 — eSocial: transmissão em lotes (camada pronta, envio gateado)

**Status:** Aceita · 2026-07-13 · Vigora para Bloco 4 (Onda 4.6)

## Contexto

Com geração, validação XSD e assinatura prontas (ADRs 0020/0022) e os eventos
periódicos entregues (Onda 4.5), falta a última etapa do ciclo: **transmitir**
ao webservice do eSocial. O protocolo oficial é SOAP 1.2 com **mTLS** (o
certificado e-CNPJ autentica a conexão), em dois passos: `EnviarLoteEventos`
(até 50 eventos assinados por lote, agrupados por tipo) e
`ConsultarLoteEventos` (protocolo → recibos/ocorrências por evento).

Restrições: enviar como um ente público é ação de mundo real; o primeiro envio
(mesmo em produção restrita) deve ser supervisionado, com o cliente ciente.

## Decisão

1. **Modelo `LoteESocial`** — orgão, `grupo` (1=tabelas, 2=não periódicos,
   3=periódicos), status (`montado → enviado → processado/erro`),
   `protocolo_envio`, `xml_envio`, `xml_retorno`. `EventoESocial` ganha FK
   `lote_envio`.

2. **Montagem offline e validada:** `montar_lote(orgao, eventos)` aceita só
   eventos **assinados** do mesmo grupo (máx. 50), monta o envelope
   `envioLoteEventos` e o **valida contra o XSD oficial de comunicação**
   (v1.5.0, versionado em `apps/esocial/schemas/comunicacao/`).

3. **Envio gateado por configuração:** o cliente SOAP (mTLS com o material do
   cofre) só executa se `settings.ESOCIAL_TRANSMISSAO_HABILITADA=True`
   (env; default **False**) **e** o ambiente estiver explicitamente definido
   (`producao_restrita` | `producao`). Sem isso, `enviar()` levanta
   `TransmissaoDesabilitada` — o botão existe, mas não dispara nada até o dia
   do teste supervisionado.

4. **URLs por ambiente** ficam em constantes documentadas
   (produção restrita: `webservices.producaorestrita.esocial.gov.br`;
   produção: `webservices.envio.esocial.gov.br`), conferidas no dia do teste.

## Consequências

- O ciclo completo fica pronto e demonstrável offline; ligar o envio é mudar
  uma variável de ambiente, com autorização explícita.
- mTLS reutiliza o cofre (ADR-0022): chave/cert decifrados em memória e
  materializados só em arquivo temporário efêmero durante a chamada.
- Recibos/ocorrências (retorno) atualizam evento a evento
  (`processado`/`rejeitado` + `retorno` JSON) — base das retificações.

## Alternativas descartadas

- Enviar já no primeiro deploy: sem homologação combinada e sem supervisão,
  risco desnecessário.
- zeep/suds (lib SOAP): o envelope do eSocial é simples o bastante para
  montar com lxml + requests; menos dependências.
