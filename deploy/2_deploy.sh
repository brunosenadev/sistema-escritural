#!/bin/bash
# ══════════════════════════════════════════════════════
#  Sisplan — Atualizar após git push
#  Execute como ubuntu: bash deploy/2_deploy.sh
# ══════════════════════════════════════════════════════
set -e

APP_DIR="/home/ubuntu/sisplan"

echo ">>> Baixando atualizações..."
cd "$APP_DIR"
git pull origin main

echo ">>> Instalando dependências novas (se houver)..."
venv/bin/pip install -r requirements.txt --quiet

echo ">>> Reiniciando serviço..."
sudo systemctl restart sisplan

echo "✅ Deploy concluído! Status:"
sudo systemctl status sisplan --no-pager -l
