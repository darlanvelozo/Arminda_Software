#!/usr/bin/env bash
#
# backup-db.sh — backup diário do banco de produção do Arminda.
#
# - Lê DATABASE_URL do .env de produção (pg_dump entende a URL direto).
# - Formato custom (-Fc): restaura com pg_restore, comprimido nativamente.
# - Retenção: mantém os últimos N dias (default 14).
# - Também copia o .env (contém ESOCIAL_CERT_KEY — perder a chave = perder o
#   cofre de certificados) com permissão restrita.
#
# Instalação (como root):
#   install -m 750 /opt/arminda/deploy/backup-db.sh /etc/cron.daily/arminda-backup
#
set -euo pipefail

: "${ARMINDA_HOME:=/opt/arminda}"
: "${BACKUP_DIR:=/opt/arminda-backups}"
: "${RETENCAO_DIAS:=14}"

DATABASE_URL=$(grep -E '^DATABASE_URL=' "$ARMINDA_HOME/.env" | cut -d= -f2-)
if [[ -z "$DATABASE_URL" ]]; then
  echo "DATABASE_URL não encontrada em $ARMINDA_HOME/.env" >&2
  exit 1
fi

install -d -m 700 "$BACKUP_DIR"
CARIMBO=$(date +%Y%m%d-%H%M%S)

pg_dump --dbname="$DATABASE_URL" -Fc -f "$BACKUP_DIR/arminda-$CARIMBO.dump"
chmod 600 "$BACKUP_DIR/arminda-$CARIMBO.dump"

# .env (segredos, incl. chave do cofre) — cópia com data
install -m 600 "$ARMINDA_HOME/.env" "$BACKUP_DIR/env-$CARIMBO"

# Retenção
find "$BACKUP_DIR" -name 'arminda-*.dump' -mtime "+$RETENCAO_DIAS" -delete
find "$BACKUP_DIR" -name 'env-*' -mtime "+$RETENCAO_DIAS" -delete

echo "backup ok: $BACKUP_DIR/arminda-$CARIMBO.dump ($(du -h "$BACKUP_DIR/arminda-$CARIMBO.dump" | cut -f1))"
