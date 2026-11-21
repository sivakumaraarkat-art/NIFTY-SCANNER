#!/usr/bin/env bash
# ==============================================================================
# Daily Pre-Market System Maintenance, 7z Log Archiving & Cleanup Engine
# Scheduled at 6:00 AM IST (Monday to Friday)
# Target Host: ubuntu@140.245.195.112 (NiftyScanner Root)
#
# Rules:
# 1. Keep only the last 5 trading days of active raw logs.
# 2. Files older than 5 days are compressed into 7z archives in /archives/.
# 3. Archives in /archives/ are kept for 1 month (30 days); older ones auto-purged.
# 4. Cleans apt cache, journald logs, python caches, and flushes RAM.
# ==============================================================================
set -euo pipefail

LOG_FILE="/home/ubuntu/NiftyScanner/daily_maintenance.log"
exec > >(tee -a "${LOG_FILE}") 2>&1

NOW_IST=$(TZ="Asia/Kolkata" date "+%Y-%m-%d %H:%M:%S IST")
TODAY_STR=$(TZ="Asia/Kolkata" date "+%Y%m%d")

echo "========================================================"
echo "[${NOW_IST}] Starting Daily 6:00 AM System Maintenance"
echo "========================================================"

# 1. Clean Pip cache
echo "[1/8] Purging Pip download cache..."
python3 -m pip cache purge 2>/dev/null || rm -rf /home/ubuntu/.cache/pip/* 2>/dev/null || true
echo "✓ Pip cache cleared."

# 2. Clean stale Python bytecode caches (__pycache__ and .pyc)
echo "[2/8] Cleaning stale Python bytecode caches..."
find /home/ubuntu/NiftyScanner -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find /home/ubuntu/NiftyScanner -type f -name "*.pyc" -delete 2>/dev/null || true
echo "✓ Python bytecode caches refreshed."

# 3. Clean stale temporary /tmp files
echo "[3/8] Cleaning stale temporary files in /tmp..."
rm -f /tmp/cron_* /tmp/mycron /tmp/new_cron /tmp/update_cron.sh 2>/dev/null || true
find /tmp -maxdepth 1 -type f -mtime +1 -delete 2>/dev/null || true
echo "✓ Stale /tmp files removed."

# 4. Terminate any stale scanner or zombie processes from previous days
echo "[4/8] Terminating stale scanner processes from previous days..."
pkill -f "portfolio_peak_exit_guard.py" 2>/dev/null || true
echo "✓ Stale processes cleared."

# 5. Clean APT package cache
echo "[5/8] Cleaning APT package installer cache..."
sudo apt-get clean 2>/dev/null || true
echo "✓ APT cache cleaned."

# 6. Vacuum systemd journal logs to keep 7 days max
echo "[6/8] Vacuuming systemd journal logs (keeping 7 days)..."
sudo journalctl --vacuum-time=7d --vacuum-size=50M 2>/dev/null || true
sudo rm -f /var/log/*.gz /var/log/*.[0-9] 2>/dev/null || true
echo "✓ Journal and system logs vacuumed."

# 7. ARCHIVE LOGS OLDER THAN 5 DAYS (7-ZIP ENGINE) & AUTO-PURGE OLDER THAN 30 DAYS
echo "[7/8] Processing Log Archiving (5-Day Retention + 7z Compression + 1-Month Purge)..."
ARCHIVE_DIR="/home/ubuntu/NiftyScanner/archives"
mkdir -p "${ARCHIVE_DIR}"

ARCHIVE_FILE="${ARCHIVE_DIR}/logs_archive_${TODAY_STR}.7z"
TEMP_FILELIST="/tmp/files_to_archive_${TODAY_STR}.txt"
rm -f "${TEMP_FILELIST}"

# Collect files older than 5 days from all active log directories
find /home/ubuntu/NiftyScanner/nifty_v14_7/logs/replay -type f -name "*.jsonl" -mtime +5 >> "${TEMP_FILELIST}" 2>/dev/null || true
find /home/ubuntu/NiftyScanner/nifty_v14_7/logs -maxdepth 1 -type f -name "stage10_output_*.log" -mtime +5 >> "${TEMP_FILELIST}" 2>/dev/null || true
find /home/ubuntu/NiftyScanner/cron_logs -type f -name "*.log" -mtime +5 >> "${TEMP_FILELIST}" 2>/dev/null || true
find /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/logs -type f \( -name "*.json" -o -name "*.log" \) -mtime +5 >> "${TEMP_FILELIST}" 2>/dev/null || true
find /home/ubuntu/NiftyScanner/PORTFOLIO_PEAK_EXIT_GUARD/logs -type f -name "*.log" -mtime +5 >> "${TEMP_FILELIST}" 2>/dev/null || true

if [ -s "${TEMP_FILELIST}" ]; then
    NUM_FILES=$(wc -l < "${TEMP_FILELIST}")
    echo "   • Found ${NUM_FILES} log files older than 5 days to archive."
    echo "   • Compressing into 7z: ${ARCHIVE_FILE}..."
    7z a -mx=7 "${ARCHIVE_FILE}" @"${TEMP_FILELIST}" >/dev/null 2>&1

    if [ -f "${ARCHIVE_FILE}" ]; then
        ARCHIVE_SIZE=$(ls -lh "${ARCHIVE_FILE}" | awk '{print $5}')
        echo "   ✓ 7z archive created successfully (Size: ${ARCHIVE_SIZE})."

        # Safely remove only the files that were listed and archived
        while IFS= read -r f; do
            if [ -f "$f" ]; then
                rm -f "$f"
            fi
        done < "${TEMP_FILELIST}"
        echo "   ✓ Successfully removed original uncompressed files older than 5 days."
    fi
else
    echo "   • No log files older than 5 days needed archiving today."
fi
rm -f "${TEMP_FILELIST}"

# AUTO-PURGE ARCHIVES OLDER THAN 30 DAYS (1 MONTH)
echo "   • Checking for 7z archives older than 30 days (1 month)..."
PURGED_COUNT=$(find "${ARCHIVE_DIR}" -type f -name "logs_archive_*.7z" -mtime +30 | wc -l)
if [ "${PURGED_COUNT}" -gt 0 ]; then
    find "${ARCHIVE_DIR}" -type f -name "logs_archive_*.7z" -mtime +30 -delete
    echo "   ✓ Auto-purged ${PURGED_COUNT} archive(s) older than 30 days."
else
    echo "   ✓ All archives are within the 30-day retention window."
fi

# 8. Sync filesystem buffers and release cached RAM
echo "[8/8] Syncing filesystem buffers and releasing cached RAM..."
sync
# Drop clean pagecache, dentries, and inodes
sudo sh -c "echo 3 > /proc/sys/vm/drop_caches" 2>/dev/null || true
echo "✓ Memory buffers and pagecache refreshed."

# Verify Swap
if ! swapon --show | grep -q "/swapfile"; then
    echo "WARNING: Swap was inactive. Activating /swapfile..."
    sudo swapon /swapfile 2>/dev/null || true
fi

echo -e "\n--- System Resource Snapshot ---"
free -h
echo ""
df -h /
echo ""
echo "--- Storage Breakdown ---"
du -sh /home/ubuntu/NiftyScanner/nifty_v14_7/logs 2>/dev/null || true
du -sh /home/ubuntu/NiftyScanner/cron_logs 2>/dev/null || true
du -sh /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/logs 2>/dev/null || true
du -sh "${ARCHIVE_DIR}" 2>/dev/null || true

echo "========================================================"
echo " Daily Maintenance Completed Successfully at $(TZ="Asia/Kolkata" date "+%H:%M:%S IST")"
echo " System is ready for 7:00 AM Token Auth & Market Trading"
echo "========================================================"
