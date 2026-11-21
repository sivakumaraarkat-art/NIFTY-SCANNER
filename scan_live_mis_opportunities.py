"""
scan_live_mis_opportunities.py
Scans liquid F&O and high-turnover stocks live via Zerodha Kite Connect
to identify the highest-probability BUY (Long) and SELL (Short) MIS intraday setups.
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
        # Banking & Financials (Leaders today)
        "NSE:HDFCBANK", "NSE:ICICIBANK", "NSE:SBIN", "NSE:AXISBANK", "NSE:KOTAKBANK",
        # IT (Severe Weakness today)
        "NSE:INFY", "NSE:TCS", "NSE:WIPRO", "NSE:HCLTECH", "NSE:TECHM",
        # Heavyweights & Energy
        "NSE:RELIANCE", "NSE:LT", "NSE:BHARTIARTL", "NSE:COALINDIA",
        # Auto & High-Beta
        "NSE:TATAMOTORS", "NSE:M&M", "NSE:ASHOKLEY", "NSE:MARUTI",
        # Metals & Defense
        "NSE:TATASTEEL", "NSE:HINDALCO", "NSE:JCP", "NSE:COCHINSHIP", "NSE:BEL", "NSE:HAL",
        # Midcap Momentum
        "NSE:KAYNES", "NSE:DIXON", "NSE:TITAGARH", "NSE:PCBL"
    ]

    quotes = kite.quote(symbols)
    nifty_quote = kite.quote(["NSE:NIFTY 50"]).get("NSE:NIFTY 50", {})
    nifty_ltp = nifty_quote.get("last_price", 24921.0)
    nifty_ohlc = nifty_quote.get("ohlc", {})
    nifty_prev = nifty_ohlc.get("close", nifty_ltp)
    nifty_chg_pct = ((nifty_ltp - nifty_prev) / nifty_prev * 100) if nifty_prev else 0.0

    long_candidates = []
    short_candidates = []

    for s in symbols:
        sym = s.replace("NSE:", "")
        q = quotes.get(s)
        if not q:
            continue
        ltp = q.get("last_price", 0.0)
        ohlc = q.get("ohlc", {})
        prev = ohlc.get("close", ltp)
        open_p = ohlc.get("open", ltp)
        high = ohlc.get("high", ltp)
        low = ohlc.get("low", ltp)
        chg_pct = ((ltp - prev) / prev * 100) if prev else 0.0

        day_range = (high - low) if high > low else 1.0
        # Position in day's range: 1.0 = at day high, 0.0 = at day low
        range_pos = (ltp - low) / day_range
        # Relative Strength vs NIFTY
        rs_vs_nifty = chg_pct - nifty_chg_pct

        info = {
            "sym": sym,
            "ltp": ltp,
            "open": open_p,
            "high": high,
            "low": low,
            "chg_pct": chg_pct,
            "range_pos": range_pos,
            "rs_vs_nifty": rs_vs_nifty
        }

        # Long Candidate: Green, strong RS, trading in upper 40% of day's range (range_pos > 0.6)
        if chg_pct > 0 and range_pos >= 0.6:
            long_candidates.append(info)

        # Short Candidate: Red, weak RS, trading in lower 40% of day's range (range_pos <= 0.4)
        if chg_pct < 0 and range_pos <= 0.4:
            short_candidates.append(info)

    long_candidates.sort(key=lambda x: (x["range_pos"], x["rs_vs_nifty"]), reverse=True)
    short_candidates.sort(key=lambda x: (x["range_pos"], x["rs_vs_nifty"]))

    print("=" * 85)
    print(f"⚡ LIVE MIS INTRADAY SCANNER | NIFTY: ₹{nifty_ltp:,.2f} ({nifty_chg_pct:+.2f}%)")
    print("=" * 85)

    print("\n🟢 TOP INTRADAY MIS BUY CANDIDATES (STRONG RELATIVE STRENGTH & NEAR HIGHS):")
    print("-" * 85)
    for c in long_candidates[:4]:
        # Formulate Trade Plan
        entry = c["ltp"]
        sl = round(c["low"] if (entry - c["low"]) / entry < 0.015 else entry * 0.992, 2)
        risk = entry - sl
        t1 = round(entry + (risk * 1.5), 2)
        t2 = round(entry + (risk * 2.5), 2)
        print(f"  • {c['sym']:<12} | LTP: ₹{c['ltp']:>8.2f} ({c['chg_pct']:>+5.2f}%) | Day High: ₹{c['high']:>8.2f} | Range Pos: {c['range_pos']*100:>4.0f}%")
        print(f"    👉 MIS BUY PLAN: Entry @ ₹{entry:.2f} | SL: ₹{sl:.2f} | Target 1: ₹{t1:.2f} | Target 2: ₹{t2:.2f}")

    print("\n🔴 TOP INTRADAY MIS SELL / SHORT CANDIDATES (HEAVY BREAKDOWN & NEAR LOWS):")
    print("-" * 85)
    for c in short_candidates[:4]:
        entry = c["ltp"]
        sl = round(c["high"] if (c["high"] - entry) / entry < 0.015 else entry * 1.008, 2)
        risk = sl - entry
        t1 = round(entry - (risk * 1.5), 2)
        t2 = round(entry - (risk * 2.5), 2)
        print(f"  • {c['sym']:<12} | LTP: ₹{c['ltp']:>8.2f} ({c['chg_pct']:>+5.2f}%) | Day Low: ₹{c['low']:>8.2f} | Range Pos: {c['range_pos']*100:>4.0f}%")
        print(f"    👉 MIS SHORT PLAN: Sell @ ₹{entry:.2f} | SL: ₹{sl:.2f} | Target 1: ₹{t1:.2f} | Target 2: ₹{t2:.2f}")

    print("=" * 85)
    print("⏰ MIS STRICT RULES: All intraday MIS trades auto square-off at 03:12 - 03:15 PM!")

except Exception as e:
    print(f"❌ Scan error: {e}")
