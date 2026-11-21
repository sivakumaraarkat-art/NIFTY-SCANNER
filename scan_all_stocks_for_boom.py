"""
scan_all_stocks_for_boom.py
===========================
Comprehensive Multi-Factor Intraday Scanner across all NSE F&O Equities
to identify the #1 High-Conviction "BOOM" Candidate for Today's Intraday Session.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# UTF-8 fix for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent

# 1. Initialize Kite Connect
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()

from kiteconnect import KiteConnect
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

# 2. Load F&O Universe
with open(ROOT / "trader-in" / "fo_list.txt", "r", encoding="utf-8") as f:
    symbols = [line.strip() for line in f if line.strip() and not line.startswith("#")]

symbols = [s for s in symbols if s not in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]]
print(f"[*] Loaded {len(symbols)} F&O symbols to scan.")

# 3. Batch Fetch Quotes
nse_symbols = [f"NSE:{s}" for s in symbols]
quotes = {}
batch_size = 100
for i in range(0, len(nse_symbols), batch_size):
    batch = nse_symbols[i:i+batch_size]
    quotes.update(kite.quote(batch))

nifty_q = kite.quote(["NSE:NIFTY 50"]).get("NSE:NIFTY 50", {})
n_ohlc = nifty_q.get("ohlc", {})
n_open = n_ohlc.get("open", 25323.15)
n_close = n_ohlc.get("close", 25227.95)
nifty_move = ((n_close - n_open) / n_open * 100) if n_open else -0.38

print(f"[*] Benchmark NIFTY 50 Yesterday: Open={n_open:.2f}, Close={n_close:.2f}, Move={nifty_move:+.2f}%")

# 4. Calculate Intraday Metrics for Each Stock
records = []
for s in symbols:
    q = quotes.get(f"NSE:{s}")
    if not q:
        continue
    tok = q.get("instrument_token")
    ohlc = q.get("ohlc", {})
    o = ohlc.get("open", 0.0)
    h = ohlc.get("high", 0.0)
    l = ohlc.get("low", 0.0)
    c = ohlc.get("close", 0.0)
    ltp = q.get("last_price", c)

    if o <= 0 or h <= l or c <= 0:
        continue

    # Move from Open to Close
    move_pct = ((c - o) / o) * 100
    # Range position: 1.0 = at high, 0.0 = at low
    range_pos = (c - l) / (h - l)
    # Total expansion percentage
    day_range_pct = ((h - l) / o) * 100
    # Relative Strength vs NIFTY 50
    rs_vs_nifty = move_pct - nifty_move

    records.append({
        "symbol": s,
        "token": tok,
        "ltp": ltp,
        "open": o,
        "high": h,
        "low": l,
        "close": c,
        "move_pct": move_pct,
        "range_pos": range_pos,
        "day_range_pct": day_range_pct,
        "rs_vs_nifty": rs_vs_nifty
    })

# Top Long candidates: Closed high, positive move, high RS vs Nifty
top_long_cands = sorted(
    [r for r in records if r["move_pct"] > 0.0 and r["range_pos"] >= 0.50],
    key=lambda x: (x["rs_vs_nifty"], x["range_pos"]),
    reverse=True
)[:15]

# Top Short candidates: Closed low, negative move, negative RS vs Nifty
top_short_cands = sorted(
    [r for r in records if r["move_pct"] < 0.0 and r["range_pos"] <= 0.50],
    key=lambda x: (x["rs_vs_nifty"], -x["range_pos"])
)[:15]

print("\n" + "=" * 95)
print(f"🔥 SCREENED TOP {len(top_long_cands)} LONG CANDIDATES (Relative Strength vs Weak Nifty)")
print("=" * 95)
for r in top_long_cands:
    print(f"{r['symbol']:<15} Open: {r['open']:<8.2f} High: {r['high']:<8.2f} Low: {r['low']:<8.2f} Close: {r['close']:<8.2f} Move: {r['move_pct']:<+6.2f}% RangePos: {r['range_pos']:<4.2f} RS: {r['rs_vs_nifty']:<+6.2f}%")

print("\n" + "=" * 95)
print(f"⚠️ SCREENED TOP {len(top_short_cands)} SHORT CANDIDATES (Severe Breakdown vs Nifty)")
print("=" * 95)
for r in top_short_cands:
    print(f"{r['symbol']:<15} Open: {r['open']:<8.2f} High: {r['high']:<8.2f} Low: {r['low']:<8.2f} Close: {r['close']:<8.2f} Move: {r['move_pct']:<+6.2f}% RangePos: {r['range_pos']:<4.2f} RS: {r['rs_vs_nifty']:<+6.2f}%")

# 5. Fetch Daily Historical Candles for These Top 30 Candidates
to_d = datetime.now()
from_d = to_d - timedelta(days=45)

def fetch_details(cands, direction="BUY"):
    detailed = []
    for item in cands:
        s = item["symbol"]
        tok = item["token"]
        try:
            candles = kite.historical_data(tok, from_d, to_d, "day")
            time.sleep(0.35) # rate limit guard
            if len(candles) < 20:
                continue
            df = pd.DataFrame(candles)

            # Daily data
            c = df["close"]
            h = df["high"]
            l = df["low"]
            v = df["volume"]

            # Exclude the latest candle for 20-day high/low benchmark
            high_20d = float(h.iloc[-21:-1].max()) if len(df) >= 21 else float(h.max())
            low_20d = float(l.iloc[-21:-1].min()) if len(df) >= 21 else float(l.min())

            # 20 EMA and 50 SMA
            ema20 = float(c.ewm(span=20, adjust=False).mean().iloc[-1])
            sma50 = float(c.rolling(50).mean().iloc[-1]) if len(df) >= 50 else ema20

            # RSI 14
            delta = c.diff()
            gain = delta.clip(lower=0).rolling(14).mean()
            loss = (-delta.clip(upper=0)).rolling(14).mean()
            rs = gain / (loss + 1e-9)
            rsi = float((100 - (100 / (1 + rs))).iloc[-1])

            # ATR 14
            tr1 = h - l
            tr2 = (h - c.shift(1)).abs()
            tr3 = (l - c.shift(1)).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = float(tr.rolling(14).mean().iloc[-1])
            atr_pct = (atr / item["ltp"]) * 100

            # Volume surge ratio
            vol_avg_20 = float(v.iloc[-21:-1].mean()) if len(df) >= 21 else float(v.mean())
            last_vol = float(v.iloc[-1])
            vol_surge = last_vol / vol_avg_20 if vol_avg_20 > 0 else 1.0

            # 1-day turnover in Cr
            turnover_cr = (item["ltp"] * last_vol) / 1e7

            # Conviction Scoring
            score = 50.0
            if direction == "BUY":
                if item["close"] >= high_20d:
                    score += 22
                    setup = "20-DAY HIGH BREAKOUT 🔥"
                elif item["close"] >= high_20d * 0.985:
                    score += 15
                    setup = "TESTING 20-DAY RESISTANCE 🚀"
                elif item["close"] > ema20 and item["close"] > sma50:
                    score += 10
                    setup = "BULLISH TREND CONTINUATION"
                else:
                    setup = "MEAN REVERSION BOUNCE"

                if vol_surge >= 2.0:
                    score += 15
                elif vol_surge >= 1.25:
                    score += 10

                if 58 <= rsi <= 76:
                    score += 12
                elif 50 <= rsi < 58:
                    score += 6

                if item["rs_vs_nifty"] >= 2.0:
                    score += 12
                elif item["rs_vs_nifty"] >= 1.0:
                    score += 7

                if item["range_pos"] >= 0.80:
                    score += 8
                elif item["range_pos"] >= 0.65:
                    score += 4

                # Intraday Risk Management Levels
                risk = round(max(atr * 0.70, item["ltp"] * 0.010), 2)
                sl = round(item["ltp"] - risk, 2)
                t1 = round(item["ltp"] + (risk * 1.5), 2)
                t2 = round(item["ltp"] + (risk * 2.5), 2)

            else: # SELL / SHORT
                if item["close"] <= low_20d:
                    score += 22
                    setup = "20-DAY LOW BREAKDOWN 💥"
                elif item["close"] <= low_20d * 1.015:
                    score += 15
                    setup = "BREAKING MULTI-WEEK SUPPORT ⚠️"
                elif item["close"] < ema20 and item["close"] < sma50:
                    score += 10
                    setup = "BEARISH TREND DOWNTREND"
                else:
                    setup = "PULLBACK RESISTANCE REJECTION"

                if vol_surge >= 2.0:
                    score += 15
                elif vol_surge >= 1.25:
                    score += 10

                if 25 <= rsi <= 42:
                    score += 12
                elif 42 < rsi <= 48:
                    score += 6

                if item["rs_vs_nifty"] <= -2.0:
                    score += 12
                elif item["rs_vs_nifty"] <= -1.0:
                    score += 7

                if item["range_pos"] <= 0.20:
                    score += 8
                elif item["range_pos"] <= 0.35:
                    score += 4

                risk = round(max(atr * 0.70, item["ltp"] * 0.010), 2)
                sl = round(item["ltp"] + risk, 2)
                t1 = round(item["ltp"] - (risk * 1.5), 2)
                t2 = round(item["ltp"] - (risk * 2.5), 2)

            detailed.append({
                "symbol": s,
                "direction": direction,
                "ltp": item["ltp"],
                "open": item["open"],
                "high": item["high"],
                "low": item["low"],
                "close": item["close"],
                "move_pct": round(item["move_pct"], 2),
                "rs_vs_nifty": round(item["rs_vs_nifty"], 2),
                "range_pos": round(item["range_pos"], 2),
                "high_20d": round(high_20d, 2),
                "low_20d": round(low_20d, 2),
                "rsi": round(rsi, 1),
                "atr": round(atr, 2),
                "atr_pct": round(atr_pct, 2),
                "vol_surge": round(vol_surge, 2),
                "turnover_cr": round(turnover_cr, 1),
                "score": round(min(score, 99.0), 1),
                "setup": setup,
                "sl": sl,
                "t1": t1,
                "t2": t2,
                "risk": risk
            })
        except Exception as e:
            print(f"Error analyzing {s}: {e}")
    return detailed

print("\n[*] Auditing Historical Candles & Multi-Layer Indicators for Top Candidates...")
final_bullish = fetch_details(top_long_cands, "BUY")
final_bearish = fetch_details(top_short_cands, "SELL")

final_bullish.sort(key=lambda x: x["score"], reverse=True)
final_bearish.sort(key=lambda x: x["score"], reverse=True)

print("\n" + "=" * 115)
print("🏆 TOP RANKED BULLISH BOOM CANDIDATES (BUY INTRADAY)")
print("=" * 115)
print(f"{'Symbol':<12} {'LTP':<9} {'Move%':<7} {'RS(Nifty)':<10} {'RSI':<6} {'Vol Surge':<10} {'Turnover(Cr)':<13} {'Score':<6} {'Setup':<28}")
print("-" * 115)
for c in final_bullish[:8]:
    print(f"{c['symbol']:<12} {c['ltp']:<9.2f} {c['move_pct']:<+7.2f}% {c['rs_vs_nifty']:<+10.2f}% {c['rsi']:<6.1f} {c['vol_surge']:<10.2f}x {c['turnover_cr']:<13.1f} {c['score']:<6.1f} {c['setup']:<28}")

print("\n" + "=" * 115)
print("💥 TOP RANKED BEARISH BREAKDOWN CANDIDATES (SELL INTRADAY)")
print("=" * 115)
print(f"{'Symbol':<12} {'LTP':<9} {'Move%':<7} {'RS(Nifty)':<10} {'RSI':<6} {'Vol Surge':<10} {'Turnover(Cr)':<13} {'Score':<6} {'Setup':<28}")
print("-" * 115)
for c in final_bearish[:8]:
    print(f"{c['symbol']:<12} {c['ltp']:<9.2f} {c['move_pct']:<+7.2f}% {c['rs_vs_nifty']:<+10.2f}% {c['rsi']:<6.1f} {c['vol_surge']:<10.2f}x {c['turnover_cr']:<13.1f} {c['score']:<6.1f} {c['setup']:<28}")

with open("boom_candidates_scan.json", "w", encoding="utf-8") as f:
    json.dump({"bullish": final_bullish, "bearish": final_bearish}, f, indent=2)

print("\n[*] Done! Detailed rankings saved to boom_candidates_scan.json")
