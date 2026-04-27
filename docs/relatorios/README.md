# Relatórios quinzenais

Pasta onde ficam os PDFs dos relatórios enviados ao cliente a cada 15 dias.

## Convenção de nome

```
AAAA-MM-DD-relatorio-NN.pdf
```

Exemplos:
- `2026-05-15-relatorio-01.pdf`
- `2026-05-30-relatorio-02.pdf`

## Como linkar no painel

Após adicionar o PDF aqui, registre uma entrada em `status-page/status.json`:

```json
{
  "data": "2026-05-15",
  "titulo": "Relatório 01 — Primeira quinzena do Bloco 1",
  "url": "https://github.com/darlanvelozo/Arminda_Software/raw/main/docs/relatorios/2026-05-15-relatorio-01.pdf"
}
```
