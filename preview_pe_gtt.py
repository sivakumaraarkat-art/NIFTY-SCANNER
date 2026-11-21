from kiteconnect import KiteConnect
from pathlib import Path

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

SYMBOL = "NIFTY26N1725000PE"
EXCHANGE = "NFO"
QTY = 130
BUY_PRICE = 95.0
TARGET_TRIGGER = 120.0
TARGET_PRICE = 120.0
SL_TRIGGER = 76.0
SL_PRICE = 75.0

q = kite.quote([f"{EXCHANGE}:{SYMBOL}"]).get(f"{EXCHANGE}:{SYMBOL}", {})
ltp = q.get("last_price", 98.0)

print(f"Option: {SYMBOL} | Live LTP: ₹{ltp:.2f}")
print(f"Holding: {QTY} shs (2 lots) bought @ ₹{BUY_PRICE:.2f}")
print(f"Target 1: ₹{TARGET_PRICE:.2f} -> Value: ₹{QTY * TARGET_PRICE:,.2f} | Profit: +₹{QTY * (TARGET_PRICE - BUY_PRICE):,.2f} (+{((TARGET_PRICE - BUY_PRICE)/BUY_PRICE)*100:.1f}%)")
print(f"Stop Loss: ₹{SL_PRICE:.2f} -> Value: ₹{QTY * SL_PRICE:,.2f} | Risk: -₹{QTY * (BUY_PRICE - SL_PRICE):,.2f} (-{((BUY_PRICE - SL_PRICE)/BUY_PRICE)*100:.1f}%)")
