#!/usr/bin/env bash
#
# setup-demo.sh — instalação inicial da demo do Arminda em uma máquina nova.
#
# Idempotente: pode rodar quantas vezes precisar — só reaplica os passos
# que ainda não foram feitos.
#
# O que faz:
#   1. Verifica dependências do sistema (python 3.12+, node 20+, postgres, cloudflared)
#   2. Cria/recria virtualenv do backend e instala requirements
#   3. Cria banco PostgreSQL `arminda_demo` se não existir
#   4. Aplica migrations
#   5. Cria superuser admin@arminda.test (se ainda não existir)
#   6. Cria tenant `smoke_arminda` + Domain
#   7. Cria usuário smoke-admin@arminda.test com papel admin_municipio
#   8. Popula dados com seed-demo.py (23 servidores, 11 rubricas, 3 folhas calculadas)
#   9. Instala deps do frontend e gera build de produção
#
# Uso:
#   ./setup-demo.sh                # roda tudo
#   ./setup-demo.sh --skip-build   # pula `npm run build` (já buildado)
#

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

SKIP_BUILD=0
for arg in "$@"; do
  case "$arg" in
    --skip-build) SKIP_BUILD=1 ;;
    *) echo "Flag desconhecida: $arg"; exit 1 ;;
  esac
done

# ============================================================
# Configuração (pode sobrescrever via env)
# ============================================================
: "${DEMO_DB_NAME:=arminda_demo}"
: "${DEMO_DB_USER:=$(whoami)}"
: "${DEMO_ADMIN_EMAIL:=admin@arminda.test}"
: "${DEMO_ADMIN_PASSWORD:=arminda-admin-2026}"
: "${DEMO_USER_EMAIL:=smoke-admin@arminda.test}"
: "${DEMO_USER_PASSWORD:=arminda-smoke-2026}"
: "${DEMO_TENANT_SCHEMA:=smoke_arminda}"
: "${DEMO_TENANT_NAME:=Smoke Test}"

step() {
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "▶ $1"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}
ok() { echo "  ✓ $1"; }

# ============================================================
# 1. Dependências do sistema
# ============================================================
step "Verificando dependências do sistema"

require() {
  if ! command -v "$1" &>/dev/null; then
    echo "  ✗ Falta: $1"
    echo "    Instale: $2"
    exit 1
  fi
  ok "$1 presente"
}

require python3 "sudo apt install python3.12 python3.12-venv"
require node "https://nodejs.org/  ou  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash - && sudo apt install nodejs"
require npm "vem com node"
require psql "sudo apt install postgresql"
require cloudflared "https://github.com/cloudflare/cloudflared/releases  ou  sudo apt install cloudflared"

# ============================================================
# 2. Backend venv + requirements
# ============================================================
step "Backend: virtualenv + requirements"

cd "$ROOT/backend"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  ok "venv criado em backend/.venv"
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
ok "requirements instalados"

# ============================================================
# 3. Banco PostgreSQL
# ============================================================
step "PostgreSQL: banco $DEMO_DB_NAME"

if ! psql -U "$DEMO_DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DEMO_DB_NAME"; then
  createdb -U "$DEMO_DB_USER" "$DEMO_DB_NAME"
  ok "banco criado: $DEMO_DB_NAME"
else
  ok "banco já existe: $DEMO_DB_NAME"
fi

# Exporta DATABASE_URL e settings da demo
export DATABASE_URL="postgres://${DEMO_DB_USER}@localhost:5432/${DEMO_DB_NAME}"
export DJANGO_SETTINGS_MODULE="arminda.settings.demo"
export DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY:-demo-secret-key-nao-use-em-prod-arminda-2026}"
echo "  → DATABASE_URL=$DATABASE_URL"
echo "  → DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"

# ============================================================
# 4. Migrations
# ============================================================
step "Django: migrate"
python manage.py migrate --noinput
ok "migrations aplicadas"

# ============================================================
# 5/6/7. Superuser + tenant + usuário demo
# ============================================================
step "Seed mínimo: superuser, tenant e usuário admin do município"

python manage.py shell -c "
from apps.core.models import Domain, Municipio, UsuarioMunicipioPapel
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import connection

User = get_user_model()
connection.set_schema_to_public()

# Superuser
su, criado = User.objects.update_or_create(
    email='${DEMO_ADMIN_EMAIL}',
    defaults={'nome_completo': 'Admin Demo', 'is_staff': True, 'is_superuser': True, 'is_active': True},
)
su.set_password('${DEMO_ADMIN_PASSWORD}')
su.save()
print(f'  superuser: {su.email} ({\"criado\" if criado else \"atualizado\"})')

# Tenant smoke
muni, criado = Municipio.objects.update_or_create(
    schema_name='${DEMO_TENANT_SCHEMA}',
    defaults={'nome': '${DEMO_TENANT_NAME}', 'uf': 'MA', 'codigo_ibge': '9999990'},
)
print(f'  tenant: {muni.schema_name} ({\"criado\" if criado else \"atualizado\"})')

Domain.objects.update_or_create(
    domain='${DEMO_TENANT_SCHEMA}.localhost',
    defaults={'tenant': muni, 'is_primary': True},
)

# Usuário demo + papel admin no município
u, criado = User.objects.update_or_create(
    email='${DEMO_USER_EMAIL}',
    defaults={'nome_completo': 'Smoke Admin', 'is_active': True, 'precisa_trocar_senha': False},
)
u.set_password('${DEMO_USER_PASSWORD}')
u.save()
print(f'  usuário demo: {u.email} ({\"criado\" if criado else \"atualizado\"})')

g = Group.objects.get(name='admin_municipio')
UsuarioMunicipioPapel.objects.update_or_create(usuario=u, municipio=muni, defaults={'grupo': g})
print('  papel admin_municipio atribuído')
"

# ============================================================
# 8. Seed completo (23 servidores, rubricas, folhas)
# ============================================================
step "Seed completo: 23 servidores, 11 rubricas, 3 folhas calculadas"
python manage.py shell < "$ROOT/seed-demo.py"
ok "seed concluído"

deactivate

# ============================================================
# 9. Frontend
# ============================================================
if [[ "$SKIP_BUILD" -eq 1 ]]; then
  step "Frontend: pulando build (--skip-build)"
else
  step "Frontend: install + build"
  cd "$ROOT/frontend"
  if [[ ! -d node_modules ]]; then
    npm install --silent
    ok "deps instaladas"
  fi
  npm run build
  ok "build em frontend/dist/"
fi

# ============================================================
# Resumo final
# ============================================================
echo ""
echo "═══════════════════════════════════════════════════"
echo "  ✅ Setup completo. Demo pronta pra subir."
echo "═══════════════════════════════════════════════════"
echo ""
echo "  Próximo passo:"
echo "    ./start-demo.sh"
echo ""
echo "  Credenciais de acesso ao sistema:"
echo "    e-mail:    $DEMO_USER_EMAIL"
echo "    senha:     $DEMO_USER_PASSWORD"
echo "    município: $DEMO_TENANT_NAME"
echo ""
echo "  Django admin (em http://localhost:8000/admin/):"
echo "    e-mail:    $DEMO_ADMIN_EMAIL"
echo "    senha:     $DEMO_ADMIN_PASSWORD"
echo ""
