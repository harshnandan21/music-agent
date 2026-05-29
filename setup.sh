#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Music Agent — Hetzner Server Setup
# Run as root: bash setup.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e

APP_DIR=/opt/music-agent
REPO_URL=https://github.com/harshnandan21/music-agent.git
VENV="$APP_DIR/venv/bin/python"

echo "============================================"
echo "  Music Agent — Server Setup"
echo "============================================"

[ "$(id -u)" != "0" ] && echo "Run as root: sudo bash setup.sh" && exit 1

# ── 1. System packages ────────────────────────────────────────────────────────
echo "[1/6] Installing system packages..."
apt-get update -qq
apt-get install -y python3.12 python3.12-venv python3-pip ffmpeg git curl

# ── 2. Clone / pull repo ──────────────────────────────────────────────────────
echo "[2/6] Cloning repo..."
if [ -d "$APP_DIR/.git" ]; then
    echo "  Repo exists — pulling latest..."
    cd "$APP_DIR" && git pull
else
    git clone "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"

# ── 3. Python virtualenv + packages ──────────────────────────────────────────
echo "[3/6] Setting up Python environment..."
python3.12 -m venv venv
venv/bin/pip install --quiet --upgrade pip
venv/bin/pip install --quiet -r requirements.txt

# ── 4. .env file ──────────────────────────────────────────────────────────────
echo "[4/6] Configuring environment variables..."
if [ -f .env ]; then
    echo "  .env already exists — skipping."
else
    echo "  Paste each value and press Enter:"
    echo ""
    read -p  "  GEMINI_API_KEY          : " GEMINI_API_KEY
    read -p  "  TELEGRAM_BOT_TOKEN      : " TELEGRAM_BOT_TOKEN
    read -p  "  TELEGRAM_CHAT_ID        : " TELEGRAM_CHAT_ID
    read -p  "  YT_PLAYLIST_MORNING     : " YT_PLAYLIST_MORNING
    read -p  "  YT_PLAYLIST_FOCUS       : " YT_PLAYLIST_FOCUS
    read -p  "  YT_PLAYLIST_STRESS      : " YT_PLAYLIST_STRESS
    read -p  "  YT_PLAYLIST_SLEEP       : " YT_PLAYLIST_SLEEP
    read -p  "  YT_PLAYLIST_MIDNIGHT    : " YT_PLAYLIST_MIDNIGHT

    cat > .env << ENVEOF
GEMINI_API_KEY=$GEMINI_API_KEY
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID
YT_PLAYLIST_MORNING=$YT_PLAYLIST_MORNING
YT_PLAYLIST_FOCUS=$YT_PLAYLIST_FOCUS
YT_PLAYLIST_STRESS=$YT_PLAYLIST_STRESS
YT_PLAYLIST_SLEEP=$YT_PLAYLIST_SLEEP
YT_PLAYLIST_MIDNIGHT=$YT_PLAYLIST_MIDNIGHT
ENVEOF
    echo "  .env created."
fi

# ── 5. YouTube OAuth tokens ───────────────────────────────────────────────────
echo "[5/6] Setting up YouTube OAuth tokens..."
if [ ! -f youtube_token.json ]; then
    echo ""
    echo "  On your LOCAL machine, run:"
    echo "    python -c \"import base64,open; print(base64.b64encode(open('youtube_token.json','rb').read()).decode())\""
    echo ""
    read -p  "  Paste base64-encoded youtube_token.json: " YT_TOKEN_B64
    echo "$YT_TOKEN_B64" | base64 -d > youtube_token.json
    echo "  youtube_token.json written."
else
    echo "  youtube_token.json already exists — skipping."
fi

if [ ! -f client_secret.json ]; then
    echo ""
    echo "  On your LOCAL machine, run:"
    echo "    python -c \"import base64; print(base64.b64encode(open('client_secret.json','rb').read()).decode())\""
    echo ""
    read -p  "  Paste base64-encoded client_secret.json : " YT_SECRET_B64
    echo "$YT_SECRET_B64" | base64 -d > client_secret.json
    echo "  client_secret.json written."
else
    echo "  client_secret.json already exists — skipping."
fi

# ── 6. Cron job (8 AM IST = 2:30 AM UTC) ─────────────────────────────────────
echo "[6/6] Setting up daily cron job (8 AM IST)..."
cat > /etc/cron.d/music-agent << CRONEOF
30 2 * * * root cd $APP_DIR && $APP_DIR/venv/bin/python startup.py >> /var/log/music-agent.log 2>&1
CRONEOF
chmod 644 /etc/cron.d/music-agent
service cron restart 2>/dev/null || true
echo "  Cron job set."

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "============================================"
echo "  Setup complete!"
echo "============================================"
echo ""
echo "  Test run : cd $APP_DIR && venv/bin/python studio/orchestrator.py --draft"
echo "  Live logs: tail -f /var/log/music-agent.log"
echo ""
