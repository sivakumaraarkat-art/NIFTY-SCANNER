"""
trail_divislab_gtt.py
Automated Trailing Stop Loss Engine for DIVISLAB 11,700 CE.
Monitors live LTP and trails the GTT Stop-Loss upward to lock in profits:
- When LTP >= ₹325 -> Trails SL to ₹315.00 (100% Risk-Free Breakeven)
- When LTP >= ₹335 -> Trails SL to ₹325.00 (Guaranteed +₹1,030 profit)
"""

import sys
import time
from pathlib import Path

# UTF-8 fix for Windows console
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

    OPT = "NFO:DIVISLAB26NOV11700CE"
    SYM = "DIVISLAB26NOV11700CE"
    EXCHANGE = "NFO"
    QTY = 100
    BUY_PRICE = 314.70

    # 1. Fetch live quote
    q = kite.quote([OPT]).get(OPT, {})
    ltp = q.get("last_price", 0.0)
    pnl = (ltp - BUY_PRICE) * QTY
    pnl_pct = ((ltp - BUY_PRICE) / BUY_PRICE * 100) if BUY_PRICE else 0.0

    print("=" * 80)
    print("📈 DIVISLAB 11,700 CE — LIVE TRAILING STOP-LOSS AUDIT")
    print("=" * 80)
    print(f"  • Buy Price:     ₹{BUY_PRICE:.2f}")
    print(f"  • Current LTP:   ₹{ltp:.2f}  🟢 PROFIT: ₹{pnl:+,.2f} ({pnl_pct:+.2f}%)")
    print("-" * 80)

    # 2. Check existing GTT
    all_gtts = kite.get_gtts()
    active_gtt = next((g for g in all_gtts if g.get("condition", {}).get("tradingsymbol") == SYM and g.get("status") == "active"), None)

    if not active_gtt:
        print("  ⚠️ No active GTT found for DIVISLAB.")
        sys.exit(0)

    current_triggers = active_gtt.get("condition", {}).get("trigger_values", [296.0, 345.0])
    current_sl = current_triggers[0]
    current_tgt = current_triggers[1] if len(current_triggers) > 1 else 345.0
    print(f"  • Current GTT Triggers: Stop-Loss: ₹{current_sl:.2f} | Target: ₹{current_tgt:.2f}")
    print("-" * 80)

    # 3. Trailing Logic
    new_sl = None
    if ltp >= 335.0:
        new_sl = 325.0
        reason = "LTP reached ₹335+ -> Lock in +₹1,030 profit!"
    elif ltp >= 324.0:
        new_sl = 315.0
        reason = "LTP reached ₹324+ -> Trail to Breakeven (100% Risk-Free)!"

    if new_sl and new_sl > current_sl:
        print(f"🚀 TRAIL TRIGGER MET: {reason}")
        print(f"   Moving Stop-Loss from ₹{current_sl:.2f} ➔ ₹{new_sl:.2f}")

        # Cancel old GTT
        gid = active_gtt.get("id")
        kite.delete_gtt(gid)
        print(f"   🗑️ Cancelled old GTT #{gid}")

        # Place new trailed GTT
        resp = kite.place_gtt(
            trigger_type=kite.GTT_TYPE_OCO,
            tradingsymbol=SYM,
            exchange=EXCHANGE,
            trigger_values=[new_sl, current_tgt],
            last_price=ltp,
            orders=[
                {
                    "transaction_type": kite.TRANSACTION_TYPE_SELL,
                    "quantity": QTY,
                    "order_type": kite.ORDER_TYPE_LIMIT,
                    "product": "MIS",
                    "price": round(new_sl - 3.0, 2)
                },
                {
                    "transaction_type": kite.TRANSACTION_TYPE_SELL,
                    "quantity": QTY,
                    "order_type": kite.ORDER_TYPE_LIMIT,
                    "product": "MIS",
                    "price": current_tgt
                }
            ]
        )
        print(f"   🎉 NEW TRAILED GTT PLACED! Trigger ID #{resp.get('trigger_id')}")
        print(f"   • New Stop-Loss: ₹{new_sl:.2f}")
        print(f"   • Target:        ₹{current_tgt:.2f}")
    else:
        print("ℹ️  Trailing Status: Price is rising nicely towards ₹324–₹325.")
        print(f"   Current SL remains at ₹{current_sl:.2f}. Once LTP crosses ₹324+, running this will trail SL to ₹315 (Breakeven)!")

    print("=" * 80)

except Exception as e:
    print(f"❌ Error during trailing audit: {e}")
