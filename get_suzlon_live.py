"""
get_suzlon_live.py
Fetches live quote, technical moving averages, RSI, pivot levels,
and user's Zerodha portfolio holding details for SUZLON.
"""

import sys
import io
import json
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

# Fix UTF-8 encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent

try:
    from kiteconnect import KiteConnect
    api_key = (ROOT / ".kite_api_key").read_text(encoding="utf-8").strip()
    access_token = (ROOT / ".kite_access_token").read_text(encoding="utf-8").strip()
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
except Exception as e:
    print(f"❌ Failed to connect to Kite API: {e}")
    sys.exit(1)

symbol = "NSE:SUZLON"

print("=" * 90)
print(f"📡 ZERODHA LIVE AUDIT & TECHNICAL ANALYSIS — SUZLON ENERGY LIMITED")
print("=" * 90)

# 1. LIVE QUOTE & CIRCUIT LIMITS
try:
    quotes = kite.quote([symbol])
    q = quotes.get(symbol, {})
    ltp = q.get("last_price", 0.0)
    ohlc = q.get("ohlc", {})
    prev_close = ohlc.get("close", ltp)
    open_price = ohlc.get("open", 0.0)
    high_price = ohlc.get("high", 0.0)
    low_price = ohlc.get("low", 0.0)
    chg = ((ltp - prev_close) / prev_close * 100) if prev_close else 0.0
    vol = q.get("volume", 0)
    lower_circuit = q.get("lower_circuit_limit", 0.0)
    upper_circuit = q.get("upper_circuit_limit", 0.0)

    print("\n1. 📊 LIVE ZERODHA MARKET QUOTE:")
    print("-" * 90)
    print(f"  • Current LTP:           ₹{ltp:,.2f}")
    print(f"  • Today's Change:        {chg:>+6.2f}% ({ltp - prev_close:>+6.2f} pts)")
    print(f"  • Today's Open:          ₹{open_price:,.2f}")
    print(f"  • Today's High:          ₹{high_price:,.2f}")
    print(f"  • Today's Low:           ₹{low_price:,.2f}")
    print(f"  • Previous Close:        ₹{prev_close:,.2f}")
    print(f"  • Traded Volume:         {vol:,d} shares")
    print(f"  • Circuit Bands:         Lower: ₹{lower_circuit:.2f} | Upper: ₹{upper_circuit:.2f}")

except Exception as e:
    print(f"⚠️ Error fetching quote: {e}")

# 2. USER'S HOLDINGS IN ZERODHA
try:
    holdings = kite.holdings()
    suzlon_holding = next((h for h in holdings if h.get("tradingsymbol") == "SUZLON"), None)

    print("\n2. 💼 YOUR ZERODHA PORTFOLIO HOLDING IN SUZLON:")
    print("-" * 90)
    if suzlon_holding:
        qty = suzlon_holding.get("quantity", 0) + suzlon_holding.get("t1_quantity", 0)
        avg = suzlon_holding.get("average_price", 0.0)
        pnl = suzlon_holding.get("pnl", 0.0)
        inv = qty * avg
        cur = qty * ltp
        pnl_pct = (pnl / inv * 100) if inv > 0 else 0.0
        status = "🟢 IN PROFIT" if pnl >= 0 else "🔴 IN LOSS"

        print(f"  • Quantity Held:         {qty:,d} shares")
        print(f"  • Your Buy Average:      ₹{avg:,.2f}")
        print(f"  • Current Market Price:  ₹{ltp:,.2f}")
        print(f"  • Total Capital Invested:₹{inv:,.2f}")
        print(f"  • Current Market Value:  ₹{cur:,.2f}")
        print(f"  • Unrealized P&L:        ₹{pnl:+,.2f} ({pnl_pct:>+6.2f}%)  [{status}]")
    else:
        print("  ℹ️ No active SUZLON holding found in Zerodha CNC portfolio.")

except Exception as e:
    print(f"⚠️ Error checking holdings: {e}")

# 3. TECHNICAL MOVING AVERAGES & RSI
try:
    inst_token = q.get("instrument_token")
    if not inst_token:
        # NSE:SUZLON instrument token fallback
        inst_token = 1066497

    today = datetime.now()
    from_date = today - timedelta(days=120)
    bars = kite.historical_data(inst_token, from_date.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"), "day")

    if bars:
        closes = np.array([b["close"] for b in bars])
        highs = np.array([b["high"] for b in bars])
        lows = np.array([b["low"] for b in bars])

        sma_20 = np.mean(closes[-20:]) if len(closes) >= 20 else 0.0
        sma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else 0.0
        sma_100 = np.mean(closes[-100:]) if len(closes) >= 100 else 0.0

        # RSI 14
        deltas = np.diff(closes)
        if len(deltas) >= 14:
            seed = deltas[:14]
            up = seed[seed >= 0].sum() / 14
            down = -seed[seed < 0].sum() / 14
            rs = up / down if down != 0 else 0
            rsi = 100. - 100. / (1. + rs)
            for d in deltas[14:]:
                upval = d if d > 0 else 0.
                downval = -d if d < 0 else 0.
                up = (up * 13 + upval) / 14
                down = (down * 13 + downval) / 14
                rs = up / down if down != 0 else 0
                rsi = 100. - 100. / (1. + rs)
        else:
            rsi = 50.0

        # 30-day High & Low
        high_30d = np.max(highs[-30:])
        low_30d = np.min(lows[-30:])

        print("\n3. 📈 TECHNICAL BENCHMARKS & TREND STRUCTURE:")
        print("-" * 90)
        print(f"  • 20-Day SMA:            ₹{sma_20:,.2f}  ({'🟢 Above' if ltp > sma_20 else '🔴 Below'})")
        print(f"  • 50-Day SMA:            ₹{sma_50:,.2f}  ({'🟢 Above' if ltp > sma_50 else '🔴 Below'})")
        print(f"  • 14-Day RSI:            {rsi:.1f}  ({'Overbought' if rsi > 70 else ('Oversold' if rsi < 30 else 'Neutral / Healthy')})")
        print(f"  • 30-Day High:           ₹{high_30d:,.2f}")
        print(f"  • 30-Day Low:            ₹{low_30d:,.2f}")

except Exception as e:
    print(f"⚠️ Error calculating technicals: {e}")

print("=" * 90)
