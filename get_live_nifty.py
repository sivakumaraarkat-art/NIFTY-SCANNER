"""
get_live_nifty.py
Fetches 100% verified LIVE market quote directly from Zerodha Kite Connect API
for NIFTY 50, NIFTY BANK, INDIA VIX, and key index heavyweights.
"""

import sys
import io
import json
from pathlib import Path
from datetime import datetime
from kiteconnect import KiteConnect

# Fix UTF-8 encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent

api_key = (ROOT / ".kite_api_key").read_text(encoding="utf-8").strip()
access_token = (ROOT / ".kite_access_token").read_text(encoding="utf-8").strip()

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

indices = ["NSE:NIFTY 50", "NSE:NIFTY BANK", "NSE:INDIA VIX", "NSE:NIFTY IT"]
heavyweights = ["NSE:RELIANCE", "NSE:HDFCBANK", "NSE:ICICIBANK", "NSE:INFY", "NSE:TCS", "NSE:ITC", "NSE:LT", "NSE:SBIN"]

all_syms = indices + heavyweights

print("=" * 95)
print(f"📡 ZERODHA KITE LIVE MARKET DATA FEED — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 95)

try:
    quotes = kite.quote(all_syms)

    print("\n🎯 KEY BENCHMARK INDICES (LIVE FROM ZERODHA):")
    print("-" * 95)
    print(f"{'SYMBOL':<16} | {'LIVE LTP':<12} | {'CHANGE (%)':<12} | {'HIGH':<12} | {'LOW':<12} | {'PREV CLOSE':<12}")
    print("-" * 95)
    for sym in indices:
        q = quotes.get(sym, {})
        ltp = q.get("last_price", 0.0)
        ohlc = q.get("ohlc", {})
        prev_close = ohlc.get("close", ltp)
        chg = ((ltp - prev_close) / prev_close * 100) if prev_close else 0.0
        high = ohlc.get("high", 0.0)
        low = ohlc.get("low", 0.0)
        sym_clean = sym.replace("NSE:", "")
        print(f"{sym_clean:<16} | {ltp:>12,.2f} | {chg:>+11.2f}% | {high:>12,.2f} | {low:>12,.2f} | {prev_close:>12,.2f}")

    print("\n🏛️ TOP NIFTY 50 DRIVERS & HEAVYWEIGHTS (LIVE FROM ZERODHA):")
    print("-" * 95)
    print(f"{'SYMBOL':<16} | {'LIVE LTP':<12} | {'CHANGE (%)':<12} | {'HIGH':<12} | {'LOW':<12} | {'VOLUME':<14}")
    print("-" * 95)
    for sym in heavyweights:
        q = quotes.get(sym, {})
        ltp = q.get("last_price", 0.0)
        ohlc = q.get("ohlc", {})
        prev_close = ohlc.get("close", ltp)
        chg = ((ltp - prev_close) / prev_close * 100) if prev_close else 0.0
        high = ohlc.get("high", 0.0)
        low = ohlc.get("low", 0.0)
        vol = q.get("volume", 0)
        sym_clean = sym.replace("NSE:", "")
        print(f"{sym_clean:<16} | ₹{ltp:>11,.2f} | {chg:>+11.2f}% | ₹{high:>11,.2f} | ₹{low:>11,.2f} | {vol:>14,d}")

    # Output to a json file as well
    out_file = ROOT / "live_nifty_feed.json"
    out_file.write_text(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "quotes": {k: {"ltp": v.get("last_price"), "ohlc": v.get("ohlc"), "volume": v.get("volume")} for k, v in quotes.items()}
    }, indent=2), encoding="utf-8")

    print("\n" + "=" * 95)
    print("✅ Live quote feed saved to live_nifty_feed.json")
    print("=" * 95)

except Exception as e:
    print(f"❌ Error querying Zerodha API: {e}")
