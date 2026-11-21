"""
check_divis_gtt_execution.py
Checks whether the DIVISLAB GTT triggered and executed the exit order.
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

    SYM = "DIVISLAB26NOV11700CE"

    # 1. Check Positions
    positions = kite.positions().get("net", [])
    divis_pos = next((p for p in positions if p.get("tradingsymbol") == SYM), None)

    print("=" * 80)
    print("🔍 DIVISLAB GTT TRIGGER & POSITION AUDIT")
    print("=" * 80)

    if not divis_pos or divis_pos.get("quantity", 0) == 0:
        print("🎉 POSITION SQUARED OFF & CLOSED!")
        if divis_pos:
            print(f"  • Realized P&L: ₹{divis_pos.get('pnl'):+,.2f}")
    else:
        qty = divis_pos.get("quantity")
        avg = divis_pos.get("average_price")
        ltp = divis_pos.get("last_price")
        pnl = divis_pos.get("pnl")
        print(f"  ⚠️ POSITION STILL OPEN: {qty} Qty @ Avg ₹{avg:.2f}")
        print(f"  • Current LTP: ₹{ltp:.2f}")
        print(f"  • P&L:         ₹{pnl:+,.2f}")

    # 2. Check Order Book
    print("\n📋 DIVISLAB ORDERS TODAY:")
    print("-" * 80)
    orders = kite.orders()
    divis_orders = [o for o in orders if o.get("tradingsymbol") == SYM]
    for o in divis_orders:
        print(f"  • Order #{o.get('order_id')} | {o.get('transaction_type')} {o.get('quantity')} Qty | Status: {o.get('status')} | Price: {o.get('average_price', o.get('price'))} | Msg: {o.get('status_message')}")

    # 3. Check GTT
    print("\n🛡️ GTT STATUS:")
    print("-" * 80)
    gtts = kite.get_gtts()
    divis_gtts = [g for g in gtts if g.get("condition", {}).get("tradingsymbol") == SYM]
    for g in divis_gtts:
        print(f"  • GTT #{g.get('id')} | Status: {g.get('status')} | Triggers: {g.get('condition', {}).get('trigger_values')}")

    print("=" * 80)

except Exception as e:
    print(f"❌ Error: {e}")
