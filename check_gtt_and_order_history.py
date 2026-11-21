"""
check_gtt_and_order_history.py
Checks whether the GTT order triggered or if the position is already closed.
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

    OPT_SYMBOL = "NIFTY26N0925200CE"

    # 1. Check Positions
    positions = kite.positions().get("net", [])
    active_pos = [p for p in positions if p.get("tradingsymbol") == OPT_SYMBOL]

    print("=" * 80)
    print("🔍 AUDIT: GTT TRIGGER & NIFTY POSITION STATUS")
    print("=" * 80)

    if not active_pos or active_pos[0].get("quantity", 0) == 0:
        print("🎉 POSITION ALREADY SQUARED OFF / CLOSED!")
        if active_pos:
            p = active_pos[0]
            print(f"  • Realized P&L: ₹{p.get('pnl'):+,.2f}")
    else:
        p = active_pos[0]
        qty = p.get("quantity")
        avg = p.get("average_price")
        ltp = p.get("last_price")
        pnl = p.get("pnl")
        print(f"  ⚠️ POSITION IS STILL OPEN: {qty} Qty @ Avg ₹{avg:.2f}")
        print(f"  • Current LTP: ₹{ltp:.2f}")
        print(f"  • Live P&L:    ₹{pnl:+,.2f}")

    # 2. Check Orders Today
    print("\n📋 TODAY'S ORDERS:")
    print("-" * 80)
    orders = kite.orders()
    nifty_orders = [o for o in orders if o.get("tradingsymbol") == OPT_SYMBOL]
    if not nifty_orders:
        print("  No executed orders for NIFTY today.")
    else:
        for o in nifty_orders:
            print(f"  • Order #{o.get('order_id')} | {o.get('transaction_type')} {o.get('quantity')} Qty | Status: {o.get('status')} | Price: {o.get('average_price', o.get('price'))} | Status Msg: {o.get('status_message')}")

    # 3. Check GTTs
    print("\n🛡️ GTT STATUS:")
    print("-" * 80)
    gtts = kite.get_gtts()
    nifty_gtts = [g for g in gtts if g.get("condition", {}).get("tradingsymbol") == OPT_SYMBOL]
    for g in nifty_gtts:
        print(f"  • GTT #{g.get('id')} | Status: {g.get('status')} | Triggers: {g.get('condition', {}).get('trigger_values')}")

    print("=" * 80)

except Exception as e:
    print(f"❌ Error: {e}")
