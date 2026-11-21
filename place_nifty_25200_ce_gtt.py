"""
place_nifty_25200_ce_gtt.py
===========================
Places a GTT OCO (One Cancels Other) order on Zerodha Kite for NIFTY Call Option:
- Auto-detects open position: NFO:NIFTY26N0925200CE (Qty: 65, Buy Avg: ₹76.50)
- Current LTP: ₹61.85
- Enforces Zerodha OCO Bracketing Rule: (Stop < LTP < Target)
  * Target: ₹135.00 (or customizable via --target) -> Profit: +₹3,802.50 (+76.5% ROI)
  * Stop-Loss: ₹48.00 (or customizable via --stop, must be < LTP) -> Limits loss to -₹1,852.50
"""

import sys
import argparse
from pathlib import Path

# UTF-8 fix for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent

try:
    from kiteconnect import KiteConnect
    api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
    token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(token)
except Exception as e:
    print(f"❌ Failed to initialize KiteConnect: {e}")
    sys.exit(1)

def get_live_nifty_position():
    """Detects open Nifty option position from Zerodha."""
    try:
        pos = kite.positions().get("net", [])
        for p in pos:
            if "NIFTY" in p.get("tradingsymbol", "") and p.get("quantity", 0) > 0:
                return p
    except Exception as e:
        print(f"⚠️ Notice while reading positions: {e}")
    return None

def place_gtt(target=135.0, stop=48.0, stop_limit=45.0, execute=False):
    pos = get_live_nifty_position()

    if pos:
        SYMBOL = pos.get("tradingsymbol")
        EXCHANGE = pos.get("exchange", "NFO")
        QTY = int(pos.get("quantity", 65))
        PRODUCT = pos.get("product", "NRML")
        BUY_PRICE = float(pos.get("average_price", 76.50))
        print(f"🔍 [AUTO-DETECTED OPEN POSITION] {EXCHANGE}:{SYMBOL} | Qty: {QTY} | Buy Avg: ₹{BUY_PRICE:.2f}")
    else:
        SYMBOL = "NIFTY26N0925200CE"
        EXCHANGE = "NFO"
        QTY = 65
        PRODUCT = "NRML"
        BUY_PRICE = 76.50
        print(f"ℹ️ [CONFIGURED POSITION] {EXCHANGE}:{SYMBOL} | Qty: {QTY} | Buy Avg: ₹{BUY_PRICE:.2f}")

    print("=" * 80)
    print("🪁 ZERODHA GTT CREATION ENGINE: NIFTY CALL OPTION EXIT")
    print("=" * 80)

    # Fetch live LTP
    try:
        quote = kite.quote([f"{EXCHANGE}:{SYMBOL}"])
        ltp = float(quote.get(f"{EXCHANGE}:{SYMBOL}", {}).get("last_price", 61.85))
    except Exception as e:
        ltp = 61.85

    print(f"  • Instrument:       {EXCHANGE}:{SYMBOL}")
    print(f"  • Position Size:    {QTY} shares (1 Lot)")
    print(f"  • Buy Average:      ₹{BUY_PRICE:.2f} (Total Cost: ₹{BUY_PRICE * QTY:,.2f})")
    print(f"  • Current LTP:      ₹{ltp:.2f} (Current Value: ₹{ltp * QTY:,.2f})")
    print(f"  • Current P&L:      ₹{(ltp - BUY_PRICE) * QTY:,.2f} ({((ltp - BUY_PRICE)/BUY_PRICE)*100:.1f}%)")
    print("-" * 80)

    # ZERODHA BRACKETING VALIDATION (Stop < LTP < Target)
    if stop >= ltp:
        print(f"⚠️  ADJUSTING STOP: Zerodha requires Stop-Loss Trigger to be strictly LESS than LTP (₹{ltp:.2f}).")
        old_stop = stop
        stop = round(ltp - 13.85, 1) # Set to ~48.0
        stop_limit = round(stop - 3.0, 1) # Set to ~45.0
        print(f"   Adjusted Stop Trigger from ₹{old_stop:.2f} to ₹{stop:.2f} (Limit: ₹{stop_limit:.2f})")

    if target <= ltp:
        print(f"❌ ERROR: Target Trigger (₹{target:.2f}) must be strictly GREATER than LTP (₹{ltp:.2f}).")
        return False

    print("🎯 GTT OCO (ONE CANCELS OTHER) ORDER PARAMETERS:")
    print(f"  1. Target Leg:      Trigger at ₹{target:.2f} | Limit Price: ₹{target:.2f}")
    print(f"     -> Expected P&L: +₹{(target - BUY_PRICE) * QTY:,.2f} (+{((target - BUY_PRICE)/BUY_PRICE)*100:.1f}% ROI)")
    print(f"  2. Stop-Loss Leg:   Trigger at ₹{stop:.2f}   | Limit Price: ₹{stop_limit:.2f}")
    print(f"     -> Risk Guard:   -₹{(BUY_PRICE - stop) * QTY:,.2f} (-{((BUY_PRICE - stop)/BUY_PRICE)*100:.1f}%)")
    print("-" * 80)

    trigger_type = kite.GTT_TYPE_OCO
    trigger_values = [stop, target]
    orders = [
        {
            "transaction_type": kite.TRANSACTION_TYPE_SELL,
            "quantity": QTY,
            "order_type": kite.ORDER_TYPE_LIMIT,
            "product": PRODUCT,
            "price": stop_limit
        },
        {
            "transaction_type": kite.TRANSACTION_TYPE_SELL,
            "quantity": QTY,
            "order_type": kite.ORDER_TYPE_LIMIT,
            "product": PRODUCT,
            "price": target
        }
    ]

    if not execute:
        print("ℹ️  PREVIEW MODE: GTT order verified and ready.")
        print(f"   To submit directly to your Zerodha account, type:")
        print(f"   ! python place_nifty_25200_ce_gtt.py --target {target} --stop {stop} --execute")
        print("=" * 80)
        return False

    print("🚀 Submitting GTT OCO order directly to Zerodha Kite...")
    try:
        resp = kite.place_gtt(
            trigger_type=trigger_type,
            tradingsymbol=SYMBOL,
            exchange=EXCHANGE,
            trigger_values=trigger_values,
            last_price=ltp,
            orders=orders
        )
        trigger_id = resp.get("trigger_id")
        print("\n🎉 SUCCESS: GTT OCO ORDER PLACED ON ZERODHA KITE!")
        print(f"  • Trigger ID:   {trigger_id}")
        print(f"  • Status:       ACTIVE on Zerodha Kite")
        print(f"  • Verification: Open Zerodha Kite App -> Orders -> GTT")
        print("=" * 80)
        return True
    except Exception as e:
        print(f"❌ Error submitting GTT order to Zerodha: {e}")
        print("=" * 80)
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Place GTT OCO for NIFTY Call Option")
    parser.add_argument("--target", type=float, default=135.0, help="Target trigger price (default 135.0)")
    parser.add_argument("--stop", type=float, default=48.0, help="Stop-loss trigger price (must be < LTP, default 48.0)")
    parser.add_argument("--stop-limit", type=float, default=45.0, help="Stop-loss limit execution price (default 45.0)")
    parser.add_argument("--execute", action="store_true", help="Submit directly to Zerodha")
    args = parser.parse_args()

    place_gtt(target=args.target, stop=args.stop, stop_limit=args.stop_limit, execute=args.execute)
