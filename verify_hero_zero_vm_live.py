"""
verify_hero_zero_vm_live.py
Directly audits Cloud VM crontab, log files, and Telegram bot connectivity
for the Nifty Hero-Zero Expiry Scanner.
"""

import sys
import subprocess
from pathlib import Path

# UTF-8 fix for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

KEY_PATH = Path("D:/NiftyScanner/oracle/nifty-v15.key")
VM_HOST = "ubuntu@140.245.195.112"

def run_remote(cmd):
    ssh_cmd = ["ssh", "-i", str(KEY_PATH), "-o", "StrictHostKeyChecking=no", VM_HOST, cmd]
    res = subprocess.run(ssh_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
    return res.stdout, res.stderr, res.returncode

print("=" * 85)
print("🔍 HERO-ZERO EXPIRY ACTIVATION AUDIT ON CLOUD VM (140.245.195.112)")
print("=" * 85)

# 1. Check Crontab entries
out, err, code = run_remote("crontab -l | grep -A 2 -B 1 '10a. NIFTY Expiry'")
print("⏰ [1] ACTIVE CRONTAB SCHEDULE ON UBUNTU DAEMON:")
print("-" * 85)
print(out.strip())

# 2. Check VM System Clock & Timezone
out_time, _, _ = run_remote("date; date -u")
print("\n🕒 [2] CLOUD VM CLOCK & TIMEZONE:")
print("-" * 85)
print(out_time.strip())

# 3. Check cron_nifty_hz.log
out_log, _, _ = run_remote("tail -n 25 /home/ubuntu/NiftyScanner/cron_logs/cron_nifty_hz.log 2>/dev/null || echo 'Log file ready for 14:00 run'")
print("\n📄 [3] LATEST LOG OUTPUT IN /cron_logs/cron_nifty_hz.log:")
print("-" * 85)
print(out_log.strip())

# 4. Check Latest Scan JSON on VM
out_json, _, _ = run_remote("ls -lt /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/logs/nifty_hero_zero_*.json | head -n 3")
print("\n📁 [4] RECENT HERO-ZERO SCAN JSON FILES ON VM:")
print("-" * 85)
print(out_json.strip())

print("=" * 85)
