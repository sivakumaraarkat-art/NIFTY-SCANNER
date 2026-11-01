"""Scan Nifty 100 and Midcap 150 for 2-Month Swing Momentum & High-Probability Entries."""

import sys
import os
import csv
import time
from datetime import date, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scanners.options_data_provider import get_kite_client

def load_symbols():
    symbols = []
    base_dir = ROOT / "data" / "nse_cap_segments"
    for fname in ["nifty100.csv", "nifty_midcap150.csv"]:
        fpath = base_dir / fname
        if fpath.exists():
            with open(fpath, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    s = row.get("symbol", "").strip().upper()
                    if s and s not in symbols:
                        symbols.append(s)
    return symbols

def calculate_metrics(df):
    if len(df) < 60:
        return None
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
    volume = df["volume"].values

    current_price = float(close[-1])

    # SMAs
    sma20 = float(np.mean(close[-20:]))
    sma50 = float(np.mean(close[-50:]))
    sma200 = float(np.mean(close[-200:])) if len(close) >= 200 else float(np.mean(close))

    # RSI 14
    diff = np.diff(close[-15:])
    gains = np.where(diff > 0, diff, 0)
    losses = np.where(diff < 0, -diff, 0)
    avg_gain = float(np.mean(gains))
    avg_loss = float(np.mean(losses))
    if avg_loss == 0:
        rsi = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))

    # ATR 14
    tr = []
    for i in range(len(close) - 14, len(close)):
        h_l = high[i] - low[i]
        h_pc = abs(high[i] - close[i-1])
        l_pc = abs(low[i] - close[i-1])
        tr.append(max(h_l, h_pc, l_pc))
    atr14 = float(np.mean(tr))

    # Volume expansion
    vol_avg_20 = float(np.mean(volume[-21:-1]))
    vol_ratio = float(volume[-1] / vol_avg_20) if vol_avg_20 > 0 else 1.0

    # Returns
    ret_20d = float(((current_price / close[-20]) - 1.0) * 100.0)
    ret_50d = float(((current_price / close[-50]) - 1.0) * 100.0) if len(close) >= 50 else 0.0

    # 20-day and 52-week highs
    high_20d = float(np.max(high[-20:]))
    high_52w = float(np.max(high[-252:])) if len(high) >= 252 else float(np.max(high))
    dist_from_52w_high = float(((high_52w - current_price) / high_52w) * 100.0)

    score = 0
    setup_name = ""
    reasons = []

    # Trend score (max 30)
    if current_price > sma20 > sma50 > sma200:
        score += 30
        reasons.append("Golden Trend Alignment (Price > 20 > 50 > 200 SMA)")
    elif current_price > sma20 > sma50:
        score += 25
        reasons.append("Bullish Trend Alignment (Price > 20 > 50 SMA)")
    elif current_price > sma50:
        score += 15
        reasons.append("Above 50 SMA")
    else:
        return None  # Disqualify stocks below 50 SMA

    # Momentum & 2-Month trajectory score (max 25)
    if ret_50d >= 12.0:
        score += 15
        reasons.append(f"Strong 2-Month Momentum (+{ret_50d:.1f}%)")
    elif ret_50d >= 5.0:
        score += 10
        reasons.append(f"Positive 2-Month Momentum (+{ret_50d:.1f}%)")

    if ret_20d >= 3.0:
        score += 10
        reasons.append(f"Short-Term Acceleration (+{ret_20d:.1f}% 20d)")

    # RSI score (max 20)
    if 55.0 <= rsi <= 68.0:
        score += 20
        reasons.append(f"Ideal Swing Momentum RSI ({rsi:.1f})")
    elif 50.0 <= rsi < 55.0:
        score += 15
        reasons.append(f"Support Base RSI ({rsi:.1f})")
    elif 68.0 < rsi <= 76.0:
        score += 10
        reasons.append(f"High Momentum Breakout RSI ({rsi:.1f})")

    # Proximity & Pattern Setup (max 25)
    if current_price >= high_20d * 0.985:
        score += 15
        setup_name = "20-Day Range Breakout 🚀"
        reasons.append("At / Near 20-Day High Breakout")
    elif abs(current_price - sma20) / current_price <= 0.025:
        score += 15
        setup_name = "20-SMA Trend Pullback Bounce 📈"
        reasons.append("Support Bounce at 20 SMA")
    elif abs(current_price - sma50) / current_price <= 0.035:
        score += 12
        setup_name = "50-SMA Value Pullback 🛡️"
        reasons.append("Support Bounce at 50 SMA")
    else:
        setup_name = "Consolidation Continuation 📊"

    if vol_ratio >= 1.25:
        score += 10
        reasons.append(f"Volume Surge ({vol_ratio:.1f}x 20d avg)")
    elif vol_ratio >= 0.9:
        score += 5

    if dist_from_52w_high <= 10.0:
        score += 5
        reasons.append(f"Near 52W High ({dist_from_52w_high:.1f}% away)")

    # Stop loss calculation (clamped between 4% and 7.5% for swing trades)
    raw_sl = current_price - (1.5 * atr14)
    risk_pct = (current_price - raw_sl) / current_price
    if risk_pct < 0.04:
        sl = current_price * 0.96
    elif risk_pct > 0.075:
        sl = current_price * 0.925
    else:
        sl = raw_sl

    risk_pts = current_price - sl
    t1 = current_price + (risk_pts * 2.0)  # 1:2 R:R (3-4 weeks)
    t2 = current_price + (risk_pts * 3.5)  # 1:3.5 R:R (2-month target)

    return {
        "price": current_price,
        "score": score,
        "setup": setup_name,
        "rsi": rsi,
        "ret_20d": ret_20d,
        "ret_50d": ret_50d,
        "vol_ratio": vol_ratio,
        "dist_52w": dist_from_52w_high,
        "sl": sl,
        "risk_pct": ((current_price - sl) / current_price) * 100.0,
        "t1": t1,
        "t1_pct": ((t1 - current_price) / current_price) * 100.0,
        "t2": t2,
        "t2_pct": ((t2 - current_price) / current_price) * 100.0,
        "reasons": reasons
    }

def main():
    print("=" * 80)
    print("SCANNING NIFTY 100 & MIDCAP 150 FOR 2-MONTH SWING MOMENTUM SETUPS")
    print("=" * 80)
    kite = get_kite_client()
    symbols = load_symbols()
    print(f"Loaded {len(symbols)} universe symbols.")

    instruments = kite.instruments("NSE")
    token_map = {i["tradingsymbol"]: i["instrument_token"] for i in instruments if i["instrument_type"] == "EQ" and i["segment"] == "NSE"}

    start_date = (date.today() - timedelta(days=320)).isoformat()
    end_date = date.today().isoformat()

    results = []
    print(f"Fetching daily candles for {len(symbols)} stocks...")
    for idx, sym in enumerate(symbols, 1):
        tok = token_map.get(sym)
        if not tok:
            continue
        try:
            records = kite.historical_data(tok, start_date, end_date, "day")
            if not records or len(records) < 60:
                continue
            df = pd.DataFrame(records)
            m = calculate_metrics(df)
            if m and m["score"] >= 70:
                m["symbol"] = sym
                results.append(m)
        except Exception:
            pass
        if idx % 50 == 0:
            print(f"  Processed {idx}/{len(symbols)} stocks...")

    # Rank by score, then 50d return, then volume
    results.sort(key=lambda x: (-x["score"], -x["ret_50d"], -x["vol_ratio"]))

    print("\n" + "=" * 80)
    print(f"TOP QUALIFIED 2-MONTH SWING CANDIDATES ({len(results)} Found)")
    print("=" * 80)

    for i, r in enumerate(results[:10], 1):
        print(f"\n#{i} {r['symbol']} | Score: {r['score']}/100 | Setup: {r['setup']}")
        print(f"    Current Price: Rs {r['price']:.2f} | RSI: {r['rsi']:.1f} | 20d: +{r['ret_20d']:.1f}% | 50d: +{r['ret_50d']:.1f}% | Vol: {r['vol_ratio']:.1f}x")
        print(f"    Entry Level  : Rs {r['price']:.2f}")
        print(f"    Stop Loss    : Rs {r['sl']:.2f} (-{r['risk_pct']:.1f}%)")
        print(f"    Target 1 (1M): Rs {r['t1']:.2f} (+{r['t1_pct']:.1f}%) [R:R 1:2.0]")
        print(f"    Target 2 (2M): Rs {r['t2']:.2f} (+{r['t2_pct']:.1f}%) [R:R 1:3.5]")
        print(f"    Catalysts    : {', '.join(r['reasons'])}")

if __name__ == "__main__":
    main()
