import sys
from pathlib import Path
from kiteconnect import KiteConnect
import numpy as np
import json

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

with open(ROOT / "trader-in" / "fo_list.txt", "r", encoding="utf-8") as f:
    symbols = [line.strip() for line in f if line.strip() and not line.startswith("#")]

print(f"Total F&O symbols to scan: {len(symbols)}")

# Batch query quotes (max 500 per call on Kite)
nse_symbols = [f"NSE:{s}" for s in symbols]
quotes = {}
batch_size = 100
for i in range(0, len(nse_symbols), batch_size):
    batch = nse_symbols[i:i+batch_size]
    q_batch = kite.quote(batch)
    quotes.update(q_batch)

print(f"Successfully received quotes for {len(quotes)} symbols.")

scored = []
for s in symbols:
    k_sym = f"NSE:{s}"
    d = quotes.get(k_sym)
    if not d:
        continue

    ltp = d.get("last_price", 0.0)
    ohlc = d.get("ohlc", {})
    prev_close = ohlc.get("close", ltp)
    open_p = ohlc.get("open", ltp)
    high_p = ohlc.get("high", ltp)
    low_p = ohlc.get("low", ltp)
    volume = d.get("volume", 0)

    if ltp <= 0 or prev_close <= 0:
        continue

    day_chg_pct = (ltp - prev_close) / prev_close * 100

    # Intraday range & position within day's range
    day_range = high_p - low_p
    range_pos = (ltp - low_p) / day_range if day_range > 0 else 0.5

    scored.append({
        "symbol": s,
        "ltp": ltp,
        "prev_close": prev_close,
        "day_chg_pct": day_chg_pct,
        "high": high_p,
        "low": low_p,
        "volume": volume,
        "range_pos": range_pos,
        "inst_token": d.get("instrument_token")
    })

print(f"Parsed {len(scored)} liquid F&O stocks.")

with open("fo_scanned_quotes.json", "w", encoding="utf-8") as f:
    json.dump(scored, f, indent=2)
