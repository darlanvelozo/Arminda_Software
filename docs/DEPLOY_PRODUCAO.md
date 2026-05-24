# Deploy em produção — Arminda

Este é o **runbook operacional** para subir e manter o Arminda em
produção numa VPS Linux. A primeira instância roda em
**arminda.site** (VPS Hostinger Ubuntu 24.04).

> Para a demo (snapshot apresentável), ver [`DEMO.md`](../DEMO.md) na
> branch `demo`. Para visão técnica geral, ver `/guia-admin` no
> próprio sistema.

---

## TL;DR

```bash
# Setup inicial (1 vez por VPS):
sudo /opt/arminda/deploy/setup-producao.sh
sudo certbot --nginx -d arminda.site -d www.arminda.site --redirect

# A cada release:
sudo /opt/arminda/deploy/deploy.sh

# Frontend (mudou):
# (no laptop)
cd frontend && npm run build
rsync -avz --delete dist/ arminda-vps:/opt/arminda/frontend-dist/
```

---

## Arquitetura em produção

```
                          internet
                             │
                             ▼
                    ┌──────────────────┐
                    │  Nginx :443/:80  │ ← TLS via Let's Encrypt
                    │  arminda.site    │   (certbot --nginx)
                    └────────┬─────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
  ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
  │ /            │   │ /api/*       │   │ /static/         │
  │ SPA Vite     │   │ /admin/      │   │ collectstatic    │
  │ dist/        │   │ proxy_pass → │   │ alias backend-   │
  │              │   │ 127.0.0.1:   │   │ static/          │
  │              │   │   8001       │   │                  │
  └──────────────┘   └──────┬───────┘   └──────────────────┘
                            │
                            ▼
                  ┌──────────────────┐
                  │  gunicorn        │
                  │  arminda-backend │ systemd unit
                  │  .service        │
                  │  2 workers       │
                  └──────┬───────────┘
                         │
                         ▼
                  ┌──────────────────┐
                  │  PostgreSQL 16   │ loopback 127.0.0.1:5432
                  │  arminda_prod    │ multi-tenant (django-tenants)
                  └──────────────────┘
```

---

## Pré-requisitos da VPS

| Item | Mínimo |
|---|---|
| Sistema | Ubuntu 22.04+ ou Debian 12 |
| CPU | 1 vCPU |
| RAM | 2 GB (4 GB recomendado, principalmente se compartilha) |
| Disco | 20 GB (50 GB recomendado para crescer dados de tenants) |
| Portas abertas | 22 (SSH), 80 e 443 (Nginx) |
| DNS | A `arminda.site` → IP da VPS; CNAME `www` → `arminda.site` |

PostgreSQL e Nginx **podem ser compartilhados** com outras aplicações
na mesma VPS — o setup só cria role/database/vhost dedicados.

---

## Passo 1 — Acesso SSH

```bash
# (no laptop)
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519       # se não tiver
cat ~/.ssh/id_ed25519.pub                         # copia
# Cole no painel da VPS / GitHub deploy keys.

# Atalho no ~/.ssh/config:
cat >> ~/.ssh/config <<'EOF'
Host arminda-vps
    HostName 2.24.122.160
    User root
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
EOF

# Teste:
ssh arminda-vps -- "whoami && uname -a"
```

---

## Passo 2 — Clonar o repositório

O repositório do Arminda é privado. A forma recomendada é **deploy
key SSH dedicada** (read-only, escopo só desse repo):

```bash
# (na VPS, já como root)
ssh-keygen -t ed25519 -f ~/.ssh/arminda_deploy -N '' -C 'arminda-vps-deploy'
cat ~/.ssh/arminda_deploy.pub
# Cole essa chave em:
# github.com/darlanvelozo/Arminda_Software/settings/keys → Add deploy key
# (DEIXE "Allow write access" DESMARCADO)

# Configura SSH pra usar essa chave ao falar com github.com
cat >> ~/.ssh/config <<'EOF'
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/arminda_deploy
    IdentitiesOnly yes
EOF

# Testa
ssh -T git@github.com  # deve responder "Hi darlanvelozo/Arminda_Software!"

# Clona
mkdir -p /opt/arminda
git clone git@github.com:darlanvelozo/Arminda_Software.git /opt/arminda
```

---

## Passo 3 — Setup automatizado

```bash
sudo /opt/arminda/deploy/setup-producao.sh
```

Esse script é **idempotente** (pode rodar várias vezes). Ele:

1. Atualiza pacotes do sistema + instala dependências
   (`python3-venv`, `build-essential`, `libpq-dev`, `nginx`, `certbot`).
2. Cria usuário OS `arminda` (sem login por senha, com chave SSH
   herdada do root).
3. Cria role PostgreSQL `arminda` e database `arminda_prod`. Senha do
   banco é **gerada e gravada em `/opt/arminda/.env`**
   (modo 600, owner `arminda:arminda`).
4. Cria virtualenv em `/opt/arminda/backend/.venv` e instala
   `requirements.txt`.
5. Aplica migrations (`manage.py migrate`).
6. Coleta arquivos estáticos (`collectstatic`).
7. Instala e habilita `arminda-backend.service` (systemd).
8. Instala vhost Nginx `arminda.site.conf` (HTTP) e recarrega o Nginx.

Ao final:

- `systemctl status arminda-backend` → mostra rodando.
- `curl -sf http://127.0.0.1:8001/api/health/` → `{"status":"ok",...}`
- `curl -sf http://arminda.site/api/health/` → idem (via Nginx, ainda
  sem TLS).

---

## Passo 4 — HTTPS (Certbot + Let's Encrypt)

Antes de rodar o `certbot`, garanta que:

- O DNS de `arminda.site` aponta para o IP da VPS (`dig arminda.site +short`).
- Nginx está respondendo em `http://arminda.site/.well-known/acme-challenge/test`
  (200 ou 404 — não 502).

```bash
sudo certbot --nginx \
  -d arminda.site \
  -d www.arminda.site \
  --redirect \
  --agree-tos \
  --email darlanveloso14@gmail.com
```

Isso reescreve `/etc/nginx/sites-available/arminda.site.conf`
adicionando os blocos `listen 443 ssl` e o redirect 80→443. O
Certbot configura **renovação automática** (timer systemd):

```bash
systemctl status certbot.timer
sudo certbot renew --dry-run  # confere
```

---

## Passo 5 — Superuser e dados iniciais

```bash
sudo -iu arminda
cd /opt/arminda/backend
source .venv/bin/activate
python manage.py createsuperuser
# Se quiser dados de demo (Smoke Test município com 23 servidores):
python manage.py shell < /opt/arminda/seed-demo.py
```

---

## Passo 6 — Subir o frontend

O build do Vite **NÃO roda na VPS** (1 vCPU + 4 GB RAM seria
desperdício; build local é instantâneo). Fluxo:

```bash
# (no laptop)
cd frontend
cp deploy/env/frontend.env.production.example .env.production  # 1 vez
npm run build
rsync -avz --delete dist/ arminda-vps:/opt/arminda/frontend-dist/
```

Não precisa restart de nada — Nginx serve direto.

---

## Releases (rotina contínua)

Toda vez que entra código novo na `main`:

```bash
# (no laptop)
git push origin main

# (na VPS)
sudo /opt/arminda/deploy/deploy.sh
# - git pull
# - pip install (se requirements mudou)
# - manage.py migrate
# - collectstatic
# - systemctl restart arminda-backend
# - smoke em /api/health/
```

Esse script falha de forma explícita (`set -e`) e faz o smoke do
healthcheck no fim. Se falhar, status anterior continua válido
porque migrations e static foram aplicados, mas o restart pode ter
parado o serviço — em caso de erro, ver `journalctl -u arminda-backend -n 50`.

### Rollback rápido

```bash
# (na VPS)
cd /opt/arminda
sudo -u arminda git log --oneline -10           # ache o último bom
sudo -u arminda git checkout <SHA>
sudo /opt/arminda/deploy/deploy.sh --no-restart
# (se a versão antiga não precisa de migrations novas, pula migrate)
sudo systemctl restart arminda-backend
```

Para um rollback que envolve **reverter migrations**, é mais
complicado — sempre prefira fazer migrations **idempotentes e
retrocompatíveis** durante o desenvolvimento.

---

## Operação no dia-a-dia

| O que | Comando |
|---|---|
| Logs do backend (live) | `journalctl -u arminda-backend -f` |
| Status do backend | `systemctl status arminda-backend` |
| Reload do Nginx | `sudo nginx -t && sudo systemctl reload nginx` |
| Healthcheck público | `curl -sf https://arminda.site/api/health/` |
| Conectar no banco | `sudo -u postgres psql arminda_prod` |
| Backup do banco | `sudo -u postgres pg_dump -Fc arminda_prod > arminda_$(date +%F).dump` |
| Restaurar dump | `sudo -u postgres pg_restore -d arminda_prod arminda_*.dump` |
| Conferir certificado SSL | `sudo certbot certificates` |
| Renovar SSL manualmente | `sudo certbot renew` |

---

## Postgres compartilhado com outras aplicações

Se a VPS já tem outras aplicações usando o Postgres (ex.: `biazul`):

- O Arminda **não toca em databases ou roles** de outras aplicações.
- Compartilha as configurações globais do `postgresql.conf` —
  cuidado se quiser tunar `shared_buffers`, `work_mem`, etc.
- Para uma carga maior, ideal é separar as instâncias (porta
  diferente ou banco gerenciado).

---

## Monitoramento (próximos passos — Bloco 6+)

A primeira instância de produção **ainda não** tem monitoramento
externo. O que existe:

- `journalctl -u arminda-backend` (logs locais)
- `/health/` e `/status/` (endpoints públicos)
- Fail2ban no SSH (já instalado pela Hostinger)
- Monarx agent (antimalware, instalado pela Hostinger)

Backlog (Bloco 6):

- [ ] Cron + script que dispara `pg_dump` diário pra outro disco
- [ ] Healthcheck externo (UptimeRobot, BetterStack ou similar)
- [ ] Grafana/Prometheus se a carga crescer
- [ ] Alertas via WhatsApp/e-mail quando `/api/health/` retornar 503
  por mais de 1 minuto

---

## Limitações conhecidas da v0.8.1

- Container Docker do importador Fiorilli (`apps.imports.adapters.firebird`)
  **não roda em produção** ainda — o importador é desenhado pra ser
  executado em ambiente isolado (CI ou laptop com Docker), nunca na VPS
  de produção (PII em trânsito).
- Frontend build é manual (rsync) — não há CI/CD automático ainda.
  Backlog: GitHub Action com `npm run build` + `rsync` no push pra `main`.
- Sem CDN — Nginx serve direto. Ok pra cargas atuais; revisar a partir
  de 100+ municípios.

---

## Convivência com outras aplicações na VPS

A primeira VPS da Hostinger já tinha a aplicação `biazul` rodando
quando o Arminda subiu. O cuidado tomado:

- Postgres compartilhado, mas com role/database **separados**.
- Nginx compartilhado, mas com vhost (`server_name arminda.site`)
  **separado**.
- Arminda em `/opt/arminda/`, biazul em `/opt/biazul/`.
- Backend Arminda em **8001** (8000 está reservada para biazul).
- Nada de `systemctl restart nginx` cego — sempre `nginx -t && reload`.

Para qualquer mudança que possa afetar a outra aplicação (pacote do
sistema, configuração global do Postgres ou do Nginx), **avisar
antes**.
