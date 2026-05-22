#!/bin/bash
# Music Agent — Railway entrypoint
# Runs once at 7 PM IST daily (13:30 UTC) via Railway cron

set -e

echo "[startup] Installing dependencies..."
pip install -q -r requirements.txt

echo "[startup] Starting music agent pipeline..."
cd /app
python orchestrator.py
