"""
buy_gail_mis_direct.py
======================
Places an immediate MIS Limit Buy order on Zerodha Kite for GAIL 190 CE (NFO:GAIL26NOV190CE).
Uses MIS product to avoid SEBI physical delivery settlement margins (requires ~₹9,000 margin).
"""

import sys
import argparse
from pathlib import Path

# Fix Windows console UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent

# Kite Connect
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()

from kiteconnect import KiteConnect
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

def place_direct_mis_order(limit_price=None, lots=1, execute=False):
    opt_symbol = "GAIL26NOV190CE"
    exchange = kite.EXCHANGE_NFO
    lot_size = 3550
    qty = lots * lot_size
    product = kite.PRODUCT_MIS

    q = kite.quote([f"NFO:{opt_symbol}"]).get(f"NFO:{opt_symbol}", {})
    ltp = q.get("last_price", 2.40)
    depth = q.get("depth", {})
    best_bid = depth.get("buy", [{}])[0].get("price", 0)
    best_ask = depth.get("sell", [{}])[0].get("price", 0)

    # If no limit given, set at best ask + 0.05 buffer to guarantee immediate fill
    if limit_price is None:
        limit_price = round(max(best_ask, ltp) + 0.05, 2)

    total_capital = qty * limit_price

    print("=" * 80)
    print("🎯 ZERODHA DIRECT MIS BUY ORDER TICKET: GAIL 190 CE")
    print("=" * 80)
    print(f"• Tradingsymbol:   {opt_symbol}")
    print(f"• Exchange:       NFO")
    print(f"• Product:        MIS (Intraday — Margin: ~₹9,000, Fits your ₹40.5k balance)")
    print(f"• Current LTP:    ₹{ltp:.2f} (Best Bid: ₹{best_bid:.2f} | Best Ask: ₹{best_ask:.2f})")
    print(f"• Limit Price:    ₹{limit_price:.2f}")
    print(f"• Quantity:       {qty:,} shares ({lots} lot{'s' if lots > 1 else ''})")
    print(f"• Max Capital:    ₹{total_capital:,.2f}")
    print("=" * 80)

    if not execute:
        print("\n⚠️ PREVIEW MODE: Order has NOT been sent to Zerodha yet.")
        print("To execute this order live, run:")
        print(f"   python buy_gail_mis_direct.py --execute --price {limit_price} --lots {lots}")
        return

    print("🚀 Placing live MIS Limit Buy order on Zerodha Kite...")
    resp = kite.place_order(
        variety=kite.VARIETY_REGULAR,
        exchange=exchange,
        tradingsymbol=opt_symbol,
        transaction_type=kite.TRANSACTION_TYPE_BUY,
        quantity=qty,
        product=product,
        order_type=kite.ORDER_TYPE_LIMIT,
        price=limit_price
    )

    order_id = resp.get("order_id") if isinstance(resp, dict) else resp
    print(f"\n🎉 SUCCESS! Order #{order_id} placed on Zerodha Kite!")
    print(f"   • Status: Submitted to Exchange (MIS Limit @ ₹{limit_price:.2f})")
    print("=" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Place Direct MIS Buy for GAIL 190 CE")
    parser.add_argument("--execute", action="store_true", help="Execute the live order on Kite")
    parser.add_argument("--price", type=float, default=None, help="Limit buy price")
    parser.add_argument("--lots", type=int, default=1, help="Number of lots (3550 qty each)")
    args = parser.parse_args()

    place_direct_mis_order(limit_price=args.price, lots=args.lots, execute=args.execute)
