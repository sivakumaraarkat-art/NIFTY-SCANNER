"""
adjust_target_limit.py
Modifies the open target limit order for DATAPATTNS26NOV3900CE (Order ID: 2119675625991090176)
from ₹243.00 to institutional high-probability target ₹239.50.
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

ORDER_ID = "2119675625991090176"
NEW_TARGET_PRICE = 239.50

try:
    from kiteconnect import KiteConnect

    api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
    token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(token)

    # 1. Fetch current status of the order
    orders = kite.orders()
    target_order = next((o for o in orders if str(o.get("order_id")) == ORDER_ID), None)

    if not target_order:
        print(f"❌ Order #{ORDER_ID} not found in today's order book.")
        sys.exit(1)

    status = target_order.get("status")
    current_price = target_order.get("price")
    tsym = target_order.get("tradingsymbol")
    qty = target_order.get("quantity")

    print("=" * 80)
    print(f"📋 TARGET LIMIT ORDER MODIFICATION: {tsym} (Qty: {qty})")
    print(f"   • Current Status:       {status}")
    print(f"   • Existing Limit Price: ₹{current_price:.2f}")
    print(f"   • Calibrated New Price: ₹{NEW_TARGET_PRICE:.2f}")
    print("=" * 80)

    if status not in ["OPEN", "TRIGGER PENDING"]:
        print(f"⚠️ Order cannot be modified because status is '{status}'.")
        sys.exit(0)

    # Modify Order
    resp = kite.modify_order(
        variety=kite.VARIETY_REGULAR,
        order_id=ORDER_ID,
        price=NEW_TARGET_PRICE,
        order_type=kite.ORDER_TYPE_LIMIT
    )

    print(f"✅ SUCCESS! Order #{ORDER_ID} modified to ₹{NEW_TARGET_PRICE:.2f}!")
    print(f"   Response Order ID: {resp}")

except Exception as e:
    print(f"❌ Modification failed: {e}")
