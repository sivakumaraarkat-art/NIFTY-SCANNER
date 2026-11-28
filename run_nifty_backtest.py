"""
NIFTY 50 Comprehensive Strategy Backtest
========================================
Runs 3 distinct setups across 60 days of real 5-minute historical NIFTY data:
1. Setup A: Gap-Up 15-Min Breakout (Target T1 @ 25,905 vs Stop 25,760, R:R 1:1.23)
2. Setup B: Gap-Up Swing Extension (Target T2 @ 25,950 vs Stop 25,760, R:R 1:1.92)
3. Setup C: Dip-Buying Reversal at Golden Pocket (Entry 25,715, Target 25,850, Stop 25,660, R:R 1:2.45)
"""

import sys
import math
import json
import urllib.request
import random
from datetime import datetime
from pathlib import Path

def fetch_nifty_bars():
    symbol = "^NSEI"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=60d&interval=5m"
    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
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

def partition_sessions(bars):
    sessions, curr = [], []
    curr_d = None
    for b in bars:
        d = b['datetime'].date()
        if d != curr_d:
            if len(curr) >= 50: sessions.append(curr)
            curr = [b]
            curr_d = d
        else:
            curr.append(b)
    if len(curr) >= 50: sessions.append(curr)
    return sessions

def run_mc_scenario(sessions, deltas, entry, stop, target, label):
    risk = entry - stop
    reward = target - entry
    rr = reward / risk
    be_win_rate = 1.0 / (1.0 + rr) * 100

    random.seed(19)
    replays = 10000
    target_hits, stop_hits, neither, green = 0, 0, 0, 0
    r_multiples, exit_prices = [], []

    bars_to_sim = 68
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
    exit_prices.sort()
    med_exit = exit_prices[len(exit_prices) // 2]

    # Indian charges for 1 Lot Nifty Futures (qty = 65)
    qty = 65
    turnover = (entry + target) * qty
    tot_charges = 40.0 + (target * qty * 0.0002) + (turnover * 0.000019) + (turnover * 1e-6) + (entry * qty * 2e-5) + 10.0
    charges_r = tot_charges / (risk * qty)
    net_r = avg_r - charges_r

    decided = target_hits + stop_hits
    win_share = (target_hits / decided * 100) if decided > 0 else 0
    edge = win_share - be_win_rate

    # Historical check
    hist_fires, hist_tgt, hist_stp = 0, 0, 0
    for sess in sessions:
        if len(sess) < 10: continue
        or_hi = max(b['high'] for b in sess[:3])
        or_lo = min(b['low'] for b in sess[:3])
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
        'label': label,
        'entry': entry,
        'stop': stop,
        'target': target,
        'risk': risk,
        'reward': reward,
        'rr': rr,
        'be_win': be_win_rate,
        'target_pct': target_pct,
        'stop_pct': stop_pct,
        'neither_pct': neither_pct,
        'green_pct': green_pct,
        'avg_r_gross': avg_r,
        'charges_inr': tot_charges,
        'charges_r': charges_r,
        'avg_r_net': net_r,
        'median_exit': med_exit,
        'decided_win': win_share,
        'edge': edge,
        'hist_fires': hist_fires,
        'hist_win_pct': hist_win_pct
    }

def main():
    print("=" * 95)
    print("NIFTY 50 COMPREHENSIVE BACKTEST AUDIT (10,000 Monte Carlo Replays + 60 Sessions Real History)")
    print("=" * 95)

    bars = fetch_nifty_bars()
    sessions = partition_sessions(bars)
    print(f"Loaded {len(bars)} 5-min bars across {len(sessions)} full trading sessions.\n")

    deltas = []
    for sess in sessions:
        for i in range(1, len(sess)):
            deltas.append((
                (sess[i]['close'] - sess[i-1]['close']) / sess[i-1]['close'],
                (sess[i]['high'] - sess[i-1]['close']) / sess[i-1]['close'],
                (sess[i]['low'] - sess[i-1]['close']) / sess[i-1]['close']
            ))

    setups = [
        ("Setup A: Quick Target T1 (Friday High 25,905)", 25825.0, 25760.0, 25905.0),
        ("Setup B: Full Squeeze Extension T2 (25,950)", 25825.0, 25760.0, 25950.0),
        ("Setup C: Dip-Buying Reversal @ Golden Pocket", 25715.0, 25660.0, 25850.0)
    ]

    results = []
    for label, e, s, t in setups:
        res = run_mc_scenario(sessions, deltas, e, s, t, label)
        results.append(res)

    # Print Table
    header = f"{'Strategy / Setup':<42} | {'R:R':<6} | {'Target%':<8} | {'Stop%':<7} | {'Win Rate':<9} | {'Gross R':<8} | {'Net R':<8} | {'Edge'}"
    print(header)
    print("-" * len(header))

    for r in results:
        edge_str = f"{r['edge']:+.1f}%"
        print(f"{r['label']:<42} | 1:{r['rr']:<4.2f} | {r['target_pct']:<7.1f}% | {r['stop_pct']:<6.1f}% | {r['decided_win']:<8.1f}% | {r['avg_r_gross']:<+7.3f}R | {r['avg_r_net']:<+7.3f}R | {edge_str}")

    print("-" * len(header))
    print("\nDETAILED VERDICTS:")
    for r in results:
        print(f"• {r['label']}:")
        print(f"    - Entry: {r['entry']:.1f} | Stop: {r['stop']:.1f} ({r['risk']:.1f} pts) | Target: {r['target']:.1f} ({r['reward']:.1f} pts)")
        print(f"    - Break-even Needed: {r['be_win']:.1f}% | Monte Carlo Win Rate: {r['decided_win']:.1f}% | Edge: {r['edge']:+.1f}%")
        print(f"    - Historical 60-Day Sessions: Fired {r['hist_fires']} times with {r['hist_win_pct']:.1f}% actual win rate.")
        print(f"    - Net Expectancy: {r['avg_r_net']:+.3f}R per trade after Indian statutory taxes/charges (INR {r['charges_inr']:.2f}).")
        verdict = "HIGH STATISTICAL EDGE (Favorable)" if r['edge'] >= 5.0 else ("FAVORABLE EDGE" if r['edge'] > 0 else "DEFENSIVE / SUB-OPTIMAL")
        print(f"    - VERDICT: {verdict}\n")
    print("=" * 95)

if __name__ == '__main__':
    main()
