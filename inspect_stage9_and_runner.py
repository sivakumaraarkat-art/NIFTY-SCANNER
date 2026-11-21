"""
inspect_stage9_and_runner.py
Inspects run_NIFTY_V14_9_PAPER.sh and index_oi_scanner_stage9.py lines 220-280
"""

import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KEY_PATH = ROOT.parent / "oracle" / "nifty-v15.key"
VM_HOST = "ubuntu@140.245.195.112"

remote_cmds = """
echo "=== 1. RUN_NIFTY_V14_9_PAPER.SH ==="
cat /home/ubuntu/NiftyScanner/nifty_v14_7/run_NIFTY_V14_9_PAPER.sh

echo ""
echo "=== 2. INDEX_OI_SCANNER_STAGE9.PY (LINES 220-280) ==="
sed -n '220,285p' /home/ubuntu/NiftyScanner/nifty_v14_7/scripts/index_oi_scanner_stage9.py

echo ""
echo "=== 3. FIND PAPER TRADE SCRIPT (WHERE BIAS / CONFLICT IS CHECKED BEFORE OPENING TRADE) ==="
find /home/ubuntu/NiftyScanner/nifty_v14_7/ -name "*14_9*" -o -name "*stage10*" | grep -v __pycache__
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
