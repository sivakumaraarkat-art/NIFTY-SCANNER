"""
deploy_expiry_crontab_to_vm.py
Deploys updated master crontab to Cloud VM with Monday expiry activation.
"""

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

KEY_PATH = Path("D:/NiftyScanner/oracle/nifty-v15.key")
VM_HOST = "ubuntu@140.245.195.112"
LOCAL_CRON = Path("D:/NiftyScanner/STOCK_SWING_V1_updated/vm_crontab_master.txt")
REMOTE_CRON = "/home/ubuntu/NiftyScanner/vm_crontab_master.txt"

print("=" * 80)
print("🚀 DEPLOYING UPDATED MASTER CRONTAB TO CLOUD VM (140.245.195.112)")
print("=" * 80)

# Step 1: Backup remote crontab
ssh_backup = [
    "ssh", "-i", str(KEY_PATH), "-o", "StrictHostKeyChecking=no",
    VM_HOST, f"cp {REMOTE_CRON} {REMOTE_CRON}.bak"
]
subprocess.run(ssh_backup, capture_output=True, text=True, timeout=15)
print("✅ Created backup: vm_crontab_master.txt.bak on Cloud VM")

# Step 2: SCP updated file
scp_cmd = [
    "scp", "-i", str(KEY_PATH), "-o", "StrictHostKeyChecking=no",
    str(LOCAL_CRON), f"{VM_HOST}:{REMOTE_CRON}"
]
res_scp = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=15)
if res_scp.returncode == 0:
    print("✅ Uploaded updated vm_crontab_master.txt to Cloud VM")
else:
    print(f"❌ SCP failed: {res_scp.stderr}")
    sys.exit(1)

# Step 3: Install crontab on Cloud VM
ssh_install = [
    "ssh", "-i", str(KEY_PATH), "-o", "StrictHostKeyChecking=no",
    VM_HOST, f"crontab {REMOTE_CRON}"
]
res_install = subprocess.run(ssh_install, capture_output=True, text=True, timeout=15)
if res_install.returncode == 0:
    print("✅ Installed crontab successfully into Ubuntu crontab engine!")
else:
    print(f"❌ Crontab install failed: {res_install.stderr}")
    sys.exit(1)

# Step 4: Verify installed crontab
ssh_verify = [
    "ssh", "-i", str(KEY_PATH), "-o", "StrictHostKeyChecking=no",
    VM_HOST, "crontab -l | grep -A 3 '10a. NIFTY Expiry'"
]
res_verify = subprocess.run(ssh_verify, capture_output=True, text=True, timeout=15)
print("\n🔍 VERIFIED INSTALLED CRONTAB ON CLOUD VM:")
print("-" * 80)
print(res_verify.stdout.strip())
print("=" * 80)
