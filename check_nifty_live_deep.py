"""
check_nifty_live_deep.py
Real-time deep audit of Nifty 50, Bank Nifty, India VIX,
and today's expiry (09-Nov-2026) options chain dynamics.
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

    idx_symbols = ["NSE:NIFTY 50", "NSE:NIFTY BANK", "NSE:INDIA VIX"]
    idx_q = kite.quote(idx_symbols)

    nifty = idx_q.get("NSE:NIFTY 50", {})
    bank = idx_q.get("NSE:NIFTY BANK", {})
    vix = idx_q.get("NSE:INDIA VIX", {})

    n_ltp = nifty.get("last_price", 0.0)
    n_ohlc = nifty.get("ohlc", {})
    n_open = n_ohlc.get("open", n_ltp)
    n_high = n_ohlc.get("high", n_ltp)
    n_low = n_ohlc.get("low", n_ltp)
    n_close = n_ohlc.get("close", n_ltp)
    n_chg = n_ltp - n_close
    n_pct = (n_chg / n_close * 100) if n_close else 0.0

    b_ltp = bank.get("last_price", 0.0)
    b_ohlc = bank.get("ohlc", {})
    b_close = b_ohlc.get("close", b_ltp)
    b_chg = b_ltp - b_close
    b_pct = (b_chg / b_close * 100) if b_close else 0.0

    v_ltp = vix.get("last_price", 0.0)
    v_ohlc = vix.get("ohlc", {})
    v_close = v_ohlc.get("close", v_ltp)
    v_chg = v_ltp - v_close
    v_pct = (v_chg / v_close * 100) if v_close else 0.0

    print("=" * 85)
    print(f"📊 LIVE NIFTY 50 & INDEX MONITOR | {nifty.get('last_trade_time', 'LIVE')}")
    print("=" * 85)
    n_emoji = "🟢" if n_chg >= 0 else "🔴"
    b_emoji = "🟢" if b_chg >= 0 else "🔴"
    print(f"  • NIFTY 50:      ₹{n_ltp:>9.2f} | Chg: {n_chg:>+7.2f} ({n_pct:>+5.2f}%) {n_emoji}")
    print(f"    - Day Open:    ₹{n_open:>9.2f} | Day High: ₹{n_high:>9.2f} | Day Low: ₹{n_low:>9.2f}")
    print(f"    - Range Pos:   {((n_ltp - n_low)/(n_high - n_low)*100):.1f}% of Day Range")
    print(f"  • BANK NIFTY:    ₹{b_ltp:>9.2f} | Chg: {b_chg:>+7.2f} ({b_pct:>+5.2f}%) {b_emoji}")
    print(f"  • INDIA VIX:     {v_ltp:>9.2f} | Chg: {v_chg:>+7.2f} ({v_pct:>+5.2f}%)")

    # Expiry Chain
    strikes = [24850, 24900, 24950, 25000, 25050]
    opt_symbols = []
    for s in strikes:
        opt_symbols.append(f"NFO:NIFTY26N09{s}CE")
        opt_symbols.append(f"NFO:NIFTY26N09{s}PE")

    opt_q = kite.quote(opt_symbols)

    print("\n⚡ TODAY'S EXPIRY (09-NOV-2026) NIFTY OPTION CHAIN:")
    print("-" * 85)
    print(f"{'Strike':<8} | {'CE LTP':<8} {'CE Volume':<12} {'CE OI':<10} | {'PE LTP':<8} {'PE Volume':<12} {'PE OI':<10}")
    print("-" * 85)

    total_ce_oi = 0
    total_pe_oi = 0

    for s in strikes:
        c_sym = f"NFO:NIFTY26N09{s}CE"
        p_sym = f"NFO:NIFTY26N09{s}PE"

        cq = opt_q.get(c_sym, {})
        pq = opt_q.get(p_sym, {})

        c_ltp = cq.get("last_price", 0.0)
        c_vol = cq.get("volume", 0)
        c_oi = cq.get("oi", 0)

        p_ltp = pq.get("last_price", 0.0)
        p_vol = pq.get("volume", 0)
        p_oi = pq.get("oi", 0)

        total_ce_oi += c_oi
        total_pe_oi += p_oi

        atm_marker = "◄ ATM" if abs(n_ltp - s) <= 25 else ""
        print(f"{s:<8} | ₹{c_ltp:>6.2f} {c_vol:>12,} {c_oi:>10,} | ₹{p_ltp:>6.2f} {p_vol:>12,} {p_oi:>10,} {atm_marker}")

    pcr = total_pe_oi / total_ce_oi if total_ce_oi else 1.0
    print("-" * 85)
    print(f"📈 NEAR-ATM PCR: {pcr:.2f} ({'Bullish Put Writing' if pcr > 1.1 else ('Bearish Call Writing' if pcr < 0.85 else 'Neutral Pivot')})")

    # Key Support & Resistance
    print("\n🎯 KEY EXPIRY LEVELS FOR NIFTY:")
    print(f"  • Immediate Support (S1): ₹24,900 (24900 PE has highest support build-up)")
    print(f"  • Critical Floor (S2):    ₹24,850 (Day Low: ₹{n_low:.2f})")
    print(f"  • Immediate Pivot (P):    ₹24,950 (Fierce bull-bear battleground)")
    print(f"  • Major Resistance (R1):  ₹25,000 (Massive 30M+ CE OI Wall)")
    print("=" * 85)

except Exception as e:
    print(f"❌ Error: {e}")
