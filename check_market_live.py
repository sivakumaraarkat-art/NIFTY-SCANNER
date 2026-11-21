"""
check_market_live.py
Fetches real-time market indices, market internals, key heavyweights,
and top watchlist stocks directly from Zerodha Kite Connect.
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
        # Active Derivative Position
        "NFO:NIFTY26N0925200CE",
        # Major Indices
        "NSE:NIFTY 50",
        "NSE:NIFTY BANK",
        "NSE:INDIA VIX",
        # Heavyweights
        "NSE:RELIANCE",
        "NSE:HDFCBANK",
        "NSE:ICICIBANK",
        "NSE:INFY",
        "NSE:TCS",
        # Key Portfolio & Watchlist Stocks
        "NSE:COCHINSHIP",
        "NSE:TITAGARH",
        "NSE:PCBL",
        "NSE:KAYNES",
        "NSE:DIXON",
        "NSE:RVNL",
        "NSE:IRFC",
        "NSE:SUZLON",
        "NSE:ASHOKLEY",
        "NSE:COALINDIA"
    ]

    quotes = kite.quote(symbols)

    print("=" * 80)
    print("📈 LIVE NSE MARKET INTELLIGENCE & SENTIMENT")
    print("=" * 80)

    # 0. Active Option Position Live Tick
    opt_q = quotes.get("NFO:NIFTY26N0925200CE", {})
    opt_ltp = opt_q.get("last_price", 0.0)
    buy_avg = 63.00
    pnl = (opt_ltp - buy_avg) * 65
    pnl_pct = ((opt_ltp - buy_avg) / buy_avg * 100) if buy_avg else 0
    emoji = "🟢" if pnl >= 0 else "🔴"
    print(f"\n⚡ YOUR ACTIVE NIFTY OPTION LIVE TICK:")
    print(f"  {emoji} NIFTY 25,200 CE (Expiry TODAY) | LTP: ₹{opt_ltp:.2f} | P&L: ₹{pnl:+,.2f} ({pnl_pct:+.2f}%) [Cost: ₹63.00]")
    print("-" * 80)

    # 1. Benchmark Indices
    print("\n🏛️ 1. BENCHMARK INDICES & VOLATILITY:")
    print("-" * 80)
    for s, label in [("NSE:NIFTY 50", "NIFTY 50"), ("NSE:NIFTY BANK", "BANK NIFTY"), ("NSE:INDIA VIX", "INDIA VIX")]:
        q = quotes.get(s, {})
        ltp = q.get("last_price", 0.0)
        ohlc = q.get("ohlc", {})
        prev = ohlc.get("close", ltp)
        day_open = ohlc.get("open", ltp)
        day_high = ohlc.get("high", ltp)
        day_low = ohlc.get("low", ltp)
        chg = ltp - prev
        chg_pct = (chg / prev * 100) if prev > 0 else 0.0

        indicator = "🟢" if chg >= 0 else "🔴"
        print(f"  {indicator} {label:<14} | LTP: ₹{ltp:>9.2f} | Chg: {chg:>+8.2f} ({chg_pct:>+6.2f}%) | Day High: ₹{day_high:>9.2f} | Low: ₹{day_low:>9.2f}")

    # 2. Key Heavyweights
    print("\n🏢 2. INDEX HEAVYWEIGHT MOVERS (MARKET DRIVERS):")
    print("-" * 80)
    for s in ["NSE:RELIANCE", "NSE:HDFCBANK", "NSE:ICICIBANK", "NSE:INFY", "NSE:TCS"]:
        q = quotes.get(s, {})
        sym_clean = s.replace("NSE:", "")
        ltp = q.get("last_price", 0.0)
        ohlc = q.get("ohlc", {})
        prev = ohlc.get("close", ltp)
        chg = ltp - prev
        chg_pct = (chg / prev * 100) if prev > 0 else 0.0
        indicator = "🟢" if chg >= 0 else "🔴"
        print(f"  {indicator} {sym_clean:<14} | LTP: ₹{ltp:>9.2f} | Chg: {chg:>+7.2f} ({chg_pct:>+6.2f}%)")

    # 3. Portfolio & Watchlist Stocks
    print("\n🎯 3. PORTFOLIO & PRIME BUY WATCHLIST:")
    print("-" * 80)
    for s in ["NSE:COCHINSHIP", "NSE:TITAGARH", "NSE:PCBL", "NSE:KAYNES", "NSE:DIXON", "NSE:RVNL", "NSE:IRFC", "NSE:SUZLON", "NSE:ASHOKLEY", "NSE:COALINDIA"]:
        q = quotes.get(s, {})
        sym_clean = s.replace("NSE:", "")
        ltp = q.get("last_price", 0.0)
        ohlc = q.get("ohlc", {})
        prev = ohlc.get("close", ltp)
        chg = ltp - prev
        chg_pct = (chg / prev * 100) if prev > 0 else 0.0
        indicator = "🟢" if chg >= 0 else "🔴"
        print(f"  {indicator} {sym_clean:<14} | LTP: ₹{ltp:>9.2f} | Chg: {chg:>+7.2f} ({chg_pct:>+6.2f}%) | High: ₹{ohlc.get('high', 0.0):>9.2f} | Low: ₹{ohlc.get('low', 0.0):>9.2f}")

    print("=" * 80)

except Exception as e:
    print(f"❌ Error fetching market quotes: {e}")
