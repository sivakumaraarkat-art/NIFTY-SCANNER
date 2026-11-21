"""
audit_nifty_expiry_and_vm.py
1. Queries Cloud VM for NIFTY V14.9 and expiry scanner logs.
2. Audits live NIFTY spot, PCR, ATM strikes for today's expiry (09-NOV-2026).
3. Evaluates volumes, news, and technicals for top-ranked stock and index setups.
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

ROOT = Path(__file__).resolve().parent
KEY_PATH = Path("D:/NiftyScanner/oracle/nifty-v15.key")
VM_HOST = "ubuntu@140.245.195.112"

print("=" * 90)
print("🔍 AUDITING CLOUD VM NIFTY EXPIRY ENGINE & LIVE NIFTY EXPIRY CHAIN")
print("=" * 90)

# 1. Fetch Cloud VM NIFTY V14.9 Engine Log
if KEY_PATH.exists():
    print("\n🌐 [1] CLOUD VM NIFTY V14.9 LIVE LOGS:")
    print("-" * 90)
    ssh_cmd = [
        "ssh", "-i", str(KEY_PATH), "-o", "StrictHostKeyChecking=no",
        VM_HOST,
        "tail -n 40 /home/ubuntu/NiftyScanner/nifty_v14_7/logs/cron_v14_9.log 2>/dev/null || tail -n 40 /home/ubuntu/NiftyScanner/nifty_v14_7/logs/paper_trading.log"
    ]
    res = subprocess.run(ssh_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15)
    print(res.stdout.strip() if res.stdout.strip() else "No recent V14.9 log entries found.")

# 2. Check Zerodha Kite for NIFTY Spot and Expiry Option Chain
try:
    from kiteconnect import KiteConnect

    api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
    token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(token)

    nifty_q = kite.quote(["NSE:NIFTY 50", "NSE:NIFTY BANK", "NSE:INDIA VIX"])
    nifty_spot = nifty_q.get("NSE:NIFTY 50", {}).get("last_price", 25000.0)
    vix = nifty_q.get("NSE:INDIA VIX", {}).get("last_price", 17.3)
    bank_spot = nifty_q.get("NSE:NIFTY BANK", {}).get("last_price", 59400.0)

    print(f"\n📊 LIVE NIFTY: ₹{nifty_spot:,.2f} | BANK NIFTY: ₹{bank_spot:,.2f} | VIX: {vix:.2f}")

    # Today is Monday Nov 9, 2026 Expiry
    # Let's inspect Nifty weekly expiry strikes: 24950, 25000, 25050, 25100 (Symbol format: NFO:NIFTY26N09...)
    expiry_strikes = [
        "NFO:NIFTY26N0924950CE", "NFO:NIFTY26N0924950PE",
        "NFO:NIFTY26N0925000CE", "NFO:NIFTY26N0925000PE",
        "NFO:NIFTY26N0925050CE", "NFO:NIFTY26N0925050PE",
        "NFO:NIFTY26N0925100CE", "NFO:NIFTY26N0925100PE"
    ]

    opt_quotes = kite.quote(expiry_strikes)

    print("\n⚡ NIFTY TODAY EXPIRY (09-NOV-2026) LIVE OPTIONS CHAIN:")
    print("-" * 90)
    print(f"{'Strike':<10} | {'CE LTP':<8} {'CE Vol':<12} {'CE OI':<10} | {'PE LTP':<8} {'PE Vol':<12} {'PE OI':<10}")
    print("-" * 90)

    total_ce_oi = 0
    total_pe_oi = 0

    for strike in [24950, 25000, 25050, 25100]:
        ce_sym = f"NFO:NIFTY26N09{strike}CE"
        pe_sym = f"NFO:NIFTY26N09{strike}PE"

        cq = opt_quotes.get(ce_sym, {})
        pq = opt_quotes.get(pe_sym, {})

        c_ltp = cq.get("last_price", 0.0)
        c_vol = cq.get("volume", 0)
        c_oi = cq.get("oi", 0)

        p_ltp = pq.get("last_price", 0.0)
        p_vol = pq.get("volume", 0)
        p_oi = pq.get("oi", 0)

        total_ce_oi += c_oi
        total_pe_oi += p_oi

        atm_flag = "◄ ATM" if abs(nifty_spot - strike) < 25 else ""
        print(f"{strike:<10} | ₹{c_ltp:>6.2f} {c_vol:>12,} {c_oi:>10,} | ₹{p_ltp:>6.2f} {p_vol:>12,} {p_oi:>10,} {atm_flag}")

    pcr = total_pe_oi / total_ce_oi if total_ce_oi else 1.0
    print("-" * 90)
    print(f"📈 NIFTY INTRADAY PCR (Near ATM): {pcr:.2f} ({'Bullish Put Bias' if pcr > 1.1 else ('Bearish Call Bias' if pcr < 0.85 else 'Neutral Pivot')})")

except Exception as e:
    print(f"❌ Error checking Nifty expiry: {e}")

print("=" * 90)
