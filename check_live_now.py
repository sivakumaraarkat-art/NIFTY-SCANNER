from kiteconnect import KiteConnect
from pathlib import Path
import datetime

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

now = datetime.datetime.now()
q = kite.quote(["NSE:COCHINSHIP", "NSE:NIFTY 50"])
cochin = q.get("NSE:COCHINSHIP", {})
nifty = q.get("NSE:NIFTY 50", {})

print("=== LIVE MARKET AUDIT: COCHIN SHIPYARD ===")
print("Current Time:", now.strftime("%Y-%m-%d %H:%M:%S"))
ltp = cochin.get("last_price", 0.0)
ohlc = cochin.get("ohlc", {})
prev_c = ohlc.get("close", ltp)
chg = ltp - prev_c
chg_pct = (chg / prev_c * 100) if prev_c else 0

open_p = ohlc.get("open", ltp)
high_p = ohlc.get("high", ltp)
low_p = ohlc.get("low", ltp)
vol = cochin.get("volume", 0)

print(f"LTP:        ₹{ltp:.2f} ({chg:+.2f} | {chg_pct:+.2f}%)")
print(f"Today Open: ₹{open_p:.2f}")
print(f"Today High: ₹{high_p:.2f}")
print(f"Today Low:  ₹{low_p:.2f}")
print(f"Volume:     {vol:,} shares")

print("\n--- Top 5 Buyers (Bids) ---")
for b in cochin.get("depth", {}).get("buy", []):
    print(f"  ₹{b.get('price'):>7.2f} | Qty: {b.get('quantity'):>6,d} | Orders: {b.get('orders'):>3}")

print("\n--- Top 5 Sellers (Offers) ---")
for s in cochin.get("depth", {}).get("sell", []):
    print(f"  ₹{s.get('price'):>7.2f} | Qty: {s.get('quantity'):>6,d} | Orders: {s.get('orders'):>3}")

n_ltp = nifty.get("last_price", 0.0)
n_ohlc = nifty.get("ohlc", {})
n_prev = n_ohlc.get("close", n_ltp)
n_chg = ((n_ltp - n_prev) / n_prev * 100) if n_prev else 0
print(f"\nNIFTY 50: {n_ltp:.2f} ({n_chg:+.2f}%) | High: {n_ohlc.get('high')} | Low: {n_ohlc.get('low')}")
