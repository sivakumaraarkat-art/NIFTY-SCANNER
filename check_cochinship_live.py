"""
check_cochinship_live.py
Deep live audit of Cochin Shipyard Ltd (NSE:COCHINSHIP):
- Live Zerodha LTP, day range, volume, and momentum
- User's Demat holding P&L
- Key Moving Averages (20, 50, 200 DMA) and RSI
- Averaging blueprint & targets
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

    SYM = "COCHINSHIP"
    EXCHANGE = "NSE"
    FULL_SYM = f"{EXCHANGE}:{SYM}"

    # 1. Check user holdings
    holdings = kite.holdings()
    cochin_holding = next((h for h in holdings if h.get("tradingsymbol") == SYM), None)

    # 2. Fetch live quote
    q = kite.quote([FULL_SYM]).get(FULL_SYM, {})
    ltp = q.get("last_price", 0.0)
    ohlc = q.get("ohlc", {})
    prev_close = ohlc.get("close", ltp)
    day_open = ohlc.get("open", ltp)
    day_high = ohlc.get("high", ltp)
    day_low = ohlc.get("low", ltp)
    volume = q.get("volume", 0)
    inst_token = q.get("instrument_token")
    chg = ltp - prev_close
    chg_pct = (chg / prev_close * 100) if prev_close else 0.0

    # 3. Fetch historical daily data for moving averages
    to_date = datetime.now()
    from_date = to_date - timedelta(days=365)
    hist = kite.historical_data(inst_token, from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d"), "day")

    closes = np.array([b["close"] for b in hist])

    sma_20 = float(np.mean(closes[-20:])) if len(closes) >= 20 else ltp
    sma_50 = float(np.mean(closes[-50:])) if len(closes) >= 50 else ltp
    sma_200 = float(np.mean(closes[-200:])) if len(closes) >= 200 else ltp

    # RSI (14)
    deltas = np.diff(closes)
    seed = deltas[-14:]
    up = seed[seed >= 0].sum() / 14
    down = -seed[seed < 0].sum() / 14
    rs = up / down if down != 0 else 0
    rsi = 100 - (100 / (1 + rs)) if down != 0 else 50.0

    print("=" * 80)
    print("🚢 COCHIN SHIPYARD (NSE: COCHINSHIP) — LIVE TECHNICAL AUDIT")
    print("=" * 80)
    indicator = "🟢" if chg >= 0 else "🔴"
    print(f"  • Current LTP:       ₹{ltp:>8.2f} | Chg: {chg:>+6.2f} ({chg_pct:>+5.2f}%) {indicator}")
    print(f"  • Day Open / High:   ₹{day_open:>8.2f} / ₹{day_high:>8.2f}")
    print(f"  • Day Low:           ₹{day_low:>8.2f}")
    print(f"  • Today's Volume:    {volume:,} shares")
    print(f"  • Daily RSI (14):    {rsi:.1f}")
    print("-" * 80)

    if cochin_holding:
        qty = cochin_holding.get("quantity", 0) + cochin_holding.get("t1_quantity", 0)
        avg = cochin_holding.get("average_price", 0.0)
        inv = qty * avg
        cur = qty * ltp
        pnl = cur - inv
        pnl_pct = (pnl / inv * 100) if inv else 0.0
        h_emoji = "🟢" if pnl >= 0 else "🔴"
        print(f"💼 YOUR DEMAT HOLDING STATUS:")
        print(f"  • Quantity:          {qty} shares")
        print(f"  • Buy Average:       ₹{avg:.2f}")
        print(f"  • Invested Capital:  ₹{inv:,.2f}")
        print(f"  • Current Value:     ₹{cur:,.2f}")
        print(f"  • P&L:               {h_emoji} ₹{pnl:+,.2f} ({pnl_pct:+.2f}%)")
        print("-" * 80)

        # Averaging Blueprint
        print("🎯 STRATEGIC AVERAGING IMPACT (BUYING 30 SHARES @ ₹" + f"{ltp:.2f}):")
        add_qty = 30
        new_qty = qty + add_qty
        new_inv = inv + (add_qty * ltp)
        new_avg = new_inv / new_qty
        drop_in_avg = avg - new_avg
        print(f"  • Adding 30 shares:  Deploy ~₹{add_qty * ltp:,.2f}")
        print(f"  • New Total Shares:  {new_qty} shares")
        print(f"  • New Average Price: ₹{new_avg:.2f} (Slashes average by -₹{drop_in_avg:.2f} per share!)")
        print(f"  • Breakeven Point:   Only {((new_avg - ltp)/ltp)*100:+.1f}% rally needed to hit full profit!")
        print("-" * 80)

    print("📊 MOVING AVERAGE ARCHITECTURE:")
    print(f"  • 20-Day SMA  (Short-term Pivot):     ₹{sma_20:>8.2f} (Dist: {((ltp - sma_20)/sma_20)*100:>+5.2f}%)")
    print(f"  • 50-Day SMA  (Intermediate Target):  ₹{sma_50:>8.2f} (Dist: {((ltp - sma_50)/sma_50)*100:>+5.2f}%)")
    print(f"  • 200-Day SMA (Institutional Base):   ₹{sma_200:>8.2f} (Dist: {((ltp - sma_200)/sma_200)*100:>+5.2f}%)")
    print("=" * 80)

except Exception as e:
    print(f"❌ Error checking COCHINSHIP: {e}")
