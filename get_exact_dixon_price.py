"""
get_exact_dixon_price.py
Queries the exact live price of DIXON from:
  1. Zerodha Kite Connect live quote API
  2. Parquet daily cache file
  3. Yahoo Finance (DIXON.NS)
"""

import sys
import io
from pathlib import Path
import json

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent

print("=" * 60)
print("🔍 CHECKING EXACT REAL-TIME PRICE FOR DIXON (NSE:DIXON)")
print("=" * 60)

# 1. Zerodha Kite
try:
    from kiteconnect import KiteConnect
    token_file = ROOT / ".kite_access_token"
    key_file = ROOT / ".kite_api_key"
    if token_file.exists() and key_file.exists():
        access_token = token_file.read_text(encoding="utf-8").strip()
        api_key = key_file.read_text(encoding="utf-8").strip()
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)

        q = kite.quote(["NSE:DIXON"])
        if q and "NSE:DIXON" in q:
            d = q["NSE:DIXON"]
            print(f"📡 ZERODHA KITE LIVE QUOTE:")
            print(f"   Symbol: {d.get('instrument_token')} (NSE:DIXON)")
            print(f"   Last Price (LTP): ₹{d.get('last_price'):,.2f}")
            ohlc = d.get("ohlc", {})
            print(f"   Open: ₹{ohlc.get('open'):,.2f} | High: ₹{ohlc.get('high'):,.2f} | Low: ₹{ohlc.get('low'):,.2f} | Prev Close: ₹{ohlc.get('close'):,.2f}")
            print(f"   Change: {((d.get('last_price') - ohlc.get('close'))/ohlc.get('close'))*100:+.2f}%")
            print(f"   Volume: {d.get('volume'):,}")
            print(f"   Last Traded Time: {d.get('last_trade_time')}")
except Exception as e:
    print(f"❌ Zerodha Kite query error: {e}")

# 2. Parquet Cache
try:
    import pandas as pd
    p_file = ROOT / "database" / "market_data_cache" / "NSE_DIXON_daily.parquet"
    if p_file.exists():
        df = pd.read_parquet(p_file)
        print(f"\n📊 PARQUET CACHE (Last 5 Bars):")
        tail = df.tail(5)[["close", "high", "low", "volume"]]
        print(tail)
        print(f"   Latest Date in Cache: {df.index[-1] if hasattr(df, 'index') else 'N/A'}")
        if 'date' in df.columns:
            print(f"   Latest Date column: {df['date'].iloc[-1]}")
        print(f"   Latest Close in Cache: ₹{df['close'].iloc[-1]:,.2f}")
except Exception as e:
    print(f"❌ Parquet query error: {e}")

# 3. Yahoo Finance Direct Query
try:
    import urllib.request
    req = urllib.request.Request(
        "https://query2.finance.yahoo.com/v8/finance/chart/DIXON.NS?range=1d&interval=1d",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        meta = data["chart"]["result"][0]["meta"]
        reg_price = meta.get("regularMarketPrice")
        prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
        high_52w = meta.get("fiftyTwoWeekHigh")
        low_52w = meta.get("fiftyTwoWeekLow")
        print(f"\n🌐 YAHOO FINANCE LIVE FEED (DIXON.NS):")
        print(f"   Current Price: ₹{reg_price:,.2f}")
        print(f"   Previous Close: ₹{prev_close:,.2f}")
        print(f"   52-Week High: ₹{high_52w:,.2f} | 52-Week Low: ₹{low_52w:,.2f}")
except Exception as e:
    print(f"❌ Yahoo query error: {e}")

print("=" * 60)
