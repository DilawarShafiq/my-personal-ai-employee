#!/usr/bin/env bash
# =============================================================================
# One-shot deployer for the autosapien cloud stack on a fresh Oracle Cloud
# Free Tier (Ubuntu 22.04, Ampere ARM A1.Flex 4 OCPU / 24 GB RAM).
#
# Usage:
#   sudo bash deploy/cloud/bootstrap_oracle_free.sh yourdomain.example admin@email
#
# Or with a nip.io self-signed alternative (no domain needed):
#   sudo bash deploy/cloud/bootstrap_oracle_free.sh --self-signed
# =============================================================================
set -euo pipefail

DOMAIN="${1:-}"
ADMIN_EMAIL="${2:-}"
REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"

if [[ "$EUID" -ne 0 ]]; then
    echo "This script must be run as root. Re-run with: sudo bash $0 $*"
    exit 1
fi

if [[ -z "$DOMAIN" || "$DOMAIN" == "--self-signed" ]]; then
    PUBLIC_IP=$(curl -s https://checkip.amazonaws.com)
    DOMAIN="${PUBLIC_IP}.nip.io"
    ADMIN_EMAIL="${ADMIN_EMAIL:-none@localhost}"
    echo "[info] no domain provided — using $DOMAIN via nip.io"
fi

if [[ -z "$ADMIN_EMAIL" ]]; then
    echo "Usage: sudo bash $0 <domain> <admin_email>"
    exit 1
fi

echo "[1/7] Installing Docker + git..."
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg git openssl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
cat >/etc/apt/sources.list.d/docker.list <<EOF
deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable
EOF
apt-get update -qq
apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "[2/7] Opening HTTP(S) in the OS firewall..."
# Oracle Cloud ships with iptables blocking 80/443 by default.
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
netfilter-persistent save 2>/dev/null || iptables-save >/etc/iptables/rules.v4

echo "[3/7] Generating Odoo DB password + .env.cloud..."
CLOUD_ENV="$REPO_DIR/deploy/cloud/.env.cloud"
if [[ ! -f "$CLOUD_ENV" ]]; then
    cp "$REPO_DIR/deploy/cloud/.env.cloud.example" "$CLOUD_ENV"
    ODOO_PW=$(openssl rand -hex 16)
    sed -i "s|^ODOO_DB_PASSWORD=.*|ODOO_DB_PASSWORD=${ODOO_PW}|" "$CLOUD_ENV"
    sed -i "s|^DOMAIN=.*|DOMAIN=${DOMAIN}|" "$CLOUD_ENV"
    sed -i "s|^ADMIN_EMAIL=.*|ADMIN_EMAIL=${ADMIN_EMAIL}|" "$CLOUD_ENV"
    chmod 600 "$CLOUD_ENV"
    echo "  ok  wrote $CLOUD_ENV (mode 600)"
else
    echo "  skip  $CLOUD_ENV already exists"
fi

echo "[4/7] Placeholder secrets — YOU must upload Gmail creds separately..."
mkdir -p "$REPO_DIR/deploy/cloud/secrets"
chmod 700 "$REPO_DIR/deploy/cloud/secrets"
if [[ ! -f "$REPO_DIR/deploy/cloud/secrets/gmail_credentials.json" ]]; then
    cat >"$REPO_DIR/deploy/cloud/secrets/README.md" <<'EOF'
Put your Gmail OAuth client JSON here before running `docker compose up`:

  deploy/cloud/secrets/gmail_credentials.json

And the token (copy from your Local machine after minting it with the
GmailWatcher OAuth flow):

  deploy/cloud/secrets/gmail_token.json

These are git-ignored (see repo-root .gitignore) and bind-mounted
read-only into the cloud-agent container at /secrets/.
EOF
    echo "  WARN  deploy/cloud/secrets/gmail_credentials.json is MISSING"
    echo "         copy it from your Local machine before `docker compose up`"
fi

echo "[5/7] docker compose build + up..."
cd "$REPO_DIR/deploy/cloud"
docker compose --env-file .env.cloud -f docker-compose.cloud.yml build
docker compose --env-file .env.cloud -f docker-compose.cloud.yml up -d

echo "[6/7] Installing the nightly backup systemd timer..."
cp "$REPO_DIR/deploy/cloud/systemd/autosapien-backup.service" /etc/systemd/system/
cp "$REPO_DIR/deploy/cloud/systemd/autosapien-backup.timer" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now autosapien-backup.timer

echo "[7/7] Waiting for Odoo healthcheck..."
for i in {1..60}; do
    if docker compose -f docker-compose.cloud.yml ps odoo | grep -q "healthy"; then
        echo "  ok  Odoo is healthy"
        break
    fi
    sleep 5
    echo "    waiting... ($i/60)"
done

echo ""
echo "Deployment complete."
echo "  Public: https://${DOMAIN}/healthz"
echo "  Odoo:   https://${DOMAIN}/odoo/web/login   (admin / see ODOO_DB_PASSWORD in .env.cloud)"
echo ""
echo "Next steps:"
echo "  1. Upload Gmail credentials to deploy/cloud/secrets/ (see that folder's README.md)."
echo "  2. Run scripts/create_odoo_db.py against the public URL to bootstrap the 'autosapien' DB."
echo "  3. Run scripts/seed_odoo.py to populate healthcare customers and invoices."
echo "  4. Point Local's git-vault-sync at the same vault-only repo used here."
