"""
track_sensex_live.py
====================
Live real-time tracker for BSE SENSEX Spot & Key Expiry Day Hero-Zero Options.
"""

import sys
import datetime
from pathlib import Path
from kiteconnect import KiteConnect

# Fix Windows console UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent

api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

now = datetime.datetime.now()

# Query SENSEX and key expiry strikes
contracts = [
    "BSE:SENSEX",
    "BFO:SENSEX26N1983000CE",
    "BFO:SENSEX26N1983100CE",
    "BFO:SENSEX26N1983200CE",
    "BFO:SENSEX26N1983300CE",
    "BFO:SENSEX26N1982500PE",
    "BFO:SENSEX26N1982000PE"
]

q = kite.quote(contracts)

sx = q.get("BSE:SENSEX", {})
sx_ltp = sx.get("last_price", 0)
sx_ohlc = sx.get("ohlc", {})
sx_prev = sx_ohlc.get("close", sx_ltp)
sx_high = sx_ohlc.get("high", sx_ltp)
sx_low = sx_ohlc.get("low", sx_ltp)
sx_open = sx_ohlc.get("open", sx_ltp)
chg_pts = sx_ltp - sx_prev
chg_pct = (chg_pts / sx_prev * 100) if sx_prev else 0.0

print("=" * 95)
print(f"🔥 SENSEX EXPIRY REAL-TIME LIVE TRACKER | {now.strftime('%Y-%m-%d %H:%M:%S IST')}")
print("=" * 95)
print(f"• SENSEX SPOT LTP:    {sx_ltp:,.2f} ({chg_pts:+.2f} pts | {chg_pct:+.2f}%)")
print(f"• Today's Range:      Low: {sx_low:,.2f}  ───►  High: {sx_high:,.2f} (Total Move: {sx_high - sx_low:,.2f} pts!)")
print(f"• ATM Strike:         {round(sx_ltp / 100) * 100:,}")
print("=" * 95)

print("\n🚀 HERO-ZERO CALL (CE) CONTRACT PROGRESSION:")
print(f"{'Strike':<8} {'Symbol':<24} {'LTP(₹)':<8} {'High(₹)':<9} {'Low(₹)':<8} {'Volume':<12} {'Best Bid / Ask':<20} {'Status'}")
print("-" * 95)

ce_keys = [
    ("83,000 CE", "BFO:SENSEX26N1983000CE", 20),
    ("83,100 CE ⭐", "BFO:SENSEX26N1983100CE", 20),
    ("83,200 CE", "BFO:SENSEX26N1983200CE", 20),
    ("83,300 CE", "BFO:SENSEX26N1983300CE", 20),
]

for label, sym, lot in ce_keys:
    d = q.get(sym, {})
    ltp = d.get("last_price", 0.0)
    ohlc = d.get("ohlc", {})
    h = ohlc.get("high", 0.0)
    l = ohlc.get("low", 0.0)
    vol = d.get("volume", 0)
    depth = d.get("depth", {})
    b = depth.get("buy", [{}])[0].get("price", 0.0)
    a = depth.get("sell", [{}])[0].get("price", 0.0)

    status = ""
    if "83100" in sym:
        status = "TELEGRAM PICK (+55% from 8.65 alert) 🚀"
    elif ltp <= 5.0:
        status = "ULTRA-CHEAP SWEET SPOT"
    else:
        status = "ACTIVE RUNNER"

    clean_sym = sym.replace("BFO:", "")
    print(f"{label:<12} {clean_sym:<22} ₹{ltp:<7.2f} ₹{h:<8.2f} ₹{l:<7.2f} {vol:<12,d} ₹{b:.2f} / ₹{a:.2f}    {status}")

print("\n🔻 PUT (PE) REVERSAL HEDGES:")
print(f"{'Strike':<8} {'Symbol':<24} {'LTP(₹)':<8} {'High(₹)':<9} {'Low(₹)':<8} {'Volume':<12} {'Best Bid / Ask':<20}")
print("-" * 95)
for label, sym, lot in [("82,500 PE", "BFO:SENSEX26N1982500PE", 20), ("82,000 PE", "BFO:SENSEX26N1982000PE", 20)]:
    d = q.get(sym, {})
    ltp = d.get("last_price", 0.0)
    ohlc = d.get("ohlc", {})
    h = ohlc.get("high", 0.0)
    l = ohlc.get("low", 0.0)
    vol = d.get("volume", 0)
    depth = d.get("depth", {})
    b = depth.get("buy", [{}])[0].get("price", 0.0)
    a = depth.get("sell", [{}])[0].get("price", 0.0)
    clean_sym = sym.replace("BFO:", "")
    print(f"{label:<12} {clean_sym:<22} ₹{ltp:<7.2f} ₹{h:<8.2f} ₹{l:<7.2f} {vol:<12,d} ₹{b:.2f} / ₹{a:.2f}")

print("=" * 95)
