# ADR-0025 — Paridade Fiorilli: truncamento do INSS por faixa

**Status:** Aceita · 2026-07-13 · Vigora para Bloco 2 (Onda 2.7)

## Contexto

A Onda 2.7 fecha o Bloco 2 validando o cálculo do Arminda contra a folha real
do Fiorilli SIP. O harness (`apps.imports.services.paridade`) lê a tabela
`BASES` do SIP (bases e valores finais por servidor/competência), roda as
**nossas** funções tributárias de produção (`apps.calculo.tabelas`) sobre as
mesmas bases e mede o casamento centavo a centavo. Base usada: São João
Batista-MA, ~1.260 servidores/mês, competências 2024–2025 (PII fora do git,
ADR-0021).

Resultados da primeira rodada:

- **IRRF: 98,8%–99,5% exato à vista.** Semântica confirmada — a tabela incide
  sobre `BASEIRRFMES − DEDUIRRFMES` (base menos a dedução que o SIP publica).
  O motor de IRRF já está em paridade; nada a mudar.

- **Previdência progressiva:** 70,7% com o nosso arredondamento padrão
  (soma exata das faixas, arredonda o total). Investigando as divergências,
  quase todas eram de 1–2 centavos.

A causa foi identificada: o SIP **trunca a parcela de contribuição de cada
faixa** para centavos antes de somar; nós somávamos exato e arredondávamos no
fim. Reproduzindo o truncamento por faixa, o casamento sobe para **94,2%**. O
resíduo de 73 servidores (5,8%) não é erro de cálculo — é a população **RPPS**:
37 com teto/regra própria e 36 aposentados/imunes (base > 0, valor = 0). Esses
dependem da configuração de regime próprio do município (`RegimePrevidenciario`,
por-tenant), não da tabela federal.

## Decisão

1. **A função `inss()` ganha um modo de arredondamento opcional:**
   `inss(base, competencia, *, arredondamento="round"|"truncar")`. O padrão
   (`"round"`) preserva exatamente o comportamento anterior (alinhado à
   calculadora oficial da Receita); `"truncar"` aplica a convenção do SIP
   (trunca cada faixa). Nenhum teste ou holerite existente muda — o modo é
   opt-in.

2. **A seleção do modo é uma configuração de município**, não um default
   global. Municípios que migram de sistemas legados (Fiorilli, RM, etc.)
   esperam a convenção de truncamento com que seus servidores e o TCE já
   convivem; um município novo pode preferir o arredondamento oficial. A
   fiação do modo no pipeline de folha (`calcular_folha`) fica para a onda de
   configuração por-tenant, junto com a carga do RPPS.

3. **A paridade da previdência RPPS depende da regulação real do município.**
   O modelo `RegimePrevidenciario` já suporta `teto`, `faixas` e
   `modo_contribuicao`; falta apenas (a) a norma do RPPS de SJB para preencher
   os valores e (b) modelar a **imunidade do aposentado** (contribuição só
   sobre a parcela acima do teto do RGPS). Não se reverte-engenharia a config
   a partir da saída — carrega-se a regra legal.

4. **Critério de fechamento do Bloco 2 (Onda 2.7):** o motor tributário está
   validado em paridade — IRRF ≥ 98,8% e previdência RGPS 100% da população
   aplicável com o truncamento. Os casos RPPS remanescentes são configuração
   por-tenant, rastreados como pendência do módulo de previdência própria.

## Consequências

- **Positivas:** o motor de INSS/IRRF do Arminda está comprovadamente em
  paridade com o sistema incumbente sobre dados reais. O harness fica no repo
  (`manage.py paridade_fiorilli`) e serve de rede de segurança para qualquer
  mudança futura em tabelas ou cálculo. A migração de município real foi
  de-riscada de brinde (importador rodou 100% limpo em ~2.900 vínculos).

- **Custos/pendências:** o truncamento existe mas ainda não está fiado no
  cálculo de produção (é opt-in). Fechar a previdência RPPS a 100% exige a
  regulação do RPPS do município e a modelagem da imunidade de aposentado.

- **Segurança/PII:** o harness é read-only e o relatório é agregado — só
  contagens, taxas e faixas de magnitude, nunca CPF/nome/matrícula. A base
  bruta permanece fora do git (ADR-0021).
