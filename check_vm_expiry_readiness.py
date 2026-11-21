"""
check_vm_expiry_readiness.py
Inspects Cloud VM Nifty Expiry readiness:
1. Crontab schedule for Hero-Zero and Nifty V14.9
2. Master token validity on Cloud VM
3. Runs a dry-run of nifty_hero_zero_expiry_scanner.py on the Cloud VM to verify readiness!
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
    ssh_cmd = [
        "ssh", "-i", str(KEY_PATH), "-o", "StrictHostKeyChecking=no",
        VM_HOST, cmd
    ]
    res = subprocess.run(ssh_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    return res.stdout, res.stderr, res.returncode

print("=" * 85)
print("🌐 CHECKING CLOUD VM NIFTY EXPIRY READINESS (140.245.195.112)")
print("=" * 85)

# 1. Check Master Token on VM
out, err, code = run_remote("cat /home/ubuntu/NiftyScanner/.kite_access_token")
token_preview = out.strip()[:10] + "..." if out.strip() else "NONE"
print(f"🔑 Master Token on VM: {token_preview} (Valid: {'YES' if out.strip() else 'NO'})")

# 2. Check Crontab for Nifty Expiry & Hero-Zero
out, err, code = run_remote("crontab -l | grep -E 'hero_zero|v14_9|intraday'")
print("\n⏰ VM Active Crontab for Nifty Scanners:")
print("-" * 85)
print(out.strip())

# 3. Test Run Nifty Hero-Zero Scanner on the VM directly!
print("\n🧪 Testing nifty_hero_zero_expiry_scanner.py on Cloud VM:")
print("-" * 85)
test_cmd = (
    "cd /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated && "
    "PYTHONPATH=/home/ubuntu/NiftyScanner/nifty_v14_7/venv/lib/python3.12/site-packages "
    "/usr/bin/python3 src/scanners/nifty_hero_zero_expiry_scanner.py --dry-run 2>&1 || "
    "PYTHONPATH=/home/ubuntu/NiftyScanner/nifty_v14_7/venv/lib/python3.12/site-packages "
    "/usr/bin/python3 src/scanners/nifty_hero_zero_expiry_scanner.py 2>&1 | head -n 40"
)
out, err, code = run_remote(test_cmd)
print(out.strip()[:2000])

print("=" * 85)
