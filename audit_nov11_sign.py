from kiteconnect import KiteConnect
from pathlib import Path
import json

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

inst_token = 5506049
bars = kite.historical_data(inst_token, "2026-11-10", "2026-11-12", "15minute")

print(f"Total 15-min bars: {len(bars)}")
nov11_bars = [b for b in bars if "2026-11-11" in str(b["date"])]

print(f"{'Time':8} | {'Open':8} | {'High':8} | {'Low':8} | {'Close':8} | {'Volume':10}")
print("-" * 55)
for b in nov11_bars:
    t = str(b["date"])[11:16]
    o, h, l, c, v = b["open"], b["high"], b["low"], b["close"], b["volume"]
    print(f"{t:8} | {o:8.2f} | {h:8.2f} | {l:8.2f} | {c:8.2f} | {v:10,d}")
