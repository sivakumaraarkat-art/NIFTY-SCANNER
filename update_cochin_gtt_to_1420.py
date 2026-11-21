from kiteconnect import KiteConnect
from pathlib import Path

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

TRIGGER_ID = 344487058
SYMBOL = "COCHINSHIP"
EXCHANGE = "NSE"
QTY = 25
NEW_TRIGGER = 1420.0
NEW_PRICE = 1420.0

quote = kite.quote([f"{EXCHANGE}:{SYMBOL}"]).get(f"{EXCHANGE}:{SYMBOL}", {})
ltp = quote.get("last_price", 1196.0)

print("=" * 75)
print(f"🔄 UPDATING ZERODHA GTT FOR {SYMBOL} (ID: {TRIGGER_ID})")
print("=" * 75)
print(f"• Current LTP:          ₹{ltp:.2f}")
print(f"• Quantity:             {QTY} shares (CNC Delivery)")
print(f"• Old Target Trigger:   ₹1,305.00 limit")
print(f"• NEW Target Trigger:   ₹{NEW_TRIGGER:.2f} limit")
print(f"• Expected Profit:      +₹{(NEW_PRICE - 1202.0) * QTY:,.2f} (+{((NEW_PRICE - 1202.0)/1202.0)*100:.1f}%)")
print(f"• Cash Inflow on Fill:  ₹{NEW_PRICE * QTY:,.2f}")
print("-" * 75)

orders = [
    {
        "exchange": EXCHANGE,
        "tradingsymbol": SYMBOL,
        "transaction_type": kite.TRANSACTION_TYPE_SELL,
        "quantity": QTY,
        "order_type": kite.ORDER_TYPE_LIMIT,
        "product": kite.PRODUCT_CNC,
        "price": NEW_PRICE
    }
]

try:
    resp = kite.modify_gtt(
        trigger_id=TRIGGER_ID,
        trigger_type=kite.GTT_TYPE_SINGLE,
        tradingsymbol=SYMBOL,
        exchange=EXCHANGE,
        trigger_values=[NEW_TRIGGER],
        last_price=ltp,
        orders=orders
    )
    print("🎉 SUCCESS: Zerodha GTT Successfully Updated!")
    print(f"   • GTT Trigger ID: {resp.get('trigger_id')}")
    print(f"   • New Active Trigger: ₹{NEW_TRIGGER:.2f}")
    print(f"   • New Active Limit:   ₹{NEW_PRICE:.2f}")
    print(f"   • Validity:           365 Days (Good-Till-Triggered)")
    print("=" * 75)
except Exception as e:
    print(f"❌ Error updating GTT: {e}")
    # Fallback: if modify is rejected by broker, place fresh GTT and delete old
    print("Attempting delete + fresh placement fallback...")
    try:
        kite.delete_gtt(TRIGGER_ID)
        fresh_resp = kite.place_gtt(
            trigger_type=kite.GTT_TYPE_SINGLE,
            tradingsymbol=SYMBOL,
            exchange=EXCHANGE,
            trigger_values=[NEW_TRIGGER],
            last_price=ltp,
            orders=orders
        )
        print("🎉 SUCCESS via Fresh Placement!")
        print(f"   • New Trigger ID: {fresh_resp.get('trigger_id')}")
    except Exception as e2:
        print(f"❌ Fallback Error: {e2}")
