"""Fetch active master Zerodha Kite access token and api key from Oracle Cloud VM."""
import sys
import os
import subprocess
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

KEY_PATH = r"D:\NiftyScanner\oracle\nifty-v15.key"
HOST = "ubuntu@140.245.195.112"
REMOTE_TOKEN = "/home/ubuntu/NiftyScanner/.kite_access_token"
REMOTE_KEY = "/home/ubuntu/NiftyScanner/.kite_api_key"
LOCAL_TOKEN = Path(".kite_access_token")
LOCAL_KEY = Path(".kite_api_key")

def run_cmd(cmd: list[str]) -> tuple[bool, str]:
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode == 0, res.stdout.strip()

def main():
    print(f"[*] Connecting to Oracle Cloud VM ({HOST})...")

    # Fetch token
    cmd_token = ["ssh", "-i", KEY_PATH, "-o", "StrictHostKeyChecking=no", HOST, f"cat {REMOTE_TOKEN} 2>/dev/null || cat /home/ubuntu/.kite_access_token 2>/dev/null"]
    ok, token_val = run_cmd(cmd_token)
    if ok and token_val:
        token_val = token_val.strip()
        LOCAL_TOKEN.write_text(token_val, encoding="utf-8")
        print(f"[OK] Master Token synchronized successfully! (Token: {token_val[:6]}...{token_val[-4:]})")
    else:
        print("[!] Could not retrieve token from remote VM.")

    # Fetch api key
    cmd_key = ["ssh", "-i", KEY_PATH, "-o", "StrictHostKeyChecking=no", HOST, f"cat {REMOTE_KEY} 2>/dev/null || cat /home/ubuntu/.kite_api_key 2>/dev/null"]
    ok, key_val = run_cmd(cmd_key)
    if ok and key_val:
        key_val = key_val.strip()
        LOCAL_KEY.write_text(key_val, encoding="utf-8")
        print(f"[OK] API Key synchronized successfully! (API Key: {key_val})")

    # Launch live crude script cleanly in fresh process
    print("\n" + "="*80)
    print("Launching Live Crude Oil Option Scanner with Cloud Token...")
    print("="*80 + "\n")
    script = Path(__file__).resolve().parent / "get_crude_live_and_options.py"
    subprocess.run([sys.executable, str(script)])

if __name__ == "__main__":
    main()
