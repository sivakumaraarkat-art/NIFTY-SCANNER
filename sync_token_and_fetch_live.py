import sys
import os
import subprocess
import shutil
from pathlib import Path

# UTF-8 fix for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

KEY_PATH = r"D:\NiftyScanner\oracle\nifty-v15.key"
VM_HOST = "ubuntu@140.245.195.112"
REMOTE_TOKEN_PATH = "/home/ubuntu/NiftyScanner/.kite_access_token"

LOCAL_TARGETS = [
    Path(r"D:\NiftyScanner\.kite_access_token"),
    Path(r"D:\NiftyScanner\STOCK_SWING_V1_updated\.kite_access_token")
]

def sync_token():
    print("=" * 80)
    print("☁️  FETCHING MASTER KITE ACCESS TOKEN FROM CLOUD ORACLE VM")
    print("=" * 80)
    print(f"VM Host:   {VM_HOST}")
    print(f"Key Path:  {KEY_PATH}")
    print(f"Remote:    {REMOTE_TOKEN_PATH}")
    print("-" * 80)

    # Use scp to download
    temp_target = LOCAL_TARGETS[0]
    scp_cmd = [
        "scp",
        "-i", KEY_PATH,
        "-o", "StrictHostKeyChecking=no",
        f"{VM_HOST}:{REMOTE_TOKEN_PATH}",
        str(temp_target)
    ]

    try:
        print("Connecting to Oracle VM via SCP...")
        result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=20)
        if result.returncode != 0:
            print(f"❌ SCP failed with error:\n{result.stderr}")
            print("\nTrying SSH cat fallback...")
            ssh_cmd = [
                "ssh",
                "-i", KEY_PATH,
                "-o", "StrictHostKeyChecking=no",
                VM_HOST,
                f"cat {REMOTE_TOKEN_PATH}"
            ]
            ssh_res = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=20)
            if ssh_res.returncode == 0 and ssh_res.stdout.strip():
                token_val = ssh_res.stdout.strip()
                for target in LOCAL_TARGETS:
                    target.write_text(token_val, encoding="utf-8")
                print(f"✅ Master token successfully fetched via SSH: {token_val[:6]}...{token_val[-4:]}")
            else:
                print(f"❌ SSH also failed:\n{ssh_res.stderr}")
                return False
        else:
            token_val = temp_target.read_text(encoding="utf-8").strip()
            # Copy to second target
            LOCAL_TARGETS[1].write_text(token_val, encoding="utf-8")
            print(f"✅ Token downloaded successfully! ({token_val[:6]}...{token_val[-4:]})")
            print(f"   Saved to: {LOCAL_TARGETS[0]}")
            print(f"   Saved to: {LOCAL_TARGETS[1]}")

        print("\n" + "=" * 80)
        print("🚀 RUNNING LIVE ZERODHA AUDIT...")
        print("=" * 80)

        # Now run fetch_zerodha_diwali_live.py directly
        subprocess.run([sys.executable, "fetch_zerodha_diwali_live.py"])
        return True

    except Exception as e:
        print(f"❌ Exception during sync: {e}")
        return False

if __name__ == "__main__":
    sync_token()
