"""
calculate_exact_67k_plan.py
Calculates exact share quantities and budget allocation for Siva Kumar's
₹67,076.20 Zerodha account balance for tomorrow's Muhurat session.
"""

stocks = {
    "PCBL": {"ltp": 279.25, "sl": 255.00, "t1": 315.00, "t2": 350.00, "dip": 274.00},
    "TITAGARH": {"ltp": 677.85, "sl": 615.00, "t1": 745.00, "t2": 820.00, "dip": 655.00},
    "KAYNES": {"ltp": 3233.00, "sl": 2980.00, "t1": 3650.00, "t2": 4150.00, "dip": 3150.00},
    "KEI": {"ltp": 3988.00, "sl": 3720.00, "t1": 4400.00, "t2": 4850.00, "dip": 3880.00},
    "DIXON": {"ltp": 12625.00, "sl": 11750.00, "t1": 13850.00, "t2": 15200.00, "dip": 12150.00},
}

TOTAL_CAPITAL = 67076.20

print("=" * 80)
print(f"📊 EXACT ALLOCATION PLANS FOR SIVA'S ₹{TOTAL_CAPITAL:,.2f} ZERODHA BALANCE")
print("=" * 80)

# Plan A: 4 High-Conviction Stocks (PCBL, TITAGARH, KAYNES, KEI) - Optimal Sizing
# Sizing:
# PCBL: 65 shares @ 279.25 = ₹18,151.25
# TITAGARH: 26 shares @ 677.85 = ₹17,624.10
# KAYNES: 5 shares @ 3233.00 = ₹16,165.00
# KEI: 3 shares @ 3988.00 = ₹11,964.00
# Total = 18151.25 + 17624.10 + 16165.00 + 11964.00 = ₹63,904.35 (Cash reserve: ₹3,171.85)

plan_a = [
    ("PCBL", 65, 40, 25),      # total 65 (T1: 40, T2: 25)
    ("TITAGARH", 26, 16, 10),  # total 26 (T1: 16, T2: 10)
    ("KAYNES", 5, 3, 2),       # total 5  (T1: 3, T2: 2)
    ("KEI", 3, 2, 1),          # total 3  (T1: 2, T2: 1)
]

print("\n🎯 PLAN A: 4-STOCK POWER PORTFOLIO (NO DIXON - MAXIMUM CONVICTION)")
print(f"{'STOCK':10} | {'TOTAL QTY':10} | {'TOTAL COST':12} | {'T1 (TOMORROW)':15} | {'T1 COST':10} | {'T2 (DIP GTT)':14} | {'T2 COST':10}")
print("-" * 80)

total_a_cost = 0
t1_a_cost = 0
t2_a_cost = 0

for sym, tot_q, t1_q, t2_q in plan_a:
    ltp = stocks[sym]["ltp"]
    dip = stocks[sym]["dip"]
    tot_cost = tot_q * ltp
    t1_cost = t1_q * ltp
    t2_cost = t2_q * dip
    total_a_cost += tot_cost
    t1_a_cost += t1_cost
    t2_a_cost += t2_cost
    print(f"{sym:10} | {tot_q:10d} | ₹{tot_cost:10.2f} | {t1_q:2d} shares     | ₹{t1_cost:8.2f} | {t2_q:2d} sh @ ₹{dip:<6.0f} | ₹{t2_cost:8.2f}")

print("-" * 80)
print(f"Total Portfolio Cost : ₹{total_a_cost:,.2f} (Utilisation: {(total_a_cost/TOTAL_CAPITAL)*100:.1f}%)")
print(f"Tranche 1 (Tomorrow) : ₹{t1_a_cost:,.2f} ({(t1_a_cost/TOTAL_CAPITAL)*100:.1f}%)")
print(f"Tranche 2 (Dip GTT)  : ₹{t2_a_cost:,.2f} ({(t2_a_cost/TOTAL_CAPITAL)*100:.1f}%)")
print(f"Safety Cash Buffer   : ₹{TOTAL_CAPITAL - total_a_cost:,.2f}")

# Plan B: 5 Stocks INCLUDING 1 share of DIXON
# Sizing:
# DIXON: 1 share @ 12625.00 = ₹12,625.00
# PCBL: 48 shares @ 279.25 = ₹13,404.00
# TITAGARH: 20 shares @ 677.85 = ₹13,557.00
# KAYNES: 4 shares @ 3233.00 = ₹12,932.00
# KEI: 3 shares @ 3988.00 = ₹11,964.00
# Total = ₹64,482.00 (Cash reserve: ₹2,594.20)

plan_b = [
    ("DIXON", 1, 1, 0),        # 1 share tomorrow
    ("PCBL", 48, 30, 18),      # total 48 (T1: 30, T2: 18)
    ("TITAGARH", 20, 12, 8),   # total 20 (T1: 12, T2: 8)
    ("KAYNES", 4, 2, 2),       # total 4  (T1: 2, T2: 2)
    ("KEI", 3, 2, 1),          # total 3  (T1: 2, T2: 1)
]

print("\n🎯 PLAN B: 5-STOCK BALANCED PORTFOLIO (INCLUDES 1 SHARE DIXON)")
print(f"{'STOCK':10} | {'TOTAL QTY':10} | {'TOTAL COST':12} | {'T1 (TOMORROW)':15} | {'T1 COST':10} | {'T2 (DIP GTT)':14} | {'T2 COST':10}")
print("-" * 80)

total_b_cost = 0
t1_b_cost = 0
t2_b_cost = 0

for sym, tot_q, t1_q, t2_q in plan_b:
    ltp = stocks[sym]["ltp"]
    dip = stocks[sym]["dip"]
    tot_cost = tot_q * ltp
    t1_cost = t1_q * ltp
    t2_cost = t2_q * dip
    total_b_cost += tot_cost
    t1_b_cost += t1_cost
    t2_b_cost += t2_cost
    print(f"{sym:10} | {tot_q:10d} | ₹{tot_cost:10.2f} | {t1_q:2d} shares     | ₹{t1_cost:8.2f} | {t2_q:2d} sh @ ₹{dip:<6.0f} | ₹{t2_cost:8.2f}")

print("-" * 80)
print(f"Total Portfolio Cost : ₹{total_b_cost:,.2f} (Utilisation: {(total_b_cost/TOTAL_CAPITAL)*100:.1f}%)")
print(f"Tranche 1 (Tomorrow) : ₹{t1_b_cost:,.2f} ({(t1_b_cost/TOTAL_CAPITAL)*100:.1f}%)")
print(f"Tranche 2 (Dip GTT)  : ₹{t2_b_cost:,.2f} ({(t2_b_cost/TOTAL_CAPITAL)*100:.1f}%)")
print(f"Safety Cash Buffer   : ₹{TOTAL_CAPITAL - total_b_cost:,.2f}")
print("=" * 80)
