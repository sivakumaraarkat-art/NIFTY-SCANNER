"""
create_icici_gtt_oco.py
1. Cancels the standalone open limit order (Order #2119684343042453504 at ₹28.00).
2. Deploys an automated GTT OCO (One-Cancels-Other) on Zerodha Kite for ICICIBANK26NOV1580CE:
   - Target Leg: Trigger ₹28.00 | Limit ₹28.00 (Profit: +₹2,100.00)
   - Stop-Loss Leg: Trigger ₹21.50 | Limit ₹21.20 (Risk: -₹2,450.00)
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

OPT_SYMBOL = "ICICIBANK26NOV1580CE"
FULL_SYMBOL = f"NFO:{OPT_SYMBOL}"
EXCHANGE = "NFO"
QTY = 700
PRODUCT = "MIS"

OLD_ORDER_ID = "2119684343042453504"

SL_TRIGGER = 21.50
SL_LIMIT = 21.20
TARGET_TRIGGER = 28.00
TARGET_LIMIT = 28.00

try:
    from kiteconnect import KiteConnect

    api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
    token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(token)

    # 1. Fetch live quote
    q = kite.quote([FULL_SYMBOL]).get(FULL_SYMBOL, {})
    opt_ltp = q.get("last_price", 25.50)

    print("=" * 80)
    print(f"🎯 DEPLOYING GTT OCO FOR {OPT_SYMBOL} [MIS]")
    print(f"   • Current Option LTP:  ₹{opt_ltp:.2f}")
    print(f"   • Quantity:            {QTY} shares (1 Lot)")
    print(f"   • Target (OCO Leg 1):  Trigger ₹{TARGET_TRIGGER:.2f} | Limit ₹{TARGET_LIMIT:.2f} (+₹2,100.00)")
    print(f"   • Stop-Loss (OCO Leg 2): Trigger ₹{SL_TRIGGER:.2f} | Limit ₹{SL_LIMIT:.2f} (-₹2,450.00)")
    print("=" * 80)

    # 2. Cancel existing standalone limit order if open
    orders = kite.orders()
    target_order = next((o for o in orders if str(o.get("order_id")) == OLD_ORDER_ID), None)

    if target_order and target_order.get("status") in ["OPEN", "TRIGGER PENDING"]:
        print(f"🔄 Cancelling open standalone limit order #{OLD_ORDER_ID} to unlock quantity...")
        try:
            kite.cancel_order(variety=kite.VARIETY_REGULAR, order_id=OLD_ORDER_ID)
            print(f"✅ Cancelled order #{OLD_ORDER_ID} successfully.")
        except Exception as e:
            print(f"⚠️ Notice while cancelling order: {e}")

    # 3. Check for any existing GTT on this symbol and cancel it to avoid duplicates
    existing_gtts = kite.get_gtts()
    for g in existing_gtts:
        cond = g.get("condition", {})
        if cond.get("tradingsymbol") == OPT_SYMBOL and g.get("status") == "active":
            gid = g.get("id")
            print(f"🔄 Removing previous GTT #{gid} for {OPT_SYMBOL}...")
            kite.delete_gtt(gid)
            print(f"✅ GTT #{gid} removed.")

    # 4. Place fresh GTT OCO
    print("🚀 Placing fresh GTT OCO Order...")
    trigger_values = [SL_TRIGGER, TARGET_TRIGGER]

    sell_orders = [
        {
            "transaction_type": kite.TRANSACTION_TYPE_SELL,
            "quantity": QTY,
            "order_type": kite.ORDER_TYPE_LIMIT,
            "product": PRODUCT,
            "price": SL_LIMIT
        },
        {
            "transaction_type": kite.TRANSACTION_TYPE_SELL,
            "quantity": QTY,
            "order_type": kite.ORDER_TYPE_LIMIT,
            "product": PRODUCT,
            "price": TARGET_LIMIT
        }
    ]

    resp = kite.place_gtt(
        trigger_type=kite.GTT_TYPE_OCO,
        tradingsymbol=OPT_SYMBOL,
        exchange=EXCHANGE,
        trigger_values=trigger_values,
        last_price=opt_ltp,
        orders=sell_orders
    )

    gtt_id = resp.get("trigger_id")
    print(f"\n🎉 SUCCESS! GTT OCO Order #{gtt_id} successfully created on Zerodha Kite!")
    print(f"   • Status:      ACTIVE")
    print(f"   • Stop-Loss:   ₹{SL_TRIGGER:.2f} (Limit: ₹{SL_LIMIT:.2f})")
    print(f"   • Target:      ₹{TARGET_TRIGGER:.2f} (Limit: ₹{TARGET_LIMIT:.2f})")
    print("=" * 80)

except Exception as e:
    print(f"❌ Error creating GTT: {e}")
