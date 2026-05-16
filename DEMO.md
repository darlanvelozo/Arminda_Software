# Arminda — branch `demo`

> **Snapshot da v0.6.1 (Bloco 2.2) com dados curados para apresentação a
> stakeholders.** Esta branch é congelada — o desenvolvimento contínuo
> roda na `main` sem qualquer interferência aqui.

---

## TL;DR

```bash
# uma vez só, em qualquer máquina nova
./setup-demo.sh

# todas as vezes (deixar rodando no notebook 24/7)
./start-demo.sh
```

O `start-demo.sh` sobe Django + frontend + Cloudflare Tunnel, imprime
a URL pública, e fica supervisionando — se algo cair, reinicia.

---

## Visão geral

A demo roda **dois processos web + um túnel** no notebook:

```
                          internet
                              │
                  ┌───────────▼───────────┐
                  │  cloudflared tunnel    │  URL pública gratuita
                  │  ────────────────────  │  (muda a cada execução)
                  └───────────┬───────────┘
                              │
                  ┌───────────▼───────────┐
                  │  vite preview :4173   │  frontend estático
                  │  /api → proxy → 8000  │
                  └───────────┬───────────┘
                              │
                  ┌───────────▼───────────┐
                  │  gunicorn :8000       │  Django (2 workers)
                  │  + Postgres local     │
                  └───────────────────────┘
```

---

## 1. Setup inicial (uma vez por máquina)

### 1.1 Pré-requisitos do sistema

| Software       | Como instalar                                                                                    |
|----------------|--------------------------------------------------------------------------------------------------|
| Python 3.12    | `sudo apt install python3.12 python3.12-venv`                                                    |
| Node 20+       | `curl -fsSL https://deb.nodesource.com/setup_20.x \| sudo bash - && sudo apt install nodejs`      |
| PostgreSQL 16  | `sudo apt install postgresql && sudo systemctl enable --now postgresql`                          |
| cloudflared    | ver bloco abaixo                                                                                 |

#### Instalando cloudflared (uma vez)

```bash
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg \
  | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt update && sudo apt install -y cloudflared
cloudflared --version       # confere
```

#### PostgreSQL: criar usuário com seu nome de login

```bash
sudo -u postgres createuser --superuser $USER
```

### 1.2 Setup do projeto

```bash
git clone <repo>
cd Arminda_Software
git checkout demo
./setup-demo.sh
```

O `setup-demo.sh` é **idempotente** — pode rodar quantas vezes precisar
(útil quando atualizar a branch). Ele faz:

1. Verifica deps do sistema
2. Cria `backend/.venv` e instala `requirements.txt`
3. Cria banco PostgreSQL `arminda_demo` (se não existir)
4. Aplica migrations
5. Cria superuser Django (`admin@arminda.test` / `arminda-admin-2026`)
6. Cria tenant `smoke_arminda` (município "Smoke Test - MA")
7. Cria usuário operacional (`smoke-admin@arminda.test` / `arminda-smoke-2026`) com papel `admin_municipio`
8. Popula via `seed-demo.py`: 23 servidores, 7 secretarias, 11 rubricas, 3 folhas calculadas
9. `npm install` + `npm run build` do frontend

Saída esperada: **"✅ Setup completo. Demo pronta pra subir."**

---

## 2. Subir e deixar rodando 24/7

### Modo recomendado (notebook ligado o tempo todo)

Use **tmux** ou **screen** para a demo persistir entre sessões SSH/terminal:

```bash
tmux new -s arminda-demo
./start-demo.sh
# (no tmux: Ctrl+B depois D pra "destacar" sem matar — volta com `tmux attach -t arminda-demo`)
```

O `start-demo.sh` em foreground tem **supervisor embutido**:
- Verifica os 3 processos a cada 10s.
- Se algum cair, reinicia sozinho.
- Se o tunnel cair e a URL mudar, a nova URL é gravada em `.demo-run/public-url.txt`.

### Outras opções

| Comando                          | Efeito                                                  |
|----------------------------------|---------------------------------------------------------|
| `./start-demo.sh`                | sobe tudo + supervisor em foreground                    |
| `./start-demo.sh start --detach` | sobe tudo e sai (sem supervisor — usar com systemd)     |
| `./start-demo.sh stop`           | mata todos os processos da demo                         |
| `./start-demo.sh status`         | estado dos 3 processos + URL pública atual              |
| `./start-demo.sh restart`        | stop + start                                            |
| `./start-demo.sh logs`           | `tail -f` dos 3 logs combinados                         |

### Variáveis de ambiente

| Variável              | Default | Pra que serve                              |
|-----------------------|---------|---------------------------------------------|
| `DEMO_PORT_BACKEND`   | 8000    | porta do gunicorn                          |
| `DEMO_PORT_FRONTEND`  | 4173    | porta do vite preview                      |
| `DEMO_WORKERS`        | 2       | workers do gunicorn                        |
| `DEMO_NO_TUNNEL`      | 0       | se 1, não sobe cloudflared (só local)      |

---

## 3. Credenciais

Mensagem pronta para enviar ao cliente (substituir `<URL>` pela URL pública impressa pelo script):

```
URL:        <URL>
E-mail:     smoke-admin@arminda.test
Senha:      arminda-smoke-2026
Município:  Smoke Test (MA)
```

Django admin (para você):

```
URL:        http://localhost:8000/admin/
E-mail:     admin@arminda.test
Senha:      arminda-admin-2026
```

---

## 4. O que está no ar nesta demo

### Dados populados (tenant `smoke_arminda`)

- **23 servidores** em **7 secretarias**:
  - SEMED · SEMSA · SMAS · SEMAD · Gabinete · Câmara · Fundo de Saúde
- Distribuição:
  - 15 efetivos · 3 comissionados · 2 contratados · 3 eletivos
  - 8 administração · 7 saúde · 6 educação · 3 assistência social
- **27 dependentes** (para IR e salário-família)
- **11 rubricas** com fórmulas DSL reais (provento + desconto + informativa)
- **5 unidades orçamentárias 2026**
- **3 folhas mensais calculadas** (mar/abr/mai 2026)
  - Total proventos por mês: ~R$ 147 mil
  - Total descontos por mês: ~R$ 24 mil
  - **Líquido: ~R$ 123 mil/mês**

### Funcionalidades disponíveis para o usuário

- **Dashboard** com KPIs clicáveis por vínculo e por área
- **Servidores**: lista paginada + detalhe com 5 abas (pessoais, vínculos, dependentes, documentos, histórico)
- **Cargos / Lotações / Rubricas**: CRUD completo
- **Pesquisa global ⌘K** em qualquer tela
- **/guia**: manual operacional vivo dentro do sistema
- **/guia-admin**: visão técnica (só para `admin_municipio` e staff)
- **Configurações**: perfil, segurança, gestão de usuários do município

### O que **ainda não está pronto** (próximas ondas)

- Tela operacional de **Folha** com botão "calcular" — Onda 2.6
- **Holerite em PDF** — Onda 2.5
- **Tabelas legais reais** (INSS, IRRF 2026) — Onda 2.3
- **Folhas especiais** (13º, férias, rescisões) — Bloco 3
- **Obrigações federais** (eSocial, MANAD, RAIS, DIRF) — Bloco 4
- **Tribunal de Contas** (TCE-MA, Sagres-PB) — Bloco 5

Roadmap completo: dentro do sistema em `/guia` → "Em construção".

---

## 5. Manutenção

### Atualizar a demo com algo da `main`

```bash
git checkout demo
git merge main          # traz tudo o que evoluiu na main
./setup-demo.sh --skip-build  # reaplica seed/migrations
cd frontend && npm run build && cd ..
./start-demo.sh restart
```

### Resetar dados (voltar ao seed padrão)

```bash
cd backend
source .venv/bin/activate
python manage.py shell < ../seed-demo.py
deactivate
```

### Diagnosticar problemas

```bash
./start-demo.sh status         # estado rápido
./start-demo.sh logs           # logs combinados em tempo real
cat .demo-logs/django.log      # log isolado do Django
cat .demo-logs/vite.log
cat .demo-logs/tunnel.log
cat .demo-run/public-url.txt   # URL atual
```

### Backup do banco

```bash
pg_dump arminda_demo | gzip > arminda_demo_$(date +%Y%m%d).sql.gz
```

---

## 6. Estrutura desta branch

```
Arminda_Software/
├── setup-demo.sh           ⭐ instalação inicial (idempotente)
├── start-demo.sh           ⭐ subir/parar/supervisionar a demo
├── seed-demo.py            ⭐ dados do tenant smoke_arminda
├── DEMO.md                 ⭐ este documento
├── frontend/vite.config.ts proxy /api → 8000 no preview
├── backend/requirements.txt + gunicorn
└── (todo o resto = main na v0.6.1)
```

Arquivos com `⭐` são exclusivos desta branch — não existem na `main`.

---

## 7. Tag de versão

```bash
git checkout v0.6.1-demo     # snapshot exato desta demo
```

Quando atualizar a demo no futuro:

```bash
git tag -a v0.6.2-demo -m "demo: snapshot com Onda 2.3 (tabelas legais)"
git push origin v0.6.2-demo
```
