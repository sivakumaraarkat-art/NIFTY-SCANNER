from kiteconnect import KiteConnect
from pathlib import Path
import datetime

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

now = datetime.datetime.now()
symbols = [
    "BSE:SENSEX",
    "NSE:NIFTY 50",
    "BFO:SENSEX26N1281500PE",
    "BFO:SENSEX26N1281600PE",
    "BFO:SENSEX26N1281700PE",
    "BFO:SENSEX26N1281800PE",
    "BFO:SENSEX26N1282100CE",
    "BFO:SENSEX26N1282200CE",
    "NFO:NIFTY26N1725000PE"
]

quotes = kite.quote(symbols)
s_spot = quotes.get("BSE:SENSEX", {})
n_spot = quotes.get("NSE:NIFTY 50", {})

print("=" * 80)
print(f"🔥 SENSEX & HERO-ZERO LIVE PULSE — {now.strftime('%H:%M:%S IST')}")
print("=" * 80)
print(f"• SENSEX SPOT:     {s_spot.get('last_price', 0):,.2f} (Low: {s_spot.get('ohlc', {}).get('low', 0):,.2f} | High: {s_spot.get('ohlc', {}).get('high', 0):,.2f})")
print(f"• NIFTY SPOT:      {n_spot.get('last_price', 0):,.2f}")
print("-" * 80)
print("🎯 HERO-ZERO OPTIONS LTP:")
for sym in symbols[2:]:
    q = quotes.get(sym, {})
    ltp = q.get('last_price', 0)
    vol = q.get('volume', 0)
    oi = q.get('oi', 0)
    print(f"  {sym:<25} | LTP: ₹{ltp:<7.2f} | Vol: {vol:<11,} | OI: {oi:<9,}")
print("=" * 80)
