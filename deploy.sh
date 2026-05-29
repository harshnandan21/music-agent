#!/bin/bash
# Re-deploy: pull latest code and update packages.
# Run on server: bash /opt/music-agent/deploy.sh
set -e

APP_DIR=/opt/music-agent
cd "$APP_DIR"

echo "[deploy] Pulling latest code..."
git pull

echo "[deploy] Updating packages..."
venv/bin/pip install --quiet -r requirements.txt

echo "[deploy] Done. Next cron run will use updated code."
