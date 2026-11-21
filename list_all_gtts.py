from kiteconnect import KiteConnect
from pathlib import Path

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

gtts = kite.get_gtts()
print(f"Total Active GTTs in Zerodha: {len(gtts)}")
for g in gtts:
    cond = g.get("condition", {})
    gid = g.get("id")
    sym = cond.get("tradingsymbol")
    trigs = cond.get("trigger_values")
    gtype = g.get("type")
    stat = g.get("status")
    orders = g.get("orders", [])
    q = orders[0].get("quantity") if orders else 0
    p = orders[0].get("price") if orders else 0
    print(f"• ID #{gid}: {sym} [{gtype}] | Triggers: {trigs} | Qty: {q} @ ₹{p} | Status: {stat}")
