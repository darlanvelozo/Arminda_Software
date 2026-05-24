# `deploy/` — infraestrutura de produção

Tudo o que vai pra VPS para subir o Arminda em **arminda.site**.

Documentação operacional completa está em
[`docs/DEPLOY_PRODUCAO.md`](../docs/DEPLOY_PRODUCAO.md). Este README é
só o mapa do diretório.

## Arquivos

| Caminho | O que é |
|---|---|
| `setup-producao.sh` | Bootstrap **idempotente** — usuário OS, banco, venv, migrations, systemd, Nginx. Roda 1 vez na VPS nova. |
| `deploy.sh` | Release **contínuo** — `git pull` + migrate + collectstatic + restart. Roda a cada nova versão do backend. |
| `systemd/arminda-backend.service` | Unit do `gunicorn` ouvindo em 127.0.0.1:8001, com hardening (`ProtectSystem`, `NoNewPrivileges`, etc.). |
| `nginx/arminda.site.conf` | Vhost com SPA + proxy `/api/` + admin + static + healthcheck. Sem TLS — o certbot adiciona depois. |
| `env/backend.env.example` | Template do `.env` do backend (segredos preenchidos no `setup-producao.sh`). |
| `env/frontend.env.production.example` | Template do `.env.production` do frontend (`VITE_API_BASE_URL`). |

## Fluxo

### Primeira vez numa VPS

```bash
# Na VPS, como root, com o repo clonado em /opt/arminda
sudo /opt/arminda/deploy/setup-producao.sh
# Depois, configurar HTTPS:
sudo certbot --nginx -d arminda.site -d www.arminda.site --redirect
```

### Release contínuo

```bash
# No laptop:
git push origin main

# Na VPS, como root:
sudo /opt/arminda/deploy/deploy.sh
```

### Atualizar frontend

```bash
# Laptop:
cd frontend
npm run build
rsync -avz --delete dist/ arminda-vps:/opt/arminda/frontend-dist/
```

## O que **não** está aqui

- **Segredos** (senha do banco, SECRET_KEY) — gerados na hora do `setup`, ficam só em `/opt/arminda/backend/.env` na VPS.
- **Build do frontend** (`dist/`) — sempre regerado localmente, nunca commitado.
- **Certificado SSL** — gerado pelo Certbot, fora do repo.

Mais detalhes em [`docs/DEPLOY_PRODUCAO.md`](../docs/DEPLOY_PRODUCAO.md).
