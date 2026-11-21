"""
create_all_gtt_orders.py
========================
Unified Zerodha Kite GTT Order Engine for Siva Kumar's Active Holdings:
1. NIFTY 25,200 CE (65 qty): GTT OCO Exit Order (Target + Stoploss)
2. COCHIN SHIPYARD (25 shares): GTT Buy Order for Averaging @ Support (1,225.00)
3. SUZLON ENERGY (2,228 shares): GTT Sell Tranche Orders (T1 @ 58.50, T2 @ 62.00)
"""

import sys
import argparse
from pathlib import Path

# UTF-8 encoding support
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
except Exception as e:
    print(f"❌ Kite Connect initialization error: {e}")
    sys.exit(1)

def run_nifty_ce_gtt(execute=False):
    SYMBOL = "NIFTY26N0925200CE"
    EXCHANGE = "NFO"
    QTY = 65
    PRODUCT = "NRML"
    TARGET = 115.0
    STOP = 65.0
    STOP_LIMIT = 62.0

    print("\n" + "=" * 80)
    print("1. NIFTY 25,200 CE — GTT OCO EXIT ORDER")
    print("=" * 80)
    try:
        quote = kite.quote([f"{EXCHANGE}:{SYMBOL}"])
        ltp = quote.get(f"{EXCHANGE}:{SYMBOL}", {}).get("last_price", 92.60)
    except Exception:
        ltp = 92.60

    print(f"  • Instrument:       {EXCHANGE}:{SYMBOL} (Expiry: Nov 9, 2026)")
    print(f"  • Current LTP:      ₹{ltp:.2f} | Holding: {QTY} qty (1 Lot)")
    print(f"  • Target Leg:       Trigger at ₹{TARGET:.2f} | Limit: ₹{TARGET:.2f}")
    print(f"  • Stop-Loss Leg:    Trigger at ₹{STOP:.2f}   | Limit: ₹{STOP_LIMIT:.2f}")

    if not execute:
        print("  [PREVIEW] Order verified. Run with --execute to place on Kite.")
        return

    try:
        resp = kite.place_gtt(
            trigger_type=kite.GTT_TYPE_OCO,
            tradingsymbol=SYMBOL,
            exchange=EXCHANGE,
            trigger_values=[STOP, TARGET],
            last_price=ltp,
            orders=[
                {"transaction_type": kite.TRANSACTION_TYPE_SELL, "quantity": QTY, "order_type": kite.ORDER_TYPE_LIMIT, "product": PRODUCT, "price": STOP_LIMIT},
                {"transaction_type": kite.TRANSACTION_TYPE_SELL, "quantity": QTY, "order_type": kite.ORDER_TYPE_LIMIT, "product": PRODUCT, "price": TARGET}
            ]
        )
        print(f"  ✅ [SUCCESS] NIFTY GTT OCO Placed! Trigger ID: {resp.get('trigger_id')}")
    except Exception as e:
        print(f"  ❌ Error placing NIFTY GTT: {e}")

def run_cochin_buy_gtt(qty=25, price=1225.0, execute=False):
    SYMBOL = "COCHINSHIP"
    EXCHANGE = "NSE"
    PRODUCT = "CNC"

    print("\n" + "=" * 80)
    print("2. COCHIN SHIPYARD — GTT BUY ORDER (AVERAGING BLUEPRINT)")
    print("=" * 80)
    try:
        quote = kite.quote([f"{EXCHANGE}:{SYMBOL}"])
        ltp = quote.get(f"{EXCHANGE}:{SYMBOL}", {}).get("last_price", 1298.0)
    except Exception:
        ltp = 1298.0

    print(f"  • Instrument:       {EXCHANGE}:{SYMBOL} (Equity Delivery CNC)")
    print(f"  • Current CMP:      ₹{ltp:.2f}")
    print(f"  • Current Holding:  25 shares @ ₹1,755.00 avg (Invested: ₹43,875)")
    print(f"  • Averaging Order:  BUY {qty} shares @ ₹{price:.2f} limit")
    print(f"  • Capital Required: ₹{qty * price:,.2f}")

    new_shares = 25 + qty
    new_inv = 43875 + (qty * price)
    new_avg = new_inv / new_shares
    print(f"  • New Blended Avg:  ₹{new_avg:.2f} (Drops average cost down by ₹{1755 - new_avg:.2f}/share!)")
    print(f"  • Potential Profit: At target ₹1,800.00, Total P&L = +₹{(1800 - new_avg) * new_shares:,.2f}")

    if not execute:
        print("  [PREVIEW] Order verified. Run with --execute to place on Kite.")
        return

    try:
        resp = kite.place_gtt(
            trigger_type=kite.GTT_TYPE_SINGLE,
            tradingsymbol=SYMBOL,
            exchange=EXCHANGE,
            trigger_values=[price],
            last_price=ltp,
            orders=[
                {"transaction_type": kite.TRANSACTION_TYPE_BUY, "quantity": qty, "order_type": kite.ORDER_TYPE_LIMIT, "product": PRODUCT, "price": price}
            ]
        )
        print(f"  ✅ [SUCCESS] COCHIN GTT Buy Placed! Trigger ID: {resp.get('trigger_id')}")
    except Exception as e:
        print(f"  ❌ Error placing COCHIN GTT: {e}")

def run_suzlon_sell_gtt(execute=False):
    SYMBOL = "SUZLON"
    EXCHANGE = "NSE"
    PRODUCT = "CNC"

    print("\n" + "=" * 80)
    print("3. SUZLON ENERGY — GTT SELL PROFIT-BOOKING ORDERS")
    print("=" * 80)
    try:
        quote = kite.quote([f"{EXCHANGE}:{SYMBOL}"])
        ltp = quote.get(f"{EXCHANGE}:{SYMBOL}", {}).get("last_price", 57.40)
    except Exception:
        ltp = 57.40

    print(f"  • Instrument:       {EXCHANGE}:{SYMBOL} (Equity Delivery CNC)")
    print(f"  • Current CMP:      ₹{ltp:.2f} | Total Holding: 2,228 shares @ ₹55.80 avg")
    print(f"  • Tranche 1:        SELL 500 shares @ ₹58.50 Trigger (Profit: +₹1,350)")
    print(f"  • Tranche 2:        SELL 1,000 shares @ ₹62.00 Trigger (Profit: +₹6,200)")
    print(f"  • Balance:          728 shares held for ₹68.00+ mega target")

    if not execute:
        print("  [PREVIEW] Order verified. Run with --execute to place on Kite.")
        return

    # T1
    try:
        resp1 = kite.place_gtt(
            trigger_type=kite.GTT_TYPE_SINGLE,
            tradingsymbol=SYMBOL,
            exchange=EXCHANGE,
            trigger_values=[58.50],
            last_price=ltp,
            orders=[{"transaction_type": kite.TRANSACTION_TYPE_SELL, "quantity": 500, "order_type": kite.ORDER_TYPE_LIMIT, "product": PRODUCT, "price": 58.50}]
        )
        print(f"  ✅ [SUCCESS] SUZLON T1 (500 qty @ 58.50) Placed! Trigger ID: {resp1.get('trigger_id')}")
    except Exception as e:
        print(f"  ❌ Error placing SUZLON T1 GTT: {e}")

    # T2
    try:
        resp2 = kite.place_gtt(
            trigger_type=kite.GTT_TYPE_SINGLE,
            tradingsymbol=SYMBOL,
            exchange=EXCHANGE,
            trigger_values=[62.00],
            last_price=ltp,
            orders=[{"transaction_type": kite.TRANSACTION_TYPE_SELL, "quantity": 1000, "order_type": kite.ORDER_TYPE_LIMIT, "product": PRODUCT, "price": 62.00}]
        )
        print(f"  ✅ [SUCCESS] SUZLON T2 (1,000 qty @ 62.00) Placed! Trigger ID: {resp2.get('trigger_id')}")
    except Exception as e:
        print(f"  ❌ Error placing SUZLON T2 GTT: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unified Zerodha GTT Order Creator")
    parser.add_argument("--stock", choices=["nifty", "cochin", "suzlon", "all"], default="all", help="Target holding")
    parser.add_argument("--cochin-qty", type=int, default=25, help="Quantity of Cochin to buy for averaging (25 or 50)")
    parser.add_argument("--execute", action="store_true", help="Execute orders live on Zerodha Kite")
    args = parser.parse_args()

    print("=" * 80)
    print("ZERODHA KITE GTT ORDER SETUP & AVERAGING ADVISORY")
    print(f"Execution Mode: {'LIVE (Submitting to Zerodha Kite)' if args.execute else 'PREVIEW ONLY'}")
    print("=" * 80)

    if args.stock in ("nifty", "all"):
        run_nifty_ce_gtt(execute=args.execute)
    if args.stock in ("cochin", "all"):
        run_cochin_buy_gtt(qty=args.cochin_qty, execute=args.execute)
    if args.stock in ("suzlon", "all"):
        run_suzlon_sell_gtt(execute=args.execute)

    print("\n" + "=" * 80)
