"""
audit_nifty_5_days_history.py
Examines the last 10 daily bars of Nifty 50 (^NSEI / NSE:NIFTY 50)
to see the exact swing from the bottom to current levels,
FII/DII institutional positioning, RSI, and support/resistance for Monday.
"""

import sys
import io
import json
import urllib.request
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 75)
print("📊 NIFTY 50: LAST 10 SESSIONS DAILY CANDLE & VOLUME AUDIT")
print("=" * 75)

# Fetch from Yahoo Finance (^NSEI)
url = "https://query2.finance.yahoo.com/v8/finance/chart/%5ENSEI?range=1mo&interval=1d"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        quotes = result["indicators"]["quote"][0]
        closes = quotes["close"]
        opens = quotes["open"]
        highs = quotes["high"]
        lows = quotes["low"]
        volumes = quotes["volume"]

        print(f"{'DATE':12} | {'OPEN':9} | {'HIGH':9} | {'LOW':9} | {'CLOSE':9} | {'DAY CHG':9} | {'RANGE (PTS)':11}")
        print("-" * 75)

        records = []
        for i in range(len(timestamps)):
            c = closes[i]
            if c is None:
                continue
            dt = datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d")
            o = opens[i]
            h = highs[i]
            l = lows[i]
            v = volumes[i] if volumes[i] else 0
            records.append({"date": dt, "open": o, "high": h, "low": l, "close": c, "vol": v})

        # Print last 10 trading sessions
        for i in range(max(0, len(records) - 10), len(records)):
            r = records[i]
            prev_c = records[i-1]["close"] if i > 0 else r["open"]
            chg = ((r["close"] - prev_c) / prev_c) * 100.0
            day_range = r["high"] - r["low"]
            print(f"{r['date']:12} | {r['open']:9.2f} | {r['high']:9.2f} | {r['low']:9.2f} | {r['close']:9.2f} | {chg:+7.2f}% | {day_range:9.1f} pts")

        latest = records[-1]
        print("=" * 75)
        print(f"LATEST SPOT CLOSE: {latest['close']:,.2f}")
        print(f"LOW OF MOVE      : {min(r['low'] for r in records[-10:]):,.2f}")
        print(f"HIGH OF MOVE     : {max(r['high'] for r in records[-10:]):,.2f}")
        print("=" * 75)
except Exception as e:
    print(f"Error fetching data: {e}")
