"""
audit_ion_history.py
Examines multi-year price structure, volume clusters, weekly patterns,
and institutional support zones for ION EXCHANGE (INDIA).
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

ROOT = Path(__file__).resolve().parent

from kiteconnect import KiteConnect
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

today = datetime(2026, 11, 8)
from_date = today - timedelta(days=1100)
bars = kite.historical_data(417281, from_date.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"), "day")

print(f"Total Daily Bars: {len(bars)} (From {bars[0]['date'].strftime('%Y-%m-%d')} to {bars[-1]['date'].strftime('%Y-%m-%d')})")

closes = [b["close"] for b in bars]
highs = [b["high"] for b in bars]
lows = [b["low"] for b in bars]
vols = [b["volume"] for b in bars]

max_p = max(highs)
min_p = min(lows)
current_p = closes[-1]

print(f"• Period Peak (ATH / 3Y High): ₹{max_p:.2f}")
print(f"• Period Trough (3Y Low):      ₹{min_p:.2f}")
print(f"• Current Price:               ₹{current_p:.2f}")
print(f"• Drawdown from Peak:          {((current_p - max_p) / max_p) * 100:.2f}%")

# Volume Spikes
sorted_vol = sorted(bars, key=lambda x: x["volume"], reverse=True)
print("\n🔥 TOP 5 INSTITUTIONAL VOLUME SPIKES (3-YEAR WINDOW):")
print(f"{'DATE':<12} | {'VOLUME':<12} | {'OPEN':<8} | {'HIGH':<8} | {'LOW':<8} | {'CLOSE':<8} | {'DAY CHG %'}")
print("-" * 75)
for b in sorted_vol[:5]:
    dt = b["date"].strftime("%Y-%m-%d")
    v = b["volume"]
    o, h, l, c = b["open"], b["high"], b["low"], b["close"]
    chg = ((c - o) / o) * 100
    print(f"{dt:<12} | {v:>12,d} | {o:>8.2f} | {h:>8.2f} | {l:>8.2f} | {c:>8.2f} | {chg:>+7.2f}%")

# Support zones in the ₹280 - ₹320 range
print("\n🧱 HISTORICAL CONGESTION / REACTION AROUND ₹290 - ₹320 (SUPPORT ZONE):")
touches = [b for b in bars if 285.0 <= b["low"] <= 315.0 or 285.0 <= b["close"] <= 315.0]
print(f"Found {len(touches)} historical bars trading in the ₹285 - ₹315 demand band.")
if touches:
    # Look at the earliest dates and most recent
    print(f"  • First major consolidation: {touches[0]['date'].strftime('%Y-%m-%d')} - {touches[min(5, len(touches)-1)]['date'].strftime('%Y-%m-%d')}")
    print(f"  • Most recent test:          {touches[-1]['date'].strftime('%Y-%m-%d')}")

# Weekly aggregation
weekly = []
cur_w = None
cur_bar = None
for b in bars:
    dt = b["date"]
    yr, wk, _ = dt.isocalendar()
    key = (yr, wk)
    if key != cur_w:
        if cur_bar:
            weekly.append(cur_bar)
        cur_w = key
        cur_bar = {
            "date": dt,
            "open": b["open"],
            "high": b["high"],
            "low": b["low"],
            "close": b["close"],
            "volume": b["volume"]
        }
    else:
        cur_bar["high"] = max(cur_bar["high"], b["high"])
        cur_bar["low"] = min(cur_bar["low"], b["low"])
        cur_bar["close"] = b["close"]
        cur_bar["volume"] += b["volume"]
if cur_bar:
    weekly.append(cur_bar)

print(f"\n📊 LAST 8 WEEKS CANDLESTICK STRUCTURE:")
print(f"{'WEEK ENDING':<12} | {'OPEN':<8} | {'HIGH':<8} | {'LOW':<8} | {'CLOSE':<8} | {'VOL':<10} | {'WEEK CHG %'}")
print("-" * 75)
for w in weekly[-8:]:
    dt = w["date"].strftime("%Y-%m-%d")
    o, h, l, c, v = w["open"], w["high"], w["low"], w["close"], w["volume"]
    wchg = ((c - o) / o) * 100
    print(f"{dt:<12} | {o:>8.2f} | {h:>8.2f} | {l:>8.2f} | {c:>8.2f} | {v:>10,d} | {wchg:>+7.2f}%")
