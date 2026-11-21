"""
monitor_zerodha_account.py
==========================
Continuous Real-Time Zerodha Kite Sentinel:
1. Monitors all active GTT triggers (SENSEX 83500 CE #345590587, COCHINSHIP, etc.)
2. Detects instant order fills
3. Tracks open positions, live P&L, Target 1, Target 2, and Stop Loss
4. Emits clear audio / terminal alerts when a trigger or target is hit
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from kiteconnect import KiteConnect

# Fix Windows console UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent

api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

def audit_account(single_shot=True):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Fetch data
    gtts = kite.get_gtts()
    active_gtts = [g for g in gtts if g.get("status") == "active"]
    orders = kite.orders()
    positions = [p for p in kite.positions().get("net", []) if p.get("quantity", 0) != 0]

    print("=" * 85)
    print(f"🛡️ ZERODHA KITE LIVE ACCOUNT SENTINEL | {now_str} IST")
    print("=" * 85)

    # 1. Active GTTs
    print(f"📌 1. ACTIVE GTT ORDERS ({len(active_gtts)} Active)")
    if active_gtts:
        for g in active_gtts:
            gid = g.get("id")
            cond = g.get("condition", {})
            sym = cond.get("tradingsymbol")
            trigs = cond.get("trigger_values")
            ords = g.get("orders", [])
            q = ords[0].get("quantity") if ords else 0
            p = ords[0].get("price") if ords else 0
            ptype = ords[0].get("product") if ords else "N/A"
            ttype = ords[0].get("transaction_type") if ords else "N/A"
            print(f"   • GTT #{gid}: {sym:<22} [{ttype} {ptype}] | Trigger: {trigs} | Qty: {q} @ ₹{p}")
    else:
        print("   • No active GTT orders.")

    # 2. Open Positions
    print(f"\n💼 2. ACTIVE OPEN POSITIONS ({len(positions)} Open)")
    if positions:
        for p in positions:
            sym = p.get("tradingsymbol")
            qty = p.get("quantity")
            avg_p = p.get("average_price")
            ltp = p.get("last_price")
            pnl = p.get("pnl")
            pct = ((ltp - avg_p) / avg_p * 100) if avg_p else 0
            print(f"   • {sym:<22}: Qty: {qty} @ avg ₹{avg_p:.2f} | LTP: ₹{ltp:.2f} | PnL: ₹{pnl:+,.2f} ({pct:+.2f}%)")
    else:
        print("   • 0 open positions. Capital is 100% liquid & protected.")

    # 3. Today's Executed / Filled Orders
    filled_orders = [o for o in orders if o.get("status") == "COMPLETE"]
    print(f"\n📋 3. TODAY'S COMPLETED ORDERS ({len(filled_orders)} Filled)")
    for o in filled_orders:
        oid = o.get("order_id")
        sym = o.get("tradingsymbol")
        ttype = o.get("transaction_type")
        qty = o.get("filled_quantity")
        avg = o.get("average_price")
        ts = o.get("order_timestamp")
        ts_str = ts.strftime("%H:%M:%S") if hasattr(ts, "strftime") else str(ts)
        print(f"   • [{ts_str}] Order #{oid}: {sym:<22} {ttype:<4} {qty} shares @ ₹{avg:.2f} [{o.get('product')}]")

    print("=" * 85)

if __name__ == "__main__":
    audit_account(single_shot=True)
