#!/usr/bin/env bash
#
# deploy.sh — release contínuo do Arminda na VPS de produção.
#
# Sem reboots. Sem refazer setup. Apenas:
#   1. git pull origin <branch> (default: main)
#   2. pip install -r requirements.txt (caso tenha mudado)
#   3. python manage.py migrate (caso tenha migration nova)
#   4. python manage.py collectstatic --noinput
#   5. systemctl restart arminda-backend
#   6. Reload do Nginx (caso o vhost tenha mudado)
#   7. Smoke local em /api/health/
#
# Pra mudanças no frontend, o release é separado (rsync do dist/
# buildado no laptop) — ver docs/DEPLOY_PRODUCAO.md.
#
# Uso (na VPS, como root):
#   /opt/arminda/deploy/deploy.sh                    # main
#   /opt/arminda/deploy/deploy.sh develop            # outra branch
#   /opt/arminda/deploy/deploy.sh main --no-restart  # só pull + migrate
#
# É seguro rodar mesmo sem mudanças (idempotente).

set -euo pipefail

if [[ "$EUID" -ne 0 ]]; then
  echo "Execute como root."
  exit 1
fi

: "${ARMINDA_HOME:=/opt/arminda}"
: "${ARMINDA_USER:=arminda}"
: "${ARMINDA_PORT:=8001}"

BRANCH="${1:-main}"
NO_RESTART=0
for arg in "$@"; do
  [[ "$arg" == "--no-restart" ]] && NO_RESTART=1
done

step() { echo ""; echo "▶ $1"; }
ok()   { echo "  ✓ $1"; }

cd "$ARMINDA_HOME"

step "git pull origin $BRANCH"
sudo -u "$ARMINDA_USER" git fetch origin
sudo -u "$ARMINDA_USER" git checkout "$BRANCH"
sudo -u "$ARMINDA_USER" git pull --ff-only origin "$BRANCH"
CURRENT=$(sudo -u "$ARMINDA_USER" git rev-parse --short HEAD)
ok "HEAD: $CURRENT"

step "pip install (rápido — só verifica delta)"
sudo -u "$ARMINDA_USER" .venv/bin/pip install -q -r backend/requirements.txt
ok "ok"

step "migrate"
cd backend
sudo -u "$ARMINDA_USER" .venv/bin/python manage.py migrate --noinput
ok "ok"

step "collectstatic"
sudo -u "$ARMINDA_USER" .venv/bin/python manage.py collectstatic --noinput >/dev/null
ok "ok"

if [[ "$NO_RESTART" -eq 0 ]]; then
  step "systemctl restart arminda-backend"
  systemctl restart arminda-backend.service
  sleep 2
  if systemctl is-active --quiet arminda-backend.service; then
    ok "rodando"
  else
    echo "  ✗ falhou. Veja: journalctl -u arminda-backend -n 50"
    exit 1
  fi
else
  ok "restart pulado (--no-restart)"
fi

step "Healthcheck"
HEALTH=$(curl -sf -m 5 "http://127.0.0.1:$ARMINDA_PORT/api/health/" || echo "FAIL")
if [[ "$HEALTH" == *"\"status\":\"ok\""* ]]; then
  ok "/api/health/ → ok"
else
  echo "  ✗ healthcheck falhou: $HEALTH"
  exit 1
fi

echo ""
echo "════════════════════════════════════════════"
echo "  ✅ Deploy concluído. HEAD: $CURRENT"
echo "════════════════════════════════════════════"
