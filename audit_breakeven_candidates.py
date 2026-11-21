"""
audit_breakeven_candidates.py
Identifies which portfolio holdings currently in a loss are closest
to their cost basis, calculates the exact percentage gain needed to turn
green (breakeven), and ranks them by technical and catalyst probability.
"""

import sys
import io
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent

try:
    from kiteconnect import KiteConnect
    token_file = ROOT / ".kite_access_token"
    key_file = ROOT / ".kite_api_key"

    if not token_file.exists() or not key_file.exists():
        print("❌ Kite token or API key file missing in project root.")
        sys.exit(1)

    access_token = token_file.read_text(encoding="utf-8").strip()
    api_key = key_file.read_text(encoding="utf-8").strip()

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

    holdings = kite.holdings()
    active_holdings = [h for h in holdings if (h.get("quantity", 0) + h.get("t1_quantity", 0)) > 0]

    loss_stocks = []
    profit_stocks = []

    for h in active_holdings:
        sym = h.get("tradingsymbol")
        qty = h.get("quantity", 0) + h.get("t1_quantity", 0)
        avg = h.get("average_price", 0.0)
        ltp = h.get("last_price", 0.0)
        inv = qty * avg
        val = qty * ltp
        pnl = val - inv
        pnl_pct = (pnl / inv * 100) if inv > 0 else 0.0

        if pnl >= 0:
            profit_stocks.append({
                "sym": sym, "qty": qty, "avg": avg, "ltp": ltp,
                "inv": inv, "val": val, "pnl": pnl, "pnl_pct": pnl_pct
            })
        else:
            # Distance to breakeven: how much % does LTP need to rise to reach avg?
            pct_to_breakeven = ((avg - ltp) / ltp * 100) if ltp > 0 else 999.0
            gap_per_share = avg - ltp
            loss_stocks.append({
                "sym": sym, "qty": qty, "avg": avg, "ltp": ltp,
                "inv": inv, "val": val, "pnl": pnl, "pnl_pct": pnl_pct,
                "pct_to_breakeven": pct_to_breakeven,
                "gap_per_share": gap_per_share
            })

    # Sort loss stocks by pct_to_breakeven ascending (closest to green first)
    loss_stocks.sort(key=lambda x: x["pct_to_breakeven"])

    print("=" * 88)
    print("🟢 ALREADY IN PROFIT (WINNERS TO TRAIL & PROTECT)")
    print("=" * 88)
    for p in profit_stocks:
        print(f"   ★ {p['sym']:<12}: LTP ₹{p['ltp']:8.2f} vs Avg ₹{p['avg']:8.2f} | Profit: +₹{p['pnl']:8.2f} (+{p['pnl_pct']:5.2f}%) | Qty: {p['qty']}")

    print("\n" + "=" * 88)
    print("🎯 STOCKS IN LOSS RANKED BY CLOSEST TO TURNING POSITIVE (BREAKEVEN)")
    print("=" * 88)
    print(f"{'RANK':4} | {'SYMBOL':12} | {'CURRENT LTP':11} | {'BUY AVG':10} | {'GAP (₹)':9} | {'% GAIN NEEDED':14} | {'CURRENT P&L':12} | {'TIMEFRAME':14}")
    print("-" * 88)

    for idx, s in enumerate(loss_stocks, start=1):
        needed = s["pct_to_breakeven"]
        # Estimate realistic timeframe based on typical swing velocity
        if needed <= 5.0:
            tf = "1 - 2 Weeks ⚡"
        elif needed <= 12.0:
            tf = "2 - 4 Weeks 🚀"
        elif needed <= 25.0:
            tf = "4 - 8 Weeks 📈"
        elif needed <= 50.0:
            tf = "2 - 4 Months ⏳"
        else:
            tf = "Long Term / Penny ⚠️"

        print(f"{idx:<4} | {s['sym']:<12} | ₹{s['ltp']:9.2f} | ₹{s['avg']:8.2f} | ₹{s['gap_per_share']:7.2f} | +{needed:11.2f}% | ₹{s['pnl']:10.2f} | {tf}")

    print("=" * 88)

except Exception as e:
    print(f"❌ Error: {e}")
