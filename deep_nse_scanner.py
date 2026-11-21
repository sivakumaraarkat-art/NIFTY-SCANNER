import sys
from pathlib import Path
from kiteconnect import KiteConnect
import pandas as pd
import numpy as np
import json

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

CACHE_DIR = ROOT / "database" / "market_data_cache"
parquet_files = list(CACHE_DIR.glob("NSE_*_daily.parquet"))
print(f"Found {len(parquet_files)} cached stock histories.")

# Extract symbols
symbol_map = {}
for f in parquet_files:
    # Format: NSE_SYMBOL_daily.parquet
    sym = f.stem.replace("NSE_", "").replace("_daily", "")
    symbol_map[sym] = f

# Get F&O list for high liquidity focus
fo_symbols = set()
fo_file = ROOT / "trader-in" / "fo_list.txt"
if fo_file.exists():
    with open(fo_file, "r", encoding="utf-8") as f:
        fo_symbols = {line.strip() for line in f if line.strip() and not line.startswith("#")}

# Prioritize liquid universe (F&O + liquid midcaps, total ~250 symbols)
target_symbols = [s for s in symbol_map if s in fo_symbols]
if len(target_symbols) < 150:
    target_symbols = list(symbol_map.keys())[:300]

print(f"Targeting {len(target_symbols)} high-liquidity stocks for live scanning...")

# Batch fetch live Zerodha quotes
quotes = {}
batch_size = 100
for i in range(0, len(target_symbols), batch_size):
    batch = [f"NSE:{s}" for s in target_symbols[i:i+batch_size]]
    try:
        q_batch = kite.quote(batch)
        quotes.update(q_batch)
    except Exception as e:
        print(f"Error fetching batch: {e}")

print(f"Received live quotes for {len(quotes)} stocks.")

results = []

for sym in target_symbols:
    k_sym = f"NSE:{sym}"
    q = quotes.get(k_sym)
    if not q:
        continue

    ltp = q.get("last_price", 0.0)
    ohlc = q.get("ohlc", {})
    prev_close = ohlc.get("close", ltp)
    high_p = ohlc.get("high", ltp)
    low_p = ohlc.get("low", ltp)
    vol = q.get("volume", 0)

    if ltp <= 10 or prev_close <= 0:  # Skip illiquid / micro penny stocks
        continue

    # Read historical parquet
    p_file = symbol_map.get(sym)
    if not p_file or not p_file.exists():
        continue

    try:
        df = pd.read_parquet(p_file)
        if len(df) < 50:
            continue

        closes = df["close"].values
        highs = df["high"].values
        lows = df["low"].values
        volumes = df["volume"].values

        # Append live/latest candle if not present
        all_closes = np.append(closes, ltp)
        all_highs = np.append(highs, high_p)
        all_lows = np.append(lows, low_p)

        # 1. Moving Averages
        sma_20 = np.mean(all_closes[-20:])
        sma_50 = np.mean(all_closes[-50:]) if len(all_closes) >= 50 else sma_20
        sma_200 = np.mean(all_closes[-200:]) if len(all_closes) >= 200 else sma_50

        # 2. RSI (14)
        diff = np.diff(all_closes)
        gains = np.maximum(diff, 0)
        losses = np.maximum(-diff, 0)
        avg_gain = np.mean(gains[-14:])
        avg_loss = np.mean(losses[-14:])
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs)) if avg_loss != 0 else 100

        # 3. 52-Week High & Low
        h52 = np.max(all_highs[-250:])
        l52 = np.min(all_lows[-250:])
        drawdown_52w = ((ltp - h52) / h52 * 100)
        gain_from_52w_low = ((ltp - l52) / l52 * 100)

        # 4. Volume comparison
        avg_vol_20 = np.mean(volumes[-20:])
        vol_ratio = (vol / avg_vol_20) if avg_vol_20 > 0 else 1.0

        # 5. Distances
        dist_sma20 = ((ltp - sma_20) / sma_20 * 100)
        dist_sma50 = ((ltp - sma_50) / sma_50 * 100)
        dist_sma200 = ((ltp - sma_200) / sma_200 * 100)

        # 6. Scoring
        # Reversal Score: Oversold RSI (25-45), near 52W low shelf (low downside), stabilizing above 20-DMA
        rev_score = 0
        if 20 <= rsi <= 38:
            rev_score += 35
        elif 38 < rsi <= 48:
            rev_score += 25
        elif rsi < 20:
            rev_score += 30  # Extreme oversold

        if -45 <= drawdown_52w <= -20:
            rev_score += 25  # Substantial discount from peak
        elif drawdown_52w < -45:
            rev_score += 20

        if -5 <= dist_sma20 <= 5:
            rev_score += 20  # Hovering right at 20-DMA pivot
        elif dist_sma20 > 5:
            rev_score += 10

        if -8 <= dist_sma200 <= 5:
            rev_score += 20  # Bouncing right off institutional 200-DMA
        elif dist_sma200 > 5:
            rev_score += 10

        # Momentum Breakout Score
        mom_score = 0
        if 55 <= rsi <= 70:
            mom_score += 35
        if dist_sma20 > 2 and dist_sma50 > 2:
            mom_score += 25
        if dist_sma200 > 0:
            mom_score += 20
        if -10 <= drawdown_52w <= 0:
            mom_score += 20  # Near 52W high breakout

        results.append({
            "symbol": sym,
            "ltp": float(ltp),
            "prev_close": float(prev_close),
            "day_chg_pct": float(((ltp - prev_close)/prev_close*100)),
            "rsi": float(rsi),
            "sma20": float(sma_20),
            "sma50": float(sma_50),
            "sma200": float(sma_200),
            "drawdown_52w": float(drawdown_52w),
            "gain_from_52w_low": float(gain_from_52w_low),
            "dist_sma20": float(dist_sma20),
            "dist_sma200": float(dist_sma200),
            "vol_ratio": float(vol_ratio),
            "rev_score": float(rev_score),
            "mom_score": float(mom_score),
            "is_fo": (sym in fo_symbols)
        })
    except Exception as e:
        continue

# Sort by Reversal Score
top_reversals = sorted(results, key=lambda x: x["rev_score"], reverse=True)[:10]

# Sort by Momentum Score
top_momentum = sorted(results, key=lambda x: x["mom_score"], reverse=True)[:10]

output_payload = {
    "total_scanned": len(results),
    "top_reversals": top_reversals,
    "top_momentum": top_momentum
}

with open("nse_deep_scan_results.json", "w", encoding="utf-8") as f:
    json.dump(output_payload, f, indent=2)

print(f"Deep scan complete across {len(results)} stocks!")
