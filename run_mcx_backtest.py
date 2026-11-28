"""
MCX Comprehensive Strategy Backtest
===================================
Simulates the #1 Conviction Pick: Multi Commodity Exchange (MCX.NS)
- Historical Data: 60-day 5-minute bars from exchange
- Replays: 10,000 Monte Carlo Replays (Seed: 19)
- Indian Charges: Factored with Zerodha MIS/F&O statutory rates
- Setups Tested:
    1. Setup A: Quick T1 Scalp (Entry 3915, Stop 3845, Target 3980, R:R 1:0.93)
    2. Setup B: Primary Squeeze Target T2 (Entry 3915, Stop 3845, Target 4050, R:R 1:1.93)
    3. Setup C: Extended Blue-Sky Target T3 (Entry 3915, Stop 3845, Target 4180, R:R 1:3.79)
"""

import sys
import math
import json
import urllib.request
import random
from datetime import datetime
from pathlib import Path

def fetch_mcx_bars():
    symbol = "MCX.NS"
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

def run_mcx_scenario(sessions, deltas, entry, stop, target, label, lot_size=200):
    risk = entry - stop
    reward = target - entry
    rr = reward / risk
    be_win_rate = 1.0 / (1.0 + rr) * 100

    random.seed(19)
    replays = 10000
    target_hits, stop_hits, neither, green = 0, 0, 0, 0
    r_multiples, exit_prices = [], []

    # CAS stock: continuous trading 09:15 to 15:15 (72 bars).
    # Entry at 09:30 is bar 3. Exit by 15:00 is bar 69 -> 66 bars.
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
    exit_prices.sort()
    med_exit = exit_prices[len(exit_prices) // 2]

    # Indian statutory charges for MCX (1 Lot = 200 Shares for F&O, or 100 shares intraday MIS)
    qty = lot_size
    turnover = (entry + target) * qty
    # Brokerage: min(20, 0.03%) each leg = 40. STT: 0.025% on sell. Exchange: 0.00297%. SEBI: 10/Cr. Stamp: 0.003%. GST: 18%.
    brokerage = 40.0
    stt = target * qty * 0.00025
    exchange = turnover * 0.0000297
    sebi = turnover * (10 / 10000000)
    stamp = entry * qty * 0.00003
    gst = (brokerage + exchange + sebi) * 0.18
    tot_charges = brokerage + stt + exchange + sebi + stamp + gst
    charges_r = tot_charges / (risk * qty)
    net_r = avg_r - charges_r

    decided = target_hits + stop_hits
    win_share = (target_hits / decided * 100) if decided > 0 else 0
    edge = win_share - be_win_rate

    # Historical Session Re-run on actual MCX bars
    hist_fires, hist_tgt, hist_stp, hist_neither = 0, 0, 0, 0
    for sess in sessions:
        if len(sess) < 10: continue
        or_hi = max(b['high'] for b in sess[:3]) # 09:15-09:30 range
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
        'hist_tgt': hist_tgt,
        'hist_stp': hist_stp,
        'hist_win_pct': hist_win_pct
    }

def main():
    print("=" * 100)
    print("MCX INDIA (MCX.NS) COMPREHENSIVE BACKTEST AUDIT (10,000 Monte Carlo Replays + 60 Sessions Real History)")
    print("=" * 100)

    bars = fetch_mcx_bars()
    sessions = partition_sessions(bars)
    print(f"Loaded {len(bars)} 5-minute bars across {len(sessions)} full trading sessions.\n")

    deltas = []
    for sess in sessions:
        for i in range(1, len(sess)):
            deltas.append((
                (sess[i]['close'] - sess[i-1]['close']) / sess[i-1]['close'],
                (sess[i]['high'] - sess[i-1]['close']) / sess[i-1]['close'],
                (sess[i]['low'] - sess[i-1]['close']) / sess[i-1]['close']
            ))

    setups = [
        ("Setup A: Quick Scalp T1 (3,980)", 3915.0, 3845.0, 3980.0),
        ("Setup B: Primary Squeeze T2 (4,050)", 3915.0, 3845.0, 4050.0),
        ("Setup C: Blue-Sky Extension T3 (4,180)", 3915.0, 3845.0, 4180.0)
    ]

    results = []
    for label, e, s, t in setups:
        res = run_mcx_scenario(sessions, deltas, e, s, t, label)
        results.append(res)

    # Print Table
    header = f"{'Strategy / Setup':<40} | {'R:R':<6} | {'Target%':<8} | {'Stop%':<7} | {'Win Rate':<9} | {'Gross R':<8} | {'Net R':<8} | {'Edge'}"
    print(header)
    print("-" * len(header))

    for r in results:
        edge_str = f"{r['edge']:+.1f}%"
        print(f"{r['label']:<40} | 1:{r['rr']:<4.2f} | {r['target_pct']:<7.1f}% | {r['stop_pct']:<6.1f}% | {r['decided_win']:<8.1f}% | {r['avg_r_gross']:<+7.3f}R | {r['avg_r_net']:<+7.3f}R | {edge_str}")

    print("-" * len(header))
    print("\nDETAILED AUDIT & VERDICTS FOR MCX:")
    for r in results:
        print(f"• {r['label']}:")
        print(f"    - Entry: ₹{r['entry']:.1f} | Stop: ₹{r['stop']:.1f} (-₹{r['risk']:.1f}) | Target: ₹{r['target']:.1f} (+₹{r['reward']:.1f})")
        print(f"    - Break-even Threshold : {r['be_win']:.1f}% win rate required")
        print(f"    - 10k Monte Carlo Win   : {r['decided_win']:.1f}% (Edge over break-even: {r['edge']:+.1f}%)")
        print(f"    - Real History 60 Days  : Triggered {r['hist_fires']} times -> {r['hist_tgt']} Hits vs {r['hist_stp']} Stops ({r['hist_win_pct']:.1f}% Win Rate)")
        print(f"    - Indian Charges        : ₹{r['charges_inr']:.2f} ({r['charges_r']:.3f}R on 200 shares)")
        print(f"    - Net Trade Expectancy  : {r['avg_r_net']:+.3f}R net profit per trade")
        verdict = "EXCEPTIONAL STATISTICAL EDGE 🚀" if r['edge'] >= 10.0 else ("STRONG EDGE 🟢" if r['edge'] >= 5.0 else ("FAVORABLE EDGE 🟢" if r['edge'] > 0 else "SUB-OPTIMAL"))
        print(f"    - STATISTICAL VERDICT   : {verdict}\n")
    print("=" * 100)

if __name__ == '__main__':
    main()
