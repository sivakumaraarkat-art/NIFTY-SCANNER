#!/usr/bin/env bash
# ==============================================================================
# Portfolio Peak Guard Continuous Sentinel Runner
# Scheduled via crontab at 09:15 AM IST (Mon-Fri)
# ==============================================================================
set -e

DIR="/home/ubuntu/NiftyScanner/PORTFOLIO_PEAK_EXIT_GUARD"
cd "$DIR"
mkdir -p logs

LOCK_FILE="/tmp/portfolio_sentinel.lock"
LOG_FILE="logs/sentinel_continuous_$(date +%Y%m%d).log"

# Unbuffer Python standard output for real-time live streaming logs
export PYTHONUNBUFFERED=1

# Ensure single instance execution via flock
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ Another Portfolio Sentinel instance is already running. Exiting." >> "$LOG_FILE"
    exit 0
fi

/home/ubuntu/NiftyScanner/nifty_v14_7/venv/bin/python3 -u portfolio_peak_exit_guard.py \
    --use-demat \
    --send-telegram \
    --continuous \
    --interval 15 >> "$LOG_FILE" 2>&1
