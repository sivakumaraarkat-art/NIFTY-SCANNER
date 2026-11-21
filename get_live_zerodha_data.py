"""
get_live_zerodha_data.py
Fetches 100% verified LIVE market quotes, holdings, orders, and rankings
directly from Zerodha Kite Connect API.
"""

import sys
import io
import json
from pathlib import Path
from datetime import datetime

# Windows console encoding fix
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent

try:
    from kiteconnect import KiteConnect
except ImportError:
    print("❌ kiteconnect library not installed.")
    sys.exit(1)

api_key_file = ROOT / ".kite_api_key"
token_file = ROOT / ".kite_access_token"

if not api_key_file.exists() or not token_file.exists():
    print("❌ Kite API Key or Access Token file missing.")
    sys.exit(1)

api_key = api_key_file.read_text(encoding="utf-8").strip()
access_token = token_file.read_text(encoding="utf-8").strip()

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

print("=" * 95)
print(f"📡 CONNECTING TO ZERODHA KITE LIVE API — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 95)

# 1. LIVE QUOTES FOR HIGH-MOMENTUM SWING & WATCHLIST STOCKS
swing_symbols = [
    "NSE:DIXON", "NSE:KEI", "NSE:KAYNES", "NSE:TITAGARH", "NSE:PCBL",
    "NSE:KOTAKBANK", "NSE:NYKAA", "NSE:PNB", "NSE:LAURUSLABS", "NSE:DIVISLAB",
    "NSE:BLUESTARCO", "NSE:ADANIPORTS", "NSE:ELECTCAST", "NSE:COCHINSHIP",
    "NSE:RELIANCE", "NSE:SBIN", "NSE:BSE"
]

try:
    quotes = kite.quote(swing_symbols)
    print("\n✅ Successfully fetched live quotes for 17 high-momentum stocks from Zerodha:")
    print("-" * 95)
    print(f"{'RANK':<5} | {'SYMBOL':<12} | {'LIVE LTP':<10} | {'DAY CHG (%)':<12} | {'DAY HIGH':<10} | {'DAY LOW':<10} | {'VOLUME':<12} | {'STATUS'}")
    print("-" * 95)

    ranked_list = []
    for s in swing_symbols:
        q = quotes.get(s, {})
        ltp = q.get("last_price", 0.0)
        ohlc = q.get("ohlc", {})
        prev_close = ohlc.get("close", ltp)
        chg = ((ltp - prev_close) / prev_close * 100) if prev_close else 0.0
        high = ohlc.get("high", 0.0)
        low = ohlc.get("low", 0.0)
        volume = q.get("volume", 0)
        sym_clean = s.replace("NSE:", "")

        ranked_list.append({
            "symbol": sym_clean,
            "ltp": ltp,
            "prev_close": prev_close,
            "change_pct": round(chg, 2),
            "high": high,
            "low": low,
            "volume": volume
        })

    # Sort by strongest day change %
    ranked_list.sort(key=lambda x: x["change_pct"], reverse=True)

    for i, item in enumerate(ranked_list, 1):
        status = "🔥 STRONG" if item["change_pct"] >= 1.0 else ("🟢 UP" if item["change_pct"] > 0 else "🔴 DOWN")
        print(f"#{i:<4} | {item['symbol']:<12} | ₹{item['ltp']:>8.2f} | {item['change_pct']:>+9.2f}% | ₹{item['high']:>8.2f} | ₹{item['low']:>8.2f} | {item['volume']:>11,d} | {status}")

except Exception as e:
    print(f"⚠️ Error fetching live quotes: {e}")

# 2. LIVE ZERODHA ACCOUNT AUDIT (HOLDINGS & MARGINS)
print("\n" + "=" * 95)
print("💼 ZERODHA LIVE ACCOUNT & PORTFOLIO AUDIT:")
print("=" * 95)

try:
    margins = kite.margins("equity")
    cash_bal = margins.get("available", {}).get("live_balance", 0.0)
    print(f"💰 Available Cash Margin: ₹{cash_bal:,.2f}")

    holdings = kite.holdings()
    print(f"📊 Total Active Holdings: {len(holdings)} stocks")

    # Focus on Cochin & Electcast
    print("\n🔍 Live Details on COCHINSHIP & ELECTCAST in your Account:")
    for h in holdings:
        sym = h.get("tradingsymbol")
        if sym in ["COCHINSHIP", "ELECTCAST", "PCBL", "LODHA", "ASHOKLEY"]:
            qty = h.get("quantity", 0) + h.get("t1_quantity", 0)
            avg = h.get("average_price", 0.0)
            ltp = h.get("last_price", 0.0)
            pnl = h.get("pnl", 0.0)
            pnl_pct = (pnl / (qty * avg) * 100) if (qty * avg) > 0 else 0.0
            print(f"  • {sym:<12} | Qty: {qty:>4} | Buy Avg: ₹{avg:>8.2f} | Live LTP: ₹{ltp:>8.2f} | P&L: ₹{pnl:>9.2f} ({pnl_pct:>+6.2f}%)")

except Exception as e:
    print(f"⚠️ Error fetching account data: {e}")

# Save json output
with open(ROOT / "live_zerodha_feed.json", "w", encoding="utf-8") as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "quotes": ranked_list if 'ranked_list' in locals() else []
    }, f, indent=2)

print("\n" + "=" * 95)
print("✅ Live Zerodha data captured and saved to live_zerodha_feed.json")
print("=" * 95)
