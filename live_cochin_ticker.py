from kiteconnect import KiteConnect
from pathlib import Path
import datetime

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

now = datetime.datetime.now()
q = kite.quote(["NSE:COCHINSHIP"]).get("NSE:COCHINSHIP", {})

print("=== LIVE COCHIN SHIPYARD AUDIT ===")
print("Time:", now.strftime("%Y-%m-%d %H:%M:%S"))

ltp = q.get("last_price", 0.0)
ohlc = q.get("ohlc", {})
prev_c = ohlc.get("close", ltp)
open_p = ohlc.get("open", ltp)
high_p = ohlc.get("high", ltp)
low_p = ohlc.get("low", ltp)
vol = q.get("volume", 0)
chg = ltp - prev_c
chg_pct = (chg / prev_c * 100) if prev_c else 0

print(f"LTP:        ₹{ltp:.2f} ({chg:+.2f} | {chg_pct:+.2f}%)")
print(f"Today Open: ₹{open_p:.2f}")
print(f"Today High: ₹{high_p:.2f}")
print(f"Today Low:  ₹{low_p:.2f}")
print(f"Volume:     {vol:,} shares")

print("\n--- Depth Bids (Buyers) ---")
for b in q.get("depth", {}).get("buy", []):
    print(f"  ₹{b.get('price'):>7.2f} | Qty: {b.get('quantity'):>6,d} | Orders: {b.get('orders'):>3}")

print("\n--- Depth Asks (Sellers) ---")
for s in q.get("depth", {}).get("sell", []):
    print(f"  ₹{s.get('price'):>7.2f} | Qty: {s.get('quantity'):>6,d} | Orders: {s.get('orders'):>3}")

# Check user position live
holdings = kite.holdings()
cochin = next((h for h in holdings if h.get("tradingsymbol") == "COCHINSHIP"), None)
if cochin:
    qty = cochin.get("quantity", 0) + cochin.get("t1_quantity", 0)
    avg = cochin.get("average_price", 0)
    cur_val = qty * ltp
    inv = qty * avg
    pnl = cur_val - inv
    pnl_pct = (pnl / inv * 100) if inv else 0
    print(f"\n💼 Your Demat Status: {qty} shs @ ₹{avg:.2f}")
    print(f"Invested: ₹{inv:,.2f} | Live Value: ₹{cur_val:,.2f} | P&L: ₹{pnl:+,.2f} ({pnl_pct:+.2f}%)")

# Check today's 5-minute candles to see the morning progression
today_str = now.strftime("%Y-%m-%d")
bars_5m = kite.historical_data(5506049, today_str, today_str, "5minute")
print(f"\n--- Today's 5-Minute Candles (Total {len(bars_5m)} bars) ---")
for b in bars_5m[-6:]:
    t = str(b["date"])[11:16]
    print(f"  {t} | O: ₹{b['open']:.2f} | H: ₹{b['high']:.2f} | L: ₹{b['low']:.2f} | C: ₹{b['close']:.2f} | Vol: {b['volume']:,}")
