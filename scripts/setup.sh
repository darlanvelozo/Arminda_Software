#!/usr/bin/env bash
# ============================================================
# Arminda — setup inicial de ambiente local
# ============================================================
# Roda:
#   1. Sobe Postgres + Redis (Docker Compose)
#   2. Configura venv e instala deps do backend
#   3. Roda migrations
#   4. Instala deps do frontend
#
# Uso: ./scripts/setup.sh
# ============================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

color() { printf "\033[%sm%s\033[0m\n" "$1" "$2"; }
info()  { color "1;34" "→ $*"; }
ok()    { color "1;32" "✓ $*"; }
warn()  { color "1;33" "! $*"; }

# ------------------------------------------------------------
# 0. Pré-requisitos
# ------------------------------------------------------------
info "Checando pré-requisitos…"
command -v docker >/dev/null   || { warn "Docker não encontrado"; exit 1; }
command -v python3 >/dev/null  || { warn "Python 3 não encontrado"; exit 1; }
command -v node >/dev/null     || { warn "Node não encontrado"; exit 1; }
ok "Docker, Python 3 e Node disponíveis"

# ------------------------------------------------------------
# 1. .env
# ------------------------------------------------------------
if [ ! -f .env ]; then
  info "Criando .env a partir de .env.example…"
  cp .env.example .env
  ok ".env criado — ajuste valores se necessário"
else
  ok ".env já existe"
fi

# ------------------------------------------------------------
# 2. Subir Postgres + Redis
# ------------------------------------------------------------
info "Subindo Postgres + Redis (docker compose)…"
docker compose up -d
ok "Containers no ar"

# ------------------------------------------------------------
# 3. Backend
# ------------------------------------------------------------
info "Configurando backend…"
cd backend

if [ ! -d .venv ]; then
  python3 -m venv .venv
  ok "venv criada"
fi

# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
ok "Dependências Python instaladas"

# Aguarda Postgres estar pronto
info "Aguardando Postgres…"
for i in {1..30}; do
  if docker exec arminda-postgres pg_isready -U arminda >/dev/null 2>&1; then
    ok "Postgres pronto"
    break
  fi
  sleep 1
done

python manage.py migrate
ok "Migrations aplicadas"

cd "$ROOT_DIR"

# ------------------------------------------------------------
# 4. Frontend
# ------------------------------------------------------------
info "Configurando frontend…"
cd frontend
npm install --silent
ok "Dependências Node instaladas"
cd "$ROOT_DIR"

# ------------------------------------------------------------
# Pronto
# ------------------------------------------------------------
echo ""
ok "Setup concluído!"
echo ""
echo "  Para iniciar o backend:"
echo "    cd backend && source .venv/bin/activate && python manage.py runserver"
echo ""
echo "  Para iniciar o frontend (em outro terminal):"
echo "    cd frontend && npm run dev"
echo ""
