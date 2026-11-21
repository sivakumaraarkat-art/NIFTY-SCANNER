"""
sync_token_from_vm.py
Copies the master Zerodha Kite access token from the Ubuntu Cloud VM to local.
"""

import os
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

ROOT = Path(__file__).resolve().parent
KEY_PATH = Path("D:/NiftyScanner/oracle/nifty-v15.key")
VM_HOST = "ubuntu@140.245.195.112"
REMOTE_FILE = "/home/ubuntu/NiftyScanner/.kite_access_token"
LOCAL_FILE = ROOT / ".kite_access_token"

print("=" * 70)
print("🔄 FETCHING MASTER KITE TOKEN FROM CLOUD VM")
print(f"   Server: {VM_HOST}")
print(f"   Key:    {KEY_PATH}")
print("=" * 70)

if not KEY_PATH.exists():
    print(f"❌ SSH Private key not found at: {KEY_PATH}")
    sys.exit(1)

# Method 1: Try using scp command
cmd = [
    "scp",
    "-i", str(KEY_PATH),
    "-o", "StrictHostKeyChecking=no",
    f"{VM_HOST}:{REMOTE_FILE}",
    str(LOCAL_FILE)
]

try:
    print("Connecting via SCP...")
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if res.returncode == 0:
        new_token = LOCAL_FILE.read_text(encoding="utf-8").strip()
        print("✅ SUCCESS! Fresh access token downloaded from Cloud VM:")
        print(f"   Token: {new_token[:8]}...{new_token[-6:]}")
        print("\nNow run: python check_nifty_position_only.py")
        sys.exit(0)
    else:
        print(f"⚠️ SCP failed with return code {res.returncode}: {res.stderr.strip()}")
except Exception as e:
    print(f"⚠️ SCP execution exception: {e}")

# Method 2: Try SSH cat
ssh_cmd = [
    "ssh",
    "-i", str(KEY_PATH),
    "-o", "StrictHostKeyChecking=no",
    VM_HOST,
    f"cat {REMOTE_FILE}"
]

try:
    print("Attempting fallback via SSH cat...")
    res2 = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=15)
    if res2.returncode == 0 and res2.stdout.strip():
        token_str = res2.stdout.strip()
        LOCAL_FILE.write_text(token_str, encoding="utf-8")
        print("✅ SUCCESS! Fresh access token downloaded via SSH:")
        print(f"   Token: {token_str[:8]}...{token_str[-6:]}")
        print("\nNow run: python check_nifty_position_only.py")
        sys.exit(0)
    else:
        print(f"❌ SSH command failed: {res2.stderr.strip()}")
except Exception as e:
    print(f"❌ SSH command exception: {e}")

print("\n💡 Alternatively, you can log in directly to generate a fresh token by running:")
print("   python kite_auth_flow.py")
