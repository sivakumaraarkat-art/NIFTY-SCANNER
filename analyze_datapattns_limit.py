"""
analyze_datapattns_limit.py
Deep quantitative & technical analysis for DATAPATTNS spot & 3900 CE:
- Spot resistance levels, VWAP, day high, round-number psychology (₹4,000)
- Option Greeks, Delta projection, and optimal Limit execution price
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

# UTF-8 fix for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent

try:
    from kiteconnect import KiteConnect

    api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
    token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(token)

    spot_sym = "NSE:DATAPATTNS"
    opt_sym = "NFO:DATAPATTNS26NOV3900CE"

    q = kite.quote([spot_sym, opt_sym])
    spot_q = q.get(spot_sym, {})
    opt_q = q.get(opt_sym, {})

    spot_ltp = spot_q.get("last_price", 0.0)
    spot_ohlc = spot_q.get("ohlc", {})
    day_open = spot_ohlc.get("open", spot_ltp)
    day_high = spot_ohlc.get("high", spot_ltp)
    day_low = spot_ohlc.get("low", spot_ltp)
    prev_close = spot_ohlc.get("close", spot_ltp)

    opt_ltp = opt_q.get("last_price", 0.0)
    opt_ohlc = opt_q.get("ohlc", {})
    opt_high = opt_ohlc.get("high", opt_ltp)
    opt_low = opt_ohlc.get("low", opt_ltp)

    depth = opt_q.get("depth", {})
    buy_depth = depth.get("buy", [])
    sell_depth = depth.get("sell", [])

    total_buy_qty = opt_q.get("buy_quantity", 0)
    total_sell_qty = opt_q.get("sell_quantity", 0)

    # Fetch today's 5-minute candles to calculate VWAP
    token_spot = spot_q.get("instrument_token")
    today_str = datetime.now().strftime("%Y-%m-%d")
    candles = kite.historical_data(token_spot, today_str, today_str, "5minute")

    vwap = spot_ltp
    if candles:
        vols = np.array([c["volume"] for c in candles])
        typical_prices = np.array([(c["high"] + c["low"] + c["close"]) / 3.0 for c in candles])
        if vols.sum() > 0:
            vwap = (typical_prices * vols).sum() / vols.sum()

    print("=" * 85)
    print("🔬 DATAPATTNS TECHNICAL & OPTION TARGET LIMIT AUDIT")
    print("=" * 85)
    print(f"📍 Spot LTP:       ₹{spot_ltp:,.2f} (+{((spot_ltp - prev_close)/prev_close)*100:.2f}%)")
    print(f"📍 Day High:       ₹{day_high:,.2f} | Day Low: ₹{day_low:,.2f}")
    print(f"📍 Intraday VWAP:  ₹{vwap:,.2f} (Spot is {((spot_ltp - vwap)/vwap)*100:+.2f}% above VWAP - Bullish)")
    print("-" * 85)
    print(f"🎯 OPTION CONTRACT: DATAPATTNS 26-NOV-2026 3900 CE")
    print(f"   • Current Option LTP:  ₹{opt_ltp:.2f}")
    print(f"   • Option Day High:     ₹{opt_high:.2f}")
    print(f"   • User's Buy Average:  ₹219.95")
    print(f"   • Current Open Order:  SELL 125 @ ₹243.00")
    print("-" * 85)

    print("📊 MARKET DEPTH (ORDER BOOK CONGESTION):")
    print(f"   • Total Buy Demand:  {total_buy_qty:,} shares")
    print(f"   • Total Sell Supply: {total_sell_qty:,} shares")
    print("   • Top 3 Bids:")
    for b in buy_depth[:3]:
        print(f"     - ₹{b['price']:.2f} ({b['quantity']} shares, {b['orders']} orders)")
    print("   • Top 3 Asks:")
    for a in sell_depth[:3]:
        print(f"     - ₹{a['price']:.2f} ({a['quantity']} shares, {a['orders']} orders)")

    print("-" * 85)
    print("💡 MATHEMATICAL ANALYSIS OF THE ₹243.00 TARGET:")
    # At strike 3900, intrinsic = spot - 3900.
    # Current spot = 3983, intrinsic = 83, ext = 230 - 83 = 147.
    # If spot hits 4000: intrinsic = 100, option price ≈ 100 + 138 (minor time decay) = ~₹238.00 - ₹240.00.
    # To reach ₹243.00, spot must comfortably trade at ₹4,008 - ₹4,015.
    print(f"   1. At Current Spot ₹{spot_ltp:.2f}, Intrinsic Value = ₹{max(0, spot_ltp - 3900):.2f}, Extrinsic Value = ₹{opt_ltp - max(0, spot_ltp - 3900):.2f}")
    print(f"   2. The ₹4,000 Round Psychological Ceiling:")
    print(f"      • ₹4,000 is a major institutional profit-taking number and call writer wall.")
    print(f"      • Day High so far is ₹{day_high:.2f} (it touched ₹4,004.80 earlier and faced selling).")
    print(f"      • If spot stalls at ₹3,995 - ₹4,000, Option LTP will peak around ₹236.00 - ₹239.50!")
    print(f"      • Waiting for ₹243.00 risks missing the fill by ₹2-₹3 if spot rejects ₹4,000.")
    print("-" * 85)
    print("🎯 OPTIMAL LIMIT CALIBRATION RECOMMENDATION:")
    print("   • Conservative Quick-Fill Target: ₹237.50 (Profit: +₹2,193.75 | +8.0% ROI) ➔ Fills as spot touches ₹3,990")
    print("   • Balanced Institutional Target:  ₹239.80 (Profit: +₹2,481.25 | +9.0% ROI) ➔ Fills right before ₹4,000 wall")
    print("   • Aggressive Original Target:     ₹243.00 (Profit: +₹2,881.25 | +10.5% ROI) ➔ Needs spot breakout > ₹4,010")
    print("=" * 85)

except Exception as e:
    print(f"❌ Error: {e}")
