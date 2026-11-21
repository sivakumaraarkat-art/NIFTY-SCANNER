import pandas as pd
import numpy as np
from pathlib import Path

stocks = ['RVNL', 'IRFC', 'TITAGARH', 'COCHINSHIP', 'APOLLO', 'KAYNES', 'RAILTEL', 'SUZLON', 'LODHA', 'PCBL']
cache_dir = Path('database/market_data_cache')

print("=" * 105)
print(f"{'STOCK':10} | {'LTP':8} | {'TURNOVER (Cr)':15} | {'ANNUAL VOL %':14} | {'DIST TO 52W LOW':16} | {'RISK PROFILE':15}")
print("=" * 105)

for sym in stocks:
    f = cache_dir / f'NSE_{sym}_daily.parquet'
    if f.exists():
        df = pd.read_parquet(f)
        last = df.iloc[-1]
        turnover_cr = (df['volume'].tail(20) * df['close'].tail(20)).mean() / 1e7
        returns = df['close'].pct_change()
        vol_20d = returns.tail(20).std() * (252 ** 0.5) * 100
        low_52w = df['low'].tail(250).min()
        dist_to_low = ((last['close'] - low_52w) / low_52w) * 100

        # Risk classification
        if turnover_cr > 100 and dist_to_low < 5:
            risk = "LOWEST (Floor)"
        elif vol_20d > 45:
            risk = "HIGH BETA"
        elif dist_to_low < 5:
            risk = "DEEP VALUE"
        else:
            risk = "MOMENTUM / MOD"

        print(f"{sym:10} | {last['close']:8.2f} | {turnover_cr:12.2f} Cr | {vol_20d:12.1f}% | {dist_to_low:14.2f}% | {risk:15}")

print("=" * 105)
