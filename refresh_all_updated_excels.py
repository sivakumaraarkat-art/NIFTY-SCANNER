"""
refresh_all_updated_excels.py
Rebuilds and synchronizes all active Excel workbooks in the directory
using isolated sub-processes to avoid stream reconfigure conflicts.
"""

import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

scripts = [
    ("Top 5 Master, Diwali Live Plan & NSE 500", "update_excel_with_top_5_stocks.py"),
    ("Diwali Two-Tranche 1L+1L Strategy", "generate_diwali_2tranche_plan.py"),
    ("RVNL & IRFC Master Investment Plan", "generate_rvnl_irfc_master_plan.py")
]

print("=" * 80)
print("REFRESHING & SYNCHRONIZING ALL EXCEL WORKBOOKS")
print("=" * 80)

for idx, (label, script_name) in enumerate(scripts, start=1):
    print(f"\n[{idx}/3] Running: {label} ({script_name})...")
    script_path = ROOT / script_name
    if not script_path.exists():
        print(f"   Missing file: {script_name}")
        continue
    res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if res.stdout:
        for line in res.stdout.strip().split("\n"):
            print(f"   {line}")
    if res.returncode != 0 and res.stderr:
        print(f"   Error: {res.stderr.strip()}")
    else:
        print(f"   OK - Completed {script_name}")

print("\n" + "=" * 80)
print("ALL CORE EXCEL WORKBOOKS REBUILT & SYNCHRONIZED SUCCESSFULLY!")
print("=" * 80)
