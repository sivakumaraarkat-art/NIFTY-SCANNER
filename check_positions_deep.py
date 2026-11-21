"""
check_positions_deep.py
Fetches live positions, order book history, and demat holdings directly from Zerodha Kite.
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

    print("=" * 85)
    print("💼 COMPREHENSIVE ZERODHA POSITION & ORDER BOOK AUDIT")
    print("=" * 85)

    # 1. Positions
    pos_data = kite.positions()
    net = pos_data.get("net", [])
    day = pos_data.get("day", [])

    open_positions = [p for p in net if p.get("quantity", 0) != 0]
    closed_positions = [p for p in net if p.get("quantity", 0) == 0]

    print("\n🟢 ACTIVE / OPEN DERIVATIVE & INTRADAY POSITIONS:")
    print("-" * 85)
    if open_positions:
        for p in open_positions:
            tsym = p.get("tradingsymbol")
            prod = p.get("product")
            qty = p.get("quantity")
            buy_val = p.get("buy_value", 0.0)
            sell_val = p.get("sell_value", 0.0)
            ltp = p.get("last_price", 0.0)
            m2m = p.get("m2m", 0.0)
            pnl = p.get("pnl", 0.0)
            avg = p.get("average_price", 0.0)
            emoji = "🟢" if pnl >= 0 else "🔴"
            print(f"  • {tsym:<24} [{prod}] | Qty: {qty:>4} | Avg: ₹{avg:>7.2f} | LTP: ₹{ltp:>7.2f} | P&L: {emoji} ₹{pnl:+,.2f} (M2M: ₹{m2m:+,.2f})")
    else:
        print("  ℹ️  No open/active derivative or intraday positions right now.")

    print("\n📦 CLOSED POSITIONS TODAY:")
    print("-" * 85)
    total_realized_pnl = 0.0
    if closed_positions:
        for p in closed_positions:
            tsym = p.get("tradingsymbol")
            prod = p.get("product")
            pnl = p.get("pnl", 0.0)
            total_realized_pnl += pnl
            buy_qty = p.get("buy_quantity", 0)
            sell_qty = p.get("sell_quantity", 0)
            buy_p = p.get("buy_price", 0.0)
            sell_p = p.get("sell_price", 0.0)
            emoji = "🟢" if pnl >= 0 else "🔴"
            print(f"  • {tsym:<24} [{prod}] | Qty: {buy_qty} | Buy: ₹{buy_p:>7.2f} | Sell: ₹{sell_p:>7.2f} | Realized P&L: {emoji} ₹{pnl:+,.2f}")
        print(f"  💰 Net Realized P&L from Closed Trades: ₹{total_realized_pnl:+,.2f}")
    else:
        print("  • No closed positions logged today.")

    # 2. Today's Order Book
    orders = kite.orders()
    recent_orders = orders[-10:] if orders else []
    print("\n📝 RECENT ORDERS TODAY (Order Book):")
    print("-" * 85)
    if recent_orders:
        for o in recent_orders:
            oid = o.get("order_id")
            tsym = o.get("tradingsymbol")
            ttype = o.get("transaction_type")
            status = o.get("status")
            qty = o.get("quantity")
            price = o.get("price")
            avg_price = o.get("average_price", 0.0)
            otime = o.get("order_timestamp")
            tag = o.get("tag", "")
            s_emoji = "✅" if status == "COMPLETE" else ("⏳" if status in ["OPEN", "TRIGGER PENDING"] else "❌")
            print(f"  • [{otime}] {s_emoji} {status:<9} | {ttype:<4} {qty:>4} {tsym:<22} @ ₹{price:>7.2f} (Filled: ₹{avg_price:>7.2f}) | ID: {oid}")
    else:
        print("  • No orders placed today.")

    # 3. Available Margins
    margins = kite.margins()
    eq = margins.get("equity", {})
    avail = eq.get("available", {}).get("live_balance", 0.0)
    net_marg = eq.get("net", 0.0)
    print(f"\n💵 AVAILABLE MARGIN: Live Cash = ₹{avail:,.2f} | Net Margin = ₹{net_marg:,.2f}")

    print("=" * 85)

except Exception as e:
    print(f"❌ Error auditing positions: {e}")
