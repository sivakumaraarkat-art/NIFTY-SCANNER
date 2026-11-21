"""
apply_vm_v14_fix.py
===================
Reads patch_vm_code.py from disk and pipes it directly to Cloud VM via SSH STDIN.
"""

import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KEY_PATH = ROOT.parent / "oracle" / "nifty-v15.key"
VM_HOST = "ubuntu@140.245.195.112"
PATCH_FILE = ROOT / "patch_vm_code.py"

if not PATCH_FILE.exists():
    print(f"[ERROR] Patch file not found: {PATCH_FILE}")
    sys.exit(1)

with open(PATCH_FILE, "r", encoding="utf-8") as f:
    remote_code = f.read()

print(f"[*] Read patch script ({len(remote_code)} bytes).")
print(f"[*] Connecting to Cloud VM ({VM_HOST}) and executing patch via STDIN...")

ssh_cmd = [
    "ssh",
    "-o", "StrictHostKeyChecking=no",
    "-i", str(KEY_PATH),
    VM_HOST,
    "/home/ubuntu/NiftyScanner/nifty_v14_7/.venv/bin/python -"
]

res = subprocess.run(ssh_cmd, input=remote_code, capture_output=True, text=True, timeout=60)
print(res.stdout)
if res.stderr:
    print("STDERR:", res.stderr)
