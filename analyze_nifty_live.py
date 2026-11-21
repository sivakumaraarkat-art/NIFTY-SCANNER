from kiteconnect import KiteConnect
from pathlib import Path
import datetime
import numpy as np
import json

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

now = datetime.datetime.now()
print("=" * 70)
print(f"📊 LIVE NIFTY 50 MARKET & DERIVATIVE AUDIT — {now.strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# 1. Fetch live quotes for indices
index_quotes = kite.quote(["NSE:NIFTY 50", "NSE:NIFTY BANK", "NSE:INDIA VIX"])
nifty_q = index_quotes.get("NSE:NIFTY 50", {})
bank_q = index_quotes.get("NSE:NIFTY BANK", {})
vix_q = index_quotes.get("NSE:INDIA VIX", {})

n_ltp = nifty_q.get("last_price", 0.0)
n_ohlc = nifty_q.get("ohlc", {})
n_prev = n_ohlc.get("close", n_ltp)
n_open = n_ohlc.get("open", n_ltp)
n_high = n_ohlc.get("high", n_ltp)
n_low = n_ohlc.get("low", n_ltp)
n_chg = n_ltp - n_prev
n_chg_pct = (n_chg / n_prev * 100) if n_prev else 0

vix_ltp = vix_q.get("last_price", 0.0)
vix_ohlc = vix_q.get("ohlc", {})
vix_prev = vix_ohlc.get("close", vix_ltp)
vix_chg_pct = ((vix_ltp - vix_prev) / vix_prev * 100) if vix_prev else 0

bank_ltp = bank_q.get("last_price", 0.0)
bank_ohlc = bank_q.get("ohlc", {})
bank_prev = bank_ohlc.get("close", bank_ltp)
bank_chg_pct = ((bank_ltp - bank_prev) / bank_prev * 100) if bank_prev else 0

print(f"• NIFTY 50 LTP:    {n_ltp:,.2f}  |  Chg: {n_chg:+,.2f} ({n_chg_pct:+.2f}%)")
print(f"• Today Range:     Open: {n_open:,.2f} | High: {n_high:,.2f} | Low: {n_low:,.2f}")
print(f"• BANK NIFTY LTP:  {bank_ltp:,.2f} ({bank_chg_pct:+.2f}%)")
print(f"• INDIA VIX:       {vix_ltp:.2f} ({vix_chg_pct:+.2f}%)")
print("-" * 70)

# 2. Historical daily data for Moving Averages & Pivots
n_token = nifty_q.get("instrument_token")
to_date = now.strftime("%Y-%m-%d")
from_date = (now - datetime.timedelta(days=200)).strftime("%Y-%m-%d")
hist = kite.historical_data(n_token, from_date, to_date, "day")

closes = np.array([float(b["close"]) for b in hist])
highs = np.array([float(b["high"]) for b in hist])
lows = np.array([float(b["low"]) for b in hist])

sma_20 = np.mean(closes[-20:])
sma_50 = np.mean(closes[-50:])
sma_100 = np.mean(closes[-100:])
sma_200 = np.mean(closes[-200:])

# ATR (14)
tr = []
for i in range(1, len(closes)):
    tr.append(max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1])))
atr14 = np.mean(tr[-14:])

# Classical Floor Pivots from Yesterday (Last closed bar)
prev_h = highs[-1]
prev_l = lows[-1]
prev_c = closes[-1]

pivot = (prev_h + prev_l + prev_c) / 3
r1 = (2 * pivot) - prev_l
s1 = (2 * pivot) - prev_h
r2 = pivot + (prev_h - prev_l)
s2 = pivot - (prev_h - prev_l)
r3 = prev_h + 2 * (pivot - prev_l)
s3 = prev_l - 2 * (prev_h - pivot)

# Camarilla Pivots
cam_range = prev_h - prev_l
h4 = prev_c + cam_range * 1.1 / 2
h3 = prev_c + cam_range * 1.1 / 4
l3 = prev_c - cam_range * 1.1 / 4
l4 = prev_c - cam_range * 1.1 / 2

print("\n🎯 KEY MOVING AVERAGE BENCHMARKS:")
print(f"  • 20-Day SMA  (Short-term Trend):    {sma_20:,.2f} (Dist: {((n_ltp - sma_20)/sma_20)*100:+.2f}%)")
print(f"  • 50-Day SMA  (Intermediate Pivot):  {sma_50:,.2f} (Dist: {((n_ltp - sma_50)/sma_50)*100:+.2f}%)")
print(f"  • 100-Day SMA (Institutional Line):   {sma_100:,.2f} (Dist: {((n_ltp - sma_100)/sma_100)*100:+.2f}%)")
print(f"  • 200-Day SMA (Long-term Bull Floor): {sma_200:,.2f} (Dist: {((n_ltp - sma_200)/sma_200)*100:+.2f}%)")
print(f"  • Daily Expected Move (14-ATR):       ±{atr14:,.1f} points")

print("\n📐 CLASSICAL & CAMARILLA PIVOT ARCHITECTURE:")
print(f"  • Resistance 3 (R3 / Breakout Cap):   {r3:,.2f}")
print(f"  • Resistance 2 (R2 / Camarilla H4):   {r2:,.2f} (Cam H4: {h4:,.2f})")
print(f"  • Resistance 1 (R1 / Camarilla H3):   {r1:,.2f} (Cam H3: {h3:,.2f})")
print(f"  • Daily Central Pivot (P):            {pivot:,.2f}")
print(f"  • Support 1    (S1 / Camarilla L3):   {s1:,.2f} (Cam L3: {l3:,.2f})")
print(f"  • Support 2    (S2 / Camarilla L4):   {s2:,.2f} (Cam L4: {l4:,.2f})")
print(f"  • Support 3    (S3 / Trend Breakdown):{s3:,.2f}")
print("=" * 70)
