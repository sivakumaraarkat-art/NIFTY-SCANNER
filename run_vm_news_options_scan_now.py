"""
run_vm_news_options_scan_now.py
Executes run_options_intraday_scan_powerful_sl.py on the Cloud VM (140.245.195.112)
with --use-news-candidates and fetches live institutional options setups.
"""

import sys
import subprocess
import json
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

print("=" * 90)
print("🌐 EXECUTING CLOUD VM NEWS-DRIVEN OPTIONS SCANNER (LIVE)")
print("=" * 90)

# Remote command to run options scanner using news candidates
remote_cmd = (
    "cd /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated && "
    "PYTHONPATH=/home/ubuntu/NiftyScanner/nifty_v14_7/venv/lib/python3.12/site-packages "
    "/usr/bin/python3 src/scanners/run_options_intraday_scan_powerful_sl.py --use-news-candidates --min-score 50 2>&1"
)

ssh_cmd = [
    "ssh", "-i", str(KEY_PATH), "-o", "StrictHostKeyChecking=no",
    VM_HOST, remote_cmd
]

print("Connecting to Cloud VM and scanning news-driven option strikes...")
res = subprocess.run(ssh_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)

output = res.stdout

# Check if execution log was printed
log_file = None
for line in output.splitlines():
    if "Execution log saved:" in line:
        log_file = line.split("Execution log saved:")[-1].strip()
        break

print("\n" + "-" * 90)
print("📋 CLOUD VM SCANNER TERMINAL OUTPUT SUMMARY:")
print("-" * 90)

# Print clean highlights from scanner output
in_summary = False
for line in output.splitlines():
    if "CANDIDATE" in line or "TRADE EXECUTION PLAN" in line or "Summary:" in line or "Candidates found:" in line:
        in_summary = True
    if in_summary or "Option Symbol:" in line or "LTP:" in line or "Catalyst:" in line or "Score:" in line:
        print(line)

# If log file exists, read structured JSON from VM
if log_file:
    print("\n" + "=" * 90)
    print(f"📊 FETCHING STRUCTURED CANDIDATE DATA FROM {log_file} ON VM:")
    print("=" * 90)
    ssh_cat = [
        "ssh", "-i", str(KEY_PATH), "-o", "StrictHostKeyChecking=no",
        VM_HOST, f"cat /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/{log_file}"
    ]
    res_cat = subprocess.run(ssh_cat, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15)
    try:
        data = json.loads(res_cat.stdout)
        candidates = data.get("candidates", [])
        print(f"Found {len(candidates)} qualified news-backed options setups:\n")
        for i, c in enumerate(candidates, 1):
            sym = c.get("symbol")
            opt = c.get("option_symbol")
            otype = c.get("type")
            score = c.get("score")
            catalyst = c.get("sentiment_catalyst")
            spot = c.get("spot_price")
            ltp = c.get("ltp")
            t1 = c.get("t1")
            t2 = c.get("t2")
            sl = c.get("powerful_sl")
            lot = c.get("lot_size")
            cap = c.get("capital_needed")
            risk = c.get("max_risk")
            warn = c.get("warning_tag", "")

            emoji = "🟢" if otype == "CE" else "🔴"
            print(f"[{i}] {emoji} {sym:<10} | {opt:<24} | Score: {score}/100")
            print(f"    • News Catalyst: {catalyst}")
            print(f"    • Spot Price:    ₹{spot:.2f} | Option LTP: ₹{ltp:.2f}")
            print(f"    • Target 1:      ₹{t1:.2f} (+8%) | Target 2: ₹{t2:.2f} (+15%)")
            print(f"    • Powerful SL:   ₹{sl:.2f} (-20%)")
            print(f"    • Lot Size:      {lot} shares | Capital: ₹{cap:,.2f} | Max Risk: ₹{risk:,.2f}")
            if warn:
                print(f"    • Warning:       {warn}")
            print("-" * 90)
    except Exception as e:
        print(f"Notice parsing JSON: {e}")

print("=" * 90)
