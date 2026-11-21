import datetime
import pandas as pd
import numpy as np
from pathlib import Path
from kiteconnect import KiteConnect

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

now = datetime.datetime.now()
insts = kite.instruments("MCX")

# Futures
crude_futs = [i for i in insts if i.get("name") == "CRUDEOIL" and i.get("instrument_type") == "FUT"]
crude_futs = sorted(crude_futs, key=lambda x: x.get("expiry"))

nov_fut = [f for f in crude_futs if f.get("tradingsymbol") == "CRUDEOIL26NOVFUT"][0]
dec_fut = [f for f in crude_futs if f.get("tradingsymbol") == "CRUDEOIL26DECFUT"][0]

nov_quote = kite.quote([f"MCX:{nov_fut['tradingsymbol']}"])[f"MCX:{nov_fut['tradingsymbol']}"]
dec_quote = kite.quote([f"MCX:{dec_fut['tradingsymbol']}"])[f"MCX:{dec_fut['tradingsymbol']}"]

nov_ltp = nov_quote.get("last_price", 0)
dec_ltp = dec_quote.get("last_price", 0)

# Fetch historical candles for Nov & Dec fut
today_str = now.strftime("%Y-%m-%d")
from_date = (now - datetime.timedelta(days=4)).strftime("%Y-%m-%d")

# 5min candles today for Nov fut
bars_5m = kite.historical_data(nov_fut["instrument_token"], from_date, today_str, "5minute")
df_5m = pd.DataFrame(bars_5m)

bars_15m = kite.historical_data(nov_fut["instrument_token"], from_date, today_str, "15minute")
df_15m = pd.DataFrame(bars_15m)

# Technical indicators on 15m
df_15m["ema9"] = df_15m["close"].ewm(span=9, adjust=False).mean()
df_15m["ema21"] = df_15m["close"].ewm(span=21, adjust=False).mean()
df_15m["ema50"] = df_15m["close"].ewm(span=50, adjust=False).mean()

# RSI 14
delta = df_15m["close"].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
df_15m["rsi"] = 100 - (100 / (1 + rs))

# Calculate VWAP for today
df_today = df_5m[df_5m["date"].astype(str).str.startswith(today_str)].copy()
if not df_today.empty:
    vwap = (df_today["volume"] * (df_today["high"] + df_today["low"] + df_today["close"]) / 3).cumsum() / df_today["volume"].cumsum()
    current_vwap = vwap.iloc[-1]
else:
    current_vwap = 0

last_15m = df_15m.iloc[-1]
prev_15m = df_15m.iloc[-2]

# Options Analysis (Expiry: 2026-12-16)
crude_opts = [i for i in insts if i.get("name") == "CRUDEOIL" and i.get("instrument_type") in ("CE", "PE") and str(i.get("expiry")) == "2026-12-16"]

opt_syms = [f"MCX:{i['tradingsymbol']}" for i in crude_opts if 7400 <= float(i.get("strike", 0)) <= 8400]
opt_quotes = kite.quote(opt_syms)

total_ce_oi = 0
total_pe_oi = 0
max_ce_oi = 0
max_ce_strike = 0
max_pe_oi = 0
max_pe_strike = 0

for i in crude_opts:
    strike = float(i.get("strike", 0))
    if 7200 <= strike <= 8600:
        sym = f"MCX:{i['tradingsymbol']}"
        q = opt_quotes.get(sym, {})
        oi = q.get("oi", 0)
        itype = i.get("instrument_type")
        if itype == "CE":
            total_ce_oi += oi
            if oi > max_ce_oi:
                max_ce_oi = oi
                max_ce_strike = strike
        elif itype == "PE":
            total_pe_oi += oi
            if oi > max_pe_oi:
                max_pe_oi = oi
                max_pe_strike = strike

pcr = total_pe_oi / total_ce_oi if total_ce_oi else 0

# Pivot points
h = nov_quote["ohlc"]["high"]
l = nov_quote["ohlc"]["low"]
c = nov_quote["last_price"]
pivot = (h + l + c) / 3
r1 = (2 * pivot) - l
s1 = (2 * pivot) - h
r2 = pivot + (h - l)
s2 = pivot - (h - l)

print("=" * 80)
print(f"CRUDE OIL INTRADAY TECHNICALS (MCX NOV FUT: {nov_ltp} | DEC FUT: {dec_ltp})")
print(f"Time: {now.strftime('%H:%M:%S IST')} | Trend: {'BEARISH' if nov_ltp < current_vwap else 'BULLISH'}")
print("=" * 80)
print(f"• VWAP (Today):        Rs.{current_vwap:,.1f} (Price is {'BELOW' if nov_ltp < current_vwap else 'ABOVE'} VWAP by {abs(nov_ltp - current_vwap):.1f} pts)")
print(f"• 15m EMA 9:           Rs.{last_15m['ema9']:,.1f}")
print(f"• 15m EMA 21:          Rs.{last_15m['ema21']:,.1f}")
print(f"• 15m EMA 50:          Rs.{last_15m['ema50']:,.1f}")
print(f"• 15m RSI (14):        {last_15m['rsi']:.1f} ({'Oversold bounce watch' if last_15m['rsi'] < 35 else 'Neutral / Weak' if last_15m['rsi'] < 50 else 'Strong'})")
print(f"• Intraday High/Low:   High Rs.{h} | Low Rs.{l} (Range: {h - l} pts)")
print(f"• Classic Pivots:      R2: {r2:.0f} | R1: {r1:.0f} | Pivot: {pivot:.0f} | S1: {s1:.0f} | S2: {s2:.0f}")
print("-" * 80)
print(f"OPTIONS METRICS (Dec 16 Expiry):")
print(f"• Total Call OI:       {total_ce_oi:,}")
print(f"• Total Put OI:        {total_pe_oi:,}")
print(f"• PCR (Put-Call Ratio):{pcr:.2f} ({'Bearish bias / Call Writing heavy' if pcr < 0.8 else 'Bullish / Put Writing' if pcr > 1.2 else 'Neutral'})")
print(f"• Major Call Resistance: {int(max_ce_strike)} CE (OI: {max_ce_oi:,})")
print(f"• Major Put Support:     {int(max_pe_strike)} PE (OI: {max_pe_oi:,})")
print("=" * 80)

# Check specific key option quotes and market depth
focus_strikes = [
    ("CRUDEOIL26DEC7800PE", "ATM / In-play Put"),
    ("CRUDEOIL26DEC7700PE", "OTM Put (Momentum)"),
    ("CRUDEOIL26DEC7900PE", "ITM Put (High Delta)"),
    ("CRUDEOIL26DEC7900CE", "ATM Call (Reversal play)"),
    ("CRUDEOIL26DEC8000CE", "OTM Call (Major Resistance)")
]

print("\nKEY ACTIONABLE STRIKES DEPTH & QUOTES:")
print("-" * 80)
for ts, desc in focus_strikes:
    q = opt_quotes.get(f"MCX:{ts}", {})
    ohlc = q.get("ohlc", {})
    depth = q.get("depth", {})
    buy_top = depth.get("buy", [{}])[0]
    sell_top = depth.get("sell", [{}])[0]
    ltp = q.get("last_price", 0)
    chg = ((ltp - ohlc.get("close", 1)) / ohlc.get("close", 1)) * 100 if ohlc.get("close") else 0
    print(f"[{desc.upper()}] {ts}")
    print(f"  LTP: Rs.{ltp:.1f} ({chg:+.1f}%) | Day Range: Rs.{ohlc.get('low', 0):.1f} - Rs.{ohlc.get('high', 0):.1f} | Vol: {q.get('volume', 0):,} | OI: {q.get('oi', 0):,}")
    print(f"  Bid: Rs.{buy_top.get('price', 0):.1f} (qty: {buy_top.get('quantity', 0)}) | Ask: Rs.{sell_top.get('price', 0):.1f} (qty: {sell_top.get('quantity', 0)})")
    print()
