from kiteconnect import KiteConnect
from pathlib import Path
import datetime

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

now = datetime.datetime.now()
today_str = now.strftime("%Y-%m-%d")
sym = "NFO:NIFTY26N1725000PE"

q = kite.quote(["NSE:NIFTY 50", "NSE:NIFTY BANK", sym])
spot = q.get("NSE:NIFTY 50", {})
bank = q.get("NSE:NIFTY BANK", {})
pe = q.get(sym, {})

spot_ltp = spot.get("last_price", 0)
pe_ltp = pe.get("last_price", 0)
pe_high = pe.get("ohlc", {}).get("high", 0)
pe_low = pe.get("ohlc", {}).get("low", 0)

pe_token = pe.get("instrument_token")
spot_token = spot.get("instrument_token")

bars_pe = kite.historical_data(pe_token, today_str, today_str, "5minute")
bars_spot = kite.historical_data(spot_token, today_str, today_str, "5minute")

print("=" * 75)
print(f"🎯 25,000 PE (17-NOV) TARGET ₹120 FEASIBILITY AUDIT — {now.strftime('%H:%M:%S IST')}")
print("=" * 75)
print(f"• Current Nifty Spot:   {spot_ltp:,.2f}")
print(f"• Current 25000 PE LTP: ₹{pe_ltp:.2f}")
print(f"• Today's PE High:      ₹{pe_high:.2f}  (Reached when Nifty tested Day Low)")
print(f"• Today's PE Low:       ₹{pe_low:.2f}")
print(f"• Today's Spot Range:   Low: {spot.get('ohlc', {}).get('low', 0):,.2f}  |  High: {spot.get('ohlc', {}).get('high', 0):,.2f} (Range: {spot.get('ohlc', {}).get('high', 0) - spot.get('ohlc', {}).get('low', 0):.1f} pts)")
print("-" * 75)

print("\n📈 Intraday Timeline: When 25,000 PE Crossed ₹115 - ₹148 Today:")
hits = 0
for bp, bs in zip(bars_pe, bars_spot):
    if bp['high'] >= 115.0:
        hits += 1
        t = str(bp['date'])[11:16]
        ph = bp['high']
        pc = bp['close']
        sl = bs['low']
        sc = bs['close']
        print(f"   • [{t} IST] PE High: ₹{ph:6.2f} (Close: ₹{pc:6.2f}) <--> Nifty Spot Low: {sl:8.2f} (Close: {sc:8.2f})")

print(f"\nTotal 5-min intervals above ₹115 today: {hits}")

# Mathematical Delta Calculation
# Delta approximation:
# Option is OTM by (25222 - 25000) = 222 pts.
# Days to Expiry (Nov 17): 5 days.
# Approximate Delta ~ -0.28 to -0.32.
points_to_target = 120.0 - pe_ltp
pts_nifty_drop_needed = points_to_target / 0.30
implied_nifty_level = spot_ltp - pts_nifty_drop_needed

print("-" * 75)
print("📐 MATHEMATICAL PROJECTION TO HIT ₹120:")
print(f"1. Premium Gain Needed:      +₹{points_to_target:.2f} (from ₹{pe_ltp:.2f} to ₹120.00)")
print(f"2. Option Delta (Est.):      ~0.30 (gains ~₹0.30 per 1 pt Nifty drop)")
print(f"3. Nifty Spot Drop Needed:   ~{pts_nifty_drop_needed:.1f} points")
print(f"4. Target Nifty Spot Level:  ~{implied_nifty_level:,.2f}")
print(f"5. Day's Lowest Nifty Level: {spot.get('ohlc', {}).get('low', 0):,.2f}")
print("=" * 75)
