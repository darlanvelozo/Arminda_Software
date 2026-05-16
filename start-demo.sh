#!/usr/bin/env bash
#
# start-demo.sh — sobe a demo do Arminda em modo "production-like" no notebook.
#
# Esta branch (demo) é uma fotografia da v0.6.1-demo com dados curados pra
# apresentação a stakeholders. Não tem hot-reload, não tem auto-deploy.
#
# Estrutura:
#   - gunicorn (Django) em 127.0.0.1:8000 com 2 workers
#   - vite preview servindo build estático em 127.0.0.1:4173 (proxy /api → 8000)
#   - cloudflared expõe 4173 publicamente via URL grátis
#
# Por padrão roda em foreground com supervisão simples (auto-restart
# se algum subprocesso cair). Ideal para `tmux new -s demo`.
#
# Uso:
#   ./start-demo.sh           # sobe e supervisiona em foreground
#   ./start-demo.sh start     # idem ao default
#   ./start-demo.sh stop      # mata processos da demo
#   ./start-demo.sh status    # mostra estado + URL pública
#   ./start-demo.sh restart   # stop + start
#   ./start-demo.sh logs      # tail -f dos logs combinados
#
# Variáveis de ambiente opcionais:
#   DEMO_PORT_BACKEND=8000
#   DEMO_PORT_FRONTEND=4173
#   DEMO_WORKERS=2            (gunicorn workers)
#   DEMO_NO_TUNNEL=1          (não sobe cloudflared, só local)
#

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOGDIR="$ROOT/.demo-logs"
RUNDIR="$ROOT/.demo-run"
mkdir -p "$LOGDIR" "$RUNDIR"

PID_DJANGO="$RUNDIR/django.pid"
PID_VITE="$RUNDIR/vite.pid"
PID_TUNNEL="$RUNDIR/tunnel.pid"
URL_FILE="$RUNDIR/public-url.txt"

: "${DEMO_PORT_BACKEND:=8000}"
: "${DEMO_PORT_FRONTEND:=4173}"
: "${DEMO_WORKERS:=2}"
: "${DEMO_NO_TUNNEL:=0}"

# Settings dedicado da demo (sem HTTPS redirect, ALLOWED_HOSTS=*)
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-arminda.settings.demo}"
export DATABASE_URL="${DATABASE_URL:-postgres://$(whoami)@localhost:5432/arminda_demo}"
export DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY:-demo-secret-key-nao-use-em-prod-arminda-2026}"

# ============================================================
# Helpers
# ============================================================
log() { echo "[$(date +%H:%M:%S)] $*"; }
ok() { echo "  ✓ $*"; }
err() { echo "  ✗ $*" >&2; }

is_running() {
  local pidfile="$1"
  [[ -f "$pidfile" ]] && kill -0 "$(cat "$pidfile" 2>/dev/null)" 2>/dev/null
}

kill_pidfile() {
  local pidfile="$1" name="$2"
  if [[ -f "$pidfile" ]]; then
    local pid
    pid="$(cat "$pidfile" 2>/dev/null || true)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      sleep 1
      kill -9 "$pid" 2>/dev/null || true
      ok "parado: $name (pid $pid)"
    fi
    rm -f "$pidfile"
  fi
}

# Rotação simples: se log passar de 10MB, move pra .old
rotate_log() {
  local f="$1"
  if [[ -f "$f" ]] && [[ "$(stat -c%s "$f" 2>/dev/null || echo 0)" -gt 10485760 ]]; then
    mv "$f" "$f.old"
  fi
}

# ============================================================
# Comandos
# ============================================================
cmd_stop() {
  log "Parando demo..."
  kill_pidfile "$PID_TUNNEL" "cloudflared"
  kill_pidfile "$PID_VITE"   "vite preview"
  kill_pidfile "$PID_DJANGO" "gunicorn (django)"
  pkill -f "cloudflared tunnel.*localhost:${DEMO_PORT_FRONTEND}" 2>/dev/null || true
  pkill -f "vite preview.*${DEMO_PORT_FRONTEND}" 2>/dev/null || true
  pkill -f "gunicorn.*arminda" 2>/dev/null || true
  rm -f "$URL_FILE"
  log "✓ Demo derrubada."
}

cmd_status() {
  echo ""
  echo "═══════════════════════════════════════════════════"
  echo "  Status da Demo Arminda"
  echo "═══════════════════════════════════════════════════"
  if is_running "$PID_DJANGO"; then echo "  django:     🟢 rodando (pid $(cat $PID_DJANGO))"; else echo "  django:     🔴 parado"; fi
  if is_running "$PID_VITE";   then echo "  vite:       🟢 rodando (pid $(cat $PID_VITE))";   else echo "  vite:       🔴 parado"; fi
  if is_running "$PID_TUNNEL"; then echo "  tunnel:     🟢 rodando (pid $(cat $PID_TUNNEL))"; else echo "  tunnel:     🔴 parado"; fi
  echo ""
  if [[ -f "$URL_FILE" ]]; then
    echo "  URL pública: $(cat "$URL_FILE")"
  fi
  echo "  URL local:   http://localhost:${DEMO_PORT_FRONTEND}"
  echo "═══════════════════════════════════════════════════"
}

cmd_logs() {
  tail -n 50 -f "$LOGDIR/django.log" "$LOGDIR/vite.log" "$LOGDIR/tunnel.log" 2>/dev/null
}

cmd_start() {
  # Sanity checks
  if [[ ! -d "$ROOT/backend/.venv" ]]; then
    err "backend/.venv não existe. Rode: ./setup-demo.sh"
    exit 1
  fi
  if [[ ! -d "$ROOT/frontend/dist" ]]; then
    err "frontend/dist/ não existe. Rode: cd frontend && npm run build"
    exit 1
  fi
  if [[ "$DEMO_NO_TUNNEL" -ne 1 ]] && ! command -v cloudflared &>/dev/null; then
    err "cloudflared não instalado. Veja DEMO.md ou use DEMO_NO_TUNNEL=1"
    exit 1
  fi

  # Limpa run anterior
  cmd_stop >/dev/null 2>&1 || true

  # Rotaciona logs e zera o do tunnel (URL muda toda execução)
  rotate_log "$LOGDIR/django.log"
  rotate_log "$LOGDIR/vite.log"
  rotate_log "$LOGDIR/tunnel.log"
  : > "$LOGDIR/tunnel.log"

  # ---------- Django via gunicorn ----------
  log "Subindo Django via gunicorn em :${DEMO_PORT_BACKEND} (${DEMO_WORKERS} workers)..."
  cd "$ROOT/backend"
  # shellcheck disable=SC1091
  source .venv/bin/activate
  # gunicorn (preferido para prod-like); fallback runserver se ainda não tiver
  if ! python -c "import gunicorn" 2>/dev/null; then
    log "Instalando gunicorn (uma vez)..."
    pip install -q gunicorn
  fi
  nohup gunicorn arminda.wsgi:application \
    --bind "127.0.0.1:${DEMO_PORT_BACKEND}" \
    --workers "${DEMO_WORKERS}" \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    >>"$LOGDIR/django.log" 2>&1 &
  echo $! > "$PID_DJANGO"
  deactivate
  ok "django pid $(cat $PID_DJANGO)"

  # ---------- Vite preview ----------
  log "Subindo vite preview em :${DEMO_PORT_FRONTEND}..."
  cd "$ROOT/frontend"
  nohup npm run preview -- --port "${DEMO_PORT_FRONTEND}" --host 127.0.0.1 --strictPort \
    >>"$LOGDIR/vite.log" 2>&1 &
  echo $! > "$PID_VITE"
  ok "vite pid $(cat $PID_VITE)"

  # ---------- Esperar prontidão ----------
  log "Aguardando serviços responderem..."
  local pronto=0
  for _ in $(seq 1 60); do
    if curl -sf "http://localhost:${DEMO_PORT_BACKEND}/admin/login/" >/dev/null \
       && curl -sf "http://localhost:${DEMO_PORT_FRONTEND}/" >/dev/null; then
      pronto=1
      break
    fi
    sleep 1
  done
  if [[ "$pronto" -ne 1 ]]; then
    err "serviços não responderam em 60s — verifique logs em $LOGDIR/"
    exit 1
  fi
  ok "backend + frontend prontos"

  # ---------- Cloudflare Tunnel ----------
  local public_url=""
  if [[ "$DEMO_NO_TUNNEL" -ne 1 ]]; then
    log "Subindo cloudflared (URL pública)..."
    cd "$ROOT"
    nohup cloudflared tunnel --no-autoupdate \
      --url "http://localhost:${DEMO_PORT_FRONTEND}" \
      >>"$LOGDIR/tunnel.log" 2>&1 &
    echo $! > "$PID_TUNNEL"
    ok "cloudflared pid $(cat $PID_TUNNEL)"

    # Espera a URL aparecer (pega a primeira do log fresco)
    for _ in $(seq 1 60); do
      public_url=$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOGDIR/tunnel.log" | head -1 || true)
      [[ -n "$public_url" ]] && break
      sleep 1
    done
    if [[ -n "$public_url" ]]; then
      echo "$public_url" > "$URL_FILE"
      ok "URL pública: $public_url"
    else
      err "URL pública não detectada — veja $LOGDIR/tunnel.log"
    fi
  fi

  # ---------- Resumo ----------
  echo ""
  echo "═══════════════════════════════════════════════════"
  echo "  🟢 Demo Arminda — v0.6.1-demo"
  echo "═══════════════════════════════════════════════════"
  [[ -n "$public_url" ]] && echo "  URL pública: $public_url"
  echo "  URL local:   http://localhost:${DEMO_PORT_FRONTEND}"
  echo ""
  echo "  Credenciais para o cliente:"
  echo "    e-mail:    smoke-admin@arminda.test"
  echo "    senha:     arminda-smoke-2026"
  echo "    município: Smoke Test (MA)"
  echo ""
  echo "  Comandos:"
  echo "    status:    ./start-demo.sh status"
  echo "    logs:      ./start-demo.sh logs"
  echo "    parar:     ./start-demo.sh stop"
  echo "═══════════════════════════════════════════════════"
}

# ============================================================
# Supervisor — auto-restart se algum subprocesso cair
# Ativado quando rodando em foreground sem flag --no-supervisor
# ============================================================
supervisor_loop() {
  log "Supervisor ativo (auto-restart em caso de queda). Ctrl+C derruba tudo."
  trap 'log "Sinal recebido — parando..."; cmd_stop; exit 0' INT TERM

  while true; do
    sleep 10

    # Django
    if ! is_running "$PID_DJANGO"; then
      log "⚠ django caiu — reiniciando..."
      cd "$ROOT/backend"
      # shellcheck disable=SC1091
      source .venv/bin/activate
      nohup gunicorn arminda.wsgi:application \
        --bind "127.0.0.1:${DEMO_PORT_BACKEND}" \
        --workers "${DEMO_WORKERS}" \
        --access-logfile - --error-logfile - --log-level info \
        >>"$LOGDIR/django.log" 2>&1 &
      echo $! > "$PID_DJANGO"
      deactivate
    fi

    # Vite
    if ! is_running "$PID_VITE"; then
      log "⚠ vite caiu — reiniciando..."
      cd "$ROOT/frontend"
      nohup npm run preview -- --port "${DEMO_PORT_FRONTEND}" --host 127.0.0.1 --strictPort \
        >>"$LOGDIR/vite.log" 2>&1 &
      echo $! > "$PID_VITE"
    fi

    # Tunnel
    if [[ "$DEMO_NO_TUNNEL" -ne 1 ]] && ! is_running "$PID_TUNNEL"; then
      log "⚠ cloudflared caiu — reiniciando..."
      cd "$ROOT"
      nohup cloudflared tunnel --no-autoupdate \
        --url "http://localhost:${DEMO_PORT_FRONTEND}" \
        >>"$LOGDIR/tunnel.log" 2>&1 &
      echo $! > "$PID_TUNNEL"
      sleep 5
      local new_url
      new_url=$(grep -Eom1 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOGDIR/tunnel.log" | tail -1 || true)
      if [[ -n "$new_url" ]] && [[ "$new_url" != "$(cat "$URL_FILE" 2>/dev/null)" ]]; then
        echo "$new_url" > "$URL_FILE"
        log "→ nova URL pública: $new_url"
      fi
    fi
  done
}

# ============================================================
# Roteamento de comandos
# ============================================================
case "${1:-start}" in
  start)
    cmd_start
    # Se chamado interativamente OU sem --detach, entra no supervisor
    if [[ "${2:-}" != "--detach" ]]; then
      supervisor_loop
    fi
    ;;
  stop)    cmd_stop ;;
  status)  cmd_status ;;
  restart) cmd_stop; cmd_start ;;
  logs)    cmd_logs ;;
  *)
    echo "Uso: $0 {start|stop|status|restart|logs}"
    exit 1
    ;;
esac
