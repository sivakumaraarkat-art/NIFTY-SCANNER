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

spot_token = spot.get("instrument_token")
pe_token = pe.get("instrument_token")

bars_spot = kite.historical_data(spot_token, today_str, today_str, "5minute")
bars_pe = kite.historical_data(pe_token, today_str, today_str, "5minute")

print("=" * 80)
print(f"📡 NIFTY LIVE PULSE & DERIVATIVE SENTINEL — {now.strftime('%H:%M:%S IST')}")
print("=" * 80)
print(f"• NIFTY Spot:    {spot.get('last_price', 0):,.2f} (Day Low: {spot.get('ohlc', {}).get('low', 0):,.2f} | Day High: {spot.get('ohlc', {}).get('high', 0):,.2f})")
print(f"• Bank Nifty:    {bank.get('last_price', 0):,.2f} (Day Low: {bank.get('ohlc', {}).get('low', 0):,.2f} | Day High: {bank.get('ohlc', {}).get('high', 0):,.2f})")
print(f"• 25000 PE LTP:  ₹{pe.get('last_price', 0):.2f} (Holding: 130 qty @ ₹95.00)")
pnl = (pe.get('last_price', 0) - 95.0) * 130
print(f"• Current P&L:   ₹{pnl:+,.2f} ({(pe.get('last_price', 0) - 95.0):+.2f} pts)")
print("-" * 80)
print(f"{'Time':<7} | {'Spot Open':<9} {'Spot High':<9} {'Spot Low':<9} {'Spot Close':<10} | {'PE Close':<8} {'PE Volume':<10}")
print("-" * 80)
for bs, bp in zip(bars_spot[-6:], bars_pe[-6:]):
    t = str(bs['date'])[11:16]
    so, sh, sl, sc = bs['open'], bs['high'], bs['low'], bs['close']
    pc, pv = bp['close'], bp['volume']
    print(f"{t:<7} | {so:<9.2f} {sh:<9.2f} {sl:<9.2f} {sc:<10.2f} | ₹{pc:<7.2f} {pv:<10,}")
print("=" * 80)
