import sys
import os
import argparse
from pathlib import Path

# UTF-8 fix for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scanners.options_data_provider import get_kite_client

def create_cochin_gtt(mode="oco", execute=False):
    SYMBOL = "COCHINSHIP"
    EXCHANGE = "NSE"
    QTY = 82               # ~₹1,00,000 capital at ~₹1,205
    BUY_TRIGGER = 1205.0
    BUY_PRICE = 1205.0
    STOP_LOSS_TRIGGER = 1175.0
    STOP_LOSS_PRICE = 1170.0
    TARGET_TRIGGER = 1260.0
    TARGET_PRICE = 1260.0

    print("=" * 80)
    print("🪁 ZERODHA GTT CREATION ENGINE — COCHIN SHIPYARD (₹1,00,000 CAPITAL)")
    print("=" * 80)

    kite = get_kite_client()
    if not kite:
        print("❌ Kite client initialization failed. Check credentials.")
        return

    try:
        quote = kite.quote([f"{EXCHANGE}:{SYMBOL}"])
        ltp = quote.get(f"{EXCHANGE}:{SYMBOL}", {}).get("last_price", 1201.0)
        print(f"Trading Symbol:     {SYMBOL}")
        print(f"Live Market Price:  ₹{ltp:.2f}")
        print(f"Order Quantity:     {QTY} Shares")
        print("-" * 80)

        if mode == "buy":
            print("🛒 MODE: GTT BUY ORDER (AUTOMATIC ENTRY)")
            print(f"   • Trigger Price: ₹{BUY_TRIGGER:.2f}")
            print(f"   • Limit Price:   ₹{BUY_PRICE:.2f}")
            print(f"   • Total Capital: ₹{BUY_PRICE * QTY:,.2f}")
            print("   (Triggers when market opens and touches ₹1,205)")
            trigger_type = kite.GTT_TYPE_SINGLE
            trigger_values = [BUY_TRIGGER]
            orders = [
                {
                    "transaction_type": kite.TRANSACTION_TYPE_BUY,
                    "quantity": QTY,
                    "order_type": kite.ORDER_TYPE_LIMIT,
                    "product": kite.PRODUCT_CNC,
                    "price": BUY_PRICE
                }
            ]
        else:
            print("🛡️ MODE: GTT SELL OCO (PROTECTION & TARGET EXIT)")
            print(f"   • Stop-Loss Trigger: ₹{STOP_LOSS_TRIGGER:.2f} (Execution: ₹{STOP_LOSS_PRICE:.2f}) | Risk: -₹{(ltp - STOP_LOSS_TRIGGER)*QTY:,.2f}")
            print(f"   • Target Trigger:    ₹{TARGET_TRIGGER:.2f} (Execution: ₹{TARGET_PRICE:.2f}) | Profit: +₹{(TARGET_TRIGGER - ltp)*QTY:,.2f}")
            trigger_type = kite.GTT_TYPE_OCO
            trigger_values = [STOP_LOSS_TRIGGER, TARGET_TRIGGER]
            orders = [
                {
                    "transaction_type": kite.TRANSACTION_TYPE_SELL,
                    "quantity": QTY,
                    "order_type": kite.ORDER_TYPE_LIMIT,
                    "product": kite.PRODUCT_CNC,
                    "price": STOP_LOSS_PRICE
                },
                {
                    "transaction_type": kite.TRANSACTION_TYPE_SELL,
                    "quantity": QTY,
                    "order_type": kite.ORDER_TYPE_LIMIT,
                    "product": kite.PRODUCT_CNC,
                    "price": TARGET_PRICE
                }
            ]

        print("-" * 80)
        if not execute:
            print("ℹ️  SIMULATION PREVIEW ONLY.")
            print("   To place this directly on your Zerodha account, run with --execute:")
            if mode == "buy":
                print("   ! python prepare_cochinship_gtt.py --mode buy --execute")
            else:
                print("   ! python prepare_cochinship_gtt.py --mode oco --execute")
            print("=" * 80)
            return

        print(f"🚀 Submitting GTT order to Zerodha Kite...")
        gtt_response = kite.place_gtt(
            trigger_type=trigger_type,
            tradingsymbol=SYMBOL,
            exchange=EXCHANGE,
            trigger_values=trigger_values,
            last_price=ltp,
            orders=orders
        )
        trigger_id = gtt_response.get("trigger_id")
        print(f"\n🎉 SUCCESS: GTT Order Placed on Zerodha Kite!")
        print(f"   • GTT Trigger ID: {trigger_id}")
        print(f"   • Status: Active on Zerodha Kite (Check Kite App -> Orders -> GTT)")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error submitting GTT order: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["buy", "oco"], default="oco", help="buy = Entry GTT, oco = Exit StopLoss & Target")
    parser.add_argument("--execute", action="store_true", help="Submit order directly to Zerodha")
    args = parser.parse_args()
    create_cochin_gtt(mode=args.mode, execute=args.execute)
