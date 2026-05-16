#!/usr/bin/env bash
#
# start-demo.sh — sobe a demo do Arminda exposta via Cloudflare Tunnel.
#
# Esta branch (demo) é uma fotografia da v0.6.1 (Bloco 2.2 entregue) com
# dados curados pra apresentação. Não tem hot-reload — é build de produção.
#
# Estrutura:
#   - Django 8000 (banco local Postgres + tenant `smoke_arminda` populado)
#   - Vite preview 4173 servindo o build estático com proxy reverso
#   - Cloudflared expõe 4173 para internet via URL pública gratuita
#
# Pré-requisitos:
#   - cloudflared instalado (https://github.com/cloudflare/cloudflared)
#   - backend/.venv pronto (pip install -r backend/requirements.txt)
#   - frontend/dist/ buildado (npm run build em frontend/)
#   - banco local com tenant smoke_arminda populado
#
# Uso:
#   ./start-demo.sh         # sobe tudo
#   ./start-demo.sh stop    # mata processos
#

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOGDIR="$ROOT/.demo-logs"
mkdir -p "$LOGDIR"

PID_DJANGO="$LOGDIR/django.pid"
PID_VITE="$LOGDIR/vite.pid"
PID_TUNNEL="$LOGDIR/tunnel.pid"

cmd_stop() {
  for pidfile in "$PID_DJANGO" "$PID_VITE" "$PID_TUNNEL"; do
    if [[ -f "$pidfile" ]]; then
      pid=$(cat "$pidfile")
      if kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null || true
        echo "  parado: $(basename "$pidfile" .pid) ($pid)"
      fi
      rm -f "$pidfile"
    fi
  done
  pkill -f "manage.py runserver" 2>/dev/null || true
  pkill -f "vite preview" 2>/dev/null || true
  pkill -f "cloudflared tunnel" 2>/dev/null || true
  echo "✓ Demo derrubada."
}

if [[ "${1:-}" == "stop" ]]; then
  cmd_stop
  exit 0
fi

# Sanity checks
if ! command -v cloudflared &>/dev/null; then
  echo "✗ cloudflared não está instalado."
  echo "  Instale: https://github.com/cloudflare/cloudflared/releases"
  echo "  Ou: sudo apt install cloudflared (após adicionar repo)"
  exit 1
fi
if [[ ! -d "$ROOT/backend/.venv" ]]; then
  echo "✗ Backend venv não encontrada em backend/.venv"
  exit 1
fi
if [[ ! -d "$ROOT/frontend/dist" ]]; then
  echo "✗ Build do frontend não encontrado em frontend/dist/"
  echo "  Rode antes: cd frontend && npm run build"
  exit 1
fi

# Limpa qualquer execução anterior
cmd_stop >/dev/null 2>&1 || true

echo "→ Subindo backend Django (8000)..."
cd "$ROOT/backend"
# shellcheck disable=SC1091
source .venv/bin/activate
nohup python manage.py runserver 0.0.0.0:8000 \
  >"$LOGDIR/django.log" 2>&1 &
echo $! > "$PID_DJANGO"

echo "→ Subindo Vite preview (4173)..."
cd "$ROOT/frontend"
nohup npm run preview -- --port 4173 --host 127.0.0.1 \
  >"$LOGDIR/vite.log" 2>&1 &
echo $! > "$PID_VITE"

echo "→ Aguardando serviços responderem..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/admin/login/ >/dev/null \
     && curl -sf http://localhost:4173/ >/dev/null; then
    echo "  ✓ backend + frontend prontos"
    break
  fi
  sleep 1
done

echo "→ Subindo Cloudflare Tunnel (URL pública dinâmica)..."
cd "$ROOT"
nohup cloudflared tunnel --no-autoupdate --url http://localhost:4173 \
  >"$LOGDIR/tunnel.log" 2>&1 &
echo $! > "$PID_TUNNEL"

# Espera o cloudflared imprimir a URL
echo "→ Aguardando URL pública..."
PUBLIC_URL=""
for i in $(seq 1 30); do
  if grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOGDIR/tunnel.log" \
     | head -1 > "$LOGDIR/url.txt"; then
    PUBLIC_URL=$(cat "$LOGDIR/url.txt" 2>/dev/null || true)
    if [[ -n "$PUBLIC_URL" ]]; then break; fi
  fi
  sleep 1
done

echo ""
echo "=================================================="
echo " 🟢 Demo Arminda — v0.6.1-demo"
echo "=================================================="
if [[ -n "$PUBLIC_URL" ]]; then
  echo "  URL pública:  $PUBLIC_URL"
else
  echo "  URL pública: (verifique manualmente em $LOGDIR/tunnel.log)"
fi
echo "  URL local:    http://localhost:4173"
echo ""
echo "  Credenciais:"
echo "    e-mail:    smoke-admin@arminda.test"
echo "    senha:     arminda-smoke-2026"
echo "    município: Smoke Test (MA)"
echo ""
echo "  Logs:"
echo "    django:     $LOGDIR/django.log"
echo "    vite:       $LOGDIR/vite.log"
echo "    tunnel:     $LOGDIR/tunnel.log"
echo ""
echo "  Parar:        ./start-demo.sh stop"
echo "=================================================="
