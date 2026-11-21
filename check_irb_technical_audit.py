"""
check_irb_technical_audit.py
Fetches live quote, user holding status, and moving average confluence (20, 50, 100, 200 DMA)
for IRB Infrastructure Developers Ltd (NSE:IRB) via Zerodha Kite Connect.
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

    SYM = "IRB"
    EXCHANGE = "NSE"
    FULL_SYM = f"{EXCHANGE}:{SYM}"

    # 1. Check user holdings
    holdings = kite.holdings()
    irb_holding = next((h for h in holdings if h.get("tradingsymbol") == SYM), None)

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
    highs = np.array([b["high"] for b in hist])
    lows = np.array([b["low"] for b in hist])

    sma_20 = float(np.mean(closes[-20:])) if len(closes) >= 20 else ltp
    sma_50 = float(np.mean(closes[-50:])) if len(closes) >= 50 else ltp
    sma_100 = float(np.mean(closes[-100:])) if len(closes) >= 100 else ltp
    sma_200 = float(np.mean(closes[-200:])) if len(closes) >= 200 else ltp

    # RSI (14)
    deltas = np.diff(closes)
    seed = deltas[-14:]
    up = seed[seed >= 0].sum() / 14
    down = -seed[seed < 0].sum() / 14
    rs = up / down if down != 0 else 0
    rsi = 100 - (100 / (1 + rs)) if down != 0 else 50.0

    print("=" * 80)
    print("🛣️ IRB INFRASTRUCTURE DEVELOPERS (NSE: IRB) — LIVE TECHNICAL AUDIT")
    print("=" * 80)
    print(f"  • Current LTP:       ₹{ltp:>7.2f} | Chg: {chg:>+5.2f} ({chg_pct:>+5.2f}%)")
    print(f"  • Day Open / High:   ₹{day_open:>7.2f} / ₹{day_high:>7.2f}")
    print(f"  • Day Low:           ₹{day_low:>7.2f}")
    print(f"  • Today's Volume:    {volume:,} shares")
    print(f"  • Daily RSI (14):    {rsi:.1f} {'(Oversold Zone)' if rsi < 35 else '(Neutral)'}")
    print("-" * 80)

    if irb_holding:
        qty = irb_holding.get("quantity", 0) + irb_holding.get("t1_quantity", 0)
        avg = irb_holding.get("average_price", 0.0)
        pnl = (ltp - avg) * qty
        pnl_pct = (pnl / (qty * avg) * 100) if avg and qty else 0.0
        h_emoji = "🟢" if pnl >= 0 else "🔴"
        print(f"💼 YOUR DEMAT HOLDING STATUS:")
        print(f"  • Quantity:          {qty} shares")
        print(f"  • Buy Average:       ₹{avg:.2f}")
        print(f"  • Current Value:     ₹{qty * ltp:,.2f}")
        print(f"  • P&L:               {h_emoji} ₹{pnl:+,.2f} ({pnl_pct:+.2f}%)")
        print("-" * 80)

    print("📊 MOVING AVERAGE CONFLUENCE AUDIT:")
    print("-" * 80)
    mas = [
        ("20-Day SMA  (Short-term)", sma_20),
        ("50-Day SMA  (Medium-term)", sma_50),
        ("100-Day SMA (Intermediate)", sma_100),
        ("200-Day SMA (Long-term Institutional Base)", sma_200)
    ]

    closest_ma = None
    min_dist = 999.0

    for name, val in mas:
        dist_pct = ((ltp - val) / val) * 100
        dist_str = f"{dist_pct:>+6.2f}%"
        status = "At / Testing MA" if abs(dist_pct) < 1.5 else ("Above MA" if dist_pct > 0 else "Below MA")
        print(f"  • {name:<38}: ₹{val:>7.2f} | Dist: {dist_str} | Status: {status}")
        if abs(dist_pct) < min_dist:
            min_dist = abs(dist_pct)
            closest_ma = (name, val, dist_pct)

    print("-" * 80)
    print(f"🎯 KEY OBSERVATION: IRB is currently closest to the {closest_ma[0].split()[0]} (₹{closest_ma[1]:.2f}, {closest_ma[2]:+.2f}% away).")

    # Rebound / Floor Assessment
    if ltp >= sma_200 * 0.98 and ltp <= sma_200 * 1.03:
        verdict = "🔥 STRONG 200-DMA ACCUMULATION ZONE: Price is hovering right at the institutional 200-DMA!"
    elif ltp >= sma_50 * 0.98 and ltp <= sma_50 * 1.03:
        verdict = "⚡ 50-DMA PULLBACK REBOUND: Testing the 50-Day moving average!"
    elif ltp >= sma_20 * 0.98 and ltp <= sma_20 * 1.03:
        verdict = "📈 20-DMA SHORT-TERM PULLBACK: Hovering near 20-DMA support!"
    else:
        verdict = f"📌 Price is in consolidation near ₹{ltp:.2f}."

    print(f"\n💡 STRATEGIC VERDICT: {verdict}")
    print("=" * 80)

except Exception as e:
    print(f"❌ Error checking IRB: {e}")
