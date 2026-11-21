import sys
from pathlib import Path
from kiteconnect import KiteConnect

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

SYMBOL = "COCHINSHIP"
EXCHANGE = "NSE"
QTY = 25
TARGET_PRICE = 1305.0
TARGET_TRIGGER = 1305.0

quote = kite.quote([f"{EXCHANGE}:{SYMBOL}"]).get(f"{EXCHANGE}:{SYMBOL}", {})
ltp = quote.get("last_price", 1202.0)

print("=" * 70)
print("🪁 PLACING ZERODHA GTT TARGET SELL ORDER FOR COCHIN SHIPYARD")
print("=" * 70)
print(f"• Symbol:          {SYMBOL} (NSE)")
print(f"• Current Price:   ₹{ltp:.2f}")
print(f"• Order Quantity:  {QTY} shares")
print(f"• Target Trigger:  ₹{TARGET_TRIGGER:.2f}")
print(f"• Target Limit:    ₹{TARGET_PRICE:.2f}")
print(f"• Total Value:     ₹{QTY * TARGET_PRICE:,.2f}")
print(f"• Net Profit:      +₹{(TARGET_PRICE - 1202.0) * QTY:,.2f} on today's tranche")
print(f"• Validity:        1 Year (365 Days) — Waits automatically until price hits ₹1,305")
print("-" * 70)

orders = [
    {
        "transaction_type": kite.TRANSACTION_TYPE_SELL,
        "quantity": QTY,
        "order_type": kite.ORDER_TYPE_LIMIT,
        "product": kite.PRODUCT_CNC,
        "price": TARGET_PRICE
    }
]

try:
    resp = kite.place_gtt(
        trigger_type=kite.GTT_TYPE_SINGLE,
        tradingsymbol=SYMBOL,
        exchange=EXCHANGE,
        trigger_values=[TARGET_TRIGGER],
        last_price=ltp,
        orders=orders
    )
    trigger_id = resp.get("trigger_id")
    print(f"🎉 SUCCESS: GTT Order Placed on Zerodha Kite!")
    print(f"   • GTT Trigger ID: {trigger_id}")
    print(f"   • Status: ACTIVE in your Zerodha Kite App under Orders -> GTT")
    print("=" * 70)
except Exception as e:
    print(f"❌ Error placing GTT order: {e}")
