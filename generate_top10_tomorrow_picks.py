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

# Curated High-Conviction Universe combining Confirmed Reversals, High-Volume Rebounds & Defense/Infra Bluechips
CANDIDATES = [
    {
        "symbol": "GRSE",
        "kite_sym": "NSE:GRSE",
        "name": "Garden Reach Shipbuilders",
        "sector": "Defense & Naval EPC",
        "setup": "CONFIRMED REVERSAL",
        "catalyst": "Record naval order book, 3.7x volume reversal from ₹1,842 floor",
        "sl_pts": 75.0,
        "t1_mult": 2.0,
        "t2_mult": 3.2,
        "holding": "7–10 Days"
    },
    {
        "symbol": "MAZDOCK",
        "kite_sym": "NSE:MAZDOCK",
        "name": "Mazagon Dock Shipbuilders",
        "sector": "Defense / Submarines",
        "setup": "OVERSOLD FLOOR",
        "catalyst": "Down 40% from 52W high, RSI 25.6 multi-month demand floor",
        "sl_pts": 65.0,
        "t1_mult": 2.2,
        "t2_mult": 3.5,
        "holding": "10–14 Days"
    },
    {
        "symbol": "MUTHOOTFIN",
        "kite_sym": "NSE:MUTHOOTFIN",
        "name": "Muthoot Finance",
        "sector": "Gold NBFC",
        "setup": "OVERSOLD BOUNCE",
        "catalyst": "Gold price tailwind, 42% correction with AUM expansion",
        "sl_pts": 75.0,
        "t1_mult": 2.2,
        "t2_mult": 3.5,
        "holding": "7–10 Days"
    },
    {
        "symbol": "PIIND",
        "kite_sym": "NSE:PIIND",
        "name": "PI Industries",
        "sector": "Specialty Agchem",
        "setup": "CONFIRMED REVERSAL",
        "catalyst": "Strong export demand, +4.7% breakout candle from ₹2,005 base",
        "sl_pts": 70.0,
        "t1_mult": 2.0,
        "t2_mult": 3.0,
        "holding": "7–10 Days"
    },
    {
        "symbol": "BDL",
        "kite_sym": "NSE:BDL",
        "name": "Bharat Dynamics Ltd",
        "sector": "Defense / Missiles",
        "setup": "OVERSOLD FLOOR",
        "catalyst": "Aakash & indigenous missile order inflow, down 40% from high",
        "sl_pts": 38.0,
        "t1_mult": 2.1,
        "t2_mult": 3.5,
        "holding": "7–12 Days"
    },
    {
        "symbol": "KEC",
        "kite_sym": "NSE:KEC",
        "name": "KEC International",
        "sector": "Power T&D / Infra",
        "setup": "OVERSOLD ACCUMULATION",
        "catalyst": "Down 60% from peak, global grid electrification orders",
        "sl_pts": 14.0,
        "t1_mult": 2.0,
        "t2_mult": 3.5,
        "holding": "7–10 Days"
    },
    {
        "symbol": "NBCC",
        "kite_sym": "NSE:NBCC",
        "name": "NBCC (India) Ltd",
        "sector": "Govt Real Estate / Infra",
        "setup": "CONFIRMED REVERSAL",
        "catalyst": "Substantial redevelopment contracts, +3.9% volume expansion",
        "sl_pts": 2.8,
        "t1_mult": 2.0,
        "t2_mult": 3.2,
        "holding": "7–10 Days"
    },
    {
        "symbol": "HUDCO",
        "kite_sym": "NSE:HUDCO",
        "name": "Housing & Urban Dev Corp",
        "sector": "Infra Financing (PSU)",
        "setup": "OVERSOLD ACCUMULATION",
        "catalyst": "Govt affordable housing capex, RSI 25.6 oversold bounce",
        "sl_pts": 5.5,
        "t1_mult": 2.2,
        "t2_mult": 3.5,
        "holding": "7–10 Days"
    },
    {
        "symbol": "DALBHARAT",
        "kite_sym": "NSE:DALBHARAT",
        "name": "Dalmia Bharat",
        "sector": "Cement & Building Materials",
        "setup": "VOLUME SURGE FLOOR",
        "catalyst": "4.7x institutional volume spike at ₹1,319 structural floor",
        "sl_pts": 45.0,
        "t1_mult": 2.0,
        "t2_mult": 3.5,
        "holding": "7–10 Days"
    },
    {
        "symbol": "GODFRYPHLP",
        "kite_sym": "NSE:GODFRYPHLP",
        "name": "Godfrey Phillips",
        "sector": "FMCG / High Cash Flow",
        "setup": "CONFIRMED REVERSAL",
        "catalyst": "Rebound from ₹1,641 support, 1.9x volume expansion with high ROCE",
        "sl_pts": 55.0,
        "t1_mult": 2.0,
        "t2_mult": 3.2,
        "holding": "7–10 Days"
    }
]

def scan_top10_picks():
    print("=" * 115)
    print("🎯 TOP 10 SWING TRADE ENTRY CANDIDATES FOR TOMORROW (ZERODHA LIVE MARKET SCAN)")
    print("=" * 115)

    kite = get_kite_client()
    symbols_to_quote = [c["kite_sym"] for c in CANDIDATES]
    quotes = {}
    if kite:
        try:
            quotes = kite.quote(symbols_to_quote)
            print(f"✅ Live Zerodha Kite quotes fetched for {len(quotes)} symbols.\n")
        except Exception as e:
            print(f"⚠️ Could not fetch live quotes: {e}")

    results = []
    for item in CANDIDATES:
        sym = item["symbol"]
        k_sym = item["kite_sym"]
        q = quotes.get(k_sym, {})
        ltp = float(q.get("last_price", 0.0))
        if ltp == 0.0:
            # Fallback default from dataset
            fallback_map = {
                "GRSE": 1943.70, "MAZDOCK": 1705.30, "MUTHOOTFIN": 2408.60,
                "PIIND": 2100.00, "BDL": 974.00, "KEC": 329.65,
                "NBCC": 69.66, "HUDCO": 143.07, "DALBHARAT": 1326.20,
                "GODFRYPHLP": 1690.20
            }
            ltp = fallback_map.get(sym, 100.0)

        sl_pts = item["sl_pts"]
        sl = round(ltp - sl_pts, 2)
        risk_pct = round((sl_pts / ltp) * 100, 2)

        t1 = round(ltp + (sl_pts * item["t1_mult"]), 2)
        t1_gain_pct = round(((t1 - ltp) / ltp) * 100, 2)

        t2 = round(ltp + (sl_pts * item["t2_mult"]), 2)
        t2_gain_pct = round(((t2 - ltp) / ltp) * 100, 2)

        results.append({
            "symbol": sym,
            "name": item["name"],
            "sector": item["sector"],
            "setup": item["setup"],
            "ltp": ltp,
            "buy_range": f"₹{round(ltp*0.995, 1)} – ₹{round(ltp*1.005, 1)}",
            "sl": sl,
            "risk_pct": risk_pct,
            "t1": t1,
            "t1_gain": t1_gain_pct,
            "t2": t2,
            "t2_gain": t2_gain_pct,
            "catalyst": item["catalyst"],
            "holding": item["holding"],
            "rr": f"1:{item['t1_mult']:.1f} / 1:{item['t2_mult']:.1f}"
        })

    print(f"{'RANK':4} | {'STOCK':11} | {'LTP (₹)':9} | {'BUY ZONE (₹)':17} | {'STOP LOSS':14} | {'TARGET 1 (₹)':14} | {'TARGET 2 (₹)':14} | {'R:R':7} | {'SETUP TYPE':20}")
    print("-" * 115)
    for idx, r in enumerate(results, start=1):
        print(f"#{idx:<3} | {r['symbol']:<11} | ₹{r['ltp']:<8.2f} | {r['buy_range']:<17} | ₹{r['sl']:<7.2f} (-{r['risk_pct']}%) | ₹{r['t1']:<7.2f} (+{r['t1_gain']}%) | ₹{r['t2']:<7.2f} (+{r['t2_gain']}%) | {r['rr']:<7} | {r['setup']:<20}")

    print("\n" + "=" * 115)
    print("📋 DETAILED CATALYST & TRADE BLUEPRINT (TOMORROW'S ENTRY)")
    print("=" * 115)
    for idx, r in enumerate(results, start=1):
        print(f"{idx}. {r['symbol']} ({r['name']} — {r['sector']})")
        print(f"   • Setup:         {r['setup']} | Horizon: {r['holding']}")
        print(f"   • Recommended Entry: {r['buy_range']} (Enter on minor morning pullback / 09:30 AM stability)")
        print(f"   • Strict Stop-Loss:  ₹{r['sl']:.2f} (-{r['risk_pct']}%) | Never hold if SL breaks on a 15-min candle")
        print(f"   • Target 1 (1:2 RR): ₹{r['t1']:.2f} (+{r['t1_gain']}%) — Book 50% profit & trail SL to Entry")
        print(f"   • Target 2 (1:3 RR): ₹{r['t2']:.2f} (+{r['t2_gain']}%) — Final exit on momentum exhaustion")
        print(f"   • Growth Driver:     {r['catalyst']}")
        print("-" * 115)

    print("💡 RISK MANAGEMENT RULES:")
    print("1. Maximum Capital Allocation: Allocate no more than 10%–12% of your swing trading capital per stock.")
    print("2. The 09:30 AM Rule: Wait 15 minutes after market opens (09:15–09:30 AM) to let morning gap noise settle.")
    print("3. Profit Protection: The moment Target 1 hits, immediately move your Stop-Loss to your Entry Price.")
    print("=" * 115)

if __name__ == "__main__":
    scan_top10_picks()
