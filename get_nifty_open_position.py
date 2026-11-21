"""
get_nifty_open_position.py
Retrieves the user's exact open Nifty position from Zerodha Kite.
"""

import sys
from pathlib import Path
from kiteconnect import KiteConnect

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent

try:
    api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
    token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(token)

    positions = kite.positions().get("net", [])
    nifty_positions = [p for p in positions if "NIFTY" in p.get("tradingsymbol", "") and p.get("quantity", 0) != 0]

    print("=" * 80)
    print("ZERODHA LIVE OPEN NIFTY POSITIONS:")
    print("=" * 80)
    if not nifty_positions:
        print("No open Nifty positions with non-zero quantity found in net positions.")
        # Check all net positions just in case
        for p in positions:
            if p.get("quantity", 0) != 0:
                print(f"Other open position: {p.get('tradingsymbol')} | Qty: {p.get('quantity')} | Avg: {p.get('average_price')} | Product: {p.get('product')}")
    else:
        for p in nifty_positions:
            sym = p.get("tradingsymbol")
            qty = p.get("quantity")
            avg_price = p.get("average_price")
            product = p.get("product")
            exchange = p.get("exchange")
            m2m = p.get("m2m")
            pnl = p.get("pnl")
            ltp = p.get("last_price")
            print(f"Symbol:       {exchange}:{sym}")
            print(f"Quantity:     {qty}")
            print(f"Avg Price:    ₹{avg_price}")
            print(f"LTP:          ₹{ltp}")
            print(f"Product:      {product}")
            print(f"P&L:          ₹{pnl}")
            print(f"M2M:          ₹{m2m}")
    print("=" * 80)

except Exception as e:
    print(f"Error fetching positions: {e}")
