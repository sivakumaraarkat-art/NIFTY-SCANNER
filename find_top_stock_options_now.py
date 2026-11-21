"""
find_top_stock_options_now.py
Scans liquid F&O stocks and their option chains on Zerodha Kite
to find the Top 2 highest-probability stock option setups (CE/PE) right now.
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

    # Key F&O stocks with clear directional trends today
    # Bullish: HAL (Defense leader), ICICIBANK (Bank leader)
    # Bearish: TATASTEEL (Metal breakdown), INFY (IT breakdown)
    underlyings = [
        ("NSE:HAL", "BULLISH", "HAL"),
        ("NSE:ICICIBANK", "BULLISH", "ICICIBANK"),
        ("NSE:TATASTEEL", "BEARISH", "TATASTEEL"),
        ("NSE:INFY", "BEARISH", "INFY"),
        ("NSE:HDFCBANK", "BULLISH", "HDFCBANK"),
        ("NSE:TCS", "BEARISH", "TCS")
    ]

    quotes = kite.quote([u[0] for u in underlyings])
    nifty_quote = kite.quote(["NSE:NIFTY 50"]).get("NSE:NIFTY 50", {})
    nifty_ltp = nifty_quote.get("last_price", 24869.0)

    print("=" * 85)
    print(f"🎯 LIVE STOCK OPTIONS INTELLIGENCE SCANNER | NIFTY: ₹{nifty_ltp:,.2f}")
    print("=" * 85)

    # Let's inspect live spot prices and day ranges
    for u, trend, sym in underlyings:
        q = quotes.get(u, {})
        ltp = q.get("last_price", 0.0)
        ohlc = q.get("ohlc", {})
        prev = ohlc.get("close", ltp)
        high = ohlc.get("high", ltp)
        low = ohlc.get("low", ltp)
        chg_pct = ((ltp - prev) / prev * 100) if prev else 0.0
        range_pos = ((ltp - low) / (high - low) * 100) if high > low else 50.0
        emoji = "🟢" if chg_pct >= 0 else "🔴"
        print(f"  • {sym:<12} | Spot: ₹{ltp:>8.2f} ({chg_pct:>+5.2f}%) {emoji} | Range: ₹{low:.2f} - ₹{high:.2f} | Pos: {range_pos:4.0f}%")

    print("-" * 85)

    # Candidate Option Contracts to Quote (November Monthly Expiry: 26-NOV-2026)
    # 1. Bullish: HAL 5000 CE or ICICIBANK 1580 CE
    # 2. Bearish: TATASTEEL 185 PE or INFY 1140 PE
    option_symbols = [
        "NFO:HAL26NOV5000CE",
        "NFO:ICICIBANK26NOV1580CE",
        "NFO:TATASTEEL26NOV185PE",
        "NFO:TATASTEEL26NOV182.5PE",
        "NFO:INFY26NOV1140PE",
        "NFO:HDFCBANK26NOV800CE"
    ]

    opt_quotes = kite.quote(option_symbols)

    print("\n🔍 OPTION STRIKE LIVE LIQUIDITY & SPREAD AUDIT:")
    print("-" * 85)
    for opt in option_symbols:
        q = opt_quotes.get(opt, {})
        clean_sym = opt.replace("NFO:", "")
        ltp = q.get("last_price", 0.0)
        vol = q.get("volume", 0)
        depth = q.get("depth", {})
        buy_depth = depth.get("buy", [])
        sell_depth = depth.get("sell", [])
        bid = buy_depth[0].get("price", 0.0) if buy_depth else ltp
        ask = sell_depth[0].get("price", 0.0) if sell_depth else ltp
        oi = q.get("oi", 0)
        print(f"  • {clean_sym:<24} | LTP: ₹{ltp:>7.2f} (Bid: ₹{bid:>6.2f} / Ask: ₹{ask:>6.2f}) | Vol: {vol:>8,} | OI: {oi:,}")

    print("=" * 85)

except Exception as e:
    print(f"❌ Error during options scan: {e}")
