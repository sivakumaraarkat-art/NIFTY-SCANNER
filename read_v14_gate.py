"""
read_v14_gate.py
Reads lines 1075 to 1105 of NIFTY_V14_9_PAPER_FINAL_DB_SNAPSHOT.py on the Cloud VM
"""

import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KEY_PATH = ROOT.parent / "oracle" / "nifty-v15.key"
VM_HOST = "ubuntu@140.245.195.112"

remote_cmd = "sed -n '1075,1105p' /home/ubuntu/NiftyScanner/nifty_v14_7/scripts/NIFTY_V14_9_PAPER_FINAL_DB_SNAPSHOT.py"

ssh_cmd = [
    "ssh",
    "-o", "StrictHostKeyChecking=no",
    "-i", str(KEY_PATH),
    VM_HOST,
    remote_cmd
]

res = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
print(res.stdout)
if res.stderr:
    print("STDERR:", res.stderr)
