# ADR-0021 — Lições da engenharia reversa do Fiorilli SIP (eSocial e folha)

**Status:** Aceita · 2026-07-03 · Vigora para Blocos 2 (2.7) e 4

## Contexto

Recebemos a engenharia reversa de bases reais do **Fiorilli SIP_7** (Firebird),
de dois entes do Maranhão (Brejo e São João Batista), documentada em
[`docs/referencia/analise-fiorilli-sip.md`](../referencia/analise-fiorilli-sip.md).
O `.7z`/`.FDB` bruto **não fica no repositório** (PII real — LGPD, CLAUDE.md §7);
vive fora de qualquer checkout git. Este ADR registra o que a análise **valida**
no Arminda, as **lacunas** que ela expõe (sobretudo eSocial) e as **decisões**
decorrentes.

## O que a análise valida (não revisitar)

Decisões já tomadas que a base real confirma como corretas:

- **Regime num único campo** (`Vinculo.regime`) — o legado tinha `CLT_OU_ESTATUTO`
  (derivado por trigger) divergindo de `REGIME_JURIDICO_TRAB`; fonte de bug real.
- **Chave serial** (não composta `empresa+código`).
- **Competência de 1ª classe com estado** (`Folha.status`).
- **Separar geração do envio** de eventos eSocial (outbox) — ADR-0020.
- **CNPJ por órgão** (`OrgaoEmissor`), CBO no cargo, incidências por flag na rubrica.
- Multi-tenant por schema (o legado é 1 arquivo por ente).

## Decisões

1. **Snapshot de incidência ao fechar a folha (inegociável).** O `MOVIMENTO`
   do legado congela as flags de incidência no momento do cálculo, para que
   "folha paga não mude sozinha" se a rubrica for editada depois. Nosso
   `Lancamento` guarda só `valor`. **Decisão:** ao fechar a folha, congelar por
   lançamento o contexto fiscal (flags de incidência + natureza eSocial da
   rubrica). Implementação na **Onda 4.4**.

2. **Natureza de rubrica eSocial (Tabela 3) na `Rubrica`.** Cada rubrica precisa
   do código oficial de natureza (+ códigos de incidência CP/IRRF/FGTS) para ser
   aceita nos eventos periódicos. **Decisão:** adicionar o de-para na `Rubrica` e
   publicar via **S-1010**. Implementação na **Onda 4.3** (esta).

3. **`ResumoFolha` persistido por vínculo × competência** (o `BASES` do legado):
   bases por obrigação (INSS/IRRF/FGTS/RPPS) + flags de exclusão por evento
   (S-1200/S-1202/S-1210). Insumo dos periódicos e de retificações.
   Implementação na **Onda 4.4**.

4. **S-1202 (RPPS) é prioridade, não opcional.** É o evento de remuneração do
   servidor estatutário — o diferencial do setor público que folhas privadas não
   fazem. Vai junto do S-1200 na **Onda 4.5**.

5. **Qualificação cadastral (consulta gratuita à Receita).** Confere
   CPF+Nome+Nascimento antes de admitir/manter vínculo. Baixo risco (é consulta,
   não envio), melhora dados antes de qualquer evento. Antecipável.

6. **Proveniência/confiança de dado sensível.** Marcar "nascimento confirmado por
   documento" vs "herdado de importação" — o legado tinha 221 nascimentos
   divergentes, >60% placeholders (01/01). Entra com LGPD (Bloco 10) ou antes,
   junto da qualificação cadastral.

7. **Status eSocial na competência** (encerramento/reabertura — S-1298/S-1299).
   Estender `Folha.status`/ciclo. Onda de periódicos/fechamento.

8. **A base SJB destrava a Onda 2.7 (paridade Fiorilli).** Passa a ser possível
   comparar o cálculo do Arminda com `MOVIMENTO`/`BASES` reais, competência a
   competência (critério de aceite da 2.7 e do MANAD). **Uso PII-safe:** importar
   em schema isolado, comparar agregados/bases; não versionar dado individual.

## Consequências

- Reordena o Bloco 4 (ver ROADMAP): 4.3 (natureza de rubrica) → 4.4 (snapshot +
  ResumoFolha) → 4.5 (S-1200/S-1202/S-1210).
- A 2.7 deixa de estar bloqueada por falta de dados.
- Tabelas de domínio oficiais (CBO, natureza de rubrica, tipo de logradouro)
  são **dados de referência versionados**, não enum fixo no código.

## Referências

- [`docs/referencia/analise-fiorilli-sip.md`](../referencia/analise-fiorilli-sip.md)
- ADR-0009 (importador Fiorilli), ADR-0013 (incidências), ADR-0020 (eSocial).
