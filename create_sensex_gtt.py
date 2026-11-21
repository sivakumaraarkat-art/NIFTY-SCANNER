"""
create_sensex_gtt.py
====================
Places an automated GTT order on Zerodha Kite for BSE SENSEX Hero-Zero Options.
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

def place_sensex_gtt(symbol="SENSEX26N1983400CE", trigger=None, limit=None, lots=4, execute=False):
    exchange = "BFO"
    lot_size = 20
    qty = lots * lot_size
    product = "MIS"

    q = kite.quote([f"BFO:{symbol}"]).get(f"BFO:{symbol}", {})
    ltp = q.get("last_price", 8.85)
    depth = q.get("depth", {})
    best_bid = depth.get("buy", [{}])[0].get("price", 0)
    best_ask = depth.get("sell", [{}])[0].get("price", 0)

    # Zerodha rule: trigger must be at least 0.5% / 0.15 away from last_price
    min_buffer = 0.50
    if trigger is None or (trigger - ltp) < 0.20:
        new_trigger = round(ltp + min_buffer, 1)
        trigger = new_trigger

    if limit is None or limit <= trigger:
        limit = round(trigger + 0.40, 1)

    total_capital = qty * limit

    print("=" * 80)
    print("🎯 ZERODHA SENSEX HERO-ZERO GTT ORDER TICKET")
    print("=" * 80)
    print(f"• Tradingsymbol:   {symbol} (Expiring TODAY: 19-Nov-2026)")
    print(f"• Exchange:       {exchange}")
    print(f"• Product:        {product}")
    print(f"• Current LTP:    ₹{ltp:.2f} (Bid: ₹{best_bid:.2f} | Ask: ₹{best_ask:.2f})")
    print(f"• Trigger Price:  ₹{trigger:.2f} (Breakout trigger)")
    print(f"• Limit Price:    ₹{limit:.2f}")
    print(f"• Quantity:       {qty} shares ({lots} lots)")
    print(f"• Total Capital:  ₹{total_capital:,.2f} max")
    print("-" * 80)
    print(f"• Target 1 (2x):  ₹{limit * 2:.2f} (Profit: +₹{total_capital:,.2f})")
    print(f"• Target 2 (4x):  ₹{limit * 4:.2f} (Profit: +₹{total_capital * 3:,.2f})")
    print(f"• Stop Loss:      ₹{max(1.0, trigger * 0.5):.2f} (Max Risk: ~₹{total_capital * 0.5:,.2f})")
    print("=" * 80)

    if not execute:
        print("\n⚠️ PREVIEW MODE: Order has NOT been sent to Zerodha yet.")
        print("To place this GTT order live on Kite, run:")
        print(f"   python create_sensex_gtt.py --execute --symbol {symbol} --trigger {trigger} --limit {limit} --lots {lots}")
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

    try:
        resp = kite.place_gtt(
            trigger_type=kite.GTT_TYPE_SINGLE,
            tradingsymbol=symbol,
            exchange=exchange,
            trigger_values=[trigger],
            last_price=ltp,
            orders=buy_orders
        )

        gid = resp.get("trigger_id")
        print(f"\n🎉 SUCCESS! GTT Trigger #{gid} successfully placed on Zerodha Kite!")
        print(f"   • Status:        ACTIVE 🟢")
        print(f"   • Trigger Price: ₹{trigger:.2f}")
        print(f"   • Limit Price:   ₹{limit:.2f}")
        print(f"   • Quantity:      {qty} shares ({lots} lots)")
        print(f"   • Total Risk:    Only ₹{total_capital:,.2f}")
        print("=" * 80)
    except Exception as e:
        print(f"❌ Zerodha GTT Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Place SENSEX Hero-Zero GTT on Zerodha")
    parser.add_argument("--execute", action="store_true", help="Execute the live order on Kite")
    parser.add_argument("--symbol", type=str, default="SENSEX26N1983400CE", help="SENSEX Option Symbol")
    parser.add_argument("--trigger", type=float, default=None, help="GTT trigger price")
    parser.add_argument("--limit", type=float, default=None, help="GTT limit price")
    parser.add_argument("--lots", type=int, default=4, help="Number of lots (20 qty each)")
    args = parser.parse_args()

    place_sensex_gtt(symbol=args.symbol, trigger=args.trigger, limit=args.limit, lots=args.lots, execute=args.execute)
