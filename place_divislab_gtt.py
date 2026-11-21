"""
place_divislab_gtt.py
Places a calibrated OCO GTT for DIVISLAB26NOV11700CE:
- Stop-Loss: ₹296.00 (Risk: -₹1,870)
- Target:    ₹345.00 (Profit: +₹3,030)
- Risk/Reward: 1 : 1.62
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

    OPT = "NFO:DIVISLAB26NOV11700CE"
    SYM = "DIVISLAB26NOV11700CE"
    EXCHANGE = "NFO"
    QTY = 100
    BUY_PRICE = 314.70

    # Get live quote
    q = kite.quote([OPT]).get(OPT, {})
    ltp = q.get("last_price", 310.0)

    # Risk-Reward Calibration
    SL_TRIGGER = 296.0
    SL_LIMIT = 292.0
    TGT_TRIGGER = 345.0
    TGT_LIMIT = 345.0

    print("=" * 80)
    print("🛡️ GTT OCO CREATION: DIVISLAB 11,700 CE")
    print("=" * 80)
    print(f"  • Instrument:       {SYM}")
    print(f"  • Position:         {QTY} shares @ ₹{BUY_PRICE:.2f} avg")
    print(f"  • Current LTP:      ₹{ltp:.2f}")
    print(f"  • Stop-Loss Leg:    Trigger ₹{SL_TRIGGER:.2f} | Limit ₹{SL_LIMIT:.2f} (Loss: -₹{(BUY_PRICE - SL_TRIGGER) * QTY:,.2f})")
    print(f"  • Target Leg:       Trigger ₹{TGT_TRIGGER:.2f} | Limit ₹{TGT_LIMIT:.2f} (Profit: +₹{(TGT_TRIGGER - BUY_PRICE) * QTY:,.2f})")
    print(f"  • Risk / Reward:    1 : {((TGT_TRIGGER - BUY_PRICE) / (BUY_PRICE - SL_TRIGGER)):.2f}")
    print("-" * 80)

    # Cancel any existing GTT for this symbol
    all_gtts = kite.get_gtts()
    for g in all_gtts:
        if g.get("condition", {}).get("tradingsymbol") == SYM and g.get("status") == "active":
            gid = g.get("id")
            try:
                kite.delete_gtt(gid)
                print(f"  🗑️ Cancelled existing GTT #{gid}")
            except Exception as e:
                print(f"  ⚠️ Could not cancel GTT #{gid}: {e}")

    # Check if position is MIS or NRML
    pos = kite.positions().get("net", [])
    divis_pos = next((p for p in pos if p.get("tradingsymbol") == SYM and p.get("quantity", 0) != 0), None)
    product_type = divis_pos.get("product", "MIS") if divis_pos else "MIS"
    print(f"  • Detected Position Product: {product_type}")

    # Place GTT OCO
    resp = kite.place_gtt(
        trigger_type=kite.GTT_TYPE_OCO,
        tradingsymbol=SYM,
        exchange=EXCHANGE,
        trigger_values=[SL_TRIGGER, TGT_TRIGGER],
        last_price=ltp,
        orders=[
            {
                "transaction_type": kite.TRANSACTION_TYPE_SELL,
                "quantity": QTY,
                "order_type": kite.ORDER_TYPE_LIMIT,
                "product": product_type,
                "price": SL_LIMIT
            },
            {
                "transaction_type": kite.TRANSACTION_TYPE_SELL,
                "quantity": QTY,
                "order_type": kite.ORDER_TYPE_LIMIT,
                "product": product_type,
                "price": TGT_LIMIT
            }
        ]
    )

    gtt_id = resp.get("trigger_id")
    print("\n🎉 SUCCESS: GTT OCO ORDER CREATED ON ZERODHA KITE!")
    print(f"  • GTT Trigger ID:   #{gtt_id}")
    print(f"  • Status:           ACTIVE")
    print(f"  • Stop-Loss:        ₹{SL_TRIGGER:.2f} (Caps risk to -₹{(BUY_PRICE - SL_TRIGGER) * QTY:,.2f})")
    print(f"  • Target:           ₹{TGT_TRIGGER:.2f} (Locks in +₹{(TGT_TRIGGER - BUY_PRICE) * QTY:,.2f} profit)")
    print("=" * 80)

except Exception as e:
    print(f"❌ Error placing GTT: {e}")
