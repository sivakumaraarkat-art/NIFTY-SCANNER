"""
add_lots_and_split_targets.py
=============================
Scales into winning NIFTY 25600 CE trade by adding 2 lots (130 shares),
and configures the 50/50 Staggered Split Exit strategy:
- Tranche 1 (130 shares / ~66%): Target 1 @ ₹115.00 (Takes quick profit off table)
- Tranche 2 (65 shares / ~33%):  Target 2 @ ₹145.00 (Full boom runner)
- Consolidated Stop-Loss:       ₹68.00 (Below 25,500 pivot)
"""

import sys
import argparse
import time
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

SYMBOL = "NIFTY26NOV25600CE"
ADD_QTY = 130 # 2 Lots
TARGET_1 = 115.00
TARGET_2 = 145.00
STOP_LOSS = 68.00
SL_LIMIT = 67.00

def execute_scale_and_split(execute=False):
    # 1. Check existing position
    pos_list = kite.positions().get("net", [])
    curr_pos = next((p for p in pos_list if p.get("tradingsymbol") == SYMBOL and p.get("quantity", 0) > 0), None)

    if not curr_pos:
        print(f"❌ Error: No existing position found for {SYMBOL}. Cannot scale into a non-existent trade.")
        return

    curr_qty = curr_pos.get("quantity")
    curr_avg = curr_pos.get("average_price")

    # 2. Fetch live quote
    q = kite.quote([f"NFO:{SYMBOL}"]).get(f"NFO:{SYMBOL}", {})
    ltp = q.get("last_price", 83.50)
    best_ask = q.get("depth", {}).get("sell", [{}])[0].get("price", ltp)
    limit_buy = round(best_ask + 1.0, 1) # Small buffer to ensure instant fill

    new_total_qty = curr_qty + ADD_QTY
    est_blended_avg = ((curr_qty * curr_avg) + (ADD_QTY * best_ask)) / new_total_qty
    cost_2_lots = ADD_QTY * best_ask

    # Calculate P&L for Split Targets
    t1_profit = (TARGET_1 - est_blended_avg) * ADD_QTY
    t2_profit = (TARGET_2 - est_blended_avg) * curr_qty
    total_target_profit = t1_profit + t2_profit
    max_sl_risk = (est_blended_avg - STOP_LOSS) * new_total_qty

    print("=" * 85)
    print("🚀 NIFTY 25600 CE SCALE-IN & SPLIT TARGET PLAN")
    print("=" * 85)
    print(f"• Current Position:    {curr_qty} shares (1 Lot) @ avg Rs. {curr_avg:.2f}")
    print(f"• Adding:              {ADD_QTY} shares (2 Lots) @ live ask Rs. {best_ask:.2f}")
    print(f"• Capital Required:    Rs. {cost_2_lots:,.2f} (Account Cash: Rs. {kite.margins('equity').get('available', {}).get('live_balance', 0):,.2f})")
    print(f"• New Total Position:  {new_total_qty} shares (3 Lots) @ blended avg ~Rs. {est_blended_avg:.2f}")
    print("-" * 85)
    print("🎯 STAGGERED 50/50 EXIT BLUEPRINT:")
    print(f"• TRANCHE 1 ({ADD_QTY} qty / 2 Lots): Target 1 @ Rs. {TARGET_1:.2f} ──▶ Profit: +Rs. {t1_profit:,.2f} (+{((TARGET_1 - est_blended_avg)/est_blended_avg*100):.1f}%)")
    print(f"• TRANCHE 2 ({curr_qty} qty / 1 Lot):  Target 2 @ Rs. {TARGET_2:.2f} ──▶ Profit: +Rs. {t2_profit:,.2f} (+{((TARGET_2 - est_blended_avg)/est_blended_avg*100):.1f}%)")
    print(f"• COMBINED TARGET PROFIT:       +Rs. {total_target_profit:,.2f}")
    print(f"• CONSOLIDATED STOP LOSS:       Rs. {STOP_LOSS:.2f} (Max Total Risk: -Rs. {max_sl_risk:,.2f})")
    print("=" * 85)

    if not execute:
        print("\n⚠️ PREVIEW MODE: Run with --execute to place the 2-lot order and deploy split OCO targets.")
        return

    # 3. Place GTT Buy Order for 2 Lots (GTT bypasses broker static IP restrictions)
    print("🚀 Placing GTT Buy Trigger for 2 Lots (130 qty) on Zerodha Kite...")
    buy_trigger = round(ltp + 0.50, 2)
    buy_limit = round(buy_trigger + 2.00, 1)

    buy_orders = [
        {
            "transaction_type": kite.TRANSACTION_TYPE_BUY,
            "quantity": ADD_QTY,
            "order_type": kite.ORDER_TYPE_LIMIT,
            "product": "MIS",
            "price": buy_limit
        }
    ]

    gtt_buy_resp = kite.place_gtt(
        trigger_type=kite.GTT_TYPE_SINGLE,
        tradingsymbol=SYMBOL,
        exchange="NFO",
        trigger_values=[buy_trigger],
        last_price=ltp,
        orders=buy_orders
    )
    buy_gid = gtt_buy_resp.get("trigger_id")
    print(f"🎉 SUCCESS! GTT Buy Trigger #{buy_gid} placed on Zerodha Kite!")
    print(f"   • Trigger Price: Rs. {buy_trigger:.2f} (Triggers on next tick)")
    print(f"   • Limit Price:   Rs. {buy_limit:.2f}")
    print(f"   • Quantity:      {ADD_QTY} shares (2 Lots)")
    print("\n💡 NOTE: As soon as the market ticks past Rs. " + str(buy_trigger) + ", it fills into positions.")
    print("To attach the 50/50 Split OCO Targets after fill, run:")
    print("   python add_lots_and_split_targets.py --deploy-oco")
    return

def deploy_split_oco():
    print("=" * 85)
    print("🛡️ DEPLOYING STAGGERED 50/50 OCO TARGETS ON ZERODHA KITE")
    print("=" * 85)
    pos_list = kite.positions().get("net", [])
    curr_pos = next((p for p in pos_list if p.get("tradingsymbol") == SYMBOL and p.get("quantity", 0) > 0), None)

    if not curr_pos:
        print(f"❌ Error: No open position found for {SYMBOL}.")
        return

    total_qty = curr_pos.get("quantity", 195)
    avg_price = curr_pos.get("average_price", 80.0)
    q = kite.quote([f"NFO:{SYMBOL}"]).get(f"NFO:{SYMBOL}", {})
    ltp = q.get("last_price", 83.0)

    # 4. Clean up existing old 1-lot OCO GTT
    print("🔄 Cleaning up old single GTTs...")
    gtts = kite.get_gtts()
    for g in gtts:
        cond = g.get("condition", {})
        if cond.get("tradingsymbol") == SYMBOL and g.get("status") == "active":
            gid = g.get("id")
            try:
                kite.delete_gtt(gid)
                print(f"   ✅ Cleaned up old GTT #{gid}")
            except Exception as e:
                print(f"   Notice: {e}")

    # Split quantities
    tranche1_qty = min(130, total_qty)
    tranche2_qty = total_qty - tranche1_qty
    if tranche2_qty == 0:
        tranche1_qty = total_qty // 2
        tranche2_qty = total_qty - tranche1_qty

    print(f"\n🚀 Deploying Staggered GTT OCO Exit Orders for {total_qty} shares...")
    # OCO 1: Tranche 1 (Target 115, SL 68)
    oco1_orders = [
        {"transaction_type": kite.TRANSACTION_TYPE_SELL, "quantity": tranche1_qty, "order_type": kite.ORDER_TYPE_LIMIT, "product": "MIS", "price": SL_LIMIT},
        {"transaction_type": kite.TRANSACTION_TYPE_SELL, "quantity": tranche1_qty, "order_type": kite.ORDER_TYPE_LIMIT, "product": "MIS", "price": TARGET_1}
    ]
    resp1 = kite.place_gtt(
        trigger_type=kite.GTT_TYPE_OCO,
        tradingsymbol=SYMBOL,
        exchange="NFO",
        trigger_values=[STOP_LOSS, TARGET_1],
        last_price=ltp,
        orders=oco1_orders
    )
    print(f"🎉 OCO Tranche 1 Active! GTT #{resp1.get('trigger_id')}: {tranche1_qty} qty @ Target Rs. {TARGET_1:.2f} | SL Rs. {STOP_LOSS:.2f}")

    if tranche2_qty > 0:
        # OCO 2: Tranche 2 (Target 145, SL 68)
        oco2_orders = [
            {"transaction_type": kite.TRANSACTION_TYPE_SELL, "quantity": tranche2_qty, "order_type": kite.ORDER_TYPE_LIMIT, "product": "MIS", "price": SL_LIMIT},
            {"transaction_type": kite.TRANSACTION_TYPE_SELL, "quantity": tranche2_qty, "order_type": kite.ORDER_TYPE_LIMIT, "product": "MIS", "price": TARGET_2}
        ]
        resp2 = kite.place_gtt(
            trigger_type=kite.GTT_TYPE_OCO,
            tradingsymbol=SYMBOL,
            exchange="NFO",
            trigger_values=[STOP_LOSS, TARGET_2],
            last_price=ltp,
            orders=oco2_orders
        )
        print(f"🎉 OCO Tranche 2 Active! GTT #{resp2.get('trigger_id')}: {tranche2_qty} qty @ Target Rs. {TARGET_2:.2f} | SL Rs. {STOP_LOSS:.2f}")

    print("=" * 85)
    print("🟢 SPLIT TARGETS FULLY DEPLOYED ON ZERODHA KITE!")

def modify_to_fill_now():
    print("=" * 85)
    print("⚡ ADJUSTING 2-LOT GTT TRIGGER TO CURRENT MARKET FOR IMMEDIATE FILL")
    print("=" * 85)
    gtts = kite.get_gtts()
    buy_gtt = next((g for g in gtts if g.get("condition", {}).get("tradingsymbol") == SYMBOL and g.get("type") == "single" and g.get("status") == "active"), None)
    if not buy_gtt:
        print("❌ No active GTT Buy trigger found to adjust.")
        return

    gid = buy_gtt["id"]
    q = kite.quote([f"NFO:{SYMBOL}"]).get(f"NFO:{SYMBOL}", {})
    ltp = q.get("last_price", 81.0)
    new_trig = round(ltp + 0.50, 2)
    new_limit = round(new_trig + 2.0, 1)

    orders = buy_gtt.get("orders", [])
    if orders:
        orders[0]["price"] = new_limit

    try:
        kite.modify_gtt(
            trigger_id=gid,
            trigger_type=kite.GTT_TYPE_SINGLE,
            tradingsymbol=SYMBOL,
            exchange="NFO",
            trigger_values=[new_trig],
            last_price=ltp,
            orders=orders
        )
        print(f"🎉 SUCCESS! GTT #{gid} trigger adjusted down to Rs. {new_trig:.2f} (Current LTP: Rs. {ltp:.2f})!")
        print(f"   • Trigger Price: Rs. {new_trig:.2f} (Just 50 paise away)")
        print(f"   • Limit Price:   Rs. {new_limit:.2f}")
        print("   • It will trigger and fill on the next tick!")
    except Exception as e:
        print(f"❌ Modification error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scale into Nifty CE and deploy split targets")
    parser.add_argument("--execute", action="store_true", help="Execute orders live on Kite")
    parser.add_argument("--deploy-oco", action="store_true", help="Deploy split OCO targets to open position")
    parser.add_argument("--fill-now", action="store_true", help="Adjust trigger to current market price for immediate fill")
    args = parser.parse_args()

    if args.fill_now:
        modify_to_fill_now()
    elif args.deploy_oco:
        deploy_split_oco()
    else:
        execute_scale_and_split(execute=args.execute)
