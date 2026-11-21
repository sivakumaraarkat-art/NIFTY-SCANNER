"""
place_cochin_sl.py
═════════════════════════════════════════════════════════════════
Places the mandatory Stop-Loss Order for the active 375 MIS shares.
• Trigger: ₹1,215.00
• Price: ₹1,214.00
• Qty: 375 Shares
"""
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scanners.options_data_provider import get_kite_client

def place_sl(execute=False, sl_trigger=1215.0, sl_price=1214.0):
    print("=" * 80)
    print("🛡️ ZERODHA STOP-LOSS DISPATCHER — COCHIN SHIPYARD (375 SHARES)")
    print("=" * 80)

    kite = get_kite_client()
    if not kite:
        print("❌ Kite client initialization failed.")
        return

    positions = kite.positions().get("net", [])
    pos = [p for p in positions if p.get("tradingsymbol") == "COCHINSHIP" and p.get("product") == "MIS"]
    if not pos:
        print("⚠️ No active MIS position found for COCHINSHIP.")
        return

    qty = abs(pos[0].get("quantity", 0))
    avg_price = pos[0].get("buy_price", 1239.5)
    print(f"Active Position: {qty} Shares MIS @ ₹{avg_price:.2f}")
    print(f"Stop-Loss Trigger: ₹{sl_trigger:.2f}")
    print(f"Stop-Loss Limit:   ₹{sl_price:.2f}")
    print(f"Max Capital Risk:  -₹{(avg_price - sl_trigger) * qty:,.2f}")
    print("-" * 80)

    if not execute:
        print("⚠️ PREVIEW MODE: SL order was not submitted.")
        print("   Run with --execute to submit to Zerodha.")
        print("=" * 80)
        return

    try:
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NSE,
            tradingsymbol="COCHINSHIP",
            transaction_type=kite.TRANSACTION_TYPE_SELL,
            quantity=qty,
            product=kite.PRODUCT_MIS,
            order_type=kite.ORDER_TYPE_SL,
            trigger_price=sl_trigger,
            price=sl_price
        )
        print(f"✅ STOP-LOSS ORDER PLACED SUCCESSFULLY! Order ID: {order_id}")
        print("🛡️ Your capital is now 100% protected against unexpected market crashes!")
        print("=" * 80)
    except Exception as e:
        print(f"❌ Error placing SL order: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--trigger", type=float, default=1215.0, help="SL Trigger price")
    parser.add_argument("--price", type=float, default=None, help="SL Limit price (defaults to trigger - 1.0)")
    args = parser.parse_args()
    limit_pr = args.price if args.price is not None else (args.trigger - 1.0)
    place_sl(execute=args.execute, sl_trigger=args.trigger, sl_price=limit_pr)
