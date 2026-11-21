"""
inspect_v14_paper_script.py
Searches inside NIFTY_V14_9_PAPER_FINAL_DB_SNAPSHOT.py on VM
to see how it filters trades, checks PCR, checks bias, and sends telegram notifications.
"""

import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KEY_PATH = ROOT.parent / "oracle" / "nifty-v15.key"
VM_HOST = "ubuntu@140.245.195.112"

remote_cmds = """
TARGET="/home/ubuntu/NiftyScanner/nifty_v14_7/scripts/NIFTY_V14_9_PAPER_FINAL_DB_SNAPSHOT.py"

echo "=== 1. SEARCH FOR 'WITH CAUTION' OR CONFLICT CHECKS ==="
grep -in "CAUTION" "$TARGET"
grep -in "conflict" "$TARGET" | head -n 15

echo ""
echo "=== 2. SEARCH FOR ENTRY CONDITIONS ==="
grep -inE "def should_enter|def check_entry|can_enter|entry_gate" "$TARGET"

echo ""
echo "=== 3. SEARCH FOR PCR THRESHOLDS ==="
grep -in "pcr" "$TARGET" | head -n 20

echo ""
echo "=== 4. SEARCH FOR TELEGRAM MESSAGES ==="
grep -in "telegram" "$TARGET" | head -n 20
"""

ssh_cmd = [
    "ssh",
    "-o", "StrictHostKeyChecking=no",
    "-i", str(KEY_PATH),
    VM_HOST,
    remote_cmds
]

res = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=60)
print(res.stdout)
if res.stderr:
    print("STDERR:", res.stderr)
