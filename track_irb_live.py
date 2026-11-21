"""
track_irb_live.py
=================
Live tracker for IRB Infrastructure Developers (NSE:IRB) & user's portfolio holding.
"""

import sys
from pathlib import Path
from kiteconnect import KiteConnect

# Fix Windows console UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent

api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

q = kite.quote(["NSE:IRB"])["NSE:IRB"]
ltp = q.get("last_price", 0.0)
o = q.get("ohlc", {})
prev = o.get("close", ltp)
open_p = o.get("open", ltp)
high_p = o.get("high", ltp)
low_p = o.get("low", ltp)
chg = ltp - prev
pct = (chg / prev * 100) if prev else 0.0
vol = q.get("volume", 0)
depth = q.get("depth", {})
buys = depth.get("buy", [])
sells = depth.get("sell", [])

holdings = kite.holdings()
irb_h = next((h for h in holdings if h.get("tradingsymbol") == "IRB"), None)

print("=" * 80)
print("🛣️ LIVE TRACKER: IRB INFRASTRUCTURE DEVELOPERS (NSE:IRB)")
print("=" * 80)
print(f"• Current Market Price (LTP): ₹{ltp:.2f} ({chg:+.2f} | {pct:+.2f}%)")
print(f"• Previous Close:             ₹{prev:.2f}")
print(f"• Today Open:                 ₹{open_p:.2f}")
print(f"• Today High:                 ₹{high_p:.2f}")
print(f"• Today Low:                  ₹{low_p:.2f}")
print(f"• Total Volume Today:         {vol:,} shares")
print(f"• Day Turnover:               ₹{(ltp * vol) / 1e7:.2f} Crore")

if irb_h:
    qty = irb_h.get("quantity", 0)
    avg_p = irb_h.get("average_price", 0)
    cur_val = qty * ltp
    inv_val = qty * avg_p
    pnl = cur_val - inv_val
    pnl_pct = (pnl / inv_val * 100) if inv_val else 0
    print("-" * 80)
    print("💼 YOUR PORTFOLIO HOLDING:")
    print(f"• Total Shares Held:          {qty:,} shares (CNC Delivery)")
    print(f"• Average Cost Price:         ₹{avg_p:.2f}")
    print(f"• Total Invested Value:       ₹{inv_val:,.2f}")
    print(f"• Current Market Value:       ₹{cur_val:,.2f}")
    print(f"• Unrealized Holding P&L:     {pnl:+,.2f} INR ({pnl_pct:+.2f}%)")

print("-" * 80)
print("📊 ORDER BOOK DEPTH:")
print(f"{'Buyers (Bids)':<35} | {'Sellers (Offers)':<35}")
print("-" * 80)
for i in range(max(len(buys), len(sells))):
    b = buys[i] if i < len(buys) else {}
    s = sells[i] if i < len(sells) else {}
    b_str = f"₹{b.get('price', 0):>5.2f} (Qty: {b.get('quantity', 0):>7,d} | Orders: {b.get('orders', 0):>2})" if b else ""
    s_str = f"₹{s.get('price', 0):>5.2f} (Qty: {s.get('quantity', 0):>7,d} | Orders: {s.get('orders', 0):>2})" if s else ""
    print(f"{b_str:<35} | {s_str:<35}")

print("=" * 80)
