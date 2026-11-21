"""
analyze_divislab_position.py
Analyzes the live active MIS position in DIVISLAB 11700 CE:
- Spot price, day range, and momentum
- Option strike dynamics and Greeks/spread
- Strict Stop Loss and Target levels for MIS intraday square-off
"""

import sys
from pathlib import Path

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

    OPT = "NFO:DIVISLAB26NOV11700CE"
    SPOT = "NSE:DIVISLAB"

    quotes = kite.quote([OPT, SPOT])
    q_opt = quotes.get(OPT, {})
    q_spot = quotes.get(SPOT, {})

    spot_ltp = q_spot.get("last_price", 0.0)
    spot_ohlc = q_spot.get("ohlc", {})
    spot_prev = spot_ohlc.get("close", spot_ltp)
    spot_high = spot_ohlc.get("high", spot_ltp)
    spot_low = spot_ohlc.get("low", spot_ltp)
    spot_chg = spot_ltp - spot_prev
    spot_chg_pct = (spot_chg / spot_prev * 100) if spot_prev else 0.0

    opt_ltp = q_opt.get("last_price", 0.0)
    opt_ohlc = q_opt.get("ohlc", {})
    opt_high = opt_ohlc.get("high", opt_ltp)
    opt_low = opt_ohlc.get("low", opt_ltp)
    opt_volume = q_opt.get("volume", 0)
    depth = q_opt.get("depth", {})
    buy_depth = depth.get("buy", [])
    sell_depth = depth.get("sell", [])
    best_bid = buy_depth[0].get("price", 0.0) if buy_depth else opt_ltp
    best_ask = sell_depth[0].get("price", 0.0) if sell_depth else opt_ltp

    buy_price = 314.70
    qty = 100
    pnl = (opt_ltp - buy_price) * qty
    pnl_pct = ((opt_ltp - buy_price) / buy_price * 100) if buy_price else 0.0

    print("=" * 80)
    print("💊 LIVE TRADE ANALYSIS: DIVISLAB 11,700 CE (MIS INTRADAY)")
    print("=" * 80)
    print(f"  • DIVISLAB Spot:    ₹{spot_ltp:>9.2f} | Chg: {spot_chg:>+7.2f} ({spot_chg_pct:>+6.2f}%)")
    print(f"    - Day High:       ₹{spot_high:>9.2f}")
    print(f"    - Day Low:        ₹{spot_low:>9.2f}")
    print("-" * 80)
    print(f"  • Option:           DIVISLAB 26 NOV 11,700 CE (Expiry: 26-Nov-2026)")
    print(f"    - Product:        MIS (⚠️ AUTO SQUARES OFF TODAY BY 03:15 PM)")
    print(f"    - Quantity:       {qty} shares (1 Lot)")
    print(f"    - Buy Average:    ₹{buy_price:.2f}")
    print(f"    - Current LTP:    ₹{opt_ltp:.2f} (Bid: ₹{best_bid:.2f} | Ask: ₹{best_ask:.2f})")
    print(f"    - Day High / Low: ₹{opt_high:.2f} / ₹{opt_low:.2f} | Traded Vol: {opt_volume:,}")
    emoji = "🟢" if pnl >= 0 else "🔴"
    print(f"    - Current P&L:    {emoji} ₹{pnl:+,.2f} ({pnl_pct:+.2f}%)")
    print("-" * 80)

    # Risk-Reward Blueprint
    # For a ₹314 buy, strict SL should be ₹295 (-₹19.70 risk = -₹1,970)
    # Target 1: ₹335 (+₹20.30 gain = +₹2,030)
    # Target 2: ₹350 (+₹35.30 gain = +₹3,530)
    sl = 295.00
    t1 = 335.00
    t2 = 350.00
    print("🎯 INTRADAY MIS STRATEGY BLUEPRINT:")
    print(f"  🛡️ STRICT STOP-LOSS:   ₹{sl:.2f} (Max Risk: -₹{(buy_price - sl) * qty:,.2f})")
    print(f"  🎯 TARGET 1 (Quick):   ₹{t1:.2f} (Gain: +₹{(t1 - buy_price) * qty:,.2f})")
    print(f"  🎯 TARGET 2 (Stretch): ₹{t2:.2f} (Gain: +₹{(t2 - buy_price) * qty:,.2f})")
    print("  ⏰ TIME CUT-OFF:       Exit by 03:10 PM IST!")
    print("=" * 80)

except Exception as e:
    print(f"❌ Error: {e}")
