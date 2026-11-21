"""
check_nifty_live.py
═════════════════════════════════════════════════════════════════════════════
Live NIFTY Index & Option Chain Audit:
  1. Fetches live NSE:NIFTY 50 Spot price & Day's Range.
  2. Resolves ATM Call (CE) and Put (PE) strikes.
  3. Evaluates Spot technical levels (Support, Pivot, Resistance).
  4. Formulates clear, low-risk actionable recommendations for:
     - Nifty Options (CE vs PE)
     - Nifty ETF (NIFTYBEES) for festive delivery
═════════════════════════════════════════════════════════════════════════════
"""

import sys
import io
from pathlib import Path

# UTF-8 fix for Windows
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scanners.options_data_provider import get_kite_client, INDEX_MAP

def audit_nifty():
    print("=" * 80)
    print("🎯 LIVE NIFTY 50 INDEX AUDIT & TRADE SETUP")
    print("=" * 80)

    kite = get_kite_client()
    if not kite:
        print("❌ Could not connect to Kite. Check access token.")
        return

    sym = "NSE:NIFTY 50"
    quotes = kite.quote([sym, "NSE:NIFTYBEES"])
    q_nifty = quotes.get(sym, {})
    q_bees = quotes.get("NSE:NIFTYBEES", {})

    if not q_nifty:
        print("❌ Could not fetch NIFTY quote.")
        return

    spot = float(q_nifty.get("last_price", 0.0))
    ohlc = q_nifty.get("ohlc", {})
    open_p = float(ohlc.get("open", spot))
    high_p = float(ohlc.get("high", spot))
    low_p = float(ohlc.get("low", spot))
    close_prev = float(ohlc.get("close", spot))

    chg_pts = spot - close_prev
    chg_pct = (chg_pts / close_prev) * 100.0 if close_prev else 0.0
    day_range = high_p - low_p
    dist_from_high = high_p - spot
    dist_from_low = spot - low_p

    bees_ltp = float(q_bees.get("last_price", 0.0))
    bees_close = float(q_bees.get("ohlc", {}).get("close", bees_ltp))
    bees_chg = ((bees_ltp - bees_close) / bees_close) * 100.0 if bees_close else 0.0

    # Nearest 50 strike
    atm_strike = int(round(spot / 50.0) * 50)

    print(f"📊 NIFTY 50 SPOT LTP:       {spot:,.2f}  ({chg_pts:+.2f} pts | {chg_pct:+.2f}%)")
    print(f"📈 Today's Range:           Low: {low_p:,.2f}  <--->  High: {high_p:,.2f}  (Span: {day_range:.1f} pts)")
    print(f"📍 Distance from Day High:  {dist_from_high:.1f} pts ({(dist_from_high/high_p*100):.2f}% off high)")
    print(f"📍 Distance from Day Low:   {dist_from_low:.1f} pts ({(dist_from_low/low_p*100):.2f}% above low)")
    print(f"🎯 ATM Strike:              {atm_strike}")
    if bees_ltp > 0:
        print(f"🐝 NIFTYBEES (ETF) LTP:     ₹{bees_ltp:.2f} ({bees_chg:+.2f}%)")
    print("-" * 80)

    # Technical Interpretation
    print("🧠 TECHNICAL SETUP & DIWALI RECOMMENDATION:")
    print("-" * 80)

    # Check if near high or low
    if dist_from_low < day_range * 0.35:
        trend = "Consolidating near Day's Low (Support Test)"
        rec_opt = f"BUY {atm_strike} CE only if NIFTY reclaims {open_p:.0f} with volume"
    elif dist_from_high < day_range * 0.35:
        trend = "Trading near Day's High (Bullish Strength)"
        rec_opt = f"{atm_strike} CE Breakout setup toward {atm_strike + 150}"
    else:
        trend = "Mid-range Chop / Consolidation"
        rec_opt = f"Wait for clear direction above {high_p:.0f} (Bullish) or below {low_p:.0f} (Bearish)"

    print(f"• Market Regime:      {trend}")
    print(f"• Immediate Support:  {low_p:.0f} (Day Low) / {atm_strike - 100:.0f}")
    print(f"• Immediate Pivot:    {open_p:.0f}")
    print(f"• Immediate Hurdle:   {high_p:.0f} (Day High) / {atm_strike + 100:.0f}")
    print("=" * 80)

    print("\n💡 ACTIONABLE PLAN FOR TODAY & SUNDAY MUHURAT:")
    print("1. ⚠️ OPTION BUYERS BEWARE OF OVERNIGHT THETA DECAY:")
    print("   Holding Index Options (CE or PE) from Friday over the entire weekend into Sunday")
    print("   means 2 full days of time-value (Theta) decay will eat away option premium.")
    print("   Unless you get a huge +150 point gap-up, options can bleed value over the weekend.")
    print("\n2. 🏆 BEST WAY TO PLAY NIFTY FOR DIWALI: NIFTYBEES (ETF)")
    print(f"   Buy NIFTYBEES at ~₹{bees_ltp:.2f} in CNC (Delivery).")
    print("   - 0% Theta decay.")
    print("   - 100% participation in Sunday Muhurat & Samvat rally.")
    print("   - Auspicious, risk-free long-term wealth compounding.")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    audit_nifty()
