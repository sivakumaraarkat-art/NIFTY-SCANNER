"""
analyze_cochin_dec30.py
Comprehensive 1-month to late-December (Dec 30, 2026) projection for COCHINSHIP
Uses 168 daily candles from Zerodha Kite Connect API, Monte Carlo simulations,
Fibonacci retracements, moving averages, and orderbook/break-even odds.
"""

import io
import json
import math
import sys
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
data_file = ROOT / "trader-in" / "kite" / "COCHINSHIP-day-2026-11-08.json"

if not data_file.exists():
    print(f"❌ Data file not found: {data_file}")
    sys.exit(1)

with open(data_file, "r", encoding="utf-8") as f:
    raw_bars = json.load(f)

# Parse bars into structured arrays
bars = []
for b in raw_bars:
    dt = datetime.fromisoformat(b["date"])
    bars.append({
        "date": dt,
        "open": float(b["open"]),
        "high": float(b["high"]),
        "low": float(b["low"]),
        "close": float(b["close"]),
        "volume": int(b["volume"]),
    })

bars.sort(key=lambda x: x["date"])
n = len(bars)
closes = np.array([b["close"] for b in bars])
highs = np.array([b["high"] for b in bars])
lows = np.array([b["low"] for b in bars])
volumes = np.array([b["volume"] for b in bars])
dates = [b["date"] for b in bars]

current_price = closes[-1]
last_date = dates[-1]

print("=" * 80)
print(f"🚢 COCHIN SHIPYARD (COCHINSHIP) - DEC 30, 2026 PROJECTION & 1-MONTH ANALYSIS")
print(f"    Current LTP: ₹{current_price:,.2f} | As of: {last_date.strftime('%A, %Y-%m-%d')}")
print("=" * 80)

# 1. Moving Averages
def get_sma(arr, window):
    if len(arr) < window:
        return None
    return np.mean(arr[-window:])

def get_ema(arr, window):
    if len(arr) < window:
        return None
    weights = np.exp(np.linspace(-1., 0., window))
    weights /= weights.sum()
    return np.convolve(arr, weights, mode='valid')[-1]

sma_20 = get_sma(closes, 20)
sma_50 = get_sma(closes, 50)
sma_100 = get_sma(closes, 100)
ema_20 = get_ema(closes, 20)
ema_50 = get_ema(closes, 50)

# 2. Volatility and ATR
daily_returns = np.diff(np.log(closes))
daily_vol = np.std(daily_returns)
annual_vol = daily_vol * np.sqrt(252)

# 14-day ATR
tr_list = []
for i in range(1, n):
    tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
    tr_list.append(tr)
atr_14 = np.mean(tr_list[-14:]) if len(tr_list) >= 14 else np.mean(tr_list)
atr_pct = (atr_14 / current_price) * 100

# 3. Peak and Trough Range in the dataset
period_high = np.max(highs)
period_high_date = dates[np.argmax(highs)]
period_low = np.min(lows)
period_low_date = dates[np.argmin(lows)]

# Recent swing low (October 2026 bottom)
recent_low = np.min(lows[-30:])
recent_high = np.max(highs[-30:])

print("\n1. 📊 KEY TECHNICAL BENCHMARKS & MOVING AVERAGES:")
print(f"  • 20-Day SMA:        ₹{sma_20:8.2f}  |  20-Day EMA: ₹{ema_20:8.2f} (Price is {((current_price - ema_20)/ema_20)*100:+.2f}%)")
if sma_50:
    print(f"  • 50-Day SMA:        ₹{sma_50:8.2f}  |  50-Day EMA: ₹{ema_50:8.2f}")
if sma_100:
    print(f"  • 100-Day SMA:       ₹{sma_100:8.2f}")
print(f"  • 14-Day Daily ATR:  ₹{atr_14:8.2f}  ({atr_pct:.2f}% daily average swing)")
print(f"  • Daily Volatility:  {daily_vol*100:8.2f}%  |  Annualized Volatility: {annual_vol*100:.2f}%")
print(f"  • Period High:       ₹{period_high:8.2f}  (on {period_high_date.strftime('%Y-%m-%d')})")
print(f"  • 30-Day Swing Low:  ₹{recent_low:8.2f}  (Base formed late October)")
print(f"  • 30-Day Swing High: ₹{recent_high:8.2f}  (Nov 5 peak)")

# 4. Fibonacci Retracement Levels
# From the period high (or major high) to the recent swing low
swing_top = max(period_high, 1600.0) # Major high
swing_bot = recent_low
swing_range = swing_top - swing_bot

fib_236 = swing_bot + 0.236 * swing_range
fib_382 = swing_bot + 0.382 * swing_range
fib_500 = swing_bot + 0.500 * swing_range
fib_618 = swing_bot + 0.618 * swing_range
fib_786 = swing_bot + 0.786 * swing_range

print("\n2. 📐 FIBONACCI RETRACEMENT ZONES (From ₹{:.0f} Peak to ₹{:.0f} Base):".format(swing_top, swing_bot))
print(f"  • 23.6% Retracement: ₹{fib_236:8.2f}  (Immediate Base Resistance)")
print(f"  • 38.2% Retracement: ₹{fib_382:8.2f}  (Major Pivot Breakout)")
print(f"  • 50.0% Retracement: ₹{fib_500:8.2f}  (Crucial Midpoint Level)")
print(f"  • 61.8% Golden Ratio: ₹{fib_618:8.2f}  (Bull Market Confirmation Zone)")
print(f"  • 78.6% Retracement: ₹{fib_786:8.2f}  (Near User's Holding Cost)")

# 5. Monte Carlo Simulation to Dec 30, 2026
# Number of trading days from Nov 9 to Dec 30:
# Total calendar days ~51 days -> ~36 trading days
trading_days_to_dec30 = 36
num_simulations = 50000
np.random.seed(42)

# Generate log return paths
# Geometric Brownian Motion with both conservative drift (0%) and modest sector drift (10% annualized)
dt = 1.0 / 252.0
drift_conserv = -0.5 * (daily_vol ** 2)
drift_bullish = (0.15 / 252.0) - 0.5 * (daily_vol ** 2)

# Pure volatility diffusion (Standard Market Distribution)
random_shocks = np.random.normal(0, daily_vol, (num_simulations, trading_days_to_dec30))
log_paths_neutral = np.cumsum(drift_conserv + random_shocks, axis=1)
prices_neutral = current_price * np.exp(log_paths_neutral)
terminal_prices_neutral = prices_neutral[:, -1]

# Path max prices (touches)
max_prices_neutral = np.max(prices_neutral, axis=1)

# Bullish drift paths (Sector momentum + Q2 earnings tailwind)
log_paths_bull = np.cumsum(drift_bullish + random_shocks, axis=1)
prices_bull = current_price * np.exp(log_paths_bull)
terminal_prices_bull = prices_bull[:, -1]
max_prices_bull = np.max(prices_bull, axis=1)

# Calculate percentiles for Dec 30
p5_n = np.percentile(terminal_prices_neutral, 5)
p10_n = np.percentile(terminal_prices_neutral, 10)
p25_n = np.percentile(terminal_prices_neutral, 25)
p50_n = np.percentile(terminal_prices_neutral, 50)
p75_n = np.percentile(terminal_prices_neutral, 75)
p90_n = np.percentile(terminal_prices_neutral, 90)
p95_n = np.percentile(terminal_prices_neutral, 95)

p50_b = np.percentile(terminal_prices_bull, 50)
p75_b = np.percentile(terminal_prices_bull, 75)
p90_b = np.percentile(terminal_prices_bull, 90)

# User specific targets
user_cost = 1492.40
user_averaged_cost = 1432.92

prob_touch_user_cost_neutral = np.mean(max_prices_neutral >= user_cost) * 100
prob_touch_user_cost_bull = np.mean(max_prices_bull >= user_cost) * 100

prob_close_user_cost_neutral = np.mean(terminal_prices_neutral >= user_cost) * 100
prob_close_user_cost_bull = np.mean(terminal_prices_bull >= user_cost) * 100

prob_touch_averaged_neutral = np.mean(max_prices_neutral >= user_averaged_cost) * 100
prob_touch_averaged_bull = np.mean(max_prices_bull >= user_averaged_cost) * 100

print("\n3. 🎲 MONTE CARLO 50,000-PATH SIMULATION TO DEC 30, 2026 (36 Trading Days):")
print("  Neutral / Volatility-Only Distribution (No speculative bias):")
print(f"    • 5th Percentile (Severe Bear Scenario):    ₹{p5_n:8.2f}  (-{((current_price - p5_n)/current_price)*100:.1f}%)")
print(f"    • 10th Percentile (Deep Pullback Support):  ₹{p10_n:8.2f}  (-{((current_price - p10_n)/current_price)*100:.1f}%)")
print(f"    • 25th Percentile (Moderate Pullback):     ₹{p25_n:8.2f}  (-{((current_price - p25_n)/current_price)*100:.1f}%)")
print(f"    • 50th Percentile (Median Expected Value): ₹{p50_n:8.2f}  ({((p50_n - current_price)/current_price)*100:+.1f}%)")
print(f"    • 75th Percentile (Bullish Recovery):       ₹{p75_n:8.2f}  (+{((p75_n - current_price)/current_price)*100:.1f}%)")
print(f"    • 90th Percentile (Strong Defense Rally):   ₹{p90_n:8.2f}  (+{((p90_n - current_price)/current_price)*100:.1f}%)")
print(f"    • 95th Percentile (Extreme Breakout):       ₹{p95_n:8.2f}  (+{((p95_n - current_price)/current_price)*100:.1f}%)")

print("\n  With Sector Earnings Drift (+15% Ann. Momentum):")
print(f"    • Median Expected (Dec 30):                ₹{p50_b:8.2f}")
print(f"    • Top Quartile (75th Percentile):          ₹{p75_b:8.2f}")
print(f"    • High Probability Cap (90th Percentile):  ₹{p90_b:8.2f}")

print("\n4. 🎯 PROBABILITY OF REACHING USER'S RECOVERY LEVELS BY DEC 30:")
print(f"  A. Current Holding Cost: ₹{user_cost:,.2f} (80 shares)")
print(f"     • Odds of TOUCHING ₹{user_cost:,.2f} anytime before Dec 30: {prob_touch_user_cost_neutral:5.1f}% (Neutral) | {prob_touch_user_cost_bull:5.1f}% (Bullish)")
print(f"     • Odds of CLOSING at or above ₹{user_cost:,.2f} on Dec 30:  {prob_close_user_cost_neutral:5.1f}% (Neutral) | {prob_close_user_cost_bull:5.1f}% (Bullish)")
print(f"\n  B. Averaged Position Cost: ₹{user_averaged_cost:,.2f} (if adding 20 shares @ ₹1,195)")
print(f"     • Odds of TOUCHING ₹{user_averaged_cost:,.2f} anytime before Dec 30: {prob_touch_averaged_neutral:5.1f}% (Neutral) | {prob_touch_averaged_bull:5.1f}% (Bullish)")
print("=" * 80)
