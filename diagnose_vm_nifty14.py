"""
diagnose_vm_nifty14.py
Connects to Cloud VM (ubuntu@140.245.195.112) via SSH and performs a deep audit
of why NIFTY V14.9 has not given any trades in the last 3 trading sessions.
"""

import sys
import io
import subprocess
from pathlib import Path

# UTF-8 fix for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent
KEY_PATH = ROOT.parent / "oracle" / "nifty-v15.key"
VM_HOST = "ubuntu@140.245.195.112"

print("=" * 95)
print(f"📡 CONNECTING TO CLOUD VM ({VM_HOST}) TO DIAGNOSE NIFTY V14.9")
print("=" * 95)

if not KEY_PATH.exists():
    print(f"❌ SSH Key not found at: {KEY_PATH}")
    sys.exit(1)

# Remote commands to diagnose V14.9
remote_cmds = """
echo "=== 1. CHECK RUNNING PYTHON PROCESSES (V14.9 & SCANNERS) ==="
ps aux | grep -E "NIFTY|python|v14" | grep -v grep

echo ""
echo "=== 2. CHECK ACTIVE CRONTAB ON VM ==="
crontab -l | grep -E "NIFTY|v14|scanner|STOCK"

echo ""
echo "=== 3. CHECK KITE ACCESS TOKEN TIMESTAMP & CONTENT ON VM ==="
ls -la /home/ubuntu/NiftyScanner/.kite* 2>/dev/null
ls -la /home/ubuntu/NiftyScanner/nifty_v14_7/.kite* 2>/dev/null
echo "Token preview in Master:"
head -c 25 /home/ubuntu/NiftyScanner/.kite_access_token 2>/dev/null; echo ""

echo ""
echo "=== 4. CHECK RECENT V14.9 LOG FILES (MODIFIED IN LAST 5 DAYS) ==="
find /home/ubuntu/NiftyScanner/ -name "*14*" -o -name "*nifty*" -type f -mtime -5 | grep -E "log|txt|json|csv" | head -n 30

echo ""
echo "=== 5. CHECK LATEST V14.9 EXECUTION LOGS & ERRORS ==="
if [ -d "/home/ubuntu/NiftyScanner/nifty_v14_7/logs" ]; then
    echo "--- Last 5 logs in nifty_v14_7/logs/ ---"
    ls -lht /home/ubuntu/NiftyScanner/nifty_v14_7/logs/ | head -n 10
    LATEST_LOG=$(ls -t /home/ubuntu/NiftyScanner/nifty_v14_7/logs/*.log 2>/dev/null | head -n 1)
    if [ -n "$LATEST_LOG" ]; then
        echo "--- Tail of latest log ($LATEST_LOG): ---"
        tail -n 40 "$LATEST_LOG"
    fi
fi

echo ""
echo "=== 6. CHECK RECENT V14.9 TRADES / DATABASE / CSV ==="
find /home/ubuntu/NiftyScanner/ -name "*trade*.csv" -o -name "*trade*.json" -o -name "*trades*.db" -type f | head -n 15
find /home/ubuntu/NiftyScanner/ -name "*trade*.csv" -exec ls -lht {} + 2>/dev/null | head -n 5

echo ""
echo "=== 7. CHECK SYSTEMD SERVICES OR TMUX/SCREEN SESSIONS ==="
tmux ls 2>/dev/null || echo "No active tmux sessions."
screen -ls 2>/dev/null || echo "No active screen sessions."
"""

ssh_cmd = [
    "ssh",
    "-o", "StrictHostKeyChecking=no",
    "-o", "ConnectTimeout=10",
    "-i", str(KEY_PATH),
    VM_HOST,
    remote_cmds
]

try:
    res = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=60)
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
except subprocess.TimeoutExpired:
    print("❌ SSH connection timed out after 60 seconds.")
except Exception as e:
    print(f"❌ Error running SSH: {e}")

print("=" * 95)
