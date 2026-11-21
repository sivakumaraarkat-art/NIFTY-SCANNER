"""
check_pre_open_908.py
=====================
Pre-Open Price Discovery Monitor for NSE & BSE (09:00 AM - 09:08 AM - 09:15 AM IST).
Fetches discovered equilibrium price, opening imbalance, buy/sell depth,
and assesses gap-up / gap-down momentum for:
- GAIL (NSE:GAIL) & GAIL 190 CE (NFO:GAIL26NOV190CE)
- SBIN (NSE:SBIN)
- POLYCAB (NSE:POLYCAB)
- NIFTY 50 (NSE:NIFTY 50)
- SENSEX (BSE:SENSEX)
"""

import sys
import time
from datetime import datetime, time as dtime
from pathlib import Path

# Fix Windows console UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent

# Kite Connect
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()

from kiteconnect import KiteConnect
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

WATCHLIST = [
    ("NSE:GAIL", "GAIL (Core Boom Focus)"),
    ("NSE:SBIN", "State Bank of India (Banking Leader)"),
    ("NSE:POLYCAB", "Polycab India (Short Watch)"),
    ("NSE:NIFTY 50", "NIFTY 50 Benchmark"),
    ("BSE:SENSEX", "SENSEX Benchmark (Today's Expiry)")
]

def audit_pre_open():
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    symbols = [s[0] for s in WATCHLIST]
    quotes = kite.quote(symbols)

    print("=" * 105)
    print(f"🔔 NSE / BSE PRE-OPEN PRICE DISCOVERY AUDIT | {now_str} IST")
    print("Pre-Open Window: 09:00 AM - 09:08 AM (Order Collection) | 09:08 AM (Price Discovery Matches)")
    print("=" * 105)

    print(f"{'Security':<38} {'Indicative / LTP':<18} {'Prev Close':<12} {'Discovered Gap':<16} {'Imbalance Qty':<15}")
    print("-" * 105)

    for sym, desc in WATCHLIST:
        q = quotes.get(sym, {})
        ltp = q.get("last_price", 0.0)
        ohlc = q.get("ohlc", {})
        prev = ohlc.get("close", ltp)
        ind_price = q.get("indicative_close_price", 0.0)
        imbalance = q.get("total_imbalance_qty", 0)

        # Discovered price is indicative_price if > 0, else ltp
        discovered_p = ind_price if ind_price > 0 else ltp
        gap_pts = discovered_p - prev
        gap_pct = (gap_pts / prev * 100) if prev else 0.0

        gap_str = f"{gap_pts:+.2f} ({gap_pct:+.2f}%)"
        price_str = f"Rs.{discovered_p:.2f}"
        if ind_price > 0:
            price_str += " (Discovered)"

        imbal_str = f"{imbalance:+,d}" if imbalance != 0 else "Balanced"

        print(f"{desc:<38} {price_str:<18} Rs.{prev:<10.2f} {gap_str:<16} {imbal_str:<15}")

    # Specific deep dive for GAIL
    gail_q = quotes.get("NSE:GAIL", {})
    g_ind = gail_q.get("indicative_close_price", 0.0)
    g_ltp = g_ind if g_ind > 0 else gail_q.get("last_price", 190.0)
    g_prev = gail_q.get("ohlc", {}).get("close", 190.0)

    print("\n" + "=" * 105)
    print("🎯 GAIL 190 CE IMMEDIATE ACTION PLAN BASED ON PRE-OPEN")
    print("=" * 105)

    if g_ind > 0:
        print(f"[*] GAIL Discovered Pre-Open Price: Rs.{g_ind:.2f} (Gap: {((g_ind - g_prev)/g_prev * 100):+.2f}%)")
        if g_ind >= 190.50:
            print("🟢 STRONG BULLISH SIGNAL: GAIL opening ABOVE Strike 190!")
            print("   -> Action: GAIL 190 CE will open strong around Rs.2.20 - Rs.2.60.")
            print("   -> Expected quick jump to T1 (Rs.3.60) in the first 15-30 minutes.")
        elif g_ind >= 189.50:
            print("🟡 NEUTRAL / FLAT OPEN: GAIL opening around 190 ATM pivot.")
            print("   -> Action: Wait for 09:15 AM open. Buy 190 CE if GAIL crosses 190.50 with volume.")
        else:
            print("⚠️ CAUTION: GAIL indicating soft open below 189.50.")
            print("   -> Action: Do not enter 190 CE until GAIL reclaims 190.20+ with volume confirmation.")
    else:
        print("[*] Pre-open order matching is still pending (final rates discover between 09:07 - 09:08 AM).")
        print("    Run this script at 09:08 AM sharp to see the exact confirmed opening price!")

    print("=" * 105)

def wait_until_908():
    now = datetime.now()
    target = now.replace(hour=9, minute=8, second=0, microsecond=0)

    if now >= target:
        print("[*] It is already past 09:08 AM IST. Running pre-open audit immediately...")
        audit_pre_open()
        return

    wait_seconds = (target - now).total_seconds()
    mins = int(wait_seconds // 60)
    secs = int(wait_seconds % 60)
    print(f"[*] Standing by for 09:08 AM IST ({mins}m {secs}s remaining)...")

    while datetime.now() < target:
        rem = (target - datetime.now()).total_seconds()
        if rem <= 0:
            break
        m = int(rem // 60)
        s = int(rem % 60)
        sys.stdout.write(f"\r⏳ Waiting for 09:08:00 AM NSE Discovery... [{m:02d}m {s:02d}s remaining]")
        sys.stdout.flush()
        time.sleep(1)

    print("\n\n🔔 09:08:00 AM REACHED! FETCHING LIVE PRE-OPEN DISCOVERED PRICES...")
    audit_pre_open()

if __name__ == "__main__":
    if "--now" in sys.argv:
        audit_pre_open()
    else:
        wait_until_908()
