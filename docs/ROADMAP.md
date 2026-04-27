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

**Critério de aceitação**
- Envio bem-sucedido em ambiente de produção restrito do governo
- Reconciliação de retornos (sucesso/erro) automática
- Reenvio com tracking de status

---

## Bloco 5 — Integração TCE

**Período estimado:** mês 8

**Escopo**
- Adaptador para o **TCE-MA** (estado da prefeitura piloto)
- Framework de adaptadores extensível para outros TCEs
- Geração e validação de arquivos no layout de cada TCE
- Histórico de remessas

**Critério de aceitação**
- Geração de remessa do TCE-MA aceita sem rejeição estrutural
- Documentação clara para adicionar novos TCEs (1 estado novo em ≤ 1 semana)

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
