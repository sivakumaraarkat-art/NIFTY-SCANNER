"""
check_nifty_position_only.py
Fetches live quote, P&L, and GTT status for the active NIFTY position.
"""

import sys
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

    # 1. Fetch Positions
    positions = kite.positions().get("net", [])
    nifty_positions = [
        p for p in positions
        if "NIFTY" in p.get("tradingsymbol", "") and p.get("quantity", 0) != 0
    ]

    print("=" * 75)
    print("🎯 LIVE NIFTY DERIVATIVE POSITION AUDIT")
    print("=" * 75)

    if not nifty_positions:
        print("  ⚠️ No active open NIFTY positions found in Net Positions.")
        # Check day positions just in case it was closed today
        day_pos = [p for p in kite.positions().get("day", []) if "NIFTY" in p.get("tradingsymbol", "")]
        for p in day_pos:
            print(f"  • Day Trade: {p.get('tradingsymbol')} | Net Qty: {p.get('quantity')} | Realized P&L: ₹{p.get('pnl'):,.2f}")
    else:
        for p in nifty_positions:
            sym = p.get("tradingsymbol")
            qty = p.get("quantity")
            avg = p.get("average_price")
            ltp = p.get("last_price")
            pnl = p.get("pnl")
            m2m = p.get("m2m")
            inv = qty * avg if qty > 0 else 0
            cur = qty * ltp if qty > 0 else 0
            pnl_pct = (pnl / inv * 100) if inv > 0 else 0.0

            print(f"  • Instrument:       {sym} ({p.get('exchange')}:{p.get('product')})")
            print(f"  • Contract Expiry:  TODAY (Monday, Nov 9, 2026)")
            print(f"  • Open Quantity:    {qty} shares (1 Lot)")
            print(f"  • Buy Average:      ₹{avg:.2f}")
            print(f"  • Live LTP:         ₹{ltp:.2f}")
            print(f"  • Capital Invested: ₹{inv:,.2f}")
            print(f"  • Current Value:    ₹{cur:,.2f}")
            status_emoji = "🟢 PROFIT" if pnl >= 0 else "🔴 LOSS"
            print(f"  • Live P&L:         {status_emoji}: ₹{pnl:+,.2f} ({pnl_pct:+.2f}%)")
            print(f"  • Day M2M:          ₹{m2m:+,.2f}")

    # 2. Fetch GTT Orders for NIFTY
    print("-" * 75)
    print("🛡️ ASSOCIATED NIFTY GTT ORDERS:")
    print("-" * 75)
    all_gtts = kite.get_gtts()
    nifty_gtts = [
        g for g in all_gtts
        if "NIFTY" in g.get("condition", {}).get("tradingsymbol", "")
    ]

    if not nifty_gtts:
        print("  ⚠️ No active GTT orders found for NIFTY.")
    else:
        for g in nifty_gtts:
            cond = g.get("condition", {})
            sym = cond.get("tradingsymbol")
            status = g.get("status")
            triggers = cond.get("trigger_values", [])
            g_id = g.get("id")
            orders = g.get("orders", [])

            print(f"  • GTT ID #{g_id} | Status: {status.upper()}")
            print(f"    - Symbol:       {sym}")
            print(f"    - Triggers:     Stop-Loss @ ₹{triggers[0] if len(triggers)>0 else 'N/A'} | Target @ ₹{triggers[1] if len(triggers)>1 else 'N/A'}")
            for ord_info in orders:
                print(f"    - Order Leg:    {ord_info.get('transaction_type')} {ord_info.get('quantity')} Qty @ Limit ₹{ord_info.get('price')}")

    print("=" * 75)

except Exception as e:
    print(f"❌ Error fetching Nifty position: {e}")
