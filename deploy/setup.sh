#!/usr/bin/env bash
# One-time setup for a fresh Ubuntu EC2 instance. Paste as "User data" at launch, or run with sudo.
# Afterwards: add the Bedrock key to /opt/rightsize/deploy/.env, then `docker compose up -d --build`.
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/NahomMA/miniliz2nd-ashenafy.git}"
APP_DIR=/opt/rightsize

apt-get update -y
apt-get install -y docker.io docker-compose-v2 git
git clone "$REPO_URL" "$APP_DIR"

# Free HTTPS hostname for the instance's public IP (sslip.io maps 1-2-3-4.sslip.io to 1.2.3.4).
IMDS=http://169.254.169.254/latest
TOKEN=$(curl -s -X PUT "$IMDS/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 300")
PUBLIC_IP=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" "$IMDS/meta-data/public-ipv4")

umask 077
cat > "$APP_DIR/deploy/.env" <<EOF
DOMAIN=${PUBLIC_IP//./-}.sslip.io
SECRET_KEY=$(openssl rand -hex 32)
AWS_REGION=us-east-2
AWS_BEARER_TOKEN_BEDROCK=
EOF

echo "Setup done. API will be at https://${PUBLIC_IP//./-}.sslip.io once started."
