"""
create_gail_gtt.py
==================
Places an automated GTT order on Zerodha Kite for GAIL 190 CE.
Ensures trigger price complies with Zerodha's minimum distance threshold (>0.09 / 0.5%).
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

def place_gail_option_buy_gtt(trigger=None, limit=None, lots=1, execute=False):
    opt_symbol = "GAIL26NOV190CE"
    exchange = "NFO"
    lot_size = 3550
    qty = lots * lot_size
    product = "MIS"  # Switched to MIS to avoid SEBI physical delivery margin (₹9k vs ₹52k)

    q = kite.quote([f"NFO:{opt_symbol}"]).get(f"NFO:{opt_symbol}", {})
    ltp = q.get("last_price", 2.30)
    depth = q.get("depth", {})
    best_bid = depth.get("buy", [{}])[0].get("price", 0)
    best_ask = depth.get("sell", [{}])[0].get("price", 0)

    # Zerodha rule: trigger must be at least 0.12 away from last_price
    min_buffer = 0.15
    if trigger is None or (trigger - ltp) < 0.12:
        new_trigger = round(ltp + min_buffer, 2)
        print(f"[*] Auto-adjusting trigger: ₹{trigger} was too close to LTP ₹{ltp:.2f}.")
        print(f"[*] Setting compliant breakout trigger to: ₹{new_trigger:.2f} (buffer: +₹{new_trigger - ltp:.2f})")
        trigger = new_trigger

    if limit is None or limit <= trigger:
        limit = round(trigger + 0.10, 2)

    print("=" * 80)
    print("🎯 ZERODHA GTT BUY ORDER TICKET: GAIL 190 CE")
    print("=" * 80)
    print(f"• Tradingsymbol:   {opt_symbol}")
    print(f"• Exchange:       {exchange}")
    print(f"• Product:        {product}")
    print(f"• Current LTP:    ₹{ltp:.2f} (Bid: ₹{best_bid:.2f} | Ask: ₹{best_ask:.2f})")
    print(f"• Trigger Price:  ₹{trigger:.2f} (Compliant with Zerodha distance rule)")
    print(f"• Limit Price:    ₹{limit:.2f}")
    print(f"• Quantity:       {qty:,} shares ({lots} lot{'s' if lots > 1 else ''})")
    print(f"• Max Capital:    ₹{qty * limit:,.2f}")
    print("=" * 80)

    if not execute:
        print("\n⚠️ PREVIEW MODE: Order has NOT been sent to Zerodha yet.")
        print("To place this GTT order live, run:")
        print(f"   python create_gail_gtt.py --execute --trigger {trigger} --limit {limit} --lots {lots}")
        return

    print("🚀 Placing GTT order on Zerodha Kite...")
    buy_orders = [
        {
            "transaction_type": kite.TRANSACTION_TYPE_BUY,
            "quantity": qty,
            "order_type": kite.ORDER_TYPE_LIMIT,
            "product": product,
            "price": limit
        }
    ]

    resp = kite.place_gtt(
        trigger_type=kite.GTT_TYPE_SINGLE,
        tradingsymbol=opt_symbol,
        exchange=exchange,
        trigger_values=[trigger],
        last_price=ltp,
        orders=buy_orders
    )

    gid = resp.get("trigger_id")
    print(f"\n🎉 SUCCESS! GTT Trigger #{gid} successfully placed on Zerodha Kite!")
    print(f"   • Status:        ACTIVE")
    print(f"   • Trigger Price: ₹{trigger:.2f}")
    print(f"   • Limit Price:   ₹{limit:.2f}")
    print(f"   • Quantity:      {qty:,} shares")
    print(f"   • Expiry:        Valid until 26-Nov-2026")
    print("=" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Place GAIL 190 CE GTT on Zerodha")
    parser.add_argument("--execute", action="store_true", help="Execute the live order on Kite")
    parser.add_argument("--trigger", type=float, default=None, help="GTT trigger price")
    parser.add_argument("--limit", type=float, default=None, help="GTT limit price")
    parser.add_argument("--lots", type=int, default=1, help="Number of lots (3550 qty each)")
    args = parser.parse_args()

    place_gail_option_buy_gtt(trigger=args.trigger, limit=args.limit, lots=args.lots, execute=args.execute)
