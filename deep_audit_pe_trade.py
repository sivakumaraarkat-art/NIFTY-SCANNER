from kiteconnect import KiteConnect
from pathlib import Path
import datetime
import json

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

now = datetime.datetime.now()
sym = "NFO:NIFTY26N1725000PE"
q = kite.quote(["NSE:NIFTY 50", sym])
nifty_spot = q.get("NSE:NIFTY 50", {})
pe_opt = q.get(sym, {})

spot_ltp = nifty_spot.get("last_price", 0)
spot_ohlc = nifty_spot.get("ohlc", {})
spot_high = spot_ohlc.get("high", 0)
spot_low = spot_ohlc.get("low", 0)
spot_open = spot_ohlc.get("open", 0)
spot_close = spot_ohlc.get("close", 0)

pe_ltp = pe_opt.get("last_price", 0)
pe_ohlc = pe_opt.get("ohlc", {})
pe_high = pe_ohlc.get("high", 0)
pe_low = pe_ohlc.get("low", 0)
pe_open = pe_ohlc.get("open", 0)
pe_close = pe_ohlc.get("close", 0)
pe_vol = pe_opt.get("volume", 0)
pe_oi = pe_opt.get("oi", 0)

print("=" * 70)
print(f"📊 LIVE AUDIT: NIFTY 25,000 PE (17-NOV-2026) — {now.strftime('%H:%M:%S')}")
print("=" * 70)
print(f"• NIFTY SPOT LTP:  {spot_ltp:,.2f}  |  Day High: {spot_high:,.2f}  |  Day Low: {spot_low:,.2f}")
print(f"• 25000 PE LTP:    ₹{pe_ltp:.2f}  |  Day High: ₹{pe_high:.2f}  |  Day Low: ₹{pe_low:.2f}")
print(f"• Open Interest:   {pe_oi:,} contracts  |  Traded Volume: {pe_vol:,}")
print("-" * 70)

# Check recent 5-min candles of 25000 PE
today_str = now.strftime("%Y-%m-%d")
inst_token = pe_opt.get("instrument_token")
bars_5m = kite.historical_data(inst_token, today_str, today_str, "5minute")
print(f"\n--- Recent 5-Min Candles for NIFTY 25000 PE ---")
for b in bars_5m[-8:]:
    t = str(b["date"])[11:16]
    print(f"  {t} | O: ₹{b['open']:6.2f} | H: ₹{b['high']:6.2f} | L: ₹{b['low']:6.2f} | C: ₹{b['close']:6.2f} | Vol: {b['volume']:,}")

# Check recent 5-min candles of Nifty Spot
spot_token = nifty_spot.get("instrument_token")
bars_spot_5m = kite.historical_data(spot_token, today_str, today_str, "5minute")
print(f"\n--- Recent 5-Min Candles for NIFTY SPOT ---")
for b in bars_spot_5m[-8:]:
    t = str(b["date"])[11:16]
    print(f"  {t} | O: {b['open']:8.2f} | H: {b['high']:8.2f} | L: {b['low']:8.2f} | C: {b['close']:8.2f}")
