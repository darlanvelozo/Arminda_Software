# Roadmap

> Plano de construção do Arminda em blocos sequenciais. Cada bloco é entregue de forma independente, testado e documentado antes de avançar.

## Princípios

1. **Risco crescente.** Construir primeiro o que é mais crítico funcionalmente e mais simples tecnicamente. Deixar inteligência e integrações externas para depois que a fundação estiver sólida.
2. **Paridade antes de diferenciação.** Sem cálculo de folha correto e obrigações legais funcionando, qualquer "diferencial moderno" (BI, IA, WhatsApp) é teatro.
3. **Validação em mundo real.** O bloco 6 (piloto) é o gate de qualidade — sistema só avança para diferenciação depois de rodar em produção paralela ao Fiorilli sem divergências.
4. **Marcos com gates.** Fim de cada bloco tem critérios objetivos de aceitação. Se não bater, replanejamos antes de avançar.

---

## Bloco 0 — Estrutura inicial

**Status:** em andamento
**Período:** sessão atual

Setup do repositório, arquitetura base, ambiente de desenvolvimento e documentação fundacional.

**Entregáveis**
- Monorepo organizado (`backend/`, `frontend/`, `docs/`, `scripts/`)
- Esqueleto Django (settings split dev/prod, apps vazias)
- Esqueleto Vite + React + TS + Tailwind + shadcn/ui
- Docker Compose (Postgres + Redis)
- CI básico no GitHub Actions
- README, ROADMAP, ARCHITECTURE, CONTRIBUTING e ADRs iniciais

**Critério de aceitação:** clonar o repo, rodar `docker compose up -d`, configurar backend e frontend, e ter as duas pontas iniciando sem erro.

---

## Bloco 1 — Fundação multi-tenant e cadastros

**Período estimado:** meses 1–2

A camada de identidade do sistema. Tudo nos blocos seguintes depende disso.

**Escopo**
- Modelo multi-tenant por schema PostgreSQL (cada município = um schema isolado)
- Autenticação (JWT) e autorização (RBAC com permissões por tela/ação)
- Cadastros centrais: Servidor (pessoa física + dependentes + documentos), Cargo (com CBO), Lotação, Vínculo Funcional (regime, matrícula, datas, situação), Rubrica (esqueleto, sem fórmula ainda)
- Histórico funcional auditado (quem mudou, quando, o que, por quê)
- Importador v1 do Firebird (Fiorilli SIP) → PostgreSQL: tabelas TRABALHADOR, CARGO, LOTACAO e seus satélites
- Telas básicas: login, dashboard, listas e formulários dos cadastros centrais

**Critério de aceitação**
- Criar 2 tenants (municípios), inserir 100 servidores em cada, garantir isolamento total
- Importar uma base real de Fiorilli em < 30 minutos
- 80%+ de cobertura de testes nas regras de domínio

---

## Bloco 2 — Engine de cálculo + DSL de rubricas

**Período estimado:** meses 3–4

O coração do produto. É aqui que o trabalho pesado acontece.

**Escopo**
- DSL (linguagem de domínio) para fórmulas de rubricas — testável, versionada, auditável
- Cálculo de folha mensal ordinária
- Incidências: INSS, IRRF, FGTS, previdência municipal própria
- Geração de holerite (PDF + visualização web)
- Reprocessamento de folha (com preservação de histórico de cálculo)
- Testes de paridade contra base real do Fiorilli

**Critério de aceitação**
- Calcular folha mensal de 500 servidores em < 10 segundos
- 0 divergências em comparação com Fiorilli em ≥ 95% dos casos de teste
- Cada rubrica tem cenários de teste documentados e versionados

---

## Bloco 3 — Folhas especiais

**Período estimado:** mês 5

Cobertura completa dos eventos de folha não-ordinários.

**Escopo**
- 13º salário (parcelas 1 e 2, com adiantamento e ajuste)
- Férias (com abono pecuniário, adiantamento e antecipação de 13º)
- Rescisão (todas as modalidades com cálculo de verbas)
- Licença-prêmio
- Folha complementar e adiantamento

**Critério de aceitação**
- Cada tipo de folha tem cenários de teste cobrindo as principais variações
- Paridade contra Fiorilli em base real

---

## Bloco 4 — Obrigações legais federais

**Período estimado:** meses 6–7

A camada que ninguém vê mas que, se quebrar, derruba o produto.

**Escopo**
- eSocial (S-1.3 ou layout vigente): eventos S-1000, S-1005, S-1010, S-1020, S-1200, S-1210, S-1280, S-2200, S-2299, S-2300, S-2399, S-2400 e relacionados
- SEFIP (enquanto coexistir)
- CAGED (enquanto coexistir)
- RAIS
- DIRF
- Informe de rendimentos do servidor
- DCTFWeb
- **MANAD** (Manual Normativo de Arquivos Digitais — IN SRP 86/2003 e atualizações; ainda exigido em fiscalizações pontuais da Receita/INSS). Geração dos blocos K (folha): K001/K050/K100/K150/K200/K250/K300/K990 + cabeçalhos 0xxx e bloco 9 de controle. Por CNPJ emissor (entidade fiscal), não por município.

**Pré-requisito de modelo**
- Entidade `OrgaoEmissor` (com CNPJ próprio) ligada a `UnidadeOrcamentaria` — uma prefeitura tem N órgãos emissores (Prefeitura, Fundo de Saúde, FMAS, Câmara). MANAD e eSocial são gerados **por órgão**, não pelo município inteiro.

**Critério de aceitação**
- Envio bem-sucedido em ambiente de produção restrito do governo
- Reconciliação de retornos (sucesso/erro) automática
- Reenvio com tracking de status
- MANAD gerado idêntico ao do sistema legado em paridade bit-a-bit para 1 competência completa

---

## Bloco 5 — Integração TCE

**Período estimado:** mês 8

**Escopo**
- Adaptador para o **TCE-MA** (SACOP/SIGFIS — estado da prefeitura-piloto)
- Adaptador para o **TCE-PB** (Sagres Folha) — alvo do segundo município
- Framework de adaptadores extensível para outros TCEs (TCE-SP Audesp, TCE-PE, TCE-CE, etc.)
- Geração e validação de arquivos no layout de cada TCE
- Histórico de remessas + reenvio
- **Configuração no admin Django** (ADR-0011): cada município ativa as integrações que precisa via tabela `IntegracaoExterna` — o frontend monta o menu dinamicamente a partir dela. Nenhuma integração fica "fantasma" para município que não usa.

**Critério de aceitação**
- Geração de remessa do TCE-MA aceita sem rejeição estrutural
- Geração de remessa do TCE-PB (Sagres) aceita sem rejeição estrutural
- Documentação clara para adicionar novos TCEs (1 estado novo em ≤ 1 semana)
- Município pode ativar/desativar integrações sem deploy de código

---

## Bloco 6 — MVP piloto em produção

**Período estimado:** mês 9

**Gate crítico do projeto.** Sem aprovação aqui, não avançamos para diferenciação.

**Escopo**
- Operação em paralelo ao Fiorilli em município real (São Raimundo do Doca Bezerra ou outro da rede)
- Validação cruzada lançamento a lançamento por 3 competências consecutivas
- Correção de divergências
- Operação sem falhas críticas por 60 dias

**Critério de aceitação**
- 3 competências (mês 1, 2, 3 de operação) com paridade ≥ 99,9%
- 0 incidentes que impactem pagamento
- Equipe da prefeitura consegue operar com ≤ 16h de treinamento

---

## Bloco 7 — Diferenciação

**Período estimado:** meses 10–12

Onde o Arminda vira produto, não só substituto.

**Escopo**
- Portal do servidor (PWA) — contracheque, férias, declarações, dados pessoais
- Bot WhatsApp — solicitar contracheque, consultar férias, abrir solicitação
- Dashboard BI — indicadores de RH, série histórica, custo por lotação, simulações
- Alertas IA — detecção de anomalias na folha (acumulação de cargos suspeita, valor fora do padrão histórico, vencimento de prazos legais)
- Importador universal — receber base de QUALQUER sistema concorrente e mapear via IA
- API pública para integrações de terceiros

**Critério de aceitação**
- Cada feature tem métrica de adoção definida e instrumentada
- App PWA passa em audit Lighthouse ≥ 90 em todas as categorias

---

## Bloco 8 — RH operacional (rotina de pessoal)

**Período estimado:** maio – setembro/2027 (em paralelo ao Bloco 9)

Cobre o dia-a-dia do RH além do cadastro. Os blocos 1-7 entregam folha
e diferenciação, mas faltam os processos contínuos de gestão de pessoas
que **alimentam** a folha — sem isso, a folha exige intervenção manual
a cada virada.

**Escopo**
- **Estágio probatório** — ciclo de 3 anos com avaliações periódicas,
  comissão, relatórios e efetivação automática (CF art. 41).
- **Progressão funcional automática** — anuênio/triênio/quinquênio
  aplicado por tempo de serviço (substitui rubrica fixa manual).
- **Frequência e ponto** — importação de AFD/biometria (padrão MTE
  Portaria 1.510), banco de horas, faltas, abonos, atrasos.
- **Férias** — período aquisitivo, escala anual, abono pecuniário
  (1/3 + venda de 10 dias), adiantamento.
- **Saúde ocupacional** — atestados, INSS afastamento (B-91, B-31),
  perícia médica, CAT (Comunicação de Acidente de Trabalho),
  retorno ao trabalho.
- **Aposentadoria** (RPPS e RGPS) — cálculo de proventos,
  integralidade vs paridade, requerimento, parecer técnico.
- **Pensão** — dependentes habilitados, cota familiar, reversão,
  pensão alimentícia.
- **Cessão de servidor** — entre entes federativos, com ou sem ônus,
  com período definido.
- **Licenças não-remuneradas** — TIP, mandato classista, etc.
- **Capacitação** — cursos, certificados, horas-aula, reembolso.
- **Diárias e passagens** — solicitação, autorização, prestação.
- **Empréstimos consignados** — margem 35% + 10% cartão, bancos
  credenciados, integração com bureaus (BMG, Banco do Brasil,
  Itaú, Bradesco, Caixa).
- **Quadro de pessoal** — cargos vagos vs ocupados, lotação ideal,
  plano de carreira.

**Critério de aceitação**
- Cada processo gera os eventos eSocial correspondentes automaticamente
  (entregue no Bloco 10, parte RPPS específico).
- 100% dos campos derivados (idade, tempo de serviço, faixa de
  progressão) calculados em runtime — nenhum cron manual.

---

## Bloco 9 — Tesouraria, contábil e LRF

**Período estimado:** maio – setembro/2027 (em paralelo ao Bloco 8)

Liga a folha ao dinheiro de verdade: gera arquivo bancário, registra
empenhos no sistema contábil, controla LRF e fecha o ciclo financeiro.

**Escopo**
- **CNAB 240** — geração de arquivo bancário para folha + consignados
  + diárias. Layouts: Banco do Brasil, Caixa, Itaú, Bradesco.
- **Conta-corrente do servidor** — créditos e débitos fora da folha
  (acertos, devoluções, glosas).
- **Conciliação bancária** — folha gerada vs retorno do banco;
  diferenças apontadas e tratadas.
- **Provisões contábeis mensais** — 13º proporcional + férias
  proporcionais empenhadas pelo regime de competência (PCASP).
- **Cálculo retroativo** — refazer N competências quando houver decisão
  judicial, acordo coletivo ou erro identificado, com reflexos em
  rubricas variáveis.
- **Integração PCASP** — geração automática de empenho, liquidação e
  pagamento no sistema contábil do município (Betha, Govbr, etc.).
- **RREO** (Relatório Resumido de Execução Orçamentária) — anexos
  de pessoal (LC 101/2000).
- **RGF** (Relatório de Gestão Fiscal) — apuração da despesa com
  pessoal (LRF art. 19/20, limite 54%/60%).
- **Painel LRF** — alerta visual quando município se aproxima do
  limite prudencial (90%) ou de alerta (95%).
- **Pré-empenho na geração da folha** — bloqueio se orçamento da
  unidade não comporta o valor calculado.

**Critério de aceitação**
- CNAB 240 testado em homologação de pelo menos 2 bancos.
- RREO/RGF passam pela conferência do controle interno do município.
- Limite LRF: alerta gerado **antes** do gestor tomar decisão (não
  depois do TCE apontar).

---

## Bloco 10 — Compliance, transparência e auditoria

**Período estimado:** outubro – dezembro/2027

Cobre exigências legais que não são folha mas afetam o município.
Sem isso, está em risco regulatório mesmo com a folha funcionando.

**Escopo**
- **Portal da Transparência** (Lei 12.527/2011) — folha pública por
  servidor com filtros por área, cargo, faixa salarial.
- **LGPD** — consentimentos rastreados, anonimização de dados
  sensíveis, exclusão sob demanda do titular (Lei 13.709/2018).
- **Certificação digital A1/A3** — assinatura eletrônica em
  declarações, contracheques e contratos oficiais (MP 2.200-2/2001).
- **Auditoria avançada com UI navegável** — timeline de quem editou
  o quê e quando, com diff campo a campo (UI do simple-history que
  já existe no backend).
- **Acessibilidade WCAG 2.1 AA** (Lei 13.146/2015) — contraste,
  navegação por teclado, leitores de tela, descrições alternativas.
- **Logs de acesso a dados sensíveis** (folha, salário, dependentes) —
  quem acessou, quando, de onde.
- **Política de retenção de dados** conforme LGPD e arquivística
  pública (TT — Tabela de Temporalidade do CONARQ).
- **eSocial RPPS específico** — S-2410 (benefício vitalício), S-2418
  (reativação), S-2420 (cessação), S-2230 (afastamento), S-2240
  (insalubridade/periculosidade), S-2250 (aviso prévio), S-2298
  (reintegração), S-2206 (alteração contratual), S-3000 (exclusão).
- **Observabilidade em produção** — Sentry para erros, Prometheus +
  Grafana para métricas, alertas proativos antes do operador notar.
- **Help desk integrado** — tickets dentro do app, FAQ, base de
  conhecimento.

**Critério de aceitação**
- Portal da Transparência audita-se contra os requisitos da
  CGU/Ouvidoria-Geral (Lei 12.527).
- LGPD: relatório de impacto à proteção de dados (RIPD) elaborado
  e aprovado.
- WCAG: auditoria automática via axe-core no CI, score ≥ 95.
- Trinta dias sem incidentes detectados pelo Sentry após o release.

---

## O que NÃO está no roadmap (intencionalmente)

- **App nativo iOS/Android** — PWA cobre 90% das necessidades iniciais; nativo só se houver demanda comprovada.
- **Módulo de ponto eletrônico próprio** — primeiro integrar com sistemas existentes (AFD, biometria), construir o próprio só se virar gargalo.
- **Módulo de concursos** — escopo paralelo, não bloqueia folha.
- **Marketplace de plugins** — discussão para depois de 50 municípios.

---

## Riscos críticos mapeados

1. **Mudanças regulatórias sem aviso prévio.** Mitigação: arquitetura de regras parametrizadas + processo de release rápido.
2. **Performance em municípios grandes** (16k+ servidores em Teresina, por exemplo). Mitigação: cálculo assíncrono via Celery + benchmarks contínuos.
3. **Migração do Fiorilli em produção.** Mitigação: importador testado em base real desde o bloco 1; coexistência gradual no bloco 6.
4. **LGPD.** Mitigação: design com privacidade desde o início — logs de acesso, criptografia de campos sensíveis, política de retenção.
5. **Paridade legal incompleta.** Mitigação: cada cálculo tem teste contra Fiorilli como gate de release.
