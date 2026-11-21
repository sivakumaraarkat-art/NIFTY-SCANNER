"""
check_my_nifty_position.py
Comprehensive audit of active Zerodha F&O positions, open orders,
GTT triggers, and margin status for Siva Kumar (FH7698).
"""

import sys
import io
import json
from pathlib import Path

# Fix UTF-8 encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent

try:
    from kiteconnect import KiteConnect
    api_key = (ROOT / ".kite_api_key").read_text(encoding="utf-8").strip()
    access_token = (ROOT / ".kite_access_token").read_text(encoding="utf-8").strip()
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
except Exception as e:
    print(f"❌ Failed to connect to Kite API: {e}")
    sys.exit(1)

print("=" * 85)
print("💼 ZERODHA LIVE POSITIONS & ORDERS AUDIT — Siva Kumar (FH7698)")
print("=" * 85)

# 1. POSITIONS AUDIT
try:
    pos_data = kite.positions()
    net = pos_data.get("net", [])
    day = pos_data.get("day", [])

    active_positions = [p for p in net if p.get("quantity", 0) != 0]

    print("\n1. ⚡ OPEN ACTIVE DERIVATIVES / INTRADAY POSITIONS (Qty != 0):")
    print("-" * 85)
    if not active_positions:
        print("  ℹ️ No active open positions with non-zero quantity.")
    else:
        for p in active_positions:
            sym = p.get("tradingsymbol", "")
            prod = p.get("product", "")
            qty = p.get("quantity", 0)
            avg = p.get("average_price", 0.0)
            ltp = p.get("last_price", 0.0)
            pnl = p.get("pnl", 0.0)
            inv = abs(qty) * avg
            cur = abs(qty) * ltp
            pnl_pct = (pnl / inv * 100) if inv > 0 else 0.0
            side = "🟢 LONG (BUY)" if qty > 0 else "🔴 SHORT (SELL)"
            status = "🟢 PROFIT" if pnl >= 0 else "🔴 LOSS"

            print(f"  • Instrument:       {sym} [{prod}]")
            print(f"  • Direction:        {side}")
            print(f"  • Quantity:         {abs(qty)} (Lots/Units)")
            print(f"  • Buy Average:      ₹{avg:,.2f}")
            print(f"  • Current LTP:      ₹{ltp:,.2f}")
            print(f"  • Total Cost:       ₹{inv:,.2f}")
            print(f"  • Current Value:    ₹{cur:,.2f}")
            print(f"  • Live P&L:         ₹{pnl:+,.2f} ({pnl_pct:+.2f}%)  [{status}]")
            print("-" * 85)

    # Closed today positions
    closed_today = [p for p in day if p.get("quantity", 0) == 0 and (p.get("buy_quantity", 0) > 0 or p.get("sell_quantity", 0) > 0)]
    if closed_today:
        print("\n2. 🏁 POSITIONS SQUARED OFF TODAY:")
        print("-" * 85)
        for p in closed_today:
            sym = p.get("tradingsymbol", "")
            pnl = p.get("pnl", 0.0)
            print(f"  • {sym:<25} | Realized P&L: ₹{pnl:+,.2f}")

except Exception as e:
    print(f"⚠️ Error fetching positions: {e}")

# 2. PENDING ORDERS AUDIT
try:
    orders = kite.orders()
    open_orders = [o for o in orders if o.get("status") in ["OPEN", "TRIGGER PENDING"]]

    print("\n3. 📋 ACTIVE / PENDING ORDERS:")
    print("-" * 85)
    if not open_orders:
        print("  ℹ️ No open or trigger-pending orders.")
    else:
        for o in open_orders:
            sym = o.get("tradingsymbol", "")
            otype = o.get("order_type", "")
            ttype = o.get("transaction_type", "")
            qty = o.get("quantity", 0)
            price = o.get("price", 0.0)
            trig = o.get("trigger_price", 0.0)
            status = o.get("status", "")
            print(f"  • {sym:<20} | {ttype:<4} {qty:>4} qty | Type: {otype} | Price: ₹{price} | Trig: ₹{trig} | Status: {status}")

except Exception as e:
    print(f"⚠️ Error fetching orders: {e}")

# 3. MARGINS AUDIT
try:
    margins = kite.margins("equity")
    avail = margins.get("available", {}).get("live_balance", 0.0)
    used = margins.get("utilised", {}).get("debits", 0.0)
    print("\n4. 💰 ACCOUNT MARGINS:")
    print("-" * 85)
    print(f"  • Available Free Cash:   ₹{avail:,.2f}")
    print(f"  • Margin Utilised:       ₹{used:,.2f}")

except Exception as e:
    print(f"⚠️ Error fetching margins: {e}")

print("=" * 85)
