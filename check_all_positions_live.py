"""
check_all_positions_live.py
Deep audit of all Zerodha Kite positions (Open F&O / MIS / CNC),
today's trades, realized/unrealized P&L, and available cash margins.
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

    pos = kite.positions()
    net_pos = pos.get("net", [])
    day_pos = pos.get("day", [])
    margins = kite.margins("equity")
    available_cash = margins.get("available", {}).get("live_balance", 0.0)

    print("=" * 80)
    print("💼 LIVE ZERODHA ACCOUNT AUDIT: POSITIONS & MARGINS")
    print("=" * 80)

    # 1. Available Margins
    print(f"💰 AVAILABLE CASH BALANCE: ₹{available_cash:,.2f}")
    print("-" * 80)

    # 2. Open Positions (Active Risk)
    open_positions = [p for p in net_pos if p.get("quantity", 0) != 0]

    print("\n⚡ 1. ACTIVE OPEN POSITIONS (CURRENT RISK):")
    print("-" * 80)
    if not open_positions:
        print("  ✅ NO OPEN POSITIONS! Your active market risk is currently 0 (Flat).")
    else:
        for p in open_positions:
            sym = p.get("tradingsymbol")
            prod = p.get("product")
            qty = p.get("quantity")
            avg = p.get("average_price")
            ltp = p.get("last_price")
            pnl = p.get("pnl")
            m2m = p.get("m2m")
            status_emoji = "🟢" if pnl >= 0 else "🔴"
            print(f"  {status_emoji} {sym} ({prod})")
            print(f"     • Quantity:   {qty}")
            print(f"     • Buy Price:  ₹{avg:.2f}")
            print(f"     • Live LTP:   ₹{ltp:.2f}")
            print(f"     • Live P&L:   ₹{pnl:+,.2f}")
            print(f"     • Day MTM:    ₹{m2m:+,.2f}")

    # 3. Closed Trades Today
    closed_positions = [p for p in net_pos if p.get("quantity", 0) == 0 and (p.get("day_buy_quantity", 0) > 0 or p.get("day_sell_quantity", 0) > 0 or p.get("pnl", 0) != 0)]
    print("\n📋 2. COMPLETED / CLOSED TRADES TODAY:")
    print("-" * 80)
    total_realized_pnl = 0.0
    if not closed_positions:
        print("  No closed intraday trades found today.")
    else:
        for p in closed_positions:
            sym = p.get("tradingsymbol")
            prod = p.get("product")
            pnl = p.get("pnl", 0.0)
            total_realized_pnl += pnl
            emoji = "🟢" if pnl >= 0 else "🔴"
            print(f"  {emoji} {sym} ({prod}): Realized P&L = ₹{pnl:+,.2f} [Closed]")

        print("-" * 80)
        net_emoji = "🟢" if total_realized_pnl >= 0 else "🔴"
        print(f"  {net_emoji} TOTAL REALIZED P&L TODAY: ₹{total_realized_pnl:+,.2f}")

    # 4. Open Orders / Triggers
    orders = kite.orders()
    pending_orders = [o for o in orders if o.get("status") in ["OPEN", "TRIGGER PENDING"]]
    print("\n⏳ 3. PENDING ORDERS IN ORDER BOOK:")
    print("-" * 80)
    if not pending_orders:
        print("  ✅ No pending orders waiting in the order book.")
    else:
        for o in pending_orders:
            print(f"  • Order #{o.get('order_id')} | {o.get('tradingsymbol')} | {o.get('transaction_type')} {o.get('quantity')} Qty @ ₹{o.get('price')} (Status: {o.get('status')})")

    # 5. Active GTTs
    gtts = kite.get_gtts()
    active_gtts = [g for g in gtts if g.get("status") == "active"]
    print("\n🛡️ 4. ACTIVE GTT ORDERS:")
    print("-" * 80)
    if not active_gtts:
        print("  No active GTT orders.")
    else:
        for g in active_gtts:
            cond = g.get("condition", {})
            print(f"  • GTT #{g.get('id')} | {cond.get('tradingsymbol')} | Triggers: {cond.get('trigger_values')}")

    print("=" * 80)

except Exception as e:
    print(f"❌ Error checking positions: {e}")
