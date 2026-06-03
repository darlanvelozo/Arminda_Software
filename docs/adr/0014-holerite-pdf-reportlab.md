# ADR-0014 — Geração de holerite: JSON estruturado + PDF via ReportLab

**Status:** Aceita · 2026-06-02 · Vigora para Bloco 2 (Onda 2.5)

## Contexto

Com a folha calculada (Ondas 2.2–2.4), falta entregar o **holerite**
(contracheque / demonstrativo de pagamento) por servidor: uma
representação **estruturada (JSON)** — para a UI, portal do servidor
(Bloco 7) e integrações — e um **PDF** imprimível.

O JSON é só uma agregação dos `Lancamento` de um vínculo numa folha
(proventos, descontos, informativas, totais + cabeçalho). A decisão real
é **como gerar o PDF**, porque isso adiciona dependência e, dependendo da
escolha, exige bibliotecas de sistema na VPS de produção.

### Opções avaliadas

- **ReportLab** — pure-Python, sem libs de sistema. Layout montado em
  código (Tables/Paragraphs/Frames). Determinístico, leve, instala via pip.
- **WeasyPrint** — HTML+CSS → PDF. Layout rico e fácil de estilizar, mas
  exige `cairo`, `pango`, `gdk-pixbuf` (apt) na VPS — fricção no deploy.
- **xhtml2pdf** — HTML simples → PDF (usa ReportLab por baixo). Sem libs
  de sistema, mas baixa fidelidade a CSS moderno.

## Decisão

**ReportLab** (`reportlab==4.2.5`). Holerite é um documento **tabular e
estável** — proventos/descontos em colunas, cabeçalho fixo, totais. O
controle programático do ReportLab cobre isso bem, sem adicionar
dependência de sistema na VPS (alinhado ao princípio das libs pure-Python
já adotadas: `firebirdsql`, `openpyxl`).

### Estrutura

- `apps.payroll.services.holerite.montar_holerite(folha, vinculo) -> dict`
  — agrega os `Lancamento` (proventos/descontos/informativas), subtotais,
  totais e cabeçalho (município via `connection.tenant`, servidor, vínculo).
  Função sem efeito colateral; é a fonte da verdade do JSON.
- `apps.payroll.services.holerite.gerar_pdf(holerite: dict) -> bytes`
  — renderiza o dict acima em PDF com ReportLab. Recebe o dict pronto
  (testável e desacoplado do banco).
- Endpoints na `FolhaViewSet` (detail, leitura):
  - `GET /api/payroll/folhas/{id}/holerite/?vinculo={id}` → JSON.
  - `GET /api/payroll/folhas/{id}/holerite-pdf/?vinculo={id}` → `application/pdf`.

Valores monetários serializados como **string** (consistente com o resto
da API; Decimal exato, sem float).

## Consequências

### Positivas
- Deploy sem `apt` novo — só `pip install reportlab`.
- JSON reaproveitável: UI, portal do servidor (Bloco 7), eSocial/relatórios.
- Geração testável: `gerar_pdf` recebe dict, asserta `%PDF` nos bytes.

### Negativas / trade-offs
- Estilizar o PDF é mais verboso que CSS. Aceitável para um layout fixo.
- Se um dia o holerite precisar de layout muito gráfico/branding pesado,
  reavaliar WeasyPrint (custo de libs de sistema).

## Histórico

- 2026-06-02 — Aceita. Versão `v0.12.0` ao final da Onda 2.5.
