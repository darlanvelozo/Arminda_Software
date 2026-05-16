# Arminda — branch `demo`

**Esta é uma fotografia para apresentação ao Dr. Renzo.**
Estado: **v0.6.1** (Bloco 2.2 entregue — cálculo de folha funcional).
Branch criada em: **2026-05-15**.

> **Atenção:** esta branch é **congelada**. Não rode `merge main` nem
> commite features novas aqui. O desenvolvimento contínuo segue na
> branch `main` sem qualquer interferência neste snapshot.

---

## Como subir a demo

### 1. Pré-requisitos (instalar uma vez)

**Cloudflared** (cria o túnel público):

```bash
# repositório oficial Cloudflare
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg \
  | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt update && sudo apt install -y cloudflared
```

**Backend venv + frontend build** já estão prontos nesta branch.

### 2. Garantir banco populado

A demo usa o tenant `smoke_arminda` com os 23 servidores, 11 rubricas
e 3 folhas calculadas. Se não estiver populado:

```bash
cd backend
source .venv/bin/activate
python manage.py shell < ../seed-demo.py     # script de seed na raiz
```

(O script já roda em modo idempotente — pode chamar quantas vezes precisar.)

### 3. Subir tudo

```bash
./start-demo.sh
```

O script sobe:

- **Django backend** em `localhost:8000`
- **Vite preview** (build estático) em `localhost:4173`
- **Cloudflare Tunnel** expondo `4173` numa URL pública dinâmica

No final imprime algo como:

```
URL pública:  https://xxxx-yyyy-zzzz.trycloudflare.com
```

**Mande essa URL pro Dr. Renzo.**

### 4. Parar

```bash
./start-demo.sh stop
```

Ou simplesmente Ctrl+C nos terminais.

---

## Credenciais para o Dr. Renzo

```
URL:        (vai chegar por mensagem — muda a cada execução do túnel)
E-mail:     smoke-admin@arminda.test
Senha:      arminda-smoke-2026
Município:  Smoke Test (MA)
```

---

## O que está pronto nesta demo

- **Dashboard** com KPIs reais: 23 servidores, distribuição por vínculo (15 efetivos / 3 comissionados / 2 temporários / 3 eletivos) e por área (8 administração / 7 saúde / 6 educação / 3 assistência social).
- **Servidores**: lista paginada de 23 servidores com nome, CPF, matrícula. Detalhe com 5 abas (pessoais, vínculos, dependentes, documentos, histórico).
- **Cargos**: 11 cargos cadastrados.
- **Lotações**: 7 secretarias (SEMED, SEMSA, SMAS, SEMAD, Gabinete, Câmara, FMS).
- **Rubricas**: 11 rubricas com fórmulas DSL reais (proventos + descontos + informativas).
- **Folhas calculadas**: 3 competências (mar/abr/mai 2026) com totais reais.
  - 03/2026: R$ 147.765 prov / R$ 24.701 desc / **R$ 123.063 líquido**
  - 04/2026: R$ 147.813 prov / R$ 24.701 desc / **R$ 123.111 líquido**
  - 05/2026: R$ 147.938 prov / R$ 24.701 desc / **R$ 123.236 líquido**
- **/guia**: manual operacional vivo dentro do sistema.
- **/guia-admin**: visão técnica (só aparece pra admin).
- **Pesquisa global ⌘K**: busca em servidores, cargos, lotações, rubricas.

## O que ainda **não está pronto** (próximas ondas)

- **Tela operacional de Folha** (Onda 2.6) — cálculo hoje é via API, sem UI.
- **Holerite em PDF** (Onda 2.5).
- **Tabelas legais reais** (Onda 2.3) — INSS e IRRF hoje são aproximações.
- **Folhas especiais** (Bloco 3) — 13º, férias, rescisões.
- **Obrigações federais** (Bloco 4) — eSocial, MANAD, SEFIP, CAGED.
- **Tribunal de Contas** (Bloco 5).

Veja roadmap completo em `/guia` → "Em construção".

---

## Diferenças desta branch para `main`

```
Arquivos novos
├── DEMO.md                       este documento
├── start-demo.sh                 script de boot
└── frontend/vite.config.ts       config `preview` com proxy /api

Arquivos modificados — nenhum
```

Nada do que está aqui afeta a `main`. Quando quiser uma demo mais nova:

```bash
git checkout demo
git merge main          # traz tudo o que evoluiu
npm run build           # rebuild frontend
./start-demo.sh         # nova URL pública
```

---

## Tag de versão

Esta demo está marcada como **`v0.6.1-demo`**.

Se quiser apontar pra um snapshot específico:

```bash
git checkout v0.6.1-demo
```
