from kiteconnect import KiteConnect
from pathlib import Path
import json

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

SYMBOL = "NIFTY26N1725000PE"
EXCHANGE = "NFO"
QTY = 130
SL_TRIGGER = 76.0
SL_PRICE = 75.0
TARGET_TRIGGER = 120.0
TARGET_PRICE = 120.0

quote = kite.quote([f"{EXCHANGE}:{SYMBOL}"]).get(f"{EXCHANGE}:{SYMBOL}", {})
ltp = quote.get("last_price", 99.0)

print("=" * 70)
print(f"🪁 SUBMITTING ZERODHA GTT OCO FOR {SYMBOL}")
print("=" * 70)
print(f"• Current Market LTP: ₹{ltp:.2f}")
print(f"• Quantity:           {QTY} shares (2 lots)")
print(f"• Stop Loss:          Trigger: ₹{SL_TRIGGER:.2f} | Limit: ₹{SL_PRICE:.2f}")
print(f"• Target Profit:      Trigger: ₹{TARGET_TRIGGER:.2f} | Limit: ₹{TARGET_PRICE:.2f}")
print("-" * 70)

orders = [
    {
        "transaction_type": kite.TRANSACTION_TYPE_SELL,
        "quantity": QTY,
        "order_type": kite.ORDER_TYPE_LIMIT,
        "product": kite.PRODUCT_NRML,
        "price": SL_PRICE
    },
    {
        "transaction_type": kite.TRANSACTION_TYPE_SELL,
        "quantity": QTY,
        "order_type": kite.ORDER_TYPE_LIMIT,
        "product": kite.PRODUCT_NRML,
        "price": TARGET_PRICE
    }
]

try:
    resp = kite.place_gtt(
        trigger_type=kite.GTT_TYPE_OCO,
        tradingsymbol=SYMBOL,
        exchange=EXCHANGE,
        trigger_values=[SL_TRIGGER, TARGET_TRIGGER],
        last_price=ltp,
        orders=orders
    )
    trigger_id = resp.get("trigger_id")
    print(f"🎉 SUCCESS: GTT OCO Placed Successfully on Zerodha Kite!")
    print(f"   • GTT Trigger ID: {trigger_id}")
    print(f"   • Status: ACTIVE in Zerodha Kite (Orders -> GTT)")
    print("=" * 70)
except Exception as e:
    print(f"❌ Error placing GTT OCO: {e}")
