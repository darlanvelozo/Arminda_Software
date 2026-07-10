# ADR-0023 — Módulo de Regularidade Fiscal (CND) — escopo e desenho

**Status:** Aceita (escopo/desenho; implementação por ondas futuras) · 2026-07-10

## Contexto

A assessoria fiscal que atende os municípios-alvo trabalha destravando a
**CND (Certidão Negativa de Débitos)** — sem ela, o município não recebe
transferência voluntária nem assina convênio. O fluxo real, documentado com
artefatos de 4 municípios (relatórios de situação fiscal do e-CAC, autos de
infração, impugnações, recursos voluntários, protocolos de juntada, processos
digitais baixados):

1. Entrar no **e-CAC** com o **certificado digital** do município (ou com
   **procuração digital** outorgada ao procurador, quando o município não
   entrega o certificado) e emitir o **Relatório de Situação Fiscal**
   (pendências SIEF, dívida ativa PGFN/SIDA, parcelamentos SISPAR).
2. Transformá-lo em **dois relatórios**, hoje manuais:
   - **da contabilidade** — pendências operacionais (retificar DCTFWeb, gerar
     boletos, resíduos GFIP, parcelamentos PEM/RFB e PEM/PGFN);
   - **da assessoria jurídica** — processos no e-Processo com **prazo de
     impugnação/recurso**, com o processo baixado para o advogado montar a
     defesa do auto de infração.
3. Preparar a peça (impugnação/recurso voluntário/resposta a TIF), revisar
   (advogado) e **protocolar** a juntada no e-CAC; o resultado chega na
   **Caixa Postal**.
4. Monitorar a Caixa Postal e **alertar prazos** (inclusive RFFP —
   Representação Fiscal para Fins Penais, que exige atenção especial).

Requisitos explícitos do cliente (áudios de 04/07, transcritos):
"o sistema tem que gerar esse relatório da contabilidade e um específico da
assessoria, separados"; "preparar o recurso e protocolizar pra gente";
"baixar os processos e disponibilizar para o advogado"; "criar um alerta
quando chegar mensagem na caixa postal com recurso pendente e prazo";
"só eu e você teremos acesso a essa parte"; "pode separar essa parte dentro
do sistema, mantendo a folha separada".

## Decisão (escopo e desenho — implementação em ondas futuras)

1. **Módulo restrito dentro do Arminda** (não um sistema à parte): app
   `fiscal`, com **papel RBAC exclusivo** (`assessor_fiscal`) — invisível
   para os demais papéis (a operação de folha não vê o módulo). Reusa o
   multi-tenant, o cofre de certificados (ADR-0022) e o `OrgaoEmissor`.

2. **Modelo de dados** (nomes indicativos):
   - `SituacaoFiscal` — snapshot do relatório do e-CAC por órgão/data;
   - `PendenciaFiscal` — item da situação (origem: SIEF/SIDA/SISPAR; tipo:
     débito, inscrição, parcelamento; valor, competência, situação);
   - `ProcessoFiscal` — processo administrativo (número, tipo de auto,
     valores, **prazo de impugnação/recurso**, status, arquivos baixados);
   - `PecaProcessual` — impugnação/recurso/resposta a TIF (arquivo, autor,
     status de revisão: rascunho → revisado → protocolado) + `Protocolo`;
   - `AlertaFiscal` — prazo/mensagem de Caixa Postal, com destinatário.
   - `ProcuracaoDigital` — outorga por órgão (alternativa ao certificado).

3. **Relatórios gerados** — replicar os dois relatórios manuais (contabilidade
   × assessoria) como saídas automáticas do módulo (HTML/PDF), com a marca do
   emissor configurável.

4. **Acesso à Receita**: a coleta autenticada (situação fiscal, caixa postal,
   e-Processo) depende do canal — certificado no cofre + (a) **ACT**/convênio,
   (b) SERPRO (Integra Contador/DTE), ou (c) automação assistida do e-CAC.
   Canal ainda **não definido** (o cliente conduz a frente do ACT); o módulo
   nasce com **importação manual dos artefatos** (upload do PDF de situação
   fiscal / processos baixados) e evolui para coleta automática quando o
   canal existir. Isso desacopla o valor imediato (organização, prazos,
   alertas, relatórios) da dependência externa.

5. **Limites de segurança/operação**: dados sigilosos — acesso só pelo papel
   exclusivo; nenhuma ação contra sistemas do governo sem autorização
   explícita; testes somente com o cliente, via procuração/certificado.

## Consequências

- Novo papel `assessor_fiscal` (junta-se aos papéis planejados de PERSONAS).
- O módulo entra no roadmap como evolução do item "monitoramento fiscal" do
  Bloco 10, reenquadrado como **Regularidade Fiscal/CND**, podendo ser
  antecipado por demanda do cliente (fase 1 — importação manual — não depende
  de canal externo nem de transmissão eSocial).
- Fase 1 (sem canal): upload/parse dos PDFs do e-CAC + processos, prazos e
  alertas, peças com workflow de revisão, dois relatórios automáticos.
- Fase 2 (com canal): coleta automática (situação fiscal, caixa postal),
  download de processos, protocolo de juntada.

## Alternativas descartadas

- **Sistema separado da folha**: duplicaria auth/tenant/infra; o isolamento
  pedido se resolve com RBAC + navegação separada dentro do Arminda.
- **Esperar o canal (ACT/SERPRO) para começar**: a fase 1 já entrega valor
  (organização, prazos, relatórios) só com os artefatos que a assessoria já
  baixa manualmente.
