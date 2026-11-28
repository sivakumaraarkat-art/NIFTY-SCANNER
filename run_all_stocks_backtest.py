"""
Comprehensive Multi-Stock Backtest Runner
=========================================
Runs 60-day historical sessions + 10,000 Monte Carlo replays (Seed: 19)
for all top-conviction F&O candidates:
1. MCX (MCX.NS)
2. COFORGE (COFORGE.NS)
3. ICICI BANK (ICICIBANK.NS)
4. ANGEL ONE (ANGELONE.NS)
5. HAL (HAL.NS)
"""

import sys
import math
import json
import urllib.request
import random
from datetime import datetime
from pathlib import Path

STOCKS_CONFIG = [
    {
        "symbol": "MCX",
        "yahoo": "MCX.NS",
        "lot_size": 200,
        "entry": 3915.0,
        "stop": 3845.0,
        "target": 3980.0,
        "target_t2": 4050.0,
        "cas": True
    },
    {
        "symbol": "COFORGE",
        "yahoo": "COFORGE.NS",
        "lot_size": 150,
        "entry": 2085.0,
        "stop": 2030.0,
        "target": 2140.0,
        "target_t2": 2200.0,
        "cas": True
    },
    {
        "symbol": "ICICIBANK",
        "yahoo": "ICICIBANK.NS",
        "lot_size": 700,
        "entry": 1602.0,
        "stop": 1580.0,
        "target": 1630.0,
        "target_t2": 1660.0,
        "cas": True
    },
    {
        "symbol": "ANGELONE",
        "yahoo": "ANGELONE.NS",
        "lot_size": 500,
        "entry": 378.5,
        "stop": 368.0,
        "target": 392.0,
        "target_t2": 408.0,
        "cas": True
    },
    {
        "symbol": "HAL",
        "yahoo": "HAL.NS",
        "lot_size": 150,
        "entry": 5110.0,
        "stop": 5010.0,
        "target": 5220.0,
        "target_t2": 5350.0,
        "cas": True
    }
]

def fetch_bars(yahoo_symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?range=60d&interval=5m"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            result = data['chart']['result'][0]
            timestamps = result['timestamp']
            quote = result['indicators']['quote'][0]
            opens, highs, lows, closes = quote['open'], quote['high'], quote['low'], quote['close']

            bars = []
            for t, o, h, l, c in zip(timestamps, opens, highs, lows, closes):
                if None in (t, o, h, l, c): continue
                bars.append({'datetime': datetime.fromtimestamp(t), 'open': o, 'high': h, 'low': l, 'close': c})
            return bars
    except Exception as e:
        print(f"Error fetching {yahoo_symbol}: {e}")
        return []

def partition_sessions(bars):
    sessions, curr = [], []
    curr_d = None
    for b in bars:
        d = b['datetime'].date()
        if d != curr_d:
            if len(curr) >= 45: sessions.append(curr)
            curr = [b]
            curr_d = d
        else:
            curr.append(b)
    if len(curr) >= 45: sessions.append(curr)
    return sessions

def run_simulation(cfg):
    sym = cfg["symbol"]
    bars = fetch_bars(cfg["yahoo"])
    sessions = partition_sessions(bars)

    if len(sessions) < 15:
        print(f"Insufficient sessions for {sym} ({len(sessions)})")
        return None

    entry = cfg["entry"]
    stop = cfg["stop"]
    target = cfg["target"]
    risk = entry - stop
    reward = target - entry
    rr = reward / risk
    be_win_rate = 1.0 / (1.0 + rr) * 100

    # Build deltas
    deltas = []
    for sess in sessions:
        for i in range(1, len(sess)):
            deltas.append((
                (sess[i]['close'] - sess[i-1]['close']) / sess[i-1]['close'],
                (sess[i]['high'] - sess[i-1]['close']) / sess[i-1]['close'],
                (sess[i]['low'] - sess[i-1]['close']) / sess[i-1]['close']
            ))

    random.seed(19)
    replays = 10000
    target_hits, stop_hits, neither, green = 0, 0, 0, 0
    r_multiples, exit_prices = [], []
    bars_to_sim = 66

    for _ in range(replays):
        p = entry
        hit_tgt, hit_stp = False, False
        for _ in range(bars_to_sim):
            dc, dh, dl = random.choice(deltas)
            bh = p * (1 + dh)
            bl = p * (1 + dl)
            p = p * (1 + dc)

            if bl <= stop:
                hit_stp = True
                r_multiples.append(-1.0)
                exit_prices.append(stop)
                break
            elif bh >= target:
                hit_tgt = True
                r_multiples.append(rr)
                exit_prices.append(target)
                break

        if hit_tgt:
            target_hits += 1
            green += 1
        elif hit_stp:
            stop_hits += 1
        else:
            neither += 1
            if p > entry: green += 1
            r = (p - entry) / risk
            r_multiples.append(r)
            exit_prices.append(p)

    target_pct = (target_hits / replays) * 100
    stop_pct = (stop_hits / replays) * 100
    neither_pct = (neither / replays) * 100
    green_pct = (green / replays) * 100
    avg_r = sum(r_multiples) / len(r_multiples)
    decided = target_hits + stop_hits
    win_share = (target_hits / decided * 100) if decided > 0 else 0
    edge = win_share - be_win_rate

    # Indian statutory charges
    qty = cfg["lot_size"]
    turnover = (entry + target) * qty
    brokerage = 40.0
    stt = target * qty * 0.00025
    exchange = turnover * 0.0000297
    sebi = turnover * 1e-6
    stamp = entry * qty * 0.00003
    gst = (brokerage + exchange + sebi) * 0.18
    tot_charges = brokerage + stt + exchange + sebi + stamp + gst
    charges_r = tot_charges / (risk * qty)
    net_r = avg_r - charges_r

    # Historical Session Re-run
    hist_fires, hist_tgt, hist_stp = 0, 0, 0
    for sess in sessions:
        if len(sess) < 10: continue
        or_hi = max(b['high'] for b in sess[:3])
        trig = False
        for b in sess[3:]:
            if not trig:
                if b['close'] > or_hi:
                    trig = True
                    hist_fires += 1
            else:
                if b['low'] <= (or_hi - risk):
                    hist_stp += 1; break
                elif b['high'] >= (or_hi + reward):
                    hist_tgt += 1; break

    hist_win_pct = (hist_tgt / (hist_tgt + hist_stp) * 100) if (hist_tgt + hist_stp) > 0 else 0

    return {
        "symbol": sym,
        "entry": entry,
        "stop": stop,
        "target": target,
        "risk": risk,
        "reward": reward,
        "rr": rr,
        "be_win": be_win_rate,
        "mc_target_pct": target_pct,
        "mc_stop_pct": stop_pct,
        "mc_win_share": win_share,
        "edge": edge,
        "gross_r": avg_r,
        "net_r": net_r,
        "charges_inr": tot_charges,
        "charges_r": charges_r,
        "hist_sessions": len(sessions),
        "hist_fires": hist_fires,
        "hist_tgt": hist_tgt,
        "hist_stp": hist_stp,
        "hist_win_pct": hist_win_pct,
        "lot_size": qty
    }

def main():
    print("=" * 105)
    print("ALL-STOCKS CONVICTION BACKTEST AUDIT (10,000 Monte Carlo Replays + 60 Sessions Real History)")
    print("=" * 105)

    results = []
    for cfg in STOCKS_CONFIG:
        print(f"Auditing {cfg['symbol']}...")
        r = run_simulation(cfg)
        if r: results.append(r)

    print("\n" + "=" * 105)
    header = f"{'Symbol':<12} | {'Setup (E / SL / Tgt)':<26} | {'R:R':<6} | {'BE Win':<7} | {'MC Win%':<8} | {'Hist Win% (Hits)':<18} | {'Net R':<8} | {'Edge'}"
    print(header)
    print("-" * 105)

    for r in results:
        setup_str = f"{r['entry']:.0f} / {r['stop']:.0f} / {r['target']:.0f}"
        hist_str = f"{r['hist_win_pct']:.1f}% ({r['hist_tgt']}/{r['hist_tgt']+r['hist_stp']})"
        edge_str = f"{r['edge']:+.1f}%"
        print(f"{r['symbol']:<12} | {setup_str:<26} | 1:{r['rr']:<4.2f} | {r['be_win']:<6.1f}% | {r['mc_win_share']:<7.1f}% | {hist_str:<18} | {r['net_r']:<+7.3f}R | {edge_str}")

    print("-" * 105)

    # Save results to JSON for GTT generator
    with open("all_stocks_backtest_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to all_stocks_backtest_results.json")

if __name__ == '__main__':
    main()
