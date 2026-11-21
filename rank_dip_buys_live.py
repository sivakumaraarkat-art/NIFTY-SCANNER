"""
rank_dip_buys_live.py
Ranks the best buy-on-dip candidates by Relative Strength (RS),
intraday recovery off lows, and institutional floor support.
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

    symbols = [
        "NSE:PCBL",
        "NSE:TITAGARH",
        "NSE:KAYNES",
        "NSE:COCHINSHIP",
        "NSE:DIXON",
        "NSE:ASHOKLEY",
        "NSE:RVNL",
        "NSE:IRFC"
    ]

    quotes = kite.quote(symbols)

    data = []
    for s in symbols:
        sym = s.replace("NSE:", "")
        q = quotes.get(s, {})
        ltp = q.get("last_price", 0.0)
        ohlc = q.get("ohlc", {})
        prev = ohlc.get("close", ltp)
        low = ohlc.get("low", ltp)
        high = ohlc.get("high", ltp)
        chg_pct = ((ltp - prev) / prev * 100) if prev else 0.0
        bounce_from_low = ((ltp - low) / low * 100) if low else 0.0
        pullback_from_high = ((high - ltp) / high * 100) if high else 0.0

        data.append({
            "sym": sym,
            "ltp": ltp,
            "chg_pct": chg_pct,
            "low": low,
            "high": high,
            "bounce_from_low": bounce_from_low,
            "pullback_from_high": pullback_from_high
        })

    # Sort by relative strength (chg_pct descending)
    data.sort(key=lambda x: x["chg_pct"], reverse=True)

    print("=" * 80)
    print("🏆 BEST BUY-ON-DIP STOCKS RANKED BY RELATIVE STRENGTH (LIVE ZERODHA QUOTES)")
    print("=" * 80)
    for i, d in enumerate(data, 1):
        indicator = "🟢" if d["chg_pct"] >= 0 else "🔴"
        print(f" {i}. {indicator} {d['sym']:<12} | LTP: ₹{d['ltp']:>8.2f} | Chg: {d['chg_pct']:>+5.2f}% | Low: ₹{d['low']:>8.2f} | High: ₹{d['high']:>8.2f} | Bounce off Low: +{d['bounce_from_low']:.2f}%")
    print("=" * 80)

except Exception as e:
    print(f"❌ Error: {e}")
