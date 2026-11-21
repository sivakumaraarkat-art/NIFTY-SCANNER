import json

with open('nse_deep_scan_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('=== TOP 10 PRIME REVERSAL SWING BUYS (VALUE / BASE ACCUMULATION) ===')
print(f"{'Symbol':12} | {'LTP (₹)':9} | {'RSI':6} | {'52W DD':9} | {'20DMA Dist':11} | {'200DMA Dist':12} | {'Score':6}")
print('-' * 75)
for r in data['top_reversals']:
    sym = r['symbol']
    ltp = f"{r['ltp']:.2f}"
    rsi = f"{r['rsi']:.1f}"
    dd = f"{r['drawdown_52w']:+.1f}%"
    d20 = f"{r['dist_sma20']:+.1f}%"
    d200 = f"{r['dist_sma200']:+.1f}%"
    sc = f"{r['rev_score']:.0f}"
    print(f"{sym:12} | {ltp:>9} | {rsi:>6} | {dd:>9} | {d20:>11} | {d200:>12} | {sc:>6}")

print('\n=== TOP 10 MOMENTUM BREAKOUT LEADERS (TREND CONTINUATION) ===')
print(f"{'Symbol':12} | {'LTP (₹)':9} | {'RSI':6} | {'52W DD':9} | {'20DMA Dist':11} | {'200DMA Dist':12} | {'Score':6}")
print('-' * 75)
for r in data['top_momentum']:
    sym = r['symbol']
    ltp = f"{r['ltp']:.2f}"
    rsi = f"{r['rsi']:.1f}"
    dd = f"{r['drawdown_52w']:+.1f}%"
    d20 = f"{r['dist_sma20']:+.1f}%"
    d200 = f"{r['dist_sma200']:+.1f}%"
    sc = f"{r['mom_score']:.0f}"
    print(f"{sym:12} | {ltp:>9} | {rsi:>6} | {dd:>9} | {d20:>11} | {d200:>12} | {sc:>6}")
