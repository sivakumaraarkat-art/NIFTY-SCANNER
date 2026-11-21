"""
check_now_live.py
Instant audit of:
- Current open positions in Zerodha Kite
- Today's order book (any new orders placed)
- Live quotes of key setups (ICICIBANK 1580 CE, NIFTY 24950 PE/CE, Nifty spot)
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

    # 1. Check Positions
    positions = kite.positions().get("net", [])
    open_pos = [p for p in positions if p.get("quantity", 0) != 0]

    # 2. Check Orders
    orders = kite.orders()
    recent_orders = orders[-5:] if orders else []

    # 3. Margins
    margin_data = kite.margins().get("equity", {})
    avail_cash = margin_data.get("available", {}).get("live_balance", 0.0)

    # 4. Quotes
    symbols_to_quote = [
        "NSE:NIFTY 50", "NSE:NIFTY BANK", "NSE:ICICIBANK",
        "NFO:ICICIBANK26NOV1580CE", "NFO:NIFTY26N0924950PE", "NFO:NIFTY26N0924950CE"
    ]
    quotes = kite.quote(symbols_to_quote)

    print("=" * 85)
    print("⚡ LIVE POSITION & MARKET RE-CHECK")
    print("=" * 85)

    if open_pos:
        print("\n💼 CURRENT OPEN POSITIONS:")
        print("-" * 85)
        for p in open_pos:
            tsym = p.get("tradingsymbol")
            prod = p.get("product")
            qty = p.get("quantity")
            avg = p.get("average_price", 0.0)
            ltp = p.get("last_price", 0.0)
            pnl = p.get("pnl", 0.0)
            m2m = p.get("m2m", 0.0)
            emoji = "🟢" if pnl >= 0 else "🔴"
            print(f"  • {tsym:<26} [{prod}] | Qty: {qty:>4} | Avg: ₹{avg:>7.2f} | LTP: ₹{ltp:>7.2f} | P&L: {emoji} ₹{pnl:+,.2f} (M2M: ₹{m2m:+,.2f})")
    else:
        print("\n💼 CURRENT OPEN POSITIONS: Zero open positions (All capital safe in cash).")

    print(f"\n💵 AVAILABLE CASH BALANCE: ₹{avail_cash:,.2f}")

    print("\n📝 LAST 3 ORDERS IN BROKER:")
    print("-" * 85)
    for o in recent_orders[-3:]:
        s_emoji = "✅" if o.get("status") == "COMPLETE" else ("⏳" if o.get("status") in ["OPEN", "TRIGGER PENDING"] else "❌")
        print(f"  • [{o.get('order_timestamp')}] {s_emoji} {o.get('status'):<9} | {o.get('transaction_type')} {o.get('quantity')} {o.get('tradingsymbol')} @ ₹{o.get('price')} (Filled: ₹{o.get('average_price')})")

    print("\n📊 LIVE MARKET QUOTES RIGHT NOW:")
    print("-" * 85)
    nifty = quotes.get("NSE:NIFTY 50", {})
    bank = quotes.get("NSE:NIFTY BANK", {})
    icici_spot = quotes.get("NSE:ICICIBANK", {})
    icici_opt = quotes.get("NFO:ICICIBANK26NOV1580CE", {})
    nifty_pe = quotes.get("NFO:NIFTY26N0924950PE", {})
    nifty_ce = quotes.get("NFO:NIFTY26N0924950CE", {})

    print(f"  • NIFTY 50 Spot:         ₹{nifty.get('last_price', 0.0):,.2f}")
    print(f"  • BANK NIFTY Spot:       ₹{bank.get('last_price', 0.0):,.2f}")
    print(f"  • ICICI Bank Spot:       ₹{icici_spot.get('last_price', 0.0):,.2f}")
    print(f"  • ICICI 1580 CE (Nov):   ₹{icici_opt.get('last_price', 0.0):.2f} (Bid: ₹{icici_opt.get('depth', {}).get('buy', [{}])[0].get('price', 0.0):.2f} / Ask: ₹{icici_opt.get('depth', {}).get('sell', [{}])[0].get('price', 0.0):.2f})")
    print(f"  • NIFTY 24950 PE (Today): ₹{nifty_pe.get('last_price', 0.0):.2f}")
    print(f"  • NIFTY 24950 CE (Today): ₹{nifty_ce.get('last_price', 0.0):.2f}")

    print("=" * 85)

except Exception as e:
    print(f"❌ Error: {e}")
