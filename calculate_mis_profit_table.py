"""
calculate_mis_profit_table.py
=============================
Computes exact Net Profit and ROI for Monday MIS Intraday Trades held until 03:00 PM.
Calculates:
- 5x Zerodha MIS Leverage Exposure
- Quantities for ₹20,000, ₹50,000, and ₹1,00,000 capital
- Target 1 (1.5R) and Target 2 (2.5R) profit
- Exact Indian statutory deductions (Brokerage, STT, Exchange, GST, SEBI, Stamp Duty)
"""

import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def calc_equity_mis_charges(buy_p, sell_p, qty):
    buy_turnover = buy_p * qty
    sell_turnover = sell_p * qty
    total_turnover = buy_turnover + sell_turnover

    # Brokerage: min(20, 0.03%) each side
    brok_buy = min(20.0, buy_turnover * 0.0003)
    brok_sell = min(20.0, sell_turnover * 0.0003)
    total_brok = brok_buy + brok_sell

    stt = sell_turnover * 0.00025 # 0.025% on sell
    exchange_charges = total_turnover * 0.0000297 # NSE 0.00297%
    sebi_charges = total_turnover * 0.000001 # Rs 10 per crore
    stamp_duty = buy_turnover * 0.00003 # 0.003% on buy
    gst = (total_brok + exchange_charges + sebi_charges) * 0.18

    total_charges = total_brok + stt + exchange_charges + sebi_charges + stamp_duty + gst
    return total_charges

stocks = [
    {
        "name": "KOTAKBANK",
        "cmp": 480.50,
        "t1": 491.10,
        "t2": 498.20,
        "sl": 473.40,
        "gain_t1": 10.60,
        "gain_t2": 17.70,
        "loss_sl": 7.10
    },
    {
        "name": "LAURUSLABS",
        "cmp": 2370.00,
        "t1": 2452.90,
        "t2": 2508.20,
        "sl": 2314.70,
        "gain_t1": 82.90,
        "gain_t2": 138.20,
        "loss_sl": 55.30
    },
    {
        "name": "ETERNAL",
        "cmp": 364.40,
        "t1": 376.70,
        "t2": 384.90,
        "sl": 356.20,
        "gain_t1": 12.30,
        "gain_t2": 20.50,
        "loss_sl": 8.20
    },
    {
        "name": "ATHERENERG",
        "cmp": 1822.90,
        "t1": 1908.90,
        "t2": 1966.20,
        "sl": 1765.60,
        "gain_t1": 86.00,
        "gain_t2": 143.30,
        "loss_sl": 57.30
    }
]

capitals = [20000, 50000, 100000]

print("=" * 110)
print("💰 INTRADAY MIS PROFIT PROJECTION TABLE (EXIT AT 03:00 PM IST)")
print("Leverage: 5x MIS Intraday Margin (Zerodha Standard)")
print("Deductions: All Government STT, Stamp Duty, GST, Exchange Fees & Brokerage Included")
print("=" * 110)

for cap in capitals:
    print(f"\n--- CAPITAL DEPLOYED: INR {cap:,.2f} (5x Buying Power: INR {cap*5:,.2f}) ---")
    print(f"{'STOCK':<12} | {'QTY':<6} | {'INVESTED (5x)':<14} | {'NET PROFIT T1 (1.5R)':<22} | {'NET PROFIT T2 (2.5R)':<22} | {'MAX SL RISK':<15}")
    print("-" * 110)
    for s in stocks:
        # 5x exposure
        buying_power = cap * 5
        qty = int(buying_power // s["cmp"])
        actual_exposure = qty * s["cmp"]

        # Target 1
        gross_t1 = (s["t1"] - s["cmp"]) * qty
        charges_t1 = calc_equity_mis_charges(s["cmp"], s["t1"], qty)
        net_t1 = gross_t1 - charges_t1
        roi_t1 = (net_t1 / cap) * 100

        # Target 2
        gross_t2 = (s["t2"] - s["cmp"]) * qty
        charges_t2 = calc_equity_mis_charges(s["cmp"], s["t2"], qty)
        net_t2 = gross_t2 - charges_t2
        roi_t2 = (net_t2 / cap) * 100

        # Stop Loss
        gross_sl = (s["cmp"] - s["sl"]) * qty
        charges_sl = calc_equity_mis_charges(s["cmp"], s["sl"], qty)
        net_sl = gross_sl + charges_sl

        print(f"{s['name']:<12} | {qty:<6} | INR {actual_exposure:<10,.2f} | +INR {net_t1:<8,.2f} (+{roi_t1:>4.1f}%)   | +INR {net_t2:<8,.2f} (+{roi_t2:>4.1f}%)   | -INR {net_sl:<8,.2f}")

print("\n" + "=" * 110)
