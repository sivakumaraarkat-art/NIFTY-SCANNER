"""
simulate_irb_averaging.py
Simulates averaging scenarios for IRB Infrastructure Developers Ltd:
- Capital required vs. resulting new average price
- Resistance ceiling risk (100-DMA @ ₹18.94)
- Clear comparison between buying now (+5.5% high) vs. buying on pullback or breakout
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

CURRENT_QTY = 3060
CURRENT_AVG = 29.64
CURRENT_INVESTED = CURRENT_QTY * CURRENT_AVG
LTP = 18.28

SMA_50 = 17.79
SMA_100 = 18.94
SMA_200 = 20.00

print("=" * 80)
print("🛣️ IRB AVERAGING MATHEMATICAL SIMULATION & DECISION MATRIX")
print("=" * 80)
print(f"  • Current Position:    {CURRENT_QTY} shares @ ₹{CURRENT_AVG:.2f} avg")
print(f"  • Current Capital:     ₹{CURRENT_INVESTED:,.2f} invested | Current Value: ₹{CURRENT_QTY * LTP:,.2f}")
print(f"  • Current Loss:        -₹{CURRENT_INVESTED - (CURRENT_QTY * LTP):,.2f} (-{((CURRENT_AVG - LTP)/CURRENT_AVG)*100:.1f}%)")
print(f"  • Live Price Now:      ₹{LTP:.2f} (+5.42% today)")
print("-" * 80)

scenarios = [
    ("Small Add (~₹20,000)", 1100),
    ("Medium Add (~₹35,000)", 1900),
    ("Equal Match (~₹55,000)", 3000)
]

print("📊 MATHEMATICAL IMPACT OF AVERAGING AT CURRENT PRICE (₹18.28):")
print("-" * 80)
for label, add_qty in scenarios:
    add_capital = add_qty * LTP
    new_qty = CURRENT_QTY + add_qty
    new_invested = CURRENT_INVESTED + add_capital
    new_avg = new_invested / new_qty
    drop_in_avg = CURRENT_AVG - new_avg
    gain_needed_to_breakeven = ((new_avg - LTP) / LTP) * 100

    print(f"  • {label}:")
    print(f"    - Fresh Capital Needed:  ₹{add_capital:,.2f} ({add_qty:,} shares)")
    print(f"    - Total Capital at Risk: ₹{new_invested:,.2f} ({new_qty:,} shares)")
    print(f"    - New Average Price:     ₹{new_avg:.2f} (Reduced by -₹{drop_in_avg:.2f})")
    print(f"    - Gain to Breakeven:     +{gain_needed_to_breakeven:.1f}% (Stock must reach ₹{new_avg:.2f})")
    print()

print("-" * 80)
print("⚠️ CRITICAL TECHNICAL RESISTANCE REALITY:")
print(f"  • Today's Price is ALREADY UP +5.42% near day's high (₹18.34).")
print(f"  • 100-Day SMA Resistance sits at ₹{SMA_100:.2f} (Only {((SMA_100 - LTP)/LTP)*100:+.1f}% above current price).")
print(f"  • 200-Day SMA Ceiling sits at    ₹{SMA_200:.2f} (Only {((SMA_200 - LTP)/LTP)*100:+.1f}% above current price).")
print("-" * 80)
print("💡 DISCIPLINED VERDICT:")
print("  ❌ DO NOT AVERAGE TODAY AT ₹18.28 (After a +5.5% intraday surge right under resistance).")
print("  ✅ SMRT STRATEGY:")
print("     Option 1: Wait for a healthy retest/pullback near ₹17.50 - ₹17.80 (50-DMA floor).")
print("     Option 2: Wait for a confirmed daily close above ₹19.00 (breaks 100-DMA resistance).")
print("=" * 80)
