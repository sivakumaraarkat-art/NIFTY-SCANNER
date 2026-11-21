"""
create_gail_gtt_oco.py
======================
Deploys an automated GTT OCO (One-Cancels-Other) Exit Order on Zerodha Kite
for the filled GAIL 190 CE (NFO:GAIL26NOV190CE) position:
- Target Leg (T2): Trigger ₹5.50 | Limit ₹5.50 (Profit: +₹9,549.50 / +96%)
- Stop-Loss Leg:   Trigger ₹1.80 | Limit ₹1.70 (Risk: -₹3,585.50)
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

OPT_SYMBOL = "GAIL26NOV190CE"
FULL_SYMBOL = f"NFO:{OPT_SYMBOL}"
EXCHANGE = "NFO"
PRODUCT = "MIS"

def deploy_gail_oco(target=5.50, sl=1.80, sl_limit=1.70, execute=False):
    # 1. Fetch live position
    pos_list = kite.positions().get("net", [])
    gail_pos = next((p for p in pos_list if p.get("tradingsymbol") == OPT_SYMBOL and p.get("quantity", 0) > 0), None)

    qty = gail_pos.get("quantity", 3550) if gail_pos else 3550
    avg_price = gail_pos.get("average_price", 2.81) if gail_pos else 2.81

    # 2. Fetch live LTP
    q = kite.quote([FULL_SYMBOL]).get(FULL_SYMBOL, {})
    opt_ltp = q.get("last_price", 2.70)

    # Calculate P&L metrics
    t_profit = (target - avg_price) * qty
    t_pct = ((target - avg_price) / avg_price) * 100
    sl_loss = (sl - avg_price) * qty
    sl_pct = ((sl - avg_price) / avg_price) * 100

    print("=" * 85)
    print("🎯 ZERODHA GTT OCO (ONE-CANCELS-OTHER) EXIT TICKET: GAIL 190 CE")
    print("=" * 85)
    print(f"• Tradingsymbol:      {OPT_SYMBOL}")
    print(f"• Product:            {PRODUCT}")
    print(f"• Filled Position:    {qty:,} shares @ avg ₹{avg_price:.2f}")
    print(f"• Current Option LTP: ₹{opt_ltp:.2f}")
    print("-" * 85)
    print(f"• TARGET LEG (T2):    Trigger: ₹{target:.2f} | Limit: ₹{target:.2f}")
    print(f"                      Expected Profit: +₹{t_profit:,.2f} ({t_pct:+.1f}%)")
    print(f"• STOP-LOSS LEG:      Trigger: ₹{sl:.2f} | Limit: ₹{sl_limit:.2f}")
    print(f"                      Max Risk:        {sl_loss:,.2f} INR ({sl_pct:+.1f}%)")
    print("=" * 85)

    if not execute:
        print("\n⚠️ PREVIEW MODE: Order has NOT been sent to Zerodha yet.")
        print("To deploy this GTT OCO live on Kite, run:")
        print(f"   python create_gail_gtt_oco.py --execute --target {target} --sl {sl}")
        return

    # 3. Clean up any previous GTT on this symbol to prevent duplicates
    print("🔄 Checking for existing GTTs to clean up...")
    try:
        existing_gtts = kite.get_gtts()
        for g in existing_gtts:
            cond = g.get("condition", {})
            if cond.get("tradingsymbol") == OPT_SYMBOL and g.get("status") in ["active", "triggered"]:
                gid = g.get("id")
                print(f"   Removing previous GTT #{gid}...")
                kite.delete_gtt(gid)
                print(f"   ✅ Cleaned up GTT #{gid}.")
    except Exception as e:
        print(f"   Notice during GTT cleanup: {e}")

    # 4. Place fresh GTT OCO
    print("🚀 Placing fresh GTT OCO on Zerodha Kite...")
    # Kite OCO rule: trigger_values must be [sl_trigger, target_trigger] in ascending order
    trigger_values = [sl, target]

    sell_orders = [
        {
            "transaction_type": kite.TRANSACTION_TYPE_SELL,
            "quantity": qty,
            "order_type": kite.ORDER_TYPE_LIMIT,
            "product": PRODUCT,
            "price": sl_limit
        },
        {
            "transaction_type": kite.TRANSACTION_TYPE_SELL,
            "quantity": qty,
            "order_type": kite.ORDER_TYPE_LIMIT,
            "product": PRODUCT,
            "price": target
        }
    ]

    resp = kite.place_gtt(
        trigger_type=kite.GTT_TYPE_OCO,
        tradingsymbol=OPT_SYMBOL,
        exchange=EXCHANGE,
        trigger_values=trigger_values,
        last_price=opt_ltp,
        orders=sell_orders
    )

    gtt_id = resp.get("trigger_id")
    print(f"\n🎉 SUCCESS! GTT OCO Order #{gtt_id} successfully deployed on Zerodha Kite!")
    print(f"   • Status:          ACTIVE 🟢")
    print(f"   • Target (T2):     Trigger ₹{target:.2f} (Profit: +₹{t_profit:,.2f})")
    print(f"   • Stop-Loss:       Trigger ₹{sl:.2f} (Risk: {sl_loss:,.2f} INR)")
    print(f"   • Mechanism:       Whichever leg hits first automatically cancels the other!")
    print("=" * 85)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy GTT OCO for GAIL 190 CE")
    parser.add_argument("--execute", action="store_true", help="Execute the live OCO order on Kite")
    parser.add_argument("--target", type=float, default=5.50, help="Target trigger and limit price (default: 5.50)")
    parser.add_argument("--sl", type=float, default=1.80, help="Stop loss trigger price (default: 1.80)")
    parser.add_argument("--sl-limit", type=float, default=1.70, help="Stop loss limit price (default: 1.70)")
    args = parser.parse_args()

    deploy_gail_oco(target=args.target, sl=args.sl, sl_limit=args.sl_limit, execute=args.execute)
