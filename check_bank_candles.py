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
q = kite.quote(["NSE:NIFTY BANK"])
bank_token = q["NSE:NIFTY BANK"]["instrument_token"]
bars = kite.historical_data(bank_token, today_str, today_str, "5minute")

print("Bank Nifty Last 6 Candles:")
for b in bars[-6:]:
    t = str(b["date"])[11:16]
    print(f"{t} | O: {b['open']:8.2f} | H: {b['high']:8.2f} | L: {b['low']:8.2f} | C: {b['close']:8.2f}")
