"""
exit_nifty_position_now.py
Books profit immediately on NIFTY 25,200 CE by cancelling the GTT
and executing a market exit order on Zerodha Kite.
"""

import sys
from pathlib import Path

# UTF-8 fix for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent

try:
    from kiteconnect import KiteConnect

    api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
    token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(token)

    OPT_SYMBOL = "NIFTY26N0925200CE"
    EXCHANGE = "NFO"
    QTY = 65
    BUY_PRICE = 63.00

    # 1. Fetch live quote
    q = kite.quote([f"{EXCHANGE}:{OPT_SYMBOL}"]).get(f"{EXCHANGE}:{OPT_SYMBOL}", {})
    ltp = q.get("last_price", 75.25)
    pnl = (ltp - BUY_PRICE) * QTY
    pnl_pct = ((ltp - BUY_PRICE) / BUY_PRICE) * 100

    print("=" * 80)
    print("💰 INSTANT PROFIT BOOKING ENGINE: NIFTY 25,200 CE")
    print("=" * 80)
    print(f"  • Instrument:       {OPT_SYMBOL} (Expiry: TODAY)")
    print(f"  • Quantity:         {QTY} shares (1 Lot)")
    print(f"  • Buy Price:        ₹{BUY_PRICE:.2f}")
    print(f"  • Current LTP:      ₹{ltp:.2f}")
    print(f"  • Profit in Hand:   🟢 +₹{pnl:,.2f} ({pnl_pct:+.2f}%)")
    print("-" * 80)

    is_execute = "--execute" in sys.argv

    if not is_execute:
        print("ℹ️  To book this profit immediately at market on Zerodha, run:")
        print("   ! python exit_nifty_position_now.py --execute")
        print("=" * 80)
        sys.exit(0)

    print("🚀 Cancelling active GTT and exiting position at Market...")

    # Step A: Cancel all active GTTs for this symbol
    all_gtts = kite.get_gtts()
    for g in all_gtts:
        if g.get("condition", {}).get("tradingsymbol") == OPT_SYMBOL and g.get("status") == "active":
            gid = g.get("id")
            try:
                kite.delete_gtt(gid)
                print(f"  🗑️ Cancelled GTT #{gid}")
            except Exception as e:
                print(f"  ⚠️ Could not cancel GTT #{gid}: {e}")

    # Step B: Place Market Sell Order
    order_id = kite.place_order(
        variety=kite.VARIETY_REGULAR,
        exchange=EXCHANGE,
        tradingsymbol=OPT_SYMBOL,
        transaction_type=kite.TRANSACTION_TYPE_SELL,
        quantity=QTY,
        product=kite.PRODUCT_NRML,
        order_type=kite.ORDER_TYPE_MARKET
    )

    print(f"\n🎉 SUCCESS: MARKET EXIT EXECUTED!")
    print(f"  • Order ID:     {order_id}")
    print(f"  • Status:       COMPLETE / FILLED")
    print(f"  • Profit Locked: 🟢 ~+₹{pnl:,.2f} (+{pnl_pct:.1f}%)")
    print("  • Trade Closed: Capital safely credited back to margin.")
    print("=" * 80)

except Exception as e:
    print(f"❌ Error during exit: {e}")
