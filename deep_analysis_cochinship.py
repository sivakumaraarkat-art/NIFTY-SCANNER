"""
deep_analysis_cochinship.py
Performs a deep technical, moving average, and profit target analysis
for Cochin Shipyard (COCHINSHIP) based on the user's live position:
80 shares @ ₹1,492.40 + 25 shares averaged @ ₹1,220.00.
"""

import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 85)
print("🚢 COCHIN SHIPYARD (NSE: COCHINSHIP) — DEEP TECHNICAL & TARGET EXIT BLUEPRINT")
print("=" * 85)

# Current Position
cur_qty = 80
cur_avg = 1492.40
cur_inv = cur_qty * cur_avg
ltp = 1220.00

# Averaged Position (+25 shares @ 1220)
add_qty = 25
add_price = 1220.00
new_qty = cur_qty + add_qty
new_inv = cur_inv + (add_qty * add_price)
new_avg = new_inv / new_qty

print(f"💼 POSITION STRUCTURAL SHIFT:")
print(f"   • Current Holding        : {cur_qty} shares @ ₹{cur_avg:,.2f} | Invested: ₹{cur_inv:,.2f} | Loss: -₹{cur_inv - (cur_qty*ltp):,.2f}")
print(f"   • Adding in Muhurat      : +{add_qty} shares @ ₹{add_price:,.2f} (Deploying ₹{add_qty*add_price:,.2f})")
print(f"   • New Blended Position   : {new_qty} shares @ ₹{new_avg:,.2f} (Total Invested: ₹{new_inv:,.2f})")
print(f"   • Cost Reduction Achieved: -₹{cur_avg - new_avg:.2f} per share (Breakeven dropped by 4.35%)")
print("-" * 85)

# Technical Benchmark Levels (Moving Averages)
# 20-DMA: ~₹1,207 (Reclaimed!)
# 50-DMA: ~₹1,349
# 100-DMA: ~₹1,415
# 200-DMA: ~₹1,452
# 52W High: ₹1,843
benchmarks = [
    ("Current Price (LTP)", ltp, "Reclaimed 20-DMA shelf", "Entry / Accumulation Base"),
    ("Target 1 (50-DMA Hurdle)", 1350.00, "First major mean-reversion line", "Short-term swing profit / Reduce risk"),
    ("Target 2 (New Breakeven)", 1430.00, "100-DMA resistance & Full Capital Recovery", "Complete Loss Erased (0.0% P&L)"),
    ("Target 3 (200-DMA Structural Line)", 1500.00, "Bull trend transition line (Old buy avg)", "Pure Green Profit (+₹7,600)"),
    ("Target 4 (Pre-Budget Wave High)", 1680.00, "Institutional Capex Allocation Peak", "Maximum Profit Wave (+₹26,500)"),
    ("Stop Loss / Capital Shield", 1120.00, "Below double-bottom low (₹1,101)", "Risk containment limit")
]

print("\n🎯 PROFIT & TARGET MATRIX FOR 105 SHARES (NEW BLENDED AVG: ₹1,427.54):")
print("-" * 85)
print(f"{'LEVEL / BENCHMARK':32} | {'PRICE (₹)':10} | {'GAIN FROM LTP':14} | {'PORTFOLIO VALUE':16} | {'NET P&L (₹)':14}")
print("-" * 85)

for name, price, desc, act in benchmarks:
    gain_pct = ((price - ltp) / ltp * 100)
    p_val = new_qty * price
    net_pnl = p_val - new_inv
    sign = "+" if net_pnl >= 0 else ""
    sign_g = "+" if gain_pct >= 0 else ""
    print(f"{name:32} | ₹{price:8.2f} | {sign_g}{gain_pct:11.2f}% | ₹{p_val:14,.2f} | {sign}₹{net_pnl:11,.2f}")

print("=" * 85)
