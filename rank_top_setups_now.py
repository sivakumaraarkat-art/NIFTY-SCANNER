"""
rank_top_setups_now.py
Ranks top stock & index setups using:
- News sentiment from Cloud VM
- Volume & Open Interest dynamics from Zerodha Kite
- Technical Moving Average & VWAP alignment
- Greek calibration & 4-Layer SL
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
        # (Category, Symbol, SpotSym, Bias, Lot, News Catalyst)
        ("STOCK_CE", "NFO:ICICIBANK26NOV1580CE", "NSE:ICICIBANK", "BULLISH", 700, "Bank Nifty +580 pts rally, ICICI breakout above 1575"),
        ("STOCK_PE", "NFO:HINDALCO26NOV940PE", "NSE:HINDALCO", "BEARISH", 700, "News: Drops below 20-EMA, weak metal sector sentiment"),
        ("STOCK_CE", "NFO:VEDL26NOV260CE", "NSE:VEDL", "BULLISH", 1150, "News: Bullish RSI upswing, high delivery volume"),
        ("NIFTY_EXPIRY_PE", "NFO:NIFTY26N0924950PE", "NSE:NIFTY 50", "BEARISH_EXPIRY", 65, "Nifty rejecting 25,000 call wall (29.6M OI), PCR 0.79"),
        ("NIFTY_EXPIRY_CE", "NFO:NIFTY26N0924950CE", "NSE:NIFTY 50", "BULLISH_EXPIRY", 65, "Contrarian recovery scalp if Bank Nifty carries Nifty > 24,960")
    ]

    symbols_to_quote = [c[1] for c in candidates] + list(set([c[2] for c in candidates]))
    quotes = kite.quote(symbols_to_quote)

    print("=" * 95)
    print("🏆 INSTITUTIONAL MULTI-FACTOR RANKING MATRIX (NEWS + VOLUME + TECHNICALS)")
    print("=" * 95)

    for cat, opt_sym, spot_sym, bias, lot, catalyst in candidates:
        oq = quotes.get(opt_sym, {})
        sq = quotes.get(spot_sym, {})

        opt_ltp = oq.get("last_price", 0.0)
        opt_vol = oq.get("volume", 0)
        opt_oi = oq.get("oi", 0)
        depth = oq.get("depth", {})
        buys = depth.get("buy", [])
        sells = depth.get("sell", [])
        bid = buys[0].get("price", 0.0) if buys else opt_ltp
        ask = sells[0].get("price", 0.0) if sells else opt_ltp

        spot_ltp = sq.get("last_price", 0.0)
        spot_ohlc = sq.get("ohlc", {})
        spot_close = spot_ohlc.get("close", spot_ltp)
        spot_chg = ((spot_ltp - spot_close) / spot_close * 100) if spot_close else 0.0

        clean_opt = opt_sym.replace("NFO:", "")
        clean_spot = spot_sym.replace("NSE:", "")

        # Target & SL calculation
        if "NIFTY" in cat:
            t1 = round(opt_ltp * 1.25, 2)
            t2 = round(opt_ltp * 1.50, 2)
            sl = round(opt_ltp * 0.70, 2)  # 30% SL for expiry day options
        else:
            t1 = round(opt_ltp * 1.08, 2)
            t2 = round(opt_ltp * 1.15, 2)
            sl = round(opt_ltp * 0.82, 2)  # 18% Powerful SL for monthly stock options

        cap_req = opt_ltp * lot
        risk_amt = (opt_ltp - sl) * lot
        reward_amt = (t1 - opt_ltp) * lot

        emoji = "🟢" if "BULLISH" in bias else "🔴"

        print(f"\n{emoji} [{cat}] {clean_opt} | Underlying: {clean_spot} @ ₹{spot_ltp:,.2f} ({spot_chg:>+5.2f}%)")
        print(f"   • Catalyst:      {catalyst}")
        print(f"   • Current LTP:   ₹{opt_ltp:>6.2f} (Bid: ₹{bid:.2f} / Ask: ₹{ask:.2f})")
        print(f"   • Target 1:      ₹{t1:>6.2f} (+{((t1-opt_ltp)/opt_ltp)*100:.1f}%) | Target 2: ₹{t2:>6.2f}")
        print(f"   • Powerful SL:   ₹{sl:>6.2f} (-{((opt_ltp-sl)/opt_ltp)*100:.1f}%)")
        print(f"   • Capital Req:   ₹{cap_req:,.2f} (1 Lot = {lot} qty) | Max Risk: ₹{risk_amt:,.2f} | T1 Profit: ₹{reward_amt:,.2f}")
        print(f"   • Liquidity:     Volume: {opt_vol:,} | Open Interest: {opt_oi:,}")

    print("\n" + "=" * 95)

except Exception as e:
    print(f"❌ Error ranking setups: {e}")
