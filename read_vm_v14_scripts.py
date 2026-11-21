"""
read_vm_v14_scripts.py
Finds the exact files and lines on Cloud VM that define:
1. PCR Conflict logic in Stage 8 / Stage 9
2. Entry checklist / retest requirement in Stage 10 / V14.9
3. Telegram notification heartbeat
"""

import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KEY_PATH = ROOT.parent / "oracle" / "nifty-v15.key"
VM_HOST = "ubuntu@140.245.195.112"

remote_cmds = """
echo "=== 1. CRON WRAPPER SCRIPT ==="
cat /home/ubuntu/NiftyScanner/nifty_v14_7/run_NIFTY_V14_9_CRON.sh

echo ""
echo "=== 2. FIND OCCURRENCES OF PCR CONFLICT IN SCRIPTS ==="
grep -rn "CONFLICTING FACTOR" /home/ubuntu/NiftyScanner/nifty_v14_7/scripts/
grep -rn "PCR is bearish" /home/ubuntu/NiftyScanner/nifty_v14_7/scripts/

echo ""
echo "=== 3. FIND ENTRY CONFIRMATION / RETEST IN SCRIPTS ==="
grep -rn "entry_confirmation" /home/ubuntu/NiftyScanner/nifty_v14_7/scripts/
grep -rn "retest" /home/ubuntu/NiftyScanner/nifty_v14_7/scripts/ | head -n 15

echo ""
echo "=== 4. MAIN ENGINE SCRIPT IN nifty_v14_7 ==="
ls -lh /home/ubuntu/NiftyScanner/nifty_v14_7/scripts/*stage10* /home/ubuntu/NiftyScanner/nifty_v14_7/scripts/*v14* 2>/dev/null
ls -lh /home/ubuntu/NiftyScanner/nifty_v14_7/*.py 2>/dev/null
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
