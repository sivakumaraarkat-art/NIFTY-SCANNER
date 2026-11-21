import sys
import os
from pathlib import Path

# UTF-8 encoding fix for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scanners.options_data_provider import get_kite_client

DIWALI_BASKET = [
    {"sym": "RVNL", "kite_sym": "NSE:RVNL", "entry": 179.67, "qty": 83, "cost": 14912.61},
    {"sym": "IRFC", "kite_sym": "NSE:IRFC", "entry": 73.37, "qty": 163, "cost": 11959.31},
    {"sym": "TITAGARH", "kite_sym": "NSE:TITAGARH", "entry": 654.15, "qty": 18, "cost": 11774.70},
    {"sym": "COCHINSHIP", "kite_sym": "NSE:COCHINSHIP", "entry": 1114.20, "qty": 10, "cost": 11142.00},
    {"sym": "APOLLO", "kite_sym": "NSE:APOLLO", "alt_sym": "NSE:APOLLOMICR", "entry": 398.75, "qty": 25, "cost": 9968.75},
    {"sym": "KAYNES", "kite_sym": "NSE:KAYNES", "entry": 3131.00, "qty": 3, "cost": 9393.00},
    {"sym": "RAILTEL", "kite_sym": "NSE:RAILTEL", "entry": 222.40, "qty": 40, "cost": 8896.00},
    {"sym": "SUZLON", "kite_sym": "NSE:SUZLON", "entry": 33.90, "qty": 206, "cost": 6983.40},
    {"sym": "LODHA", "kite_sym": "NSE:LODHA", "entry": 1037.00, "qty": 6, "cost": 6222.00},
    {"sym": "PCBL", "kite_sym": "NSE:PCBL", "entry": 276.95, "qty": 21, "cost": 5815.95},
]

def fetch_zerodha_live():
    print("=" * 95)
    print("🪁 LIVE ZERODHA KITE MARKET AUDIT — DIWALI MUHURAT TOP 10 STOCKS")
    print("=" * 95)

    kite = get_kite_client()
    if not kite:
        print("❌ Kite client initialization failed.")
        print("   Zerodha access token is expired or missing.")
        print("   Please provide your active access token to authenticate.")
        return

    symbols_to_query = []
    for item in DIWALI_BASKET:
        symbols_to_query.append(item["kite_sym"])
        if "alt_sym" in item:
            symbols_to_query.append(item["alt_sym"])

    try:
        quotes = kite.quote(symbols_to_query)
    except Exception as e:
        print(f"❌ Error querying Kite quotes: {e}")
        return

    print(f"{'STOCK':10} | {'ENTRY (₹)':10} | {'ZERODHA LTP':12} | {'NET CHG (₹)':12} | {'RETURN %':10} | {'P&L (₹)':12} | {'CURRENT VAL':12}")
    print("-" * 95)

    tot_invested = 0.0
    tot_current_val = 0.0

    for item in DIWALI_BASKET:
        sym = item["sym"]
        entry = item["entry"]
        qty = item["qty"]
        cost = item["cost"]

        q = quotes.get(item["kite_sym"])
        if not q and "alt_sym" in item:
            q = quotes.get(item["alt_sym"])

        if q:
            ltp = float(q.get("last_price", entry))
            ohlc = q.get("ohlc", {})
            cur_val = ltp * qty
            pnl_rupees = cur_val - cost
            diff_pts = ltp - entry
            pnl_pct = (diff_pts / entry) * 100.0

            tot_invested += cost
            tot_current_val += cur_val

            sign = "+" if pnl_pct >= 0 else ""
            print(f"{sym:<10} | ₹{entry:<9.2f} | ₹{ltp:<11.2f} | {sign}₹{diff_pts:<10.2f} | {sign}{pnl_pct:<8.2f}% | {sign}₹{pnl_rupees:<10.2f} | ₹{cur_val:<11.2f}")
        else:
            print(f"{sym:<10} | ₹{entry:<9.2f} | {'N/A':<12} | {'--':<12} | {'--':<10} | {'--':<12} | {'--':<12}")

    print("=" * 95)
    tot_pnl = tot_current_val - tot_invested
    tot_pnl_pct = (tot_pnl / tot_invested * 100.0) if tot_invested > 0 else 0.0
    sign = "+" if tot_pnl >= 0 else ""

    print(f"💰 Total Invested: ₹{tot_invested:,.2f}")
    print(f"📊 Current Portfolio Value: ₹{tot_current_val:,.2f}")
    print(f"🎯 Net Overall Return: {sign}₹{tot_pnl:,.2f} ({sign}{tot_pnl_pct:.2f}%)")
    print("=" * 95)

if __name__ == "__main__":
    fetch_zerodha_live()
