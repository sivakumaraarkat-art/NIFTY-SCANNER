"""
execute_cochin_mis_trade.py
═════════════════════════════════════════════════════════════════
Executes or Previews Cochin Shipyard (COCHINSHIP) Intraday MIS Trade.
• Product: MIS (5x Margin)
• Quantity: 380 Shares
• Entry: Limit Order at Current Market Price
• Stop-Loss: SL Order at ₹1,238.00
"""
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scanners.options_data_provider import get_kite_client

def execute_trade(execute=False, limit_price=None, qty=380):
    print("=" * 80)
    print("🚀 ZERODHA INTRADAY MIS ORDER DISPATCHER — COCHIN SHIPYARD")
    print("=" * 80)

    kite = get_kite_client()
    if not kite:
        print("❌ Kite client initialization failed. Check credentials.")
        return

    # 1. Fetch live quote
    quote = kite.quote(["NSE:COCHINSHIP"]).get("NSE:COCHINSHIP", {})
    ltp = float(quote.get("last_price", 0.0))
    if ltp == 0.0:
        print("❌ Could not fetch live quote.")
        return

    # 2. Check live margin
    margins = kite.margins().get("equity", {})
    avail_margin = margins.get("net", 0.0)

    buy_price = limit_price if limit_price else round(ltp + 0.5, 1) # 0.5 buffer for limit fill
    if buy_price <= 1240.0:
        sl_trigger = 1215.0
        sl_price = 1214.0
    else:
        sl_trigger = 1238.0
        sl_price = 1237.0
    target_1 = 1275.0
    target_2 = 1305.0

    req_margin = qty * buy_price * 0.20
    max_risk = (buy_price - sl_trigger) * qty
    reward_t1 = (target_1 - buy_price) * qty
    reward_t2 = (target_2 - buy_price) * qty

    print(f"Trading Symbol:       NSE:COCHINSHIP")
    print(f"Live Market Price:    ₹{ltp:.2f}")
    print(f"Product Type:         MIS (Intraday 5x Margin)")
    print(f"Order Quantity:       {qty} Shares")
    print(f"Entry Limit Price:    ₹{buy_price:.2f}")
    print(f"Total Trade Exposure: ₹{qty * buy_price:,.2f}")
    print(f"Margin Required (20%):₹{req_margin:,.2f}")
    print(f"Available Net Margin: ₹{avail_margin:,.2f}")
    print("-" * 80)
    print(f"🛡️ Stop-Loss Level:    ₹{sl_trigger:.2f} (Max Risk: -₹{max_risk:,.2f})")
    print(f"🎯 Target 1:           ₹{target_1:.2f} (Profit: +₹{reward_t1:,.2f})")
    print(f"🎯 Target 2:           ₹{target_2:.2f} (Profit: +₹{reward_t2:,.2f})")
    print(f"⏰ Auto Square-off:    03:20 PM IST")
    print("=" * 80)

    if avail_margin < req_margin:
        print(f"❌ INSUFFICIENT MARGIN! Available: ₹{avail_margin:,.2f}, Needed: ₹{req_margin:,.2f}")
        return

    if not execute:
        print("⚠️  DRY-RUN / PREVIEW MODE.")
        print("   Real money order was NOT placed on Zerodha.")
        print("   To dispatch real live order, run with: --execute")
        print("=" * 80)
        return

    # 3. Place Real Order on Zerodha Kite
    try:
        print("📡 Transmitting BUY LIMIT Order to Zerodha Exchange Gateway...")
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NSE,
            tradingsymbol="COCHINSHIP",
            transaction_type=kite.TRANSACTION_TYPE_BUY,
            quantity=qty,
            product=kite.PRODUCT_MIS,
            order_type=kite.ORDER_TYPE_LIMIT,
            price=buy_price
        )
        print(f"✅ BUY ORDER PLACED! Order ID: {order_id}")

        # Check order status
        time_to_wait = 2
        import time
        time.sleep(time_to_wait)
        order_history = kite.order_history(order_id)
        current_status = order_history[-1].get("status") if order_history else "UNKNOWN"
        print(f"   Order Status: {current_status}")

        if current_status == "COMPLETE":
            print("\n📡 Transmitting SL-LIMIT Protection Order to Zerodha Exchange Gateway...")
            try:
                sl_order_id = kite.place_order(
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
                print(f"✅ STOP-LOSS ORDER PLACED! Order ID: {sl_order_id}")
                print("🎉 Both Entry & SL protection are now ACTIVE on your Zerodha account!")
            except Exception as e_sl:
                print(f"⚠️ Could not place SL order automatically: {e_sl}")
        else:
            print(f"\n⏳ Buy Order is currently {current_status} at Limit ₹{buy_price:.2f}.")
            print(f"   It will execute as soon as COCHINSHIP drops to ₹{buy_price:.2f}.")
            print(f"   👉 Set your SL to ₹{sl_trigger:.2f} on Kite once the buy order fills.")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error during order placement: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Send live order to Zerodha")
    parser.add_argument("--price", type=float, default=None, help="Custom limit price")
    parser.add_argument("--qty", type=int, default=380, help="Order quantity (default 380)")
    args = parser.parse_args()
    execute_trade(execute=args.execute, limit_price=args.price, qty=args.qty)
