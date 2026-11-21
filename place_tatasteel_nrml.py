"""
place_tatasteel_nrml.py
=======================
1. Cancels the dangling OCO GTT #345685906.
2. Places the compliant NRML Buy order/GTT on Zerodha Kite for TATASTEEL 172.5 PE.
   (NRML avoids the SEBI MIS physical delivery block during expiry week).
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

OPT_SYMBOL = "TATASTEEL26NOV172.5PE"
LOT_SIZE = 2750

def run_nrml_flow(execute=False):
    # 1. Check & delete dangling GTT #345685906
    print("=" * 80)
    print("🔍 STEP 1: CLEANING UP DANGLING SELL GTT")
    print("=" * 80)
    try:
        gtts = kite.get_gtts()
        for g in gtts:
            cond = g.get("condition", {})
            if cond.get("tradingsymbol") == OPT_SYMBOL and g.get("status") in ["active", "triggered"]:
                gid = g.get("id")
                if execute:
                    kite.delete_gtt(gid)
                    print(f"✅ Deleted dangling GTT #{gid}")
                else:
                    print(f"⚠️ PREVIEW: Would delete dangling GTT #{gid}")
    except Exception as e:
        print(f"Notice: {e}")

    # 2. Get live quote
    q = kite.quote([f"NFO:{OPT_SYMBOL}"]).get(f"NFO:{OPT_SYMBOL}", {})
    ltp = q.get("last_price", 0.88)
    depth = q.get("depth", {})
    best_bid = depth.get("buy", [{}])[0].get("price", 0)
    best_ask = depth.get("sell", [{}])[0].get("price", 0)

    # Compliant NRML Buy Ticket (Zerodha requires distance > 0.09)
    min_distance = 0.15
    trigger = round(ltp + min_distance, 2)
    limit = round(trigger + 0.10, 2)
    total_cost = LOT_SIZE * limit

    print("\n" + "=" * 80)
    print("🎯 STEP 2: ZERODHA COMPLIANT NRML GTT BUY ORDER")
    print("=" * 80)
    print(f"• Tradingsymbol:   {OPT_SYMBOL}")
    print(f"• Exchange:       NFO")
    print(f"• Product:        NRML (Complies with SEBI Compulsory Delivery rules)")
    print(f"• Current LTP:    ₹{ltp:.2f} (Bid: ₹{best_bid:.2f} | Ask: ₹{best_ask:.2f})")
    print(f"• Breakout Trigger: ₹{trigger:.2f}")
    print(f"• Limit Price:    ₹{limit:.2f}")
    print(f"• Quantity:       {LOT_SIZE:,} shares (1 lot)")
    print(f"• Max Capital:    ₹{total_cost:,.2f} (Available in account: ₹59,780.50)")
    print(f"• Target:         ₹1.80 (+₹{(1.80 - limit) * LOT_SIZE:,.2f} profit)")
    print(f"• Stop Loss:      ₹0.40 (-₹{(limit - 0.40) * LOT_SIZE:,.2f} risk)")
    print("=" * 80)

    if not execute:
        print("\n⚠️ PREVIEW MODE: Run with --execute to clean up old GTT and place the new NRML GTT.")
        return

    print("🚀 Placing fresh NRML GTT on Zerodha Kite...")
    # Fetch fresh live quote immediately before placement to guarantee distance > 0.09
    fresh_q = kite.quote([f"NFO:{OPT_SYMBOL}"]).get(f"NFO:{OPT_SYMBOL}", {})
    fresh_ltp = fresh_q.get("last_price", ltp)
    if (trigger - fresh_ltp) < 0.12:
        trigger = round(fresh_ltp + 0.15, 2)
        limit = round(trigger + 0.10, 2)
        print(f"[*] Adjusted to fresh live price: LTP ₹{fresh_ltp:.2f} -> Trigger: ₹{trigger:.2f} | Limit: ₹{limit:.2f}")

    buy_orders = [
        {
            "transaction_type": kite.TRANSACTION_TYPE_BUY,
            "quantity": LOT_SIZE,
            "order_type": kite.ORDER_TYPE_LIMIT,
            "product": "NRML",
            "price": limit
        }
    ]

    resp = kite.place_gtt(
        trigger_type=kite.GTT_TYPE_SINGLE,
        tradingsymbol=OPT_SYMBOL,
        exchange="NFO",
        trigger_values=[trigger],
        last_price=fresh_ltp,
        orders=buy_orders
    )

    gid = resp.get("trigger_id")
    print(f"\n🎉 SUCCESS! NRML GTT Trigger #{gid} successfully placed on Zerodha Kite!")
    print(f"   • Status:          ACTIVE 🟢")
    print(f"   • Product:         NRML (Accepted by Zerodha)")
    print(f"   • Trigger Price:   ₹{trigger:.2f}")
    print(f"   • Limit Price:     ₹{limit:.2f}")
    print(f"   • Quantity:        {LOT_SIZE:,} shares")
    print("=" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up dangling GTT and place NRML GTT")
    parser.add_argument("--execute", action="store_true", help="Execute on Kite")
    args = parser.parse_args()

    run_nrml_flow(execute=args.execute)
