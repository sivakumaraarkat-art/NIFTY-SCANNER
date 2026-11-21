"""
analyze_ion_exchange.py
Comprehensive quantitative and technical analysis of ION EXCHANGE (INDIA) (NSE: IONEXCHANG)
Using live Zerodha Kite Connect API and India skills.
"""

import sys
import math
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

# Windows UTF-8 fix
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent

try:
    from kiteconnect import KiteConnect
    api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
    token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(token)
except Exception as e:
    print(f"❌ KiteConnect Error: {e}")
    sys.exit(1)

SYMBOL = "IONEXCHANG"
EXCHANGE = "NSE"
INSTRUMENT_TOKEN = 417281

# 1. Check user holdings/positions
holdings = kite.holdings()
pos = kite.positions().get("net", [])
user_holding = next((h for h in holdings if h["tradingsymbol"] == SYMBOL), None)
user_pos = next((p for p in pos if p["tradingsymbol"] == SYMBOL), None)

# 2. Fetch live quote
q = kite.quote([f"{EXCHANGE}:{SYMBOL}"])[f"{EXCHANGE}:{SYMBOL}"]
ltp = q["last_price"]
ohlc = q["ohlc"]
prev_close = ohlc["close"]
day_open = ohlc["open"]
day_high = ohlc["high"]
day_low = ohlc["low"]
volume = q["volume"]
lower_circuit = q["lower_circuit_limit"]
upper_circuit = q["upper_circuit_limit"]
chg = ltp - prev_close
chg_pct = (chg / prev_close) * 100

# 3. Fetch Historical Data (Daily for 1.5 years)
today = datetime(2026, 11, 8)
from_date = today - timedelta(days=500)
daily_bars = kite.historical_data(INSTRUMENT_TOKEN, from_date.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"), "day")

# Weekly historical data
weekly_from = today - timedelta(days=730)
# Aggregate daily to weekly or fetch 60minute/day
closes = np.array([b["close"] for b in daily_bars])
highs = np.array([b["high"] for b in daily_bars])
lows = np.array([b["low"] for b in daily_bars])
opens = np.array([b["open"] for b in daily_bars])
vols = np.array([b["volume"] for b in daily_bars])
dates = [b["date"] for b in daily_bars]

# 4. Moving Averages
ema_20 = float(np.mean(closes[-20:])) # approx
# Precise EMA 20
k = 2.0 / (20 + 1)
ema_val = closes[0]
for c in closes:
    ema_val = c * k + ema_val * (1 - k)
ema_20 = ema_val

sma_50 = float(np.mean(closes[-50:]))
sma_100 = float(np.mean(closes[-100:]))
sma_200 = float(np.mean(closes[-200:]))

# 52-week High / Low
high_52w = float(np.max(highs[-252:]))
low_52w = float(np.min(lows[-252:]))
high_20d = float(np.max(highs[-20:]))
low_20d = float(np.min(lows[-20:]))

# 5. ATR 14
tr_list = []
for i in range(1, len(closes)):
    tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
    tr_list.append(tr)
atr_14 = float(np.mean(tr_list[-14:]))

# 6. RSI 14
deltas = np.diff(closes)
up = deltas[deltas >= 0].sum() / 14 if len(deltas) >= 14 else 0
down = -deltas[deltas < 0].sum() / 14 if len(deltas) >= 14 else 0
rs = up / down if down != 0 else 0
rsi_14 = 100. - 100. / (1. + rs)

seed = deltas[:14]
up = seed[seed >= 0].sum() / 14
down = -seed[seed < 0].sum() / 14
rs = up / down if down != 0 else 0
rsi_14 = 100. - 100. / (1. + rs)
for d in deltas[14:]:
    upval = d if d > 0 else 0.
    downval = -d if d < 0 else 0.
    up = (up * 13 + upval) / 14
    down = (down * 13 + downval) / 14
    rs = up / down if down != 0 else 0
    rsi_14 = 100. - 100. / (1. + rs)

# 7. Volume metrics
avg_vol_20d = float(np.mean(vols[-20:]))
vol_ratio = volume / avg_vol_20d if avg_vol_20d > 0 else 1.0

# 8. Support and Resistance / Pivot levels
last_high = highs[-1]
last_low = lows[-1]
last_close = closes[-1]
P = (last_high + last_low + last_close) / 3.0
R1 = 2 * P - last_low
S1 = 2 * P - last_high
R2 = P + (last_high - last_low)
S2 = P - (last_high - last_low)
R3 = last_high + 2 * (P - last_low)
S3 = last_low - 2 * (last_high - P)

print("=" * 85)
print("💧 ION EXCHANGE (INDIA) LTD (NSE: IONEXCHANG) - COMPREHENSIVE AUDIT & ANALYSIS")
print("=" * 85)

print("\n1. 👤 USER HOLDINGS & POSITION CHECK:")
print("-" * 85)
if user_holding:
    qty = user_holding['quantity']
    avg = user_holding['average_price']
    inv = qty * avg
    cur = qty * ltp
    pnl = user_holding['pnl']
    pnl_pct = (pnl / inv) * 100 if inv > 0 else 0
    print(f"  • Existing Portfolio Holding: YES")
    print(f"  • Quantity:          {qty} shares")
    print(f"  • Average Buy Price: ₹{avg:.2f}")
    print(f"  • Current Value:     ₹{cur:,.2f} (Invested: ₹{inv:,.2f})")
    print(f"  • Unrealized P&L:    {'+' if pnl >= 0 else ''}₹{pnl:,.2f} ({pnl_pct:+.2f}%)")
else:
    print(f"  • Existing Portfolio Holding: NO (Fresh Investment Candidate)")
if user_pos:
    print(f"  • Open F&O/MIS Position: {user_pos['quantity']} Qty @ ₹{user_pos['average_price']:.2f}")

print("\n2. 📊 LIVE PRICE & VOLUME STRUCTURE (NSE):")
print("-" * 85)
print(f"  • Current LTP:       ₹{ltp:.2f} ({chg_pct:+.2f}% | Chg: ₹{chg:+.2f})")
print(f"  • Day Range:         Low: ₹{day_low:.2f}  -  High: ₹{day_high:.2f} (Open: ₹{day_open:.2f})")
print(f"  • Previous Close:    ₹{prev_close:.2f}")
print(f"  • Traded Volume:     {volume:,d} shares")
print(f"  • 20-Day Avg Volume: {int(avg_vol_20d):,d} shares (Vol Ratio: {vol_ratio:.2f}x)")
print(f"  • Circuits:          Lower: ₹{lower_circuit:.2f} | Upper: ₹{upper_circuit:.2f}")
print(f"  • 52-Week High/Low:  High: ₹{high_52w:.2f} | Low: ₹{low_52w:.2f}")
print(f"  • Distance from 52W High: {((ltp - high_52w) / high_52w)*100:+.2f}%")
print(f"  • Distance from 52W Low:  {((ltp - low_52w) / low_52w)*100:+.2f}%")

print("\n3. 📈 QUANTITATIVE & TECHNICAL MOMENTUM INDICATORS:")
print("-" * 85)
print(f"  • 14-Day RSI:        {rsi_14:.2f}  ({'Bullish Momentum' if rsi_14 >= 60 else 'Neutral/Consolidation' if rsi_14 >= 45 else 'Oversold / Weak'})")
print(f"  • 14-Day ATR:        ₹{atr_14:.2f} ({atr_14/ltp*100:.2f}% daily volatility band)")
print(f"  • 20-Day EMA:        ₹{ema_20:.2f} (Price vs 20 EMA: {((ltp - ema_20)/ema_20)*100:+.2f}%)")
print(f"  • 50-Day SMA:        ₹{sma_50:.2f} (Price vs 50 SMA: {((ltp - sma_50)/sma_50)*100:+.2f}%)")
print(f"  • 100-Day SMA:       ₹{sma_100:.2f}")
print(f"  • 200-Day SMA:       ₹{sma_200:.2f} (Price vs 200 SMA: {((ltp - sma_200)/sma_200)*100:+.2f}%)")

trend_status = []
if ltp > ema_20: trend_status.append("Above 20 EMA (Short-term Bullish)")
else: trend_status.append("Below 20 EMA (Short-term Pullback)")
if ltp > sma_50: trend_status.append("Above 50 SMA (Medium-term Bullish)")
else: trend_status.append("Below 50 SMA (Medium-term Correcting)")
if ltp > sma_200: trend_status.append("Above 200 SMA (Long-term Bull Market)")
else: trend_status.append("Below 200 SMA (Long-term Bearish Base)")
print(f"  • Trend Structure:   {' | '.join(trend_status)}")

print("\n4. 🎯 KEY SUPPORT & RESISTANCE LEVELS (Fibonacci & Classical Pivots):")
print("-" * 85)
print(f"  • Major Resistance 2 (R2): ₹{R2:.2f}")
print(f"  • Immediate Resistance (R1): ₹{R1:.2f}")
print(f"  • Central Pivot (P):        ₹{P:.2f}")
print(f"  • Immediate Support (S1):   ₹{S1:.2f}")
print(f"  • Major Base Support (S2):  ₹{S2:.2f}")
print(f"  • 20-Day Swing High:        ₹{high_20d:.2f}")
print(f"  • 20-Day Swing Low:         ₹{low_20d:.2f}")

print("\n5. 📜 HISTORICAL PERFORMANCE OVER RECENT PERIODS:")
print("-" * 85)
p_1w = ((ltp - closes[-5]) / closes[-5]) * 100 if len(closes) >= 5 else 0
p_1m = ((ltp - closes[-21]) / closes[-21]) * 100 if len(closes) >= 21 else 0
p_3m = ((ltp - closes[-63]) / closes[-63]) * 100 if len(closes) >= 63 else 0
p_6m = ((ltp - closes[-126]) / closes[-126]) * 100 if len(closes) >= 126 else 0
p_1y = ((ltp - closes[-252]) / closes[-252]) * 100 if len(closes) >= 252 else 0
print(f"  • 1-Week Return:     {p_1w:+.2f}%")
print(f"  • 1-Month Return:    {p_1m:+.2f}%")
print(f"  • 3-Month Return:    {p_3m:+.2f}%")
print(f"  • 6-Month Return:    {p_6m:+.2f}%")
print(f"  • 1-Year Return:     {p_1y:+.2f}%")
print("=" * 85)
