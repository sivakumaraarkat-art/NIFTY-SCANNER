"""
inspect_v14_logs.py
Reads the actual contents of the trade CSVs and stage 10 logs for Nov 4, 5, 6
on the cloud VM to see exactly what trades or filters triggered.
"""

import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KEY_PATH = ROOT.parent / "oracle" / "nifty-v15.key"
VM_HOST = "ubuntu@140.245.195.112"

remote_cmds = """
echo "=== 1. CONTENTS OF CSV TRADE FILES (Nov 4, 5, 6) ==="
for f in /home/ubuntu/NiftyScanner/nifty_v14_7/csv/stage10_paper_trades_202611*.csv; do
    echo "--- File: $f ---"
    cat "$f"
    echo ""
done

echo ""
echo "=== 2. TELEGRAM GUI LOG (ARE ALERTS BEING SENT OR BLOCKED?) ==="
tail -n 30 /home/ubuntu/NiftyScanner/nifty_v14_7/logs/telegram*.log 2>/dev/null || echo "No telegram log"

echo ""
echo "=== 3. CRON V14_9 EXECUTION WRAPPER LOG (Last 3 days) ==="
ls -lt /home/ubuntu/NiftyScanner/cron_logs/cron_v14_9* | head -n 5
for f in $(ls -t /home/ubuntu/NiftyScanner/cron_logs/cron_v14_9_202611*.log 2>/dev/null | head -n 3); do
    echo "--- $f (Head & Tail) ---"
    head -n 15 "$f"
    echo "..."
    tail -n 15 "$f"
    echo ""
done

echo ""
echo "=== 4. CHECK WHY NO TRADES WERE TAKEN (GATE / FILTER CHECKS) ==="
grep -inE "SKIP|BLOCKED|FILTER|CONFLICT|REJECT|GATE|NO TRADE|CONFIDENCE" /home/ubuntu/NiftyScanner/nifty_v14_7/logs/stage10_output_20261106.log | tail -n 25
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
