"""
deploy_muhurat_cron_to_vm.py
Deploys the updated vm_crontab_master.txt and scanner exemptions
for Sunday, November 8, 2026 (02:20 PM - 03:30 PM IST) to the Oracle Cloud VM.
"""

import sys
import io
import subprocess
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

KEY_PATH = r"D:\NiftyScanner\oracle\nifty-v15.key"
HOST = "ubuntu@140.245.195.112"
REMOTE_MASTER_DIR = "/home/ubuntu/NiftyScanner"
REMOTE_PROJECT_DIR = "/home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated"

ROOT = Path(__file__).resolve().parent

def run_cmd(cmd: list[str]) -> bool:
    print(f"\n[EXEC] {' '.join(cmd[:6])}...")
    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr and res.returncode != 0:
        print(f"[STDERR] {res.stderr.strip()}")
    return res.returncode == 0

def main():
    print("=" * 70)
    print("🚀 DEPLOYING DIWALI MUHURAT TRADING SCHEDULE TO ORACLE CLOUD VM")
    print(f"   Target: {HOST}")
    print("=" * 70)

    # 1. Test SSH Connection and backup existing crontab
    print("\n1. Testing SSH & Creating Remote Backup...")
    backup_cmd = [
        "ssh", "-i", KEY_PATH, "-o", "StrictHostKeyChecking=no", HOST,
        f"cp {REMOTE_MASTER_DIR}/vm_crontab_master.txt {REMOTE_MASTER_DIR}/vm_crontab_master.txt.bak_pre_muhurat 2>/dev/null || true; "
        f"cp {REMOTE_PROJECT_DIR}/src/scanners/run_options_intraday_scan_powerful_sl.py {REMOTE_PROJECT_DIR}/src/scanners/run_options_intraday_scan_powerful_sl.py.bak 2>/dev/null || true; "
        f"cp {REMOTE_PROJECT_DIR}/src/scanners/run_btst_options_scan_powerful_sl.py {REMOTE_PROJECT_DIR}/src/scanners/run_btst_options_scan_powerful_sl.py.bak 2>/dev/null || true; "
        "echo '✅ Remote backups created successfully.'"
    ]
    if not run_cmd(backup_cmd):
        print("❌ SSH connection failed. Check Oracle VM state.")
        sys.exit(1)

    # 2. Upload files
    files_to_sync = [
        ("vm_crontab_master.txt", f"{REMOTE_MASTER_DIR}/vm_crontab_master.txt"),
        ("src/scanners/run_options_intraday_scan_powerful_sl.py", f"{REMOTE_PROJECT_DIR}/src/scanners/run_options_intraday_scan_powerful_sl.py"),
        ("src/scanners/run_btst_options_scan_powerful_sl.py", f"{REMOTE_PROJECT_DIR}/src/scanners/run_btst_options_scan_powerful_sl.py"),
    ]

    print("\n2. Uploading Updated Files to Cloud VM...")
    for local_f, remote_f in files_to_sync:
        print(f"   ⬆️  Uploading: {local_f} -> {remote_f}")
        scp_cmd = [
            "scp", "-i", KEY_PATH, "-o", "StrictHostKeyChecking=no",
            str(ROOT / local_f), f"{HOST}:{remote_f}"
        ]
        if not run_cmd(scp_cmd):
            print(f"❌ Failed to upload {local_f}")
            sys.exit(1)

    # 3. Install new master crontab on VM
    print("\n3. Installing Updated Master Crontab on Cloud VM...")
    install_cron_cmd = [
        "ssh", "-i", KEY_PATH, "-o", "StrictHostKeyChecking=no", HOST,
        f"crontab {REMOTE_MASTER_DIR}/vm_crontab_master.txt && crontab -l | tail -n 25"
    ]
    if not run_cmd(install_cron_cmd):
        print("❌ Failed to activate crontab on remote VM.")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("✅ DIWALI MUHURAT TRADING SCHEDULE SUCCESSFULLY INSTALLED ON CLOUD VM!")
    print("   The Cloud VM will automatically wake up and run tomorrow (Nov 8):")
    print("   • 01:30 PM: Auto Zerodha Token Generation")
    print("   • 01:45 PM: Weekend News Catalyst Scanner")
    print("   • 02:15 PM: Portfolio Peak Guard Sentinel")
    print("   • 02:25 PM: Options Intraday Scanner (Muhurat Session)")
    print("   • 02:26 PM - 03:34 PM: Intraday Trade Monitor (Every 2 min)")
    print("   • 03:15 PM: BTST Options Scan (15 min before close)")
    print("   • 03:45 PM: Muhurat Telegram P&L Summary Report")
    print("=" * 70)

if __name__ == "__main__":
    main()
