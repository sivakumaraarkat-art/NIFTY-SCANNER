from kiteconnect import KiteConnect
from pathlib import Path
import datetime

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

q = kite.quote(["NSE:COCHINSHIP"]).get("NSE:COCHINSHIP", {})
ltp = q.get("last_price", 1196.0)

# Portfolio parameters
old_qty = 82
old_avg = 1485.10
old_invested = old_qty * old_avg

new_qty = 25
new_buy = 1202.0
new_invested = new_qty * new_buy

total_qty = old_qty + new_qty
total_invested = old_invested + new_invested
blended_avg = total_invested / total_qty

print("=" * 80)
print("📊 COCHIN SHIPYARD: STRATEGIC EXIT & PROFIT OPTIMIZATION ANALYSIS")
print("=" * 80)
print(f"Current LTP:           ₹{ltp:,.2f}")
print(f"Total Shares Held:     {total_qty} shares")
print(f"Blended Average:       ₹{blended_avg:,.2f} (down from ₹{old_avg:,.2f})")
print(f"Total Invested:        ₹{total_invested:,.2f}")
print(f"Current Position Val:  ₹{total_qty * ltp:,.2f} (Unrealized: ₹{(total_qty * ltp) - total_invested:+,.2f})")
print("-" * 80)

scenarios = [
    {
        "name": "Strategy A: Conservative Quick Cash (Exit 25 shs @ ₹1,305)",
        "sell_qty": 25,
        "sell_price": 1305.0,
        "holding_period": "2 - 4 Weeks",
        "description": "Sell only the 25 averaged shares at 50-DMA resistance."
    },
    {
        "name": "Strategy B: The 'Sweet Spot' Breakeven De-risk (Exit 25 shs @ ₹1,420)",
        "sell_qty": 25,
        "sell_price": 1420.0,
        "holding_period": "4 - 6 Weeks",
        "description": "Sell 25 shares exactly when the stock crosses your blended avg (₹1,419)."
    },
    {
        "name": "Strategy C: The 200-DMA Institutional Recovery (Exit 54 shs @ ₹1,460)",
        "sell_qty": 54,
        "sell_price": 1460.0,
        "holding_period": "6 - 8 Weeks (Dec/Jan)",
        "description": "Sell 50% of the entire position as 200-DMA is reclaimed."
    },
    {
        "name": "Strategy D: The Pre-Budget Defense Multiplier (Exit 54 shs @ ₹1,680)",
        "sell_qty": 54,
        "sell_price": 1680.0,
        "holding_period": "10 - 12 Weeks (Pre-Budget Jan-Feb 2027)",
        "description": "Ride the institutional defense capex pre-budget surge."
    }
]

for s in scenarios:
    cash_recovered = s["sell_qty"] * s["sell_price"]
    profit_on_tranche = s["sell_qty"] * (s["sell_price"] - (new_buy if s["sell_qty"] == 25 else blended_avg))
    remaining_qty = total_qty - s["sell_qty"]
    remaining_cost = (total_invested - cash_recovered) / remaining_qty if remaining_qty > 0 else 0
    print(f"\n▶ {s['name']}")
    print(f"   • Expected Horizon:    {s['holding_period']}")
    print(f"   • Cash Inflow:         ₹{cash_recovered:,.2f}")
    print(f"   • Net Profit Booked:   ₹{profit_on_tranche:+,.2f}")
    print(f"   • Remaining Shares:    {remaining_qty} shares")
    print(f"   • Effective Cost/sh:   ₹{remaining_cost:,.2f} on remaining {remaining_qty} shares")
    print(f"   • Logic:               {s['description']}")

print("=" * 80)
