import subprocess
import json
from pathlib import Path

KEY_PATH = Path("D:/NiftyScanner/oracle/nifty-v15.key")
VM_HOST = "ubuntu@140.245.195.112"

cmd = [
    "ssh",
    "-i", str(KEY_PATH),
    "-o", "StrictHostKeyChecking=no",
    VM_HOST,
    "cat /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/logs/intraday_scan_powerful_sl_20261109_105013.json"
]

res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
data = json.loads(res.stdout)

print("=" * 90)
print(f"📊 CLOUD VM LIVE QUALIFIED OPTIONS CANDIDATES (Scan Time: {data['execution']['timestamp']})")
print("=" * 90)

for i, c in enumerate(data.get("candidates", []), 1):
    sym = c.get("symbol")
    opt = c.get("option_symbol")
    opt_type = c.get("type")
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
    delta = c.get("delta")
    iv = c.get("iv")
    warn = c.get("warning_tag", "")

    emoji = "🟢" if opt_type == "CE" else "🔴"
    print(f"[{i}] {emoji} {sym:<10} | {opt:<24} | Score: {score}/100")
    print(f"    • Catalyst:    {catalyst}")
    print(f"    • Spot Price:  ₹{spot:.2f} | Option LTP: ₹{ltp:.2f}")
    print(f"    • Target 1:    ₹{t1:.2f} (+8%) | Target 2: ₹{t2:.2f} (+15%)")
    print(f"    • Powerful SL: ₹{sl:.2f} (-20%) | Delta: {delta} | IV: {iv:.1f}%")
    print(f"    • Lot Size:    {lot} shares | Capital: ₹{cap:,.2f} | Max Risk: ₹{risk:,.2f}")
    if warn:
        print(f"    • Warnings:    {warn}")
    print("-" * 90)
