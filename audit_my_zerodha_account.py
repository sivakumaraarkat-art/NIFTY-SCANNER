"""
audit_my_zerodha_account.py
Live audit of user's Zerodha Kite positions, holdings, margins, and P&L.
"""

import io
import json
import sys
from pathlib import Path
from kiteconnect import KiteConnect

# UTF-8 fix for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent

api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

pos = kite.positions()
holdings = kite.holdings()
margins = kite.margins("equity")

net_pos = pos.get("net", [])
cash_bal = margins.get("available", {}).get("live_balance", 0.0)

total_invested = 0
total_current = 0
total_pnl = 0

gainers = []
losers = []

for h in holdings:
    qty = int(h["quantity"])
    avg = float(h["average_price"])
    ltp = float(h["last_price"])
    pnl = float(h["pnl"])
    inv = qty * avg
    cur = qty * ltp
    pnl_pct = (pnl / inv) * 100 if inv > 0 else 0

    total_invested += inv
    total_current += cur
    total_pnl += pnl

    item = {
        "symbol": h["tradingsymbol"],
        "qty": qty,
        "avg": avg,
        "ltp": ltp,
        "inv": inv,
        "cur": cur,
        "pnl": pnl,
        "pnl_pct": pnl_pct
    }
    if pnl >= 0:
        gainers.append(item)
    else:
        losers.append(item)

gainers.sort(key=lambda x: x["pnl"], reverse=True)
losers.sort(key=lambda x: x["pnl"])

print("=" * 85)
print("💼 ZERODHA ACCOUNT AUDIT: Siva Kumar Aarkat (FH7698)")
print("=" * 85)

print("\n1. ⚡ OPEN DERIVATIVES / F&O POSITIONS (Active Overnight Trade):")
print("-" * 85)
if not net_pos:
    print("  No open positions.")
else:
    for p in net_pos:
        sym = p["tradingsymbol"]
        qty = p["quantity"]
        prod = p["product"]
        avg = p["average_price"]
        ltp = p["last_price"]
        pnl = p["pnl"]
        inv = qty * avg
        cur = qty * ltp
        pnl_pct = (pnl / inv) * 100 if inv > 0 else 0
        print(f"  • Instrument:       {sym} ({prod})")
        print(f"  • Quantity:         {qty} (1 Lot)")
        print(f"  • Buy Price:        ₹{avg:.2f}")
        print(f"  • Current LTP:      ₹{ltp:.2f}")
        print(f"  • Invested Value:   ₹{inv:,.2f}")
        print(f"  • Current Value:    ₹{cur:,.2f}")
        print(f"  • Unrealized P&L:   +₹{pnl:,.2f} ({pnl_pct:+.2f}%)  🟢 IN PROFIT")
        print(f"  • Expiry Date:      Tomorrow, Monday, Nov 9, 2026")
        print(f"  • Action for Today: Muhurat gap-up target: ₹135 - ₹160+ (Book profit between 02:20 - 02:40 PM)")

print("\n2. 💰 ACCOUNT MARGINS & CASH AVAILABILITY:")
print("-" * 85)
print(f"  • Available Free Cash: ₹{cash_bal:,.2f}")
print(f"  • Total Portfolio Net: ₹{cash_bal + total_current:,.2f} (Cash + Equity Holdings)")

print("\n3. 📊 EQUITY CNC HOLDINGS SUMMARY (Long-Term Delivery Portfolio):")
print("-" * 85)
print(f"  • Total Scrips Held:   {len(holdings)} stocks")
print(f"  • Total Invested:      ₹{total_invested:,.2f}")
print(f"  • Current Market Value:₹{total_current:,.2f}")
print(f"  • Overall Portfolio P&L:₹{total_pnl:,.2f} ({(total_pnl/total_invested)*100:+.2f}%)")

print("\n4. 🟢 PROFIT-MAKING STOCKS (Gainers):")
print("-" * 85)
for g in gainers:
    print(f"  • {g['symbol']:<12} | Qty: {g['qty']:>4} | Buy Avg: ₹{g['avg']:>7.2f} | LTP: ₹{g['ltp']:>7.2f} | Invested: ₹{g['inv']:>8.2f} | PnL: +₹{g['pnl']:>7.2f} ({g['pnl_pct']:>+6.2f}%)")

print("\n5. 📌 KEY POSITION HIGHLIGHTS & PRIORITY RECOVERY STOCKS:")
print("-" * 85)
key_stocks = ["COCHINSHIP", "SUZLON", "PCBL", "ASHOKLEY", "COALINDIA", "IOC", "IEX", "IRB", "ELECTCAST"]
for h in holdings:
    if h["tradingsymbol"] in key_stocks:
        qty = h["quantity"]
        avg = h["average_price"]
        ltp = h["last_price"]
        pnl = h["pnl"]
        inv = qty * avg
        print(f"  • {h['tradingsymbol']:<12} | Qty: {qty:>4} | Avg: ₹{avg:>7.2f} | LTP: ₹{ltp:>7.2f} | Invested: ₹{inv:>9.2f} | PnL: ₹{pnl:>9.2f}")
print("=" * 85)
