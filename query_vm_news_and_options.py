"""
query_vm_news_and_options.py
Connects to the Oracle Cloud VM (140.245.195.112) via SSH,
fetches the latest news scanner outputs, cron logs, and runs the options scanner.
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

def run_remote_ssh(cmd_str):
    ssh_cmd = [
        "ssh",
        "-i", str(KEY_PATH),
        "-o", "StrictHostKeyChecking=no",
        VM_HOST,
        cmd_str
    ]
    res = subprocess.run(ssh_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    return res.stdout or "", res.stderr or "", res.returncode

print("=" * 80)
print("🌐 CONNECTING TO CLOUD VM (140.245.195.112) — SCANNING NEWS & OPTIONS LOGS")
print("=" * 80)

# 1. Check latest news cron logs
print("\n📰 [1] LATEST INTRADAY NEWS LOGS (cron_news_intraday.log & cron_news_am.log):")
print("-" * 80)
out, err, code = run_remote_ssh("tail -n 35 /home/ubuntu/NiftyScanner/cron_logs/cron_news_intraday.log 2>/dev/null || tail -n 35 /home/ubuntu/NiftyScanner/cron_logs/cron_news_am.log")
if out.strip():
    print(out.strip())
else:
    print("No recent log text found, checking fallback...")

# 2. Check latest intraday options scan logs
print("\n⚡ [2] LATEST OPTIONS INTRADAY SCAN LOGS (cron_intraday.log):")
print("-" * 80)
out, err, code = run_remote_ssh("tail -n 45 /home/ubuntu/NiftyScanner/cron_logs/cron_intraday.log")
if out.strip():
    print(out.strip())
else:
    print("No cron_intraday.log entries found.")

# 3. List recent log files in STOCK_SWING_V1_updated/logs/
print("\n📁 [3] RECENT LOG FILES ON CLOUD VM (today):")
print("-" * 80)
out, err, code = run_remote_ssh("ls -lt /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/logs/ | head -n 15")
print(out.strip())

print("=" * 80)
