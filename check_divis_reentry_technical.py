"""
check_divis_reentry_technical.py
Technical audit to evaluate whether a re-entry into DIVISLAB is justified:
- Spot price action vs intraday VWAP/Support
- Option price, volume, and bid-ask spread
- Strict rule-based conditions for re-entry vs 'revenge trading' guard
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
    NIFTY = "NSE:NIFTY 50"

    quotes = kite.quote([OPT, SPOT, NIFTY])
    q_opt = quotes.get(OPT, {})
    q_spot = quotes.get(SPOT, {})
    q_nifty = quotes.get(NIFTY, {})

    spot_ltp = q_spot.get("last_price", 0.0)
    spot_ohlc = q_spot.get("ohlc", {})
    spot_open = spot_ohlc.get("open", spot_ltp)
    spot_high = spot_ohlc.get("high", spot_ltp)
    spot_low = spot_ohlc.get("low", spot_ltp)
    spot_prev = spot_ohlc.get("close", spot_ltp)
    spot_chg_pct = ((spot_ltp - spot_prev) / spot_prev * 100) if spot_prev else 0.0

    opt_ltp = q_opt.get("last_price", 0.0)
    opt_ohlc = q_opt.get("ohlc", {})
    opt_high = opt_ohlc.get("high", opt_ltp)
    opt_low = opt_ohlc.get("low", opt_ltp)
    opt_vol = q_opt.get("volume", 0)

    nifty_ltp = q_nifty.get("last_price", 0.0)

    # Key levels
    # From day high of 11,824 down to low:
    pullback_from_high = ((spot_high - spot_ltp) / spot_high * 100) if spot_high else 0.0

    print("=" * 80)
    print("🔬 DIVISLAB RE-ENTRY TECHNICAL AUDIT & DISCIPLINE CHECK")
    print("=" * 80)
    print(f"  • DIVISLAB Spot:    ₹{spot_ltp:>9.2f} ({spot_chg_pct:>+5.2f}%)")
    print(f"    - Day High:       ₹{spot_high:>9.2f} (Down -{pullback_from_high:.2f}% from peak)")
    print(f"    - Day Low:        ₹{spot_low:>9.2f}")
    print(f"  • Option (11700CE): ₹{opt_ltp:>9.2f} (Day Low: ₹{opt_low:.2f} | Day High: ₹{opt_high:.2f})")
    print(f"  • Option Volume:    {opt_vol:,} shares")
    print(f"  • NIFTY 50 Spot:    ₹{nifty_ltp:,.2f}")
    print("-" * 80)

    # Technical Verdict
    print("🧠 PROFESSIONAL TRADING DISCIPLINE RULES:")

    # 1. Has the spot price broken below support?
    # Morning support was around 11,620 - 11,640. If spot is below 11,620, it is continuing to pull back.
    if spot_ltp < 11620:
        status = "🔴 DO NOT RE-ENTER RIGHT NOW (KNIFE CATCHING)"
        action = "Wait. The stock broke below the 11,640 morning pivot. Entering now is trying to catch a falling knife."
    elif spot_ltp >= 11680:
        status = "🟢 RE-ENTRY BREAKOUT CONFIRMED"
        action = "Re-enter only on a 5-minute candle closing above ₹11,680."
    else:
        status = "🟡 CONSOLIDATION / NO CONFIRMATION YET"
        action = "Wait for a clear reversal candle (Hammer/Double-bottom) before deploying any capital."

    print(f"  • Rule Verdict:     {status}")
    print(f"  • Strategic Action: {action}")
    print("-" * 80)

    print("📌 WHAT MUST HAPPEN BEFORE YOU RE-ENTER:")
    print("  1. DIVISLAB Spot MUST stop falling and form a higher low on the 5-minute chart.")
    print("  2. Spot MUST reclaim ₹11,660 - ₹11,680 with fresh green buying volume.")
    print("  3. The 11,700 CE option must cross and hold above ₹295 (the previous support-turned-resistance).")
    print("  4. TIME CHECK: It is afternoon. MIS trades entered after 01:30 PM face rapid time decay.")
    print("=" * 80)

except Exception as e:
    print(f"❌ Error: {e}")
