"""
place_universal_gtt_oco.py
==========================
Universal Zerodha GTT OCO (One-Cancels-Other) Exit Engine.
Attaches Target (Leg 1) and Stop-Loss (Leg 2) to any active position:
- Supports NFO Options (NIFTY / Stock Options)
- Supports BFO Options (SENSEX)
- Supports NSE Equity Cash (MIS / CNC)
Whichever leg hits first on Zerodha's central exchange server automatically executes and cancels the other!
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

def deploy_gtt_oco(symbol, exchange="NFO", product="MIS", qty=None, target=None, sl=None, sl_limit=None, execute=False):
    full_sym = f"{exchange}:{symbol}"
    q = kite.quote([full_sym]).get(full_sym, {})
    ltp = q.get("last_price", 0.0)

    # 1. Inspect positions to auto-detect quantity if not provided
    if qty is None:
        pos_list = kite.positions().get("net", [])
        active_pos = next((p for p in pos_list if p.get("tradingsymbol") == symbol and p.get("quantity", 0) > 0), None)
        if active_pos:
            qty = active_pos.get("quantity")
            product = active_pos.get("product", product)
            avg_p = active_pos.get("average_price", ltp)
        else:
            qty = 1
            avg_p = ltp
    else:
        avg_p = ltp

    # 2. Defaults for Target (2x / +100%) and SL (50% risk cap) if omitted
    if target is None:
        target = round(ltp * 2.0, 1) if ltp <= 50 else round(ltp * 1.05, 1)
    if sl is None:
        sl = round(ltp * 0.50, 1) if ltp <= 50 else round(ltp * 0.98, 1)
    if sl_limit is None:
        sl_limit = round(max(0.5, sl - (0.10 if sl < 10 else 0.50)), 1)

    print("=" * 85)
    print("🎯 ZERODHA UNIVERSAL GTT OCO (TARGET + STOP-LOSS) TICKET")
    print("=" * 85)
    print(f"• Tradingsymbol:      {symbol}")
    print(f"• Exchange:           {exchange} | Product: {product}")
    print(f"• Position Quantity:  {qty:,} shares (Entry/Ref: ₹{avg_p:.2f} | Live LTP: ₹{ltp:.2f})")
    print("-" * 85)
    print(f"• LEG 1 — TARGET:     Trigger: ₹{target:.2f} | Limit: ₹{target:.2f}")
    print(f"                      Expected Profit: +₹{(target - avg_p) * qty:,.2f} ({((target - avg_p)/avg_p*100):+.1f}%)")
    print(f"• LEG 2 — STOP-LOSS:  Trigger: ₹{sl:.2f} | Limit: ₹{sl_limit:.2f}")
    print(f"                      Maximum Risk:    ₹{(sl - avg_p) * qty:,.2f} ({((sl - avg_p)/avg_p*100):+.1f}%)")
    print("=" * 85)

    if not execute:
        print("\n⚠️ PREVIEW MODE: Order has NOT been sent to Zerodha yet.")
        print("To deploy this live on Kite, run with --execute:")
        print(f"   python place_universal_gtt_oco.py --execute --symbol {symbol} --exchange {exchange} --product {product} --qty {qty} --target {target} --sl {sl}")
        return

    # Clean up previous GTT on this symbol to prevent stacking
    print(f"🔄 Checking for previous GTT orders on {symbol}...")
    try:
        existing_gtts = kite.get_gtts()
        for g in existing_gtts:
            cond = g.get("condition", {})
            if cond.get("tradingsymbol") == symbol and g.get("status") in ["active", "triggered"]:
                gid = g.get("id")
                kite.delete_gtt(gid)
                print(f"   ✅ Cleaned up old GTT #{gid}.")
    except Exception as e:
        print(f"   Notice during cleanup: {e}")

    # Deploy GTT OCO
    print("🚀 Transmitting fresh GTT OCO to Zerodha Kite...")
    trigger_values = [sl, target] # Must be ascending
    sell_orders = [
        {
            "transaction_type": kite.TRANSACTION_TYPE_SELL,
            "quantity": qty,
            "order_type": kite.ORDER_TYPE_LIMIT,
            "product": product,
            "price": sl_limit
        },
        {
            "transaction_type": kite.TRANSACTION_TYPE_SELL,
            "quantity": qty,
            "order_type": kite.ORDER_TYPE_LIMIT,
            "product": product,
            "price": target
        }
    ]

    resp = kite.place_gtt(
        trigger_type=kite.GTT_TYPE_OCO,
        tradingsymbol=symbol,
        exchange=exchange,
        trigger_values=trigger_values,
        last_price=ltp,
        orders=sell_orders
    )

    gtt_id = resp.get("trigger_id")
    print(f"\n🎉 SUCCESS! GTT OCO #{gtt_id} successfully deployed on Zerodha Kite!")
    print(f"   • Status:    ACTIVE 🟢 (Two-Leg OCO)")
    print(f"   • Target:    Trigger ₹{target:.2f} (Limit: ₹{target:.2f})")
    print(f"   • Stop-Loss: Trigger ₹{sl:.2f} (Limit: ₹{sl_limit:.2f})")
    print(f"   • Rule:      Whichever leg triggers first automatically cancels the other!")
    print("=" * 85)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Universal Zerodha GTT OCO Deployer")
    parser.add_argument("--execute", action="store_true", help="Execute live on Kite")
    parser.add_argument("--symbol", type=str, required=True, help="Trading symbol (e.g. GAIL26NOV190CE, NIFTY26NOV26000CE)")
    parser.add_argument("--exchange", type=str, default="NFO", choices=["NFO", "BFO", "NSE"], help="Exchange (NFO/BFO/NSE)")
    parser.add_argument("--product", type=str, default="MIS", choices=["MIS", "NRML", "CNC"], help="Product type")
    parser.add_argument("--qty", type=int, default=None, help="Quantity (auto-detected if omitted)")
    parser.add_argument("--target", type=float, default=None, help="Target trigger price")
    parser.add_argument("--sl", type=float, default=None, help="Stop loss trigger price")
    parser.add_argument("--sl-limit", type=float, default=None, help="Stop loss limit price")
    args = parser.parse_args()

    deploy_gtt_oco(
        symbol=args.symbol,
        exchange=args.exchange,
        product=args.product,
        qty=args.qty,
        target=args.target,
        sl=args.sl,
        sl_limit=args.sl_limit,
        execute=args.execute
    )
