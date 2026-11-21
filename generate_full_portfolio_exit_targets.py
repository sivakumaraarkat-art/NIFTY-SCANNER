"""
generate_full_portfolio_exit_targets.py
Generates a comprehensive master exit blueprint for all 28 Zerodha equity holdings:
- Target 1 (Intermediate / De-risking level)
- Target 2 (Major Swing / Pre-Budget High)
- Moving Average references (20/50/200 DMA)
- Exact Net P&L at Target 1 and Target 2
- Specific Sell Directive & Action Strategy for next 2-3 months
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
        print("❌ Token or API key file missing.")
        sys.exit(1)

    access_token = token_file.read_text(encoding="utf-8").strip()
    api_key = key_file.read_text(encoding="utf-8").strip()

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

    holdings = kite.holdings()
    active_holdings = [h for h in holdings if (h.get("quantity", 0) + h.get("t1_quantity", 0)) > 0]

    # Target definitions based on technical moving averages, Fibonacci extensions, and seasonal peaks
    # (T1, T2, Strategy Category, Sell Directive, Key Catalyst/MA Reference)
    STOCK_TARGET_RULES = {
        # Current Green Winners
        "ASHOKLEY": (185.00, 205.00, "PROFIT WINNER", "Sell 50% @ T1 (₹185), Trail 50% to T2 (₹205)", "20-DMA trailing, CV volume expansion"),
        "COALINDIA": (430.00, 460.00, "PROFIT WINNER", "Hold for high dividends; Sell 50% @ T1 (₹430)", "Above 200-DMA, highest dividend PSU"),
        "IOC": (155.00, 168.00, "PROFIT WINNER", "Sell 50% @ T1 (₹155), Trail balance with SL @ ₹140", "Refining margin recovery, 8%+ yield"),
        "JPL": (1550.00, 1700.00, "PROFIT WINNER", "Book 40% @ ₹1,550, Trail 60% with 20-DMA", "All-time momentum run, lock in gains"),

        # Immediate Turnaround Candidates (Loss < 25%)
        "PCBL": (315.00, 350.00, "HIGH CONVICTION", "Hold to T1 (₹315); Sell 50%, Trail 50% to T2", "200-DMA reclaimed, EV carbon growth"),
        "LODHA": (1320.00, 1420.00, "HIGH CONVICTION", "Sell 40% at Breakeven (₹1,320); Sell 60% @ T2", "Festive pre-sales peak, 200-DMA shelf"),
        "NITYAS": (75.00, 85.00, "CONSUMER SWING", "Exit 100% at Breakeven (₹75.00 - ₹80.00)", "Wedding season demand, thin liquidity"),
        "COCHINSHIP": (1430.00, 1680.00, "HIGH CONVICTION", "Sell 30% @ ₹1,430 (Avg), 40% @ ₹1,500, 30% @ T2", "50/200-DMA recovery, Pre-Budget defense surge"),

        # Mid-Range Turnarounds (Loss 25% - 55%)
        "BAJAJHFL": (98.00, 112.00, "CORE FINANCIAL", "Sell 50% @ T1 (₹98), Exit balance at Breakeven (₹109)", "Anchor lock-in selling settling down"),
        "SUZLON": (44.00, 52.00, "RENEWABLE ENERGY", "Sell 40% @ T1 (₹44.00); Sell 60% near Breakeven (₹52)", "50-DMA test, record 5.5 GW order book"),
        "ECOSMOBLTY": (135.00, 155.00, "MOMENTUM SWING", "Sell 50% @ T1 (₹135), Exit balance @ T2 (₹155)", "Corporate travel & wedding season"),
        "IEX": (125.00, 140.00, "DE-RISK ON BOUNCE", "Sell 40% @ T1 (₹125), Exit balance @ T2 (₹140)", "Market coupling overhang, trim large weight"),
        "NTPCGREEN": (102.00, 118.00, "CLEAN ENERGY", "Sell 50% @ T1 (₹102), Trail balance @ ₹118", "Post-listing discovery base building"),
        "IRB": (20.50, 23.50, "INFRA REBOUND", "Sell 60% @ T1 (₹20.50), Exit balance @ T2 (₹23.50)", "Heavy debt, exit on mean reversion to 200-DMA"),
        "IMAGICAA": (52.00, 60.00, "CONSUMER CYCLICAL", "Sell 50% @ T1 (₹52), Exit balance @ T2 (₹60)", "Holiday season theme park footfalls"),
        "EPACK": (195.00, 225.00, "EMS REBOUND", "Sell 50% @ T1 (₹195), Reduce balance @ T2 (₹225)", "Losses widening, trim on bounce"),
        "ELECTCAST": (88.00, 108.00, "VALUE INFRA", "Sell 50% @ T1 (₹88), Hold balance to T2 (₹108)", "Water pipe leader, oversold bounce"),

        # Microcaps & Penny Stocks (High Drawdown / Tax-Loss Harvesting)
        "MISHTANN": (4.50, 5.50, "EXIT ON BOUNCE", "Exit 100% on any spike to ₹4.50 – ₹5.00", "Microcap penny, recover salvage cash"),
        "HAPPSTMNDS": (375.00, 420.00, "IT REDUCE", "Sell 50% @ T1 (₹375), Exit balance @ T2 (₹420)", "Growth normalization, reallocate to leaders"),
        "MADHAVIPL": (8.50, 10.50, "TAX-LOSS / EXIT", "Exit 100% on any relief rally to ₹8.50+", "Severe breakdown, salvage remaining ₹9k"),
        "DREAMFOLKS": (75.00, 90.00, "EXIT ON BOUNCE", "Exit 100% on bounce to ₹75 – ₹85", "Airport lounge structural disruption"),
        "GTLINFRA": (1.45, 1.80, "PENNY EXIT", "Exit 100% on penny bounce; Tax-loss harvest", "Severe debt, salvage capital"),
        "ALOKINDS": (11.50, 14.00, "PENNY EXIT", "Exit 100% on bounce to ₹11.50 – ₹13.00", "Persistent losses, exit to free ₹4k-5k"),
        "SALASAR": (6.00, 7.50, "PENNY EXIT", "Exit 100% on bounce to ₹6.00+; Tax-loss harvest", "Penny breakdown, salvage cash"),
        "SAMPRE": (6.50, 8.00, "PENNY EXIT", "Exit 100% on bounce to ₹6.50+; Tax-loss harvest", "Illiquid penny, do not hold"),
        "MAHACORP": (0.50, 0.65, "PENNY EXIT", "Exit 100% on any uptick; Tax-loss harvest", "Dead penny, salvage remaining cash"),
        "STANCAP": (0.50, 0.65, "PENNY EXIT", "Exit 100% on any uptick; Tax-loss harvest", "Dead penny, salvage remaining cash"),
        "AKSHAR": (0.65, 0.85, "PENNY EXIT", "Exit 100% on any uptick; Tax-loss harvest", "Dead penny, salvage remaining cash"),
    }

    results = []
    for h in active_holdings:
        sym = h.get("tradingsymbol")
        qty = h.get("quantity", 0) + h.get("t1_quantity", 0)
        avg = h.get("average_price", 0.0)
        ltp = h.get("last_price", 0.0)
        inv = qty * avg
        val = qty * ltp
        pnl = val - inv

        rule = STOCK_TARGET_RULES.get(sym, (round(ltp * 1.15, 2), round(ltp * 1.30, 2), "GENERAL", "Sell on 15-30% gain", "Standard swing target"))
        t1, t2, cat, action, ref = rule

        t1_val = qty * t1
        t1_pnl = t1_val - inv
        t1_pct = (t1 - ltp) / ltp * 100 if ltp > 0 else 0

        t2_val = qty * t2
        t2_pnl = t2_val - inv
        t2_pct = (t2 - ltp) / ltp * 100 if ltp > 0 else 0

        results.append({
            "sym": sym, "qty": qty, "avg": avg, "ltp": ltp,
            "inv": inv, "val": val, "pnl": pnl,
            "t1": t1, "t1_pct": t1_pct, "t1_pnl": t1_pnl,
            "t2": t2, "t2_pct": t2_pct, "t2_pnl": t2_pnl,
            "cat": cat, "action": action, "ref": ref
        })

    # Group into 4 Actionable Categories
    cats = {
        "1. CORE WINNERS (TRAIL PROFIT & HARVEST)": [r for r in results if "PROFIT WINNER" in r["cat"]],
        "2. HIGH-CONVICTION REBOUND LEADERS (TURNAROUND TO PROFIT)": [r for r in results if "HIGH CONVICTION" in r["cat"]],
        "3. MIDCAP REBOUNDS & VALUE CYCLICALS (TRIM ON BOUNCE)": [r for r in results if r["cat"] in ["CORE FINANCIAL", "RENEWABLE ENERGY", "MOMENTUM SWING", "DE-RISK ON BOUNCE", "CLEAN ENERGY", "INFRA REBOUND", "CONSUMER CYCLICAL", "EMS REBOUND", "VALUE INFRA", "IT REDUCE", "CONSUMER SWING"]],
        "4. PENNY STOCKS & HARVEST CANDIDATES (EXIT ON RELIEF BOUNCE)": [r for r in results if "PENNY" in r["cat"] or "TAX-LOSS" in r["cat"] or "EXIT ON BOUNCE" in r["cat"]]
    }

    print("=" * 110)
    print("📋 MASTER PORTFOLIO EXIT BLUEPRINT: ALL 28 HOLDINGS (NEXT 2 TO 3 MONTHS)")
    print("=" * 110)

    for cat_title, stock_list in cats.items():
        print(f"\n{cat_title} ({len(stock_list)} Stocks)")
        print("-" * 110)
        print(f"{'SYMBOL':11} | {'QTY':5} | {'LTP (₹)':9} | {'AVG (₹)':9} | {'CUR P&L (₹)':12} | {'TARGET 1 (₹)':12} | {'P&L @ T1 (₹)':13} | {'TARGET 2 (₹)':12} | {'P&L @ T2 (₹)':13}")
        print("-" * 110)
        for s in stock_list:
            sign_cur = "+" if s["pnl"] >= 0 else ""
            sign_t1 = "+" if s["t1_pnl"] >= 0 else ""
            sign_t2 = "+" if s["t2_pnl"] >= 0 else ""
            print(f"{s['sym']:<11} | {s['qty']:<5} | ₹{s['ltp']:7.2f} | ₹{s['avg']:7.2f} | {sign_cur}₹{s['pnl']:10.2f} | ₹{s['t1']:7.2f} ({s['t1_pct']:+4.1f}%) | {sign_t1}₹{s['t1_pnl']:10.2f} | ₹{s['t2']:7.2f} ({s['t2_pct']:+4.1f}%) | {sign_t2}₹{s['t2_pnl']:10.2f}")
            print(f"   ↳ Action Directive: {s['action']} | Reference: {s['ref']}")

    print("\n" + "=" * 110)

except Exception as e:
    import traceback
    print(f"❌ Error: {e}")
    traceback.print_exc()
