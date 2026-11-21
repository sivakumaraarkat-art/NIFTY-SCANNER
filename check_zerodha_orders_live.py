from kiteconnect import KiteConnect
from pathlib import Path
import json

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

orders = kite.orders()
trades = kite.trades()
holdings = kite.holdings()
positions = kite.positions().get("net", [])

print("=" * 75)
print(f"📋 ZERODHA LIVE ORDERBOOK AUDIT (Total Orders: {len(orders)})")
print("=" * 75)

if not orders:
    print("No orders found on Zerodha for today yet.")
else:
    for o in orders:
        oid = o.get("order_id")
        sym = o.get("tradingsymbol")
        tt = o.get("transaction_type")
        qty = o.get("quantity")
        fq = o.get("filled_quantity")
        pr = o.get("price")
        stat = o.get("status")
        otime = o.get("order_timestamp")
        msg = o.get("status_message")
        prod = o.get("product")
        var = o.get("order_type")
        print(f"• [{stat}] {tt} {qty} shs (Filled: {fq}) {sym} [{prod}/{var}] @ ₹{pr} (Time: {otime})")
        if msg:
            print(f"   Status Msg: {msg}")

print("\n" + "=" * 75)
print(f"💼 ZERODHA LIVE TRADEBOOK (Total Trades: {len(trades)})")
print("=" * 75)
if not trades:
    print("No trades executed yet today.")
else:
    for t in trades:
        tid = t.get("trade_id")
        sym = t.get("tradingsymbol")
        tt = t.get("transaction_type")
        qty = t.get("quantity")
        pr = t.get("average_price")
        ttime = t.get("trade_timestamp")
        print(f"• Trade #{tid}: {tt} {qty} shs {sym} @ ₹{pr:.2f} (Filled at: {ttime})")

cochin_pos = next((p for p in positions if p.get("tradingsymbol") == "COCHINSHIP"), None)
if cochin_pos:
    print("\n--- Day Position for COCHINSHIP ---")
    print(f"Product: {cochin_pos.get('product')} | Net Qty: {cochin_pos.get('quantity')} | Buy Qty: {cochin_pos.get('buy_quantity')} @ ₹{cochin_pos.get('buy_price'):.2f}")

cochin_hold = next((h for h in holdings if h.get("tradingsymbol") == "COCHINSHIP"), None)
if cochin_hold:
    total_q = cochin_hold.get("quantity", 0) + cochin_hold.get("t1_quantity", 0)
    print(f"\nDemat Holding: {total_q} shares @ ₹{cochin_hold.get('average_price'):.2f}")
print("=" * 75)
