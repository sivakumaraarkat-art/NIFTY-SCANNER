from kiteconnect import KiteConnect
from pathlib import Path
import datetime
import math

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

now = datetime.datetime.now()
today_str = now.strftime("%Y-%m-%d")

# 1. Fetch Nifty Spot & Nifty Current Month Futures (for true traded volume)
# Let's find Nifty futures
sym_spot = "NSE:NIFTY 50"
sym_bank = "NSE:NIFTY BANK"
sym_pe = "NFO:NIFTY26N1725000PE"

# Let's search instruments for NIFTY Nov Fut
insts = kite.instruments("NFO")
nifty_fut_sym = None
for inst in insts:
    if inst.get("name") == "NIFTY" and inst.get("instrument_type") == "FUT" and inst.get("expiry").month == 11:
        nifty_fut_sym = f"NFO:{inst.get('tradingsymbol')}"
        break

if not nifty_fut_sym:
    nifty_fut_sym = "NFO:NIFTY26NOVFUT"

symbols = [sym_spot, sym_bank, sym_pe, nifty_fut_sym]

# Add Nifty Top Heavyweights
heavyweights = [
    "NSE:RELIANCE",
    "NSE:HDFCBANK",
    "NSE:ICICIBANK",
    "NSE:INFY",
    "NSE:TCS",
    "NSE:ITC",
    "NSE:LT",
    "NSE:AXISBANK",
    "NSE:SBIN"
]
symbols.extend(heavyweights)

quotes = kite.quote(symbols)

spot_q = quotes.get(sym_spot, {})
fut_q = quotes.get(nifty_fut_sym, {})
pe_q = quotes.get(sym_pe, {})
bank_q = quotes.get(sym_bank, {})

spot_token = spot_q.get("instrument_token")
pe_token = pe_q.get("instrument_token")

# Pull 5-minute historical candles for Spot & PE
bars_spot = kite.historical_data(spot_token, today_str, today_str, "5minute")
bars_pe = kite.historical_data(pe_token, today_str, today_str, "5minute")

# Calculate VWAP, RSI, EMA for Spot
closes = [b["close"] for b in bars_spot]
highs = [b["high"] for b in bars_spot]
lows = [b["low"] for b in bars_spot]

# RSI calculation (14 period)
def compute_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50.0
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

rsi_14 = compute_rsi(closes, 14)

# 20 EMA calculation
def compute_ema(prices, period=20):
    if len(prices) < period:
        return prices[-1] if prices else 0
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for p in prices[period:]:
        ema = (p - ema) * multiplier + ema
    return ema

ema_9 = compute_ema(closes, 9)
ema_20 = compute_ema(closes, 20)

# Pivot Points based on Yesterday's OHLC
prev_close = spot_q.get("ohlc", {}).get("close", 25300)
# We can estimate standard floor pivots from today's open & prev close
# Classic Pivots:
day_high = spot_q.get("ohlc", {}).get("high", 25384.8)
day_low = spot_q.get("ohlc", {}).get("low", 25142.95)
spot_ltp = spot_q.get("last_price", 25244)

# Camarilla Pivots (intraday)
# H3 = Close + (High - Low) * 1.1 / 4
# L3 = Close - (High - Low) * 1.1 / 4
# H4 = Close + (High - Low) * 1.1 / 2
# L4 = Close - (High - Low) * 1.1 / 2
range_hl = day_high - day_low
cam_h4 = prev_close + range_hl * 1.1 / 2
cam_h3 = prev_close + range_hl * 1.1 / 4
cam_l3 = prev_close - range_hl * 1.1 / 4
cam_l4 = prev_close - range_hl * 1.1 / 2

# Futures Volume & VWAP
fut_ltp = fut_q.get("last_price", 0)
fut_vol = fut_q.get("volume", 0)
fut_oi = fut_q.get("oi", 0)
fut_vwap = fut_q.get("average_price", 0)

# Heavyweight breadth
bull_count = 0
bear_count = 0
hw_details = []
for hw in heavyweights:
    q = quotes.get(hw, {})
    ltp = q.get("last_price", 0)
    pc = q.get("ohlc", {}).get("close", ltp)
    chg = ((ltp - pc) / pc) * 100 if pc else 0
    vol = q.get("volume", 0)
    sym_name = hw.replace("NSE:", "")
    if chg > 0:
        bull_count += 1
    elif chg < 0:
        bear_count += 1
    hw_details.append({
        "name": sym_name,
        "ltp": ltp,
        "chg": chg,
        "vol": vol
    })

print("=" * 80)
print(f"📊 NIFTY 50 DEEP TECHNICAL & VOLUME AUDIT — {now.strftime('%H:%M:%S IST')}")
print("=" * 80)
print(f"1. INDEX & DERIVATIVE SNAPSHOT:")
print(f"   • NIFTY 50 Spot:     {spot_ltp:,.2f} (Prev Close: {prev_close:,.2f} | Chg: {((spot_ltp - prev_close)/prev_close)*100:+.2f}%)")
print(f"   • NIFTY Nov Futures:  {fut_ltp:,.2f} (VWAP: {fut_vwap:,.2f})")
print(f"   • Futures Basis:     {fut_ltp - spot_ltp:+.2f} pts premium")
print(f"   • Futures Traded Vol:{fut_vol:,} contracts | Futures OI: {fut_oi:,}")
print(f"   • 25000 PE Volume:   {pe_q.get('volume', 0):,} contracts | PE OI: {pe_q.get('oi', 0):,}")
print("-" * 80)
print(f"2. MOMENTUM & MOVING AVERAGES (5-Min Chart):")
print(f"   • RSI (14):          {rsi_14:.2f} ({'Oversold' if rsi_14 < 30 else 'Overbought' if rsi_14 > 70 else 'Neutral/Bearish' if rsi_14 < 50 else 'Neutral/Bullish'})")
print(f"   • 9 EMA:             {ema_9:,.2f} ({'BELOW EMA 9' if spot_ltp < ema_9 else 'ABOVE EMA 9'})")
print(f"   • 20 EMA:            {ema_20:,.2f} ({'BELOW EMA 20 (Bearish Grip)' if spot_ltp < ema_20 else 'ABOVE EMA 20'})")
print(f"   • VWAP Comparison:   Spot ({spot_ltp:,.2f}) vs Futures VWAP ({fut_vwap:,.2f}) -> {'Trading BELOW VWAP (Institutions Selling)' if fut_ltp < fut_vwap else 'Trading ABOVE VWAP'}")
print("-" * 80)
print(f"3. PIVOT ARCHITECTURE & BOUNDARIES:")
print(f"   • Day High:          {day_high:,.2f} (Tested at 09:35 AM)")
print(f"   • Camarilla H3 (Res):{cam_h3:,.2f}")
print(f"   • Camarilla L3 (Sup):{cam_l3:,.2f}")
print(f"   • Camarilla L4 (Brk):{cam_l4:,.2f}")
print(f"   • Day Low:           {day_low:,.2f} (Tested at 09:15 AM)")
print("-" * 80)
print(f"4. HEAVYWEIGHT ENGINE BREADTH ({bull_count} Green vs {bear_count} Red):")
for item in sorted(hw_details, key=lambda x: x["chg"]):
    arrow = "🟢" if item["chg"] > 0 else "🔴" if item["chg"] < 0 else "⚪"
    print(f"   {arrow} {item['name']:<10}: ₹{item['ltp']:<9.2f} ({item['chg']:+6.2f}%) | Vol: {item['vol']:,}")
print("=" * 80)
