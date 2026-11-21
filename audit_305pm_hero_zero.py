"""
audit_305pm_hero_zero.py
Fetches live institutional technicals, volume profiles, OI concentration,
and calculates the exact 3:05 PM Hero-Zero strike recommendation.
"""

import sys
import datetime
from pathlib import Path
import pandas as pd
from kiteconnect import KiteConnect

# Fix stdout encoding for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

print("=" * 85)
print("🎯 NIFTY EXPIRY DEEP 3:05 PM HERO-ZERO TECHNICAL & VOLUME ENGINE")
print("=" * 85)

# 1. Fetch Spot 5m candles and indicators
today = datetime.date.today()
candles = kite.historical_data(256265, today, today, "5minute")
df = pd.DataFrame(candles)
df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()

last_bar = df.iloc[-1]
spot_ltp = last_bar["close"]
spot_high = df["high"].max()
spot_low = df["low"].min()
ema20 = last_bar["ema20"]
ema50 = last_bar["ema50"]
bar_time = last_bar["date"]

print(f"📊 [1] SPOT TECHNICAL AUDIT (Bar Time: {bar_time})")
print(f"    • Nifty 50 Spot:    ₹{spot_ltp:.2f}")
print(f"    • Day High / Low:   ₹{spot_high:.2f} / ₹{spot_low:.2f} (Total Range: {spot_high - spot_low:.2f} pts)")
print(f"    • 5-min EMA 20:     ₹{ema20:.2f} (Spread: {spot_ltp - ema20:+.2f} pts)")
print(f"    • 5-min EMA 50:     ₹{ema50:.2f} (Spread: {spot_ltp - ema50:+.2f} pts)")

trend = "BULLISH BREAKOUT" if spot_ltp > ema20 and spot_ltp >= 25000 else ("BEARISH REJECTION" if spot_ltp < ema20 else "SIDEWAYS CONSOLIDATION")
print(f"    • Intraday Bias:    {trend}")

# 2. Key strikes quote & OI analysis
strikes = [
    "NFO:NIFTY26N0924900PE", "NFO:NIFTY26N0924950PE", "NFO:NIFTY26N0925000PE",
    "NFO:NIFTY26N0925000CE", "NFO:NIFTY26N0925050CE", "NFO:NIFTY26N0925100CE"
]
q = kite.quote(strikes)

pe_oi = sum(q[s]["oi"] for s in strikes if "PE" in s)
ce_oi = sum(q[s]["oi"] for s in strikes if "CE" in s)
pcr = pe_oi / ce_oi if ce_oi > 0 else 0

print(f"\n🌊 [2] OPTION CHAIN & VOLUME LIQUIDITY")
print(f"    • ATM Put OI:       {pe_oi:,} contracts")
print(f"    • ATM Call OI:      {ce_oi:,} contracts")
print(f"    • Cluster PCR:      {pcr:.2f} ({'Call Writing Dominant' if pcr < 0.9 else ('Put Writing Support' if pcr > 1.1 else 'Equilibrium Battle')})")

print("\n" + "-" * 85)
print(f"{'Option Symbol':<22} | {'LTP':<8} | {'Volume':<15} | {'OI':<12} | {'Bid / Ask':<15}")
print("-" * 85)
best_ce = None
best_pe = None

for s in sorted(strikes):
    data = q[s]
    ltp = data.get("last_price", 0)
    vol = data.get("volume", 0)
    oi = data.get("oi", 0)
    depth = data.get("depth", {})
    buy_top = depth.get("buy", [{}])[0].get("price", 0) if depth.get("buy") else 0
    sell_top = depth.get("sell", [{}])[0].get("price", 0) if depth.get("sell") else 0
    sym = s.replace("NFO:", "")
    print(f"{sym:<22} | ₹{ltp:<7.2f} | {vol:<15,} | {oi:<12,} | ₹{buy_top:.2f}/₹{sell_top:.2f}")

    # Evaluate best candidate in the sweet-spot range (₹15 - ₹35)
    if "CE" in s and 12 <= ltp <= 45:
        if best_ce is None or abs(ltp - 22) < abs(best_ce["ltp"] - 22):
            best_ce = {"symbol": sym, "ltp": ltp, "oi": oi, "vol": vol}
    if "PE" in s and 12 <= ltp <= 45:
        if best_pe is None or abs(ltp - 22) < abs(best_pe["ltp"] - 22):
            best_pe = {"symbol": sym, "ltp": ltp, "oi": oi, "vol": vol}

print("=" * 85)
print("🔥 [3] 3:05 PM CANDIDATE DECISION BLUEPRINT")
print("=" * 85)
if best_ce:
    t1_ce = best_ce["ltp"] * 2.0
    t2_ce = best_ce["ltp"] * 4.0
    sl_ce = best_ce["ltp"] * 0.5
    print(f"🟢 BULLISH WINNER (Trigger if Spot Closes > 25,015):")
    print(f"    • Strike:           {best_ce['symbol']}")
    print(f"    • Entry Price:      ₹{best_ce['ltp']:.2f}")
    print(f"    • Target 1 (2x):    ₹{t1_ce:.2f} (+100%)")
    print(f"    • Target 2 (4x):    ₹{t2_ce:.2f} (+300%)")
    print(f"    • Stop Loss (SL):   ₹{sl_ce:.2f} (-50%)")
    print(f"    • 1 Lot Outlay:     ₹{best_ce['ltp'] * 65:,.2f} | Max Risk: ₹{sl_ce * 65:,.2f}")

if best_pe:
    t1_pe = best_pe["ltp"] * 2.0
    t2_pe = best_pe["ltp"] * 4.0
    sl_pe = best_pe["ltp"] * 0.5
    print(f"\n🔴 BEARISH WINNER (Trigger if Spot Drops < 24,980):")
    print(f"    • Strike:           {best_pe['symbol']}")
    print(f"    • Entry Price:      ₹{best_pe['ltp']:.2f}")
    print(f"    • Target 1 (2x):    ₹{t1_pe:.2f} (+100%)")
    print(f"    • Target 2 (4x):    ₹{t2_pe:.2f} (+300%)")
    print(f"    • Stop Loss (SL):   ₹{sl_pe:.2f} (-50%)")
    print(f"    • 1 Lot Outlay:     ₹{best_pe['ltp'] * 65:,.2f} | Max Risk: ₹{sl_pe * 65:,.2f}")

print("=" * 85)
