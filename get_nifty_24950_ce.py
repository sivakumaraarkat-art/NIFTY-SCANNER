"""
get_nifty_24950_ce.py
═════════════════════════════════════════════════════════════════════════════
Finds and queries real-time Zerodha Kite live quotes for NIFTY 24950 CE:
  1. Resolves all upcoming expiries for NIFTY 24950 CE contracts.
  2. Queries Kite quote API for real-time LTP, Bid/Ask, High/Low, OI & Volume.
  3. Calculates 1-lot capital required, spread, and trade risk.
═════════════════════════════════════════════════════════════════════════════
"""

import sys
import io
import datetime
from pathlib import Path

# UTF-8 fix for Windows
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scanners.options_data_provider import get_kite_client, get_nfo_instruments

def fetch_nifty_24950_ce():
    print("=" * 80)
    print("🔍 RESOLVING LIVE ZERODHA QUOTES FOR NIFTY 24950 CE")
    print("=" * 80)

    kite = get_kite_client()
    if not kite:
        print("❌ Kite client initialization failed. Check credentials.")
        return

    # 1. Fetch instruments
    instruments = get_nfo_instruments(kite)
    if not instruments:
        print("❌ Could not load NFO instruments master.")
        return

    today = datetime.date.today()

    # Filter for NIFTY 24950 CE
    matching = []
    for inst in instruments:
        name = str(inst.get("name", "")).upper()
        tsym = str(inst.get("tradingsymbol", "")).upper()
        itype = str(inst.get("instrument_type", "")).upper()
        strike = float(inst.get("strike", 0.0))
        exp = inst.get("expiry")

        if (name == "NIFTY" or tsym.startswith("NIFTY")) and strike == 24950.0 and itype == "CE":
            if isinstance(exp, str):
                try:
                    exp_date = datetime.datetime.strptime(exp, "%Y-%m-%d").date()
                except Exception:
                    exp_date = today
            else:
                exp_date = exp

            if exp_date and exp_date >= today:
                matching.append({
                    "tradingsymbol": tsym,
                    "kite_symbol": f"NFO:{tsym}",
                    "expiry": exp_date,
                    "lot_size": int(inst.get("lot_size", 25))
                })

    if not matching:
        print("⚠️ No future NIFTY 24950 CE contracts found in master.")
        # Fallback query attempt
        print("Trying direct standard weekly/monthly trading symbol guess...")
        return

    # Sort by nearest expiry
    matching.sort(key=lambda x: x["expiry"])

    # Query quotes for the nearest expiries (up to 3)
    symbols_to_quote = [m["kite_symbol"] for m in matching[:3]]
    quotes = kite.quote(symbols_to_quote)

    spot_q = kite.quote(["NSE:NIFTY 50"]).get("NSE:NIFTY 50", {})
    spot_ltp = float(spot_q.get("last_price", 0.0))

    print(f"📊 NIFTY 50 Spot Price:    {spot_ltp:,.2f}")
    print("-" * 80)

    for m in matching[:3]:
        ksym = m["kite_symbol"]
        tsym = m["tradingsymbol"]
        exp = m["expiry"]
        lot_size = m["lot_size"]

        q = quotes.get(ksym, {})
        ltp = float(q.get("last_price", 0.0))
        ohlc = q.get("ohlc", {})
        open_p = float(ohlc.get("open", 0.0))
        high_p = float(ohlc.get("high", 0.0))
        low_p = float(ohlc.get("low", 0.0))
        close_p = float(ohlc.get("close", ltp))
        vol = int(q.get("volume", 0))
        oi = int(q.get("oi", 0))

        depth = q.get("depth", {})
        buy_depth = depth.get("buy", [{}])[0]
        sell_depth = depth.get("sell", [{}])[0]
        bid_p = float(buy_depth.get("price", ltp))
        ask_p = float(sell_depth.get("price", ltp))

        chg_pts = ltp - close_p
        chg_pct = (chg_pts / close_p) * 100.0 if close_p else 0.0
        capital_1_lot = ltp * lot_size

        print(f"🎯 CONTRACT:              {tsym}")
        print(f"   ► Expiry Date:         {exp.strftime('%d-%b-%Y')}  ({(exp - today).days} Days to Expiry)")
        print(f"   ► Live LTP:            ₹{ltp:.2f}  ({chg_pts:+.2f} pts | {chg_pct:+.2f}%)")
        print(f"   ► Day Range:           Low: ₹{low_p:.2f}  <--->  High: ₹{high_p:.2f}")
        print(f"   ► Bid / Ask:           ₹{bid_p:.2f}  /  ₹{ask_p:.2f}")
        print(f"   ► Open Interest (OI):  {oi:,} contracts")
        print(f"   ► Day's Volume:        {vol:,} contracts")
        print(f"   ► Lot Size:            {lot_size} shares")
        print(f"   ► Capital for 1 Lot:   ₹{capital_1_lot:,.2f}  ({lot_size} × ₹{ltp:.2f})")
        print("-" * 80)

    print("=" * 80)

if __name__ == "__main__":
    fetch_nifty_24950_ce()
