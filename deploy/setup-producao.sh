#!/usr/bin/env bash
#
# setup-producao.sh — bootstrap idempotente do Arminda em uma VPS Ubuntu 24.04.
#
# Convive com OUTRAS aplicações na mesma máquina (ex.: biazul). Não
# reinicia serviços que não são da Arminda.
#
# Passos:
#   1. Atualiza pacotes do sistema + instala dependências (python venv,
#      build tools, libpq, rsync).
#   2. Cria usuário OS `arminda` (sem login por senha, com chave SSH
#      herdada do root).
#   3. Garante banco PostgreSQL `arminda_prod` + role `arminda` — senha
#      gerada uma vez e gravada em /opt/arminda/backend/.env (modo 600).
#   4. Cria diretórios /opt/arminda/{backend-static,frontend-dist,logs}.
#   5. Instala venv do backend + dependências + migrations.
#   6. Cria systemd unit /etc/systemd/system/arminda-backend.service e
#      habilita o serviço.
#   7. Instala vhost Nginx para arminda.site (HTTPS via Certbot é passo
#      manual subsequente — ver docs/DEPLOY_PRODUCAO.md).
#
# Uso:
#   sudo ./deploy/setup-producao.sh           # bootstrap completo
#   sudo ./deploy/setup-producao.sh --skip-system   # pula apt update/install
#   sudo ./deploy/setup-producao.sh --skip-nginx    # pula configuração de Nginx
#
# Requisitos:
#   - executar como root (ou via sudo)
#   - repositório já clonado em /opt/arminda
#   - DNS arminda.site apontando para o IP da VPS

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKIP_SYSTEM=0
SKIP_NGINX=0
for arg in "$@"; do
  case "$arg" in
    --skip-system) SKIP_SYSTEM=1 ;;
    --skip-nginx) SKIP_NGINX=1 ;;
    *) echo "Flag desconhecida: $arg"; exit 1 ;;
  esac
done

if [[ "$EUID" -ne 0 ]]; then
  echo "Execute como root (sudo)."
  exit 1
fi

: "${ARMINDA_HOME:=/opt/arminda}"
: "${ARMINDA_USER:=arminda}"
: "${ARMINDA_DB:=arminda_prod}"
: "${ARMINDA_DOMAIN:=arminda.site}"
: "${ARMINDA_PORT:=8001}"

step() { echo ""; echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; echo "▶ $1"; echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; }
ok()   { echo "  ✓ $1"; }
warn() { echo "  ⚠ $1"; }

# ============================================================
# 1. Sistema
# ============================================================
if [[ "$SKIP_SYSTEM" -eq 0 ]]; then
  step "Sistema: apt update + deps"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq \
    python3-venv python3-pip python3-dev build-essential libpq-dev rsync openssl \
    nginx certbot python3-certbot-nginx postgresql-client >/dev/null
  ok "deps instaladas"
else
  warn "etapa de sistema pulada (--skip-system)"
fi

# ============================================================
# 2. Usuário arminda
# ============================================================
step "Usuário OS '$ARMINDA_USER'"
if id "$ARMINDA_USER" >/dev/null 2>&1; then
  ok "já existe"
else
  adduser --disabled-password --gecos "" "$ARMINDA_USER"
  ok "criado"
fi

# Propaga chave SSH do root (se houver) para o usuário arminda
if [[ -f /root/.ssh/authorized_keys && ! -f "/home/$ARMINDA_USER/.ssh/authorized_keys" ]]; then
  mkdir -p "/home/$ARMINDA_USER/.ssh"
  cp /root/.ssh/authorized_keys "/home/$ARMINDA_USER/.ssh/authorized_keys"
  chown -R "$ARMINDA_USER:$ARMINDA_USER" "/home/$ARMINDA_USER/.ssh"
  chmod 700 "/home/$ARMINDA_USER/.ssh"
  chmod 600 "/home/$ARMINDA_USER/.ssh/authorized_keys"
  ok "chave SSH propagada"
fi

# ============================================================
# 3. PostgreSQL
# ============================================================
step "PostgreSQL: role + database"
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$ARMINDA_USER'" | grep -q 1; then
  DB_PASS=$(openssl rand -hex 24)
  sudo -u postgres psql -c "CREATE ROLE $ARMINDA_USER WITH LOGIN PASSWORD '$DB_PASS';"
  ok "role criada (senha gerada)"
  # guarda a senha para o passo 5 (.env)
  echo "$DB_PASS" > /tmp/.arminda_db_pass
  chmod 600 /tmp/.arminda_db_pass
else
  ok "role $ARMINDA_USER já existe"
fi

if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$ARMINDA_DB'" | grep -q 1; then
  sudo -u postgres psql -c "CREATE DATABASE $ARMINDA_DB OWNER $ARMINDA_USER;"
  ok "database $ARMINDA_DB criada"
else
  ok "database $ARMINDA_DB já existe"
fi
sudo -u postgres psql -qc "GRANT ALL PRIVILEGES ON DATABASE $ARMINDA_DB TO $ARMINDA_USER;"
sudo -u postgres psql -qc "ALTER ROLE $ARMINDA_USER CREATEDB;"  # django-tenants cria schemas

# ============================================================
# 4. Diretórios
# ============================================================
step "Diretórios"
mkdir -p "$ARMINDA_HOME"/{frontend-dist,logs,backend-static}
chown -R "$ARMINDA_USER:$ARMINDA_USER" "$ARMINDA_HOME"
ok "$ARMINDA_HOME pronto"

# ============================================================
# 5. Backend (venv + .env + migrations + collectstatic)
# ============================================================
step "Backend: venv + .env + migrations"

cd "$ARMINDA_HOME/backend"
if [[ ! -d .venv ]]; then
  sudo -u "$ARMINDA_USER" python3 -m venv .venv
  ok "venv criada"
fi
sudo -u "$ARMINDA_USER" .venv/bin/pip install -q -U pip wheel
sudo -u "$ARMINDA_USER" .venv/bin/pip install -q -r requirements.txt
ok "requirements instaladas"

# .env fica na RAIZ do projeto (ARMINDA_HOME), não em backend/.
# Convenção do settings/base.py: read_env(BASE_DIR.parent / ".env").
ENV_FILE="$ARMINDA_HOME/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  DB_PASS_FROM_FILE=$(cat /tmp/.arminda_db_pass 2>/dev/null || true)
  if [[ -z "$DB_PASS_FROM_FILE" ]]; then
    echo "  ✗ Não encontrei a senha do banco. Edite $ENV_FILE manualmente."
    DB_PASS_FROM_FILE="EDITE_AQUI"
  fi
  cat > "$ENV_FILE" <<EOF
DJANGO_SETTINGS_MODULE=arminda.settings.prod
DJANGO_SECRET_KEY=$(openssl rand -hex 32)
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=$ARMINDA_DOMAIN,www.$ARMINDA_DOMAIN
DJANGO_CSRF_TRUSTED_ORIGINS=https://$ARMINDA_DOMAIN,https://www.$ARMINDA_DOMAIN
CORS_ALLOWED_ORIGINS=https://$ARMINDA_DOMAIN,https://www.$ARMINDA_DOMAIN
DATABASE_URL=postgres://$ARMINDA_USER:$DB_PASS_FROM_FILE@127.0.0.1:5432/$ARMINDA_DB
EOF
  chown "$ARMINDA_USER:$ARMINDA_USER" "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  ok ".env criado em $ENV_FILE (modo 600)"
  rm -f /tmp/.arminda_db_pass
else
  ok ".env já existe em $ENV_FILE (preservado)"
fi

# Migrations + collectstatic
sudo -u "$ARMINDA_USER" .venv/bin/python manage.py migrate --noinput >/dev/null
ok "migrations aplicadas"
sudo -u "$ARMINDA_USER" .venv/bin/python manage.py collectstatic --noinput >/dev/null
ok "collectstatic concluído"

# ============================================================
# 6. systemd
# ============================================================
step "systemd unit"
install -m 644 "$ROOT/deploy/systemd/arminda-backend.service" \
  /etc/systemd/system/arminda-backend.service
systemctl daemon-reload
systemctl enable arminda-backend.service >/dev/null 2>&1
if systemctl is-active --quiet arminda-backend.service; then
  systemctl restart arminda-backend.service
  ok "service reiniciada"
else
  systemctl start arminda-backend.service
  ok "service iniciada"
fi
sleep 2
systemctl is-active --quiet arminda-backend.service && ok "rodando" || {
  warn "service não subiu — veja: journalctl -u arminda-backend -n 50"
  exit 1
}

# ============================================================
# 7. Nginx (opcional via --skip-nginx)
# ============================================================
if [[ "$SKIP_NGINX" -eq 0 ]]; then
  step "Nginx vhost"
  install -m 644 "$ROOT/deploy/nginx/arminda.site.conf" \
    /etc/nginx/sites-available/arminda.site.conf
  ln -sf /etc/nginx/sites-available/arminda.site.conf \
    /etc/nginx/sites-enabled/arminda.site.conf
  nginx -t
  systemctl reload nginx
  ok "vhost ativo (HTTP). Próximo passo: certbot (ver docs/DEPLOY_PRODUCAO.md)."
else
  warn "Nginx pulado (--skip-nginx)"
fi

echo ""
echo "═══════════════════════════════════════════════════"
echo "  ✅ Setup concluído."
echo "═══════════════════════════════════════════════════"
echo ""
echo "  Backend: systemctl status arminda-backend"
echo "  Logs:    journalctl -u arminda-backend -f"
echo "  Healthcheck: curl http://localhost:$ARMINDA_PORT/api/health/"
echo ""
echo "  Próximo passo (HTTPS):"
echo "    certbot --nginx -d $ARMINDA_DOMAIN -d www.$ARMINDA_DOMAIN --redirect"
echo ""
echo "  Frontend (do seu laptop):"
echo "    cd frontend && npm run build"
echo "    rsync -avz --delete dist/ arminda-vps:$ARMINDA_HOME/frontend-dist/"
echo ""
