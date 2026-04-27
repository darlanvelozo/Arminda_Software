# Painel de acompanhamento

Página estática que mostra o andamento do projeto Arminda para o cliente.

URL: `https://darlanvelozo.github.io/Arminda_Software/`

---

## Como funciona

Toda a informação que aparece no painel vem de um único arquivo: **`status.json`**.

Para atualizar o painel você edita esse arquivo, faz commit e push. O GitHub Pages publica automaticamente em ~30 segundos.

```
status-page/
├── index.html              # estrutura
├── status.json             # ← você edita só este arquivo
└── assets/
    ├── styles.css
    └── script.js
```

---

## Atualizando o painel — guia prático

### 1. Quando concluir um bloco

Abra `status.json` e altere:

```jsonc
"blocos": [
  {
    "numero": 0,
    "status": "concluido",        // ← muda de "em_andamento" para "concluido"
    "progresso_pct": 100,         // ← muda para 100
    "data_fim_real": "2026-04-27" // ← preenche a data real
  }
]
```

Ative o próximo bloco como "em_andamento":

```jsonc
{
  "numero": 1,
  "status": "em_andamento",
  "progresso_pct": 0
}
```

E atualize o campo geral:

```jsonc
"bloco_atual": 1,
"progresso_geral_pct": 12,
"ultima_atualizacao": "2026-05-01"
```

### 2. Quando avançar dentro de um bloco

Mude apenas o `progresso_pct` do bloco em andamento e o `progresso_geral_pct`:

```jsonc
{
  "numero": 1,
  "progresso_pct": 35  // ← estimativa honesta de quanto está pronto
}
```

E atualize a data:

```jsonc
"ultima_atualizacao": "2026-05-15"
```

### 3. Quando registrar uma atualização (changelog)

Adicione um item no início do array `changelog`:

```jsonc
"changelog": [
  {
    "data": "2026-05-15",
    "tipo": "entrega",
    "titulo": "Cadastro de servidores funcional",
    "descricao": "Tela de cadastro de servidor concluída, com validação de CPF e importação dos dados do sistema atual."
  },
  // ... itens anteriores ...
]
```

**Tipos sugeridos:** `marco` (acentuado em vermelho), `entrega`, `decisao`, `ajuste`.

### 4. Quando publicar um relatório quinzenal

1. Salve o PDF dentro de `docs/relatorios/` no repositório (crie a pasta se não existir).
2. Adicione um item no array `relatorios`:

```jsonc
"relatorios": [
  {
    "data": "2026-05-15",
    "titulo": "Relatório 01 — Primeira quinzena do Bloco 1",
    "url": "https://github.com/darlanvelozo/Arminda_Software/raw/main/docs/relatorios/2026-05-15-relatorio-01.pdf"
  }
]
```

> **Dica:** use `raw.githubusercontent.com` ou `/raw/main/` no link para que o PDF abra direto, sem passar pela interface do GitHub.

---

## Status possíveis para um bloco

| Status | Significado | Visual |
|---|---|---|
| `concluido` | Bloco entregue e aceito | Verde, barra cheia |
| `em_andamento` | Em construção agora | Âmbar, barra com pulso |
| `previsto` | Ainda não começou | Cinza, barra vazia |

---

## Ativando o GitHub Pages (apenas uma vez)

1. Vá em **Settings → Pages** no repositório `Arminda_Software`.
2. Em **Source**, escolha **GitHub Actions**.
3. Faça push da branch `main` — o workflow `.github/workflows/status-page.yml` faz o resto.

A primeira publicação leva ~1 minuto. Depois disso, cada push em `main` atualiza o painel.

---

## Testando localmente antes de publicar

Como o painel usa `fetch` para ler o `status.json`, abrir o `index.html` direto pelo navegador (file://) **não funciona** — o navegador bloqueia. Use um servidor estático rápido:

```bash
# Opção 1 — Python
cd status-page
python3 -m http.server 8080
# abrir http://localhost:8080

# Opção 2 — Node
npx serve status-page -p 8080
```

---

## Domínio personalizado (opcional, futuro)

Quando quiser usar um domínio próprio (ex.: `status.arminda.app`):

1. Compre o domínio (Registro.br, ~R$ 40/ano).
2. Configure CNAME apontando para `darlanvelozo.github.io`.
3. Em Settings → Pages → Custom domain, coloque o domínio.
4. Adicione um arquivo `status-page/CNAME` com o domínio dentro.

---

## Boas práticas

- **Atualize o painel toda quinzena, mesmo que o progresso seja pequeno.** Cliente que vê data antiga pensa que está parado.
- **Seja honesto com o `progresso_pct`.** Anunciar 90% e ficar nele por 2 meses é pior que ficar honesto em 65%.
- **No changelog, escreva em linguagem de cliente.** Evite "refatorei o serializer" — escreva "melhorei a velocidade do cadastro".
- **Não exclua entradas antigas do changelog.** O histórico inteiro é a melhor evidência de trabalho contínuo.
