import os, sys, json
from datetime import datetime, timedelta
sys.path.insert(0, '/home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated')
from src.scanners.options_data_provider import get_kite_client

kite = get_kite_client()
if not kite:
    print("Failed to get Kite client")
    sys.exit(1)

# 1. Spot Quote
spot_q = kite.quote(['NSE:VEDL']).get('NSE:VEDL', {})
ltp = spot_q.get('last_price', 0)
ohlc = spot_q.get('ohlc', {})
print("=== 1. SPOT VEDL ===")
print("LTP:", ltp)
print(f"Open: {ohlc.get('open')}, High: {ohlc.get('high')}, Low: {ohlc.get('low')}, Prev Close: {ohlc.get('close')}")
prev_close = ohlc.get('close', ltp)
pct = ((ltp - prev_close) / prev_close) * 100 if prev_close else 0
print(f"Day Change: {pct:.2f}%")

# 2. Option Quote
opt_sym = "VEDL26OCT235CE"
opt_q = kite.quote([f"NFO:{opt_sym}"]).get(f"NFO:{opt_sym}", {})
print("\n=== 2. OPTION VEDL26OCT235CE ===")
print("LTP:", opt_q.get('last_price'))
opt_ohlc = opt_q.get('ohlc', {})
print(f"Open: {opt_ohlc.get('open')}, High: {opt_ohlc.get('high')}, Low: {opt_ohlc.get('low')}, Close: {opt_ohlc.get('close')}")
depth = opt_q.get('depth', {})
buys = depth.get('buy', [])
sells = depth.get('sell', [])
best_bid = buys[0].get('price', 0) if buys else 0
best_ask = sells[0].get('price', 0) if sells else 0
print(f"Best Bid: {best_bid}, Best Ask: {best_ask}, Volume: {opt_q.get('volume')}, OI: {opt_q.get('oi')}")

# 3. Position Details
net_pos = kite.positions().get('net', [])
print("\n=== 3. USER POSITION ===")
found_pos = False
for p in net_pos:
    if "VEDL" in p.get('tradingsymbol', ''):
        found_pos = True
        print(f"Symbol: {p.get('tradingsymbol')}")
        print(f"Quantity: {p.get('quantity')}")
        print(f"Buy Avg Price: {p.get('average_price')}")
        print(f"Current Value: {p.get('value')}")
        print(f"P&L: {p.get('pnl')}")
        print(f"M2M: {p.get('m2m')}")
if not found_pos:
    print("No VEDL position found in net positions.")

# 4. Expiry & Instrument Details
instruments = kite.instruments("NFO")
opt_token = None
expiry_date = None
for inst in instruments:
    if inst.get('tradingsymbol') == opt_sym:
        expiry_date = inst.get('expiry')
        opt_token = inst.get('instrument_token')
        print("\n=== 4. CONTRACT DETAILS ===")
        print(f"Expiry: {expiry_date}")
        print(f"Strike: {inst.get('strike')}")
        print(f"Lot Size: {inst.get('lot_size')}")
        break

# 5. Spot Historical Data (Last 60 days)
spot_inst = [i for i in kite.instruments("NSE") if i.get('tradingsymbol') == 'VEDL']
if spot_inst:
    spot_token = spot_inst[0]['instrument_token']
    hist = kite.historical_data(spot_token, datetime.now() - timedelta(days=60), datetime.now(), "day")
    print("\n=== 5. TECHNICAL SUMMARY (DAILY CANDLES) ===")
    closes = [c['close'] for c in hist]
    highs = [c['high'] for c in hist]
    lows = [c['low'] for c in hist]

    def calc_ema(prices, period):
        if len(prices) < period:
            return None
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        for p in prices[period:]:
            ema = (p - ema) * multiplier + ema
        return ema

    ema20 = calc_ema(closes, 20)
    ema50 = calc_ema(closes, 50)

    def calc_rsi(prices, period=14):
        if len(prices) <= period:
            return 50.0
        gains = []
        losses = []
        for i in range(1, len(prices)):
            chg = prices[i] - prices[i-1]
            if chg > 0:
                gains.append(chg)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(chg))
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * 13 + gains[i]) / 14
            avg_loss = (avg_loss * 13 + losses[i]) / 14
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    rsi14 = calc_rsi(closes, 14)
    recent_high = max(highs[-20:])
    recent_low = min(lows[-20:])

    print(f"Last 5 Closes: {[round(c, 2) for c in closes[-5:]]}")
    if ema20: print(f"20 EMA: {ema20:.2f}")
    if ema50: print(f"50 EMA: {ema50:.2f}")
    print(f"14-Day RSI: {rsi14:.1f}")
    print(f"20-Day Range: High ₹{recent_high:.2f} | Low ₹{recent_low:.2f}")

# 6. Option Chain Context (Near Strikes)
chain_strikes = [220, 225, 230, 235, 240, 245, 250]
chain_syms = []
for s in chain_strikes:
    chain_syms.append(f"NFO:VEDL26OCT{s}CE")
    chain_syms.append(f"NFO:VEDL26OCT{s}PE")
q_chain = kite.quote(chain_syms)
print("\n=== 6. NEARBY OPTION CHAIN (OCTOBER EXPIRY) ===")
print(f"{'Strike':<8} {'CE LTP':<10} {'CE OI':<12} {'PE LTP':<10} {'PE OI':<12}")
for s in chain_strikes:
    ce_k = f"NFO:VEDL26OCT{s}CE"
    pe_k = f"NFO:VEDL26OCT{s}PE"
    ce_d = q_chain.get(ce_k, {})
    pe_d = q_chain.get(pe_k, {})
    print(f"{s:<8} {ce_d.get('last_price', 0):<10.2f} {ce_d.get('oi', 0):<12} {pe_d.get('last_price', 0):<10.2f} {pe_d.get('oi', 0):<12}")
