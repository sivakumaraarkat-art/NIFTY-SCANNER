from kiteconnect import KiteConnect
from pathlib import Path

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

print("=" * 75)
print("🔍 AUDIT: GTT TRIGGER & ORDER STATUS")
print("=" * 75)

orders = kite.orders()
for o in orders[-6:]:
    stat = o.get("status")
    sym = o.get("tradingsymbol")
    qty = o.get("quantity")
    tt = o.get("transaction_type")
    pr = o.get("price")
    avg = o.get("average_price")
    msg = o.get("status_message")
    t = str(o.get("order_timestamp"))[11:19]
    print(f"[{stat}] {t} | {tt} {qty} {sym} @ ₹{pr} (Filled Avg: ₹{avg}) | {msg}")

print("-" * 75)
pos = kite.positions().get("net", [])
for p in pos:
    sym = p.get("tradingsymbol")
    qty = p.get("quantity")
    ltp = p.get("last_price")
    pnl = p.get("pnl")
    print(f"Position: {sym} | Net Qty: {qty} | LTP: ₹{ltp} | Net P&L: ₹{pnl}")
print("=" * 75)
