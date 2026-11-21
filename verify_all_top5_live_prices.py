"""
verify_all_top5_live_prices.py
Fetches the exact real-time Zerodha Kite quotes for all 5 stocks:
DIXON, KEI, KAYNES, TITAGARH, PCBL
"""

import sys
import io
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent

try:
    from kiteconnect import KiteConnect
    token_file = ROOT / ".kite_access_token"
    key_file = ROOT / ".kite_api_key"
    access_token = token_file.read_text(encoding="utf-8").strip()
    api_key = key_file.read_text(encoding="utf-8").strip()
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

    symbols = ["NSE:DIXON", "NSE:KEI", "NSE:KAYNES", "NSE:TITAGARH", "NSE:PCBL"]
    quotes = kite.quote(symbols)

    print("=" * 75)
    print("📡 EXACT REAL-TIME ZERODHA KITE QUOTES FOR TOP 5 STOCKS:")
    print("=" * 75)
    print(f"{'SYMBOL':12} | {'LIVE LTP':12} | {'PREV CLOSE':12} | {'DAY HIGH':12} | {'DAY LOW':12} | {'CHANGE %':10}")
    print("-" * 75)

    for sym in symbols:
        if sym in quotes:
            d = quotes[sym]
            ltp = d["last_price"]
            ohlc = d.get("ohlc", {})
            prev = ohlc.get("close", ltp)
            chg = ((ltp - prev) / prev) * 100 if prev else 0
            high = ohlc.get("high", ltp)
            low = ohlc.get("low", ltp)
            clean_sym = sym.replace("NSE:", "")
            print(f"{clean_sym:12} | ₹{ltp:10.2f} | ₹{prev:10.2f} | ₹{high:10.2f} | ₹{low:10.2f} | {chg:+8.2f}%")
    print("=" * 75)
except Exception as e:
    print(f"Error fetching quotes: {e}")
