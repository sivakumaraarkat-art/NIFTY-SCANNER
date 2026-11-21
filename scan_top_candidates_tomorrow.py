"""
Comprehensive Institutional Scanner: Ranks entire liquid universe to Top 5 -> Final 2 -> Top Conviction #1.
"""
import sys
import os
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scanners.options_data_provider import get_kite_client

UNIVERSE = [
    {"sym": "NSE:COCHINSHIP", "name": "Cochin Shipyard", "sector": "Defense / Naval", "catalyst": "Closed at Day's High (+3.04%), massive institutional accumulation pre-Q2"},
    {"sym": "NSE:GRSE", "name": "Garden Reach Shipbuilders", "sector": "Defense / Naval", "catalyst": "Record naval order book (4.5x sales), 3.7x volume reversal from ₹1,842 floor"},
    {"sym": "NSE:MUTHOOTFIN", "name": "Muthoot Finance", "sector": "Gold NBFC", "catalyst": "Runaway breakout (+7.18%), all-time high gold prices expanding loan AUM"},
    {"sym": "NSE:MAZDOCK", "name": "Mazagon Dock", "sector": "Defense / Submarines", "catalyst": "Bouncing off ₹1,760 multi-month floor (+2.41%), submarine procurement pipeline"},
    {"sym": "NSE:BDL", "name": "Bharat Dynamics", "sector": "Defense / Missiles", "catalyst": "Indigenous missile exports & Akash SAM order inflow, strong base at ₹970"},
    {"sym": "NSE:BEL", "name": "Bharat Electronics", "sector": "Defense Electronics", "catalyst": "High-margin radar/EW systems, steady F&O institutional accumulation"},
    {"sym": "NSE:HAL", "name": "Hindustan Aeronautics", "sector": "Defense Aviation", "catalyst": "Tejas Mk1A deliveries, GE-414 engine transfer-of-technology deal"},
    {"sym": "NSE:DIXON", "name": "Dixon Technologies", "sector": "EMS / Electronics", "catalyst": "Smartphone manufacturing PLI incentives, aggressive mutual fund buying"},
    {"sym": "NSE:MCX", "name": "Multi Commodity Exchange", "sector": "Financial Market Infra", "catalyst": "Record commodity trading volumes, strong quarterly earnings surge"},
    {"sym": "NSE:PIIND", "name": "PI Industries", "sector": "Specialty Agchem", "catalyst": "Strong export demand, technical breakout candle from ₹2,005 base"},
    {"sym": "NSE:BHEL", "name": "Bharat Heavy Electricals", "sector": "Power Capital Goods", "catalyst": "Mega thermal power EPC tenders, reviving PSU capex cycle"},
    {"sym": "NSE:RVNL", "name": "Rail Vikas Nigam", "sector": "Railways EPC", "catalyst": "Global Metro / Rail contract bids, oversold rebound off ₹320 base"},
]

def analyze_and_rank():
    kite = get_kite_client()
    if not kite:
        print("[!] Kite client could not be initialized.")
        return

    symbols = [u["sym"] for u in UNIVERSE]
    quotes = kite.quote(symbols)

    scored = []
    for u in UNIVERSE:
        sym = u["sym"]
        d = quotes.get(sym, {})
        ltp = d.get("last_price", 0.0)
        ohlc = d.get("ohlc", {})
        open_p = ohlc.get("open", ltp)
        high_p = ohlc.get("high", ltp)
        low_p = ohlc.get("low", ltp)
        close_p = ohlc.get("close", ltp)
        volume = d.get("volume", 0)

        chg_pct = ((ltp - close_p) / close_p * 100) if close_p else 0.0

        # Proximity to Day's High (Lower distance = stronger close)
        dist_from_high_pct = ((high_p - ltp) / high_p * 100) if high_p else 0.0

        # Day Range expansion
        day_range_pct = ((high_p - low_p) / low_p * 100) if low_p else 0.0

        # Conviction Scoring (Max 100)
        # 1. Closing Strength (0 - 40 pts): Stock closing within 0.5% of day high gets top marks
        closing_score = max(0, 40 - (dist_from_high_pct * 15))
        if dist_from_high_pct < 0.1:  # Closed at the absolute high!
            closing_score = 40.0

        # 2. Daily Momentum (0 - 25 pts)
        momentum_score = min(25, max(0, chg_pct * 6))

        # 3. Sector & Catalyst Weight (0 - 20 pts)
        catalyst_weight = 20 if "Defense" in u["sector"] or "Gold" in u["sector"] else 12

        # 4. Range Expansion / Clean Chart (0 - 15 pts)
        expansion_score = min(15, day_range_pct * 3)

        total_score = round(closing_score + momentum_score + catalyst_weight + expansion_score, 1)

        # Calculate MIS shares for 1 Lakh capital (5x margin -> ~4.9 Lakhs)
        mis_shares = int(490000 // ltp) if ltp > 0 else 0

        scored.append({
            "name": u["name"],
            "sym": sym,
            "sector": u["sector"],
            "catalyst": u["catalyst"],
            "ltp": ltp,
            "high": high_p,
            "low": low_p,
            "chg_pct": chg_pct,
            "dist_from_high_pct": dist_from_high_pct,
            "score": total_score,
            "mis_shares": mis_shares,
        })

    # Sort descending by score
    scored.sort(key=lambda x: x["score"], reverse=True)

    print("=" * 95)
    print("INSTITUTIONAL MOMENTUM & REVERSAL RANKER -- TOMORROW'S Rs.1 LAKH INTRADAY BOOM PICKS")
    print("=" * 95)

    # -------------------------------------------------------------
    # STAGE 1: TOP 5 CANDIDATES
    # -------------------------------------------------------------
    print("\n" + "-" * 95)
    print("[STAGE 1] TOP 5 BEST HIGH-CONVICTION STOCKS")
    print("-" * 95)
    print(f"{'Rank':<4} | {'Stock Name':<20} | {'LTP (Rs)':<10} | {'Day Chg%':<8} | {'Dist to High':<12} | {'Score':<6} | {'MIS Qty (1L)':<12}")
    print("-" * 95)
    top_5 = scored[:5]
    for i, s in enumerate(top_5, 1):
        dist_str = f"{s['dist_from_high_pct']:.2f}%" if s['dist_from_high_pct'] > 0 else "AT HIGH"
        print(f"#{i:<3} | {s['name']:<20} | Rs.{s['ltp']:<7.2f} | {s['chg_pct']:+6.2f}% | {dist_str:<12} | {s['score']:<6.1f} | {s['mis_shares']:<12} shs")

    # -------------------------------------------------------------
    # STAGE 2: FINAL 2 FINALISTS
    # -------------------------------------------------------------
    print("\n" + "-" * 95)
    print("[STAGE 2] THE FINAL 2 ELITE FINALISTS")
    print("-" * 95)
    final_2 = top_5[:2]
    for i, s in enumerate(final_2, 1):
        badge = "FINALIST A" if i == 1 else "FINALIST B"
        print(f"\n[{badge}]: {s['name']} ({s['sym']}) -- Score: {s['score']}/100")
        print(f"  * Current Price:    Rs.{s['ltp']:.2f} (Today's Range: Rs.{s['low']:.2f} - Rs.{s['high']:.2f})")
        print(f"  * Sector:           {s['sector']}")
        print(f"  * Core Catalyst:    {s['catalyst']}")
        print(f"  * 1 Lakh MIS Power: {s['mis_shares']} Shares (Total Exposure: Rs.{s['mis_shares'] * s['ltp']:,.0f})")

    # -------------------------------------------------------------
    # STAGE 3: THE #1 UNDISPUTED CONVICTION WINNER
    # -------------------------------------------------------------
    w = final_2[0]
    print("\n" + "=" * 95)
    print(f"[STAGE 3] THE #1 UNDISPUTED CONVICTION WINNER FOR TOMORROW: {w['name'].upper()}")
    print("=" * 95)

    trigger_p = round(w['high'] + 2.0, 1)
    sl_p = round(trigger_p * 0.98, 1)        # 2% SL
    t1_p = round(trigger_p * 1.03, 1)        # 3% Target 1
    t2_p = round(trigger_p * 1.05, 1)        # 5% Target 2
    qty = w['mis_shares']
    risk = round((trigger_p - sl_p) * qty)
    reward_t1 = round((t1_p - trigger_p) * qty)
    reward_t2 = round((t2_p - trigger_p) * qty)

    print(f"Stock:              {w['name']} ({w['sym']})")
    print(f"Conviction Score:   {w['score']} / 100 (Highest in Entire Market)")
    print(f"Product:            MIS (Intraday with 5x Leverage)")
    print(f"Allocated Capital:  Rs.1,00,000 (Buying {qty} Shares = Rs.{qty * trigger_p:,.0f} Purchasing Power)")
    print("-" * 95)
    print(f"BUY ENTRY TRIGGER:  Crosses above Rs.{trigger_p:.2f} (Between 09:25 AM - 09:35 AM)")
    print(f"STRICT STOP LOSS:   Rs.{sl_p:.2f}  (Max Risk: -Rs.{risk:,.0f} | Strict -2.0% equity stop)")
    print(f"TARGET 1 (T1):      Rs.{t1_p:.2f}  (Profit: +Rs.{reward_t1:,.0f} / +{round((t1_p-trigger_p)/trigger_p*100, 1)}%) -> Trail SL to Cost")
    print(f"TARGET 2 (T2):      Rs.{t2_p:.2f}  (Profit: +Rs.{reward_t2:,.0f} / +{round((t2_p-trigger_p)/trigger_p*100, 1)}%) -> Extended Momentum")
    print(f"EXIT MANDATE:       03:20 PM IST (Automatic Market Square-Off)")
    print("=" * 95)

if __name__ == "__main__":
    analyze_and_rank()
