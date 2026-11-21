from kiteconnect import KiteConnect
from pathlib import Path
import json

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

pos = kite.positions()
net = pos.get("net", [])
day = pos.get("day", [])

print("=" * 75)
print("🔍 LIVE OPEN & DAY POSITIONS AUDIT")
print("=" * 75)
for p in net:
    sym = p.get("tradingsymbol")
    prod = p.get("product")
    qty = p.get("quantity")
    b_qty = p.get("buy_quantity")
    b_pr = p.get("buy_price")
    s_qty = p.get("sell_quantity")
    s_pr = p.get("sell_price")
    ltp = p.get("last_price")
    pnl = p.get("pnl")
    m2m = p.get("m2m")
    val = abs(qty) * ltp if ltp else 0
    print(f"• {sym} [{prod}]")
    print(f"   Net Qty: {qty} | Buy: {b_qty} @ ₹{b_pr:.2f} | Sell: {s_qty} @ ₹{s_pr:.2f}")
    print(f"   LTP: ₹{ltp:.2f} | P&L: ₹{pnl:+,.2f} | M2M: ₹{m2m:+,.2f}")
    print("-" * 75)

orders = kite.orders()
print(f"\nTotal Orders Today: {len(orders)}")
for o in orders[-6:]:
    stat = o.get("status")
    tt = o.get("transaction_type")
    qty = o.get("quantity")
    sym = o.get("tradingsymbol")
    prod = o.get("product")
    ot = o.get("order_type")
    pr = o.get("price")
    tm = o.get("order_timestamp")
    print(f"  [{stat}] {tt} {qty} {sym} [{prod}/{ot}] @ ₹{pr} ({tm})")
