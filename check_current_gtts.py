"""
check_current_gtts.py
Inspects active GTT orders and current positions on Zerodha Kite.
"""

import sys
from pathlib import Path
from kiteconnect import KiteConnect

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent

try:
    api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
    token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(token)

    print("=" * 80)
    print("ZERODHA KITE GTT AUDIT")
    print("=" * 80)

    gtts = kite.get_gtts()
    print(f"Total GTT Orders Found: {len(gtts)}")
    for g in gtts:
        cond = g.get("condition", {})
        sym = cond.get("tradingsymbol")
        status = g.get("status")
        triggers = cond.get("trigger_values")
        orders = g.get("orders", [])
        g_id = g.get("id")
        created_at = g.get("created_at")
        print(f"\n[GTT #{g_id}] {sym} | Status: {status} | Created: {created_at}")
        print(f"   Triggers: {triggers}")
        for ord_info in orders:
            print(f"   Order: {ord_info.get('transaction_type')} {ord_info.get('quantity')} qty @ Price: {ord_info.get('price')} (Type: {ord_info.get('order_type')}, Product: {ord_info.get('product')})")

    print("\n" + "=" * 80)
    print("ACTIVE DERIVATIVE POSITIONS")
    print("=" * 80)
    pos = kite.positions().get("net", [])
    active_pos = [p for p in pos if p.get("quantity", 0) != 0]
    print(f"Total Open Derivative Positions: {len(active_pos)}")
    for p in active_pos:
        print(f"   {p.get('tradingsymbol')}: Qty={p.get('quantity')}, AvgPrice={p.get('average_price')}, MTM P&L={p.get('m2m')}")

except Exception as e:
    print(f"Error: {e}")
