#!/bin/bash
# ══════════════════════════════════════════════════════
#  Sisplan — Backup diário do banco de dados
#  Adicione ao cron: crontab -e
#  0 3 * * * bash /home/ubuntu/sisplan/deploy/3_backup_db.sh
# ══════════════════════════════════════════════════════
set -e

DB_PATH="/home/ubuntu/sisplan/data/banco_dados.db"
BACKUP_DIR="/home/ubuntu/sisplan/data/backups"
DATA=$(date +%Y-%m-%d_%H-%M)

mkdir -p "$BACKUP_DIR"

# Backup seguro usando o modo de backup do SQLite
sqlite3 "$DB_PATH" ".backup $BACKUP_DIR/banco_$DATA.db"

# Mantém apenas os últimos 7 backups
ls -t "$BACKUP_DIR"/banco_*.db | tail -n +8 | xargs -r rm

echo "Backup criado: $BACKUP_DIR/banco_$DATA.db"
