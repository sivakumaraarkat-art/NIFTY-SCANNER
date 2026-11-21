"""
Morning 09:25 AM Breakout & Volume Surge Scanner for Top 1 Lakh Intraday Candidates.
Compares live 15-minute opening volume and breakout against opening high.
"""
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scanners.options_data_provider import get_kite_client

WATCHLIST = [
    {"sym": "NSE:COCHINSHIP", "name": "Cochin Shipyard", "trigger": 1240.0, "lot_mis_1l": 400},
    {"sym": "NSE:GRSE", "name": "Garden Reach Shipbuilders", "trigger": 2162.0, "lot_mis_1l": 230},
    {"sym": "NSE:MAZDOCK", "name": "Mazagon Dock", "trigger": 1835.0, "lot_mis_1l": 270},
    {"sym": "NSE:MUTHOOTFIN", "name": "Muthoot Finance", "trigger": 2745.0, "lot_mis_1l": 180},
    {"sym": "NSE:BDL", "name": "Bharat Dynamics", "trigger": 985.0, "lot_mis_1l": 500},
]

def scan_morning_setups():
    print("=" * 85)
    print("🚀 MORNING LIVE BREAKOUT & MOMENTUM RANKER (09:25 AM CHECK)")
    print(f"⏰ Scan Time: {datetime.now().strftime('%d-%b-%Y %I:%M:%S %p')}")
    print("=" * 85)

    kite = get_kite_client()
    if not kite:
        print("[!] Kite client could not be initialized.")
        return

    symbols = [w["sym"] for w in WATCHLIST]
    quotes = kite.quote(symbols)

    scored = []
    for w in WATCHLIST:
        sym = w["sym"]
        d = quotes.get(sym, {})
        ltp = d.get("last_price", 0.0)
        ohlc = d.get("ohlc", {})
        open_p = ohlc.get("open", ltp)
        high_p = ohlc.get("high", ltp)
        low_p = ohlc.get("low", ltp)
        prev_close = ohlc.get("close", ltp)

        chg_pct = ((ltp - prev_close) / prev_close * 100) if prev_close else 0.0
        open_to_curr = ((ltp - open_p) / open_p * 100) if open_p else 0.0
        dist_to_high = ((high_p - ltp) / high_p * 100) if high_p else 0.0
        volume = d.get("volume", 0)

        # Breakout status
        is_above_trigger = ltp >= w["trigger"]
        is_near_day_high = dist_to_high <= 0.3  # Trading within 0.3% of day's high
        is_green_open = ltp > open_p

        # Momentum Score (0 - 100)
        score = 50
        if is_green_open: score += 20
        if is_above_trigger: score += 20
        if is_near_day_high: score += 10
        if chg_pct > 2.0: score += 10

        scored.append({
            "name": w["name"],
            "sym": sym,
            "ltp": ltp,
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "chg_pct": chg_pct,
            "open_to_curr": open_to_curr,
            "trigger": w["trigger"],
            "is_above_trigger": is_above_trigger,
            "volume": volume,
            "qty_mis": w["lot_mis_1l"],
            "score": score
        })

    # Rank by Momentum Score
    scored.sort(key=lambda x: x["score"], reverse=True)

    print(f"{'Rank':<4} | {'Stock Name':<20} | {'Live LTP':<10} | {'Day Chg%':<8} | {'Breakout?':<11} | {'Score':<6} | {'MIS Qty (1L)':<12}")
    print("-" * 85)
    for i, s in enumerate(scored, 1):
        bo_str = "YES 🔥" if s["is_above_trigger"] else f"No (<{s['trigger']:.0f})"
        badge = "🥇" if i == 1 else ("🥈" if i == 2 else "🥉")
        print(f"{badge} #{i:<2} | {s['name']:<20} | Rs.{s['ltp']:<7.2f} | {s['chg_pct']:+6.2f}% | {bo_str:<11} | {s['score']:<6} | {s['qty_mis']:<12}")

    print("=" * 85)
    winner = scored[0]
    print(f"🏆 #1 TOP PICK TO BUY: {winner['name']} ({winner['sym']})")
    print(f"   • Recommended Action: BUY {winner['qty_mis']} Shares in MIS")
    print(f"   • Current Price: Rs.{winner['ltp']:.2f} | Opening Trigger: Rs.{winner['trigger']:.2f}")
    print(f"   • Target 1: +3.0% (Exit/Trail) | Mandatory Square-Off: 3:20 PM IST")
    print("=" * 85)

if __name__ == "__main__":
    scan_morning_setups()
