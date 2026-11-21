"""
check_position_live_now.py
Checks current active position, P&L, live quotes, and order status for DATAPATTNS.
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

    # 1. Positions
    pos_data = kite.positions()
    net = pos_data.get("net", [])
    open_pos = [p for p in net if p.get("quantity", 0) != 0]

    # 2. Live Quotes
    q = kite.quote(["NSE:DATAPATTNS", "NFO:DATAPATTNS26NOV3900CE"])
    spot_q = q.get("NSE:DATAPATTNS", {})
    opt_q = q.get("NFO:DATAPATTNS26NOV3900CE", {})

    spot_ltp = spot_q.get("last_price", 0.0)
    opt_ltp = opt_q.get("last_price", 0.0)
    opt_depth = opt_q.get("depth", {})
    bid = opt_depth.get("buy", [{}])[0].get("price", 0.0)
    ask = opt_depth.get("sell", [{}])[0].get("price", 0.0)

    # 3. Order Book
    orders = kite.orders()
    open_orders = [o for o in orders if o.get("status") in ["OPEN", "TRIGGER PENDING"]]

    # 4. GTTs
    gtts = kite.get_gtts()
    active_gtts = [g for g in gtts if g.get("status") == "active"]

    print("=" * 80)
    print(f"🎯 LIVE POSITION & MARKET DEPTH AUDIT | TIME: {opt_q.get('last_trade_time', 'NOW')}")
    print("=" * 80)
    print(f"📍 DATAPATTNS Spot Price: ₹{spot_ltp:,.2f}")
    print(f"📍 Option 3900 CE LTP:   ₹{opt_ltp:.2f} (Bid: ₹{bid:.2f} / Ask: ₹{ask:.2f})")
    print("-" * 80)

    if open_pos:
        for p in open_pos:
            sym = p.get("tradingsymbol")
            prod = p.get("product")
            qty = p.get("quantity")
            avg = p.get("average_price")
            pnl = (opt_ltp - avg) * qty
            pct = ((opt_ltp - avg) / avg * 100) if avg else 0.0
            emoji = "🟢" if pnl >= 0 else "🔴"
            print(f"💼 ACTIVE TRADE: {sym} [{prod}]")
            print(f"   • Quantity:         {qty} shares (1 Lot)")
            print(f"   • Buy Price:        ₹{avg:.2f}")
            print(f"   • Current Price:    ₹{opt_ltp:.2f}")
            print(f"   • Unrealized P&L:   {emoji} ₹{pnl:+,.2f} ({pct:+.2f}%)")
            print(f"   • Target (at ₹243): ₹{(243.0 - avg) * qty:+,.2f} (+{((243.0 - avg)/avg)*100:.1f}%)")
    else:
        print("ℹ️  No open positions found. The position may have been closed.")

    print("-" * 80)
    print("📋 ACTIVE PENDING ORDERS IN BROKER:")
    if open_orders:
        for o in open_orders:
            print(f"  • Order #{o.get('order_id')} | {o.get('transaction_type')} {o.get('quantity')} {o.get('tradingsymbol')} @ ₹{o.get('price')} ({o.get('status')})")
    else:
        print("  • No pending open orders.")

    print("📋 ACTIVE GTT ORDERS:")
    if active_gtts:
        for g in active_gtts:
            print(f"  • GTT #{g.get('id')} | Triggers: {g.get('condition', {}).get('trigger_values')}")
    else:
        print("  • No active GTT orders.")

    print("=" * 80)

except Exception as e:
    print(f"❌ Error: {e}")
