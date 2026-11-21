"""
verify_live_quotes_now.py
Fetches live Zerodha Kite quotes, volume, open interest, and market depth
for the Cloud VM's top news-backed options candidates.
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

    candidates = [
        # (Spot Symbol, Option Symbol, Type, VM Scan LTP, VM Target 1, VM Powerful SL)
        ("NSE:VEDL", "NFO:VEDL26NOV260CE", "CE", 7.65, 8.26, 6.12, 1150),
        ("NSE:DATAPATTNS", "NFO:DATAPATTNS26NOV3900CE", "CE", 211.35, 228.26, 169.08, 125),
        ("NSE:DIVISLAB", "NFO:DIVISLAB26NOV11700CE", "CE", 329.00, 355.32, 263.20, 100),
        ("NSE:AXISBANK", "NFO:AXISBANK26NOV1300PE", "PE", 23.00, 24.84, 18.40, 625),
        ("NSE:JUBLFOOD", "NFO:JUBLFOOD26NOV430PE", "PE", 12.10, 13.07, 9.68, 1250),
        ("NSE:HINDALCO", "NFO:HINDALCO26NOV940PE", "PE", 18.95, 20.47, 15.16, 700)
    ]

    symbols_to_quote = [c[0] for c in candidates] + [c[1] for c in candidates]
    quotes = kite.quote(symbols_to_quote)

    print("=" * 95)
    print("🎯 LIVE MARKET RE-VERIFICATION OF CLOUD VM NEWS-DRIVEN OPTIONS CANDIDATES")
    print("=" * 95)

    for spot_sym, opt_sym, opt_type, scan_ltp, t1, sl, lot in candidates:
        spot_q = quotes.get(spot_sym, {})
        opt_q = quotes.get(opt_sym, {})

        spot_ltp = spot_q.get("last_price", 0.0)
        spot_ohlc = spot_q.get("ohlc", {})
        spot_prev = spot_ohlc.get("close", spot_ltp)
        spot_chg = ((spot_ltp - spot_prev) / spot_prev * 100) if spot_prev else 0.0

        opt_ltp = opt_q.get("last_price", 0.0)
        opt_vol = opt_q.get("volume", 0)
        opt_oi = opt_q.get("oi", 0)
        depth = opt_q.get("depth", {})
        buys = depth.get("buy", [])
        sells = depth.get("sell", [])
        bid = buys[0].get("price", 0.0) if buys else opt_ltp
        ask = sells[0].get("price", 0.0) if sells else opt_ltp

        drift_pct = ((opt_ltp - scan_ltp) / scan_ltp * 100) if scan_ltp else 0.0
        emoji = "🟢" if opt_type == "CE" else "🔴"
        clean_opt = opt_sym.replace("NFO:", "")
        clean_spot = spot_sym.replace("NSE:", "")

        print(f"\n{emoji} {clean_spot:<10} (Spot: ₹{spot_ltp:,.2f} | Chg: {spot_chg:>+5.2f}%)")
        print(f"   Option Contract: {clean_opt} (Lot Size: {lot})")
        print(f"   • Live LTP Now:  ₹{opt_ltp:>7.2f} (Bid: ₹{bid:.2f} / Ask: ₹{ask:.2f})")
        print(f"   • Scan Entry:    ₹{scan_ltp:>7.2f} (Price Drift since scan: {drift_pct:>+5.2f}%)")
        print(f"   • Target 1:      ₹{t1:>7.2f} (+8%)")
        print(f"   • Powerful SL:   ₹{sl:>7.2f} (-20%)")
        print(f"   • Liquidity:     Vol: {opt_vol:>8,} | Open Interest: {opt_oi:,}")

    print("\n" + "=" * 95)

except Exception as e:
    print(f"❌ Error during quote verification: {e}")
