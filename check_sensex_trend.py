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
q = kite.quote(["BSE:SENSEX"])
token_s = q["BSE:SENSEX"]["instrument_token"]
bars = kite.historical_data(token_s, today_str, today_str, "5minute")

print("SENSEX Last 8 5-Minute Candles:")
print("Time  | Open     | High     | Low      | Close")
print("-" * 45)
for b in bars[-8:]:
    t = str(b["date"])[11:16]
    print(f"{t} | {b['open']:8.2f} | {b['high']:8.2f} | {b['low']:8.2f} | {b['close']:8.2f}")
