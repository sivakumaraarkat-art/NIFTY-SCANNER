"""
run_vm_test_suite.py
====================
Pipes vm_test_code.py via UTF-8 STDIN to the Cloud VM.
"""

import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KEY_PATH = ROOT.parent / "oracle" / "nifty-v15.key"
VM_HOST = "ubuntu@140.245.195.112"
TEST_FILE = ROOT / "vm_test_code.py"

if not TEST_FILE.exists():
    print(f"[ERROR] Test script not found: {TEST_FILE}")
    sys.exit(1)

with open(TEST_FILE, "rb") as f:
    remote_bytes = f.read()

print(f"[*] Read test suite ({len(remote_bytes)} bytes).")
print(f"[*] Connecting to Cloud VM ({VM_HOST}) and executing test suite...")

ssh_cmd = [
    "ssh",
    "-o", "StrictHostKeyChecking=no",
    "-i", str(KEY_PATH),
    VM_HOST,
    "/home/ubuntu/NiftyScanner/nifty_v14_7/.venv/bin/python -"
]

res = subprocess.run(ssh_cmd, input=remote_bytes, capture_output=True, timeout=60)
stdout_text = res.stdout.decode("utf-8", errors="replace")
stderr_text = res.stderr.decode("utf-8", errors="replace")

print(stdout_text)
if stderr_text:
    print("STDERR:", stderr_text)
