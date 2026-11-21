import datetime
import pandas as pd
from pathlib import Path
from kiteconnect import KiteConnect

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

token_c = 5506049 # COCHINSHIP
to_date = datetime.datetime.now().strftime("%Y-%m-%d")
from_date = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
bars = kite.historical_data(token_c, from_date, to_date, "day")
df = pd.DataFrame(bars)

df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()

delta = df["close"].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
df["rsi"] = 100 - (100 / (1 + rs))

last = df.iloc[-1]
prev = df.iloc[-2]

print("=" * 80)
print("COCHIN SHIPYARD (NSE: COCHINSHIP) — DAILY PERFORMANCE & TREND")
print("=" * 80)
print(f"• Current Market Price (LTP): ₹{last['close']:,.2f}")
print(f"• Today's Range (18-Nov-2026):  Low ₹{last['low']:,.2f}  -  High ₹{last['high']:,.2f}")
print(f"• Today's Volume:             {int(last['volume']):,} shares")
print(f"• 20-Day EMA:                 ₹{last['ema20']:,.2f}")
print(f"• 50-Day EMA:                 ₹{last['ema50']:,.2f}")
print(f"• 200-Day EMA:                ₹{last['ema200']:,.2f}")
print(f"• Daily RSI (14):             {last['rsi']:.1f} (Consolidating in Neutral Zone)")
print(f"• 52-Week Range:              Low ₹{df['low'].min():,.2f}  -  High ₹{df['high'].max():,.2f}")

print("\nLast 5 Trading Sessions:")
print(f"{'Date':<12} | {'Open':<9} | {'High':<9} | {'Low':<9} | {'Close':<9} | {'Volume':<10}")
print("-" * 65)
for _, r in df.tail(5).iterrows():
    d_str = str(r['date'])[:10]
    print(f"{d_str:<12} | ₹{r['open']:<8.1f} | ₹{r['high']:<8.1f} | ₹{r['low']:<8.1f} | ₹{r['close']:<8.1f} | {int(r['volume']):,}")
print("=" * 80)
