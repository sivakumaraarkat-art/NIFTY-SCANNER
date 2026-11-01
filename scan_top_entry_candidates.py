"""Scan top liquid stocks for high-conviction entry setups."""

import sys
from datetime import date, timedelta
from pathlib import Path
import csv
import pandas as pd

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from configuration.swing_trade_settings import load_settings
from zerodha_market_data.zerodha_connection import create_zerodha_client
from historical_market_data.technical_indicator_calculator import add_technical_indicators
from swing_strategies.swing_setup_engine import generate_setup_candidates
from trade_selection.swing_candidate_ranker import rank_trade_candidates

def load_universe_symbols():
    symbols = []
    for fname in ["nifty100.csv", "nifty_midcap150.csv"]:
        fpath = ROOT / "data" / "nse_cap_segments" / fname
        if fpath.exists():
            with open(fpath, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    sym = row.get("symbol", "").strip().upper()
                    if sym and sym not in symbols:
                        symbols.append(sym)
    return symbols

def main():
    print("==================================================================")
    print("LIVE STOCK SWING & BREAKOUT ENTRY SCANNER")
    print("==================================================================")

    settings = load_settings()
    kite = create_zerodha_client(settings)
    print("[1] Zerodha Kite connected.")

    # Load instruments mapping
    print("[2] Fetching NSE instruments...")
    nse_instruments = kite.instruments("NSE")
    inst_map = {
        i["tradingsymbol"]: i["instrument_token"]
        for i in nse_instruments
        if i["instrument_type"] == "EQ" and i["segment"] == "NSE"
    }

    symbols = load_universe_symbols()
    print(f"[3] Scanning {len(symbols)} NIFTY 100 + Midcap 150 stocks...")

    start_date = (date.today() - timedelta(days=220)).isoformat()
    end_date = date.today().isoformat()

    frames = {}
    success_count = 0
    for sym in symbols:
        token = inst_map.get(sym)
        if not token:
            continue
        try:
            records = kite.historical_data(
                instrument_token=token,
                from_date=start_date,
                to_date=end_date,
                interval="day",
            )
            if not records or len(records) < 60:
                continue
            df = pd.DataFrame(records)
            df["date"] = pd.to_datetime(df["date"])
            df = add_technical_indicators(df)
            frames[sym] = df
            success_count += 1
        except Exception as e:
            continue

    print(f"[4] Loaded technical indicators for {success_count} stocks.")

    # Generate setup candidates (minimum score lowered to 65 for wide visibility)
    # We create a temporary settings with min score 65
    from dataclasses import replace
    scan_settings = replace(settings, minimum_candidate_score=65.0)

    candidates = generate_setup_candidates(frames, scan_settings)
    print(f"[5] Setups identified: {len(candidates)}")

    ranked = rank_trade_candidates(candidates, scan_settings)
    print(f"[6] Top qualified trade setups: {len(ranked)}")
    print("==================================================================")

    if not ranked:
        print("No candidates met the minimum score threshold (>= 65).")
        return

    # Sort and display unique top symbols
    seen = set()
    unique_ranked = []
    for c in ranked:
        if c["symbol"] not in seen:
            seen.add(c["symbol"])
            unique_ranked.append(c)

    for i, c in enumerate(unique_ranked[:15], 1):
        risk_pct = ((c['entry'] - c['stop_loss']) / c['entry']) * 100 if c['entry'] else 0
        print(f"\n{i}. {c['symbol']} | Setup: {c.get('setup_type', 'Swing Watch')} | Score: {c['score']}/100")
        print(f"   Entry: Rs {c['entry']:.2f} | Stop Loss: Rs {c['stop_loss']:.2f} (Risk: {risk_pct:.1f}%)")
        print(f"   Targets: T1: Rs {c.get('target_1', 0):.2f} (R:R {c.get('risk_reward', 0):.1f}) | T2: Rs {c.get('target_2', 0):.2f}")
        print(f"   Reasons: {', '.join(c.get('reasons', []))}")

if __name__ == "__main__":
    main()
