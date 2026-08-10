#!/bin/bash
# ══════════════════════════════════════════════════════
#  Sisplan — Setup inicial no Oracle Cloud (Ubuntu 22.04)
#  Execute uma vez como root ou com sudo
#  sudo bash 1_setup.sh
# ══════════════════════════════════════════════════════
set -e

APP_DIR="/home/ubuntu/sisplan"
DATA_DIR="/home/ubuntu/sisplan/data"
REPO_URL="https://github.com/brunosenadev/sistema-escritural.git"

echo ">>> Atualizando sistema..."
apt update && apt upgrade -y

echo ">>> Instalando dependências..."
apt install -y python3.11 python3.11-venv python3-pip nginx git ufw

echo ">>> Clonando repositório..."
git clone "$REPO_URL" "$APP_DIR"
chown -R ubuntu:ubuntu "$APP_DIR"

echo ">>> Criando diretórios de dados e logs..."
mkdir -p "$DATA_DIR"
mkdir -p "$APP_DIR/logs"
chown -R ubuntu:ubuntu "$DATA_DIR" "$APP_DIR/logs"

echo ">>> Criando ambiente virtual..."
cd "$APP_DIR"
sudo -u ubuntu python3.11 -m venv venv
sudo -u ubuntu venv/bin/pip install --upgrade pip
sudo -u ubuntu venv/bin/pip install -r requirements.txt

echo ">>> Criando arquivo .env..."
cat > "$APP_DIR/.env" <<EOF
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DB_PATH=$DATA_DIR/banco_dados.db
EOF
chown ubuntu:ubuntu "$APP_DIR/.env"
chmod 600 "$APP_DIR/.env"

echo ">>> Configurando serviço systemd..."
cp "$APP_DIR/deploy/sisplan.service" /etc/systemd/system/sisplan.service
systemctl daemon-reload
systemctl enable sisplan
systemctl start sisplan

echo ">>> Configurando nginx..."
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/sisplan
ln -sf /etc/nginx/sites-available/sisplan /etc/nginx/sites-enabled/sisplan
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

echo ">>> Configurando firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo ""
echo "✅ Setup concluído!"
echo "   App rodando em: http://$(curl -s ifconfig.me)"
echo ""
echo "   Próximos passos:"
echo "   1. Copie o banco do Render para $DATA_DIR/banco_dados.db"
echo "   2. Configure o domínio no nginx.conf se necessário"
echo "   3. Para HTTPS: sudo certbot --nginx"
