"""
place_top3_gtt_budget44k.py
===========================
Places Zerodha Kite GTT Buy Orders for Top 3 Backtested Stocks calibrated to ₹44,000 Capital:
1. MCX (5 shares @ ₹3,915.00)       = ₹19,575.00 (Trigger: ₹3,914.50)
2. ICICIBANK (10 shares @ ₹1,602.00)= ₹16,020.00 (Trigger: ₹1,601.50)
3. ANGELONE (20 shares @ ₹378.50)   =  ₹7,570.00 (Trigger: ₹378.00)
----------------------------------------------------------------------
Total Allocated Capital             = ₹43,165.00 (Under ₹44,000 budget!)
"""

import sys
import argparse
from pathlib import Path

# UTF-8 handling for Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent

ORDERS = [
    {
        "symbol": "MCX",
        "exchange": "NSE",
        "tradingsymbol": "MCX",
        "qty": 5,
        "trigger_price": 3914.50,
        "limit_price": 3915.00,
        "target_price": 3980.00,
        "stop_price": 3845.00,
        "capital": 19575.00
    },
    {
        "symbol": "ICICIBANK",
        "exchange": "NSE",
        "tradingsymbol": "ICICIBANK",
        "qty": 10,
        "trigger_price": 1601.50,
        "limit_price": 1602.00,
        "target_price": 1630.00,
        "stop_price": 1580.00,
        "capital": 16020.00
    },
    {
        "symbol": "ANGELONE",
        "exchange": "NSE",
        "tradingsymbol": "ANGELONE",
        "qty": 20,
        "trigger_price": 378.00,
        "limit_price": 378.50,
        "target_price": 392.00,
        "stop_price": 368.00,
        "capital": 7570.00
    }
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Execute GTT orders on Zerodha")
    args = parser.parse_args()

    print("=" * 80)
    print("TOP 3 GTT BREAKOUT ORDER ALLOCATION (BUDGET: INR 44,000)")
    print("=" * 80)

    total_cap = 0.0
    for o in ORDERS:
        total_cap += o["capital"]
        print(f"📦 {o['symbol']}: BUY {o['qty']} shares @ Limit ₹{o['limit_price']:.2f}")
        print(f"   • Trigger Price : ₹{o['trigger_price']:.2f} (Trigger condition: Price >= Trigger)")
        print(f"   • Target (T1)   : ₹{o['target_price']:.2f} (+₹{o['target_price']-o['limit_price']:.1f}/sh)")
        print(f"   • Stop-Loss (SL): ₹{o['stop_price']:.2f} (-₹{o['limit_price']-o['stop_price']:.1f}/sh)")
        print(f"   • Capital Needed: ₹{o['capital']:,.2f}")
        print("-" * 50)

    print(f"TOTAL CAPITAL COMMITTED: ₹{total_cap:,.2f} | REMAINING CASH BUFFER: ₹{44000 - total_cap:,.2f}")
    print("=" * 80)

    if not args.execute:
        print("\n[PREVIEW MODE] To place these GTT orders live on Zerodha, run with --execute.")
        return

    # Initialize Kite Connect
    try:
        from kiteconnect import KiteConnect
        api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
        token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(token)
    except Exception as e:
        print(f"❌ Kite Connect initialization error: {e}")
        return

    print("\n🚀 SENDING GTT ORDERS TO ZERODHA KITE...")
    placed_orders = []

    for o in ORDERS:
        try:
            # Fetch LTP to ensure compliant trigger
            q = kite.quote([f"{o['exchange']}:{o['tradingsymbol']}"])
            ltp = q.get(f"{o['exchange']}:{o['tradingsymbol']}", {}).get("last_price", o["limit_price"])

            # Zerodha GTT single buy order
            resp = kite.place_gtt(
                trigger_type=kite.GTT_TYPE_SINGLE,
                tradingsymbol=o["tradingsymbol"],
                exchange=o["exchange"],
                trigger_values=[o["trigger_price"]],
                last_price=ltp,
                orders=[
                    {
                        "transaction_type": kite.TRANSACTION_TYPE_BUY,
                        "quantity": o["qty"],
                        "order_type": kite.ORDER_TYPE_LIMIT,
                        "product": kite.PRODUCT_CNC,
                        "price": o["limit_price"]
                    }
                ]
            )
            trigger_id = resp.get("trigger_id")
            print(f"   ✅ SUCCESS: {o['symbol']} GTT Placed! Trigger ID: {trigger_id}")
            placed_orders.append({"symbol": o["symbol"], "trigger_id": trigger_id, "status": "ACTIVE"})
        except Exception as e:
            print(f"   ❌ FAILED to place GTT for {o['symbol']}: {e}")

    # Save placed records
    if placed_orders:
        out_file = ROOT / "trader-in" / "active_top3_gtt_orders.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(placed_orders, f, indent=2)
        print(f"\nSaved placed order receipts to: {out_file}")

if __name__ == "__main__":
    main()
