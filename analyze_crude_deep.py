import urllib.request
import json
import datetime
import math

def fetch_yahoo_chart(symbol, interval='5m', range_val='1d'):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={range_val}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8'))

def calculate_rsi(closes, period=14):
    if len(closes) <= period:
        return 50.0
    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        if diff >= 0:
            gains.append(diff)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(diff))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def calculate_ema(closes, period):
    if len(closes) < period:
        return closes[-1]
    k = 2.0 / (period + 1)
    ema = sum(closes[:period]) / period
    for c in closes[period:]:
        ema = c * k + ema * (1 - k)
    return ema

def analyze_crude():
    print("=" * 80)
    print("CRUDE OIL MULTI-TIMEFRAME DEEP TECHNICAL ANALYSIS")
    print("=" * 80)

    # Fetch WTI 5m
    wti_5m = fetch_yahoo_chart('CL=F', '5m', '1d')['chart']['result'][0]
    meta_5m = wti_5m['meta']
    timestamps = wti_5m['timestamp']
    q_5m = wti_5m['indicators']['quote'][0]

    ltp = meta_5m['regularMarketPrice']
    day_high = meta_5m['regularMarketDayHigh']
    day_low = meta_5m['regularMarketDayLow']
    prev_close = meta_5m['chartPreviousClose']
    change = ltp - prev_close
    pct_change = (change / prev_close) * 100.0

    # Filter valid candle closes
    valid_data = []
    for t, o, h, l, c, v in zip(timestamps, q_5m['open'], q_5m['high'], q_5m['low'], q_5m['close'], q_5m['volume']):
        if c is not None and o is not None and h is not None and l is not None:
            valid_data.append((t, o, h, l, c, v or 0))

    closes = [d[4] for d in valid_data]
    highs = [d[2] for d in valid_data]
    lows = [d[3] for d in valid_data]
    vols = [d[5] for d in valid_data]

    ema9 = calculate_ema(closes, 9)
    ema21 = calculate_ema(closes, 21)
    ema50 = calculate_ema(closes, 50)
    rsi14 = calculate_rsi(closes, 14)

    # Intraday VWAP
    cum_pv = sum([(h + l + c) / 3.0 * v for (_, _, h, l, c, v) in valid_data])
    total_vol = sum(vols)
    vwap = (cum_pv / total_vol) if total_vol > 0 else ltp

    # Fetch USD/INR
    inr_data = fetch_yahoo_chart('INR=X', '1d', '1d')['chart']['result'][0]
    usd_inr = inr_data['meta']['regularMarketPrice']

    # MCX Calculated
    mcx_ltp = ltp * usd_inr
    mcx_high = day_high * usd_inr
    mcx_low = day_low * usd_inr
    mcx_prev = prev_close * usd_inr
    mcx_change = mcx_ltp - mcx_prev
    mcx_pct = (mcx_change / mcx_prev) * 100.0

    print(f"• WTI Spot (NYMEX):     ${ltp:.2f} ({change:+.2f} / {pct_change:+.2f}%)")
    print(f"• WTI Intraday Range:  Low: ${day_low:.2f} | High: ${day_high:.2f}")
    print(f"• USD / INR:           Rs.{usd_inr:.2f}")
    print(f"• MCX Projected LTP:   Rs.{mcx_ltp:,.1f} ({mcx_change:+.1f} / {mcx_pct:+.2f}%)")
    print(f"• MCX Intraday Range:  Low: Rs.{mcx_low:,.1f} | High: Rs.{mcx_high:,.1f}")
    print("-" * 80)
    print("INTRADAY MOMENTUM INDICATORS (5-Min Chart):")
    print(f"• EMA 9:               ${ema9:.2f}  (MCX ~Rs.{ema9*usd_inr:,.1f})")
    print(f"• EMA 21:              ${ema21:.2f}  (MCX ~Rs.{ema21*usd_inr:,.1f})")
    print(f"• EMA 50:              ${ema50:.2f}  (MCX ~Rs.{ema50*usd_inr:,.1f})")
    print(f"• RSI (14):            {rsi14:.1f} ({'Overbought' if rsi14 > 70 else 'Oversold' if rsi14 < 30 else 'Neutral / Healthy'})")
    print(f"• VWAP:                ${vwap:.2f}  (MCX ~Rs.{vwap*usd_inr:,.1f})")

    trend = "BULLISH" if ltp > ema21 and ema9 > ema21 else "BEARISH" if ltp < ema21 and ema9 < ema21 else "RANGEBOUND / CONSOLIDATION"
    print(f"• Current Signal:      {trend}")
    print("=" * 80)

    # Print last 8 candles
    print("RECENT 5-MIN CANDLES:")
    print("Time  | Open   | High   | Low    | Close  | Volume | Candlestick Bias")
    print("-" * 70)
    for t, o, h, l, c, v in valid_data[-8:]:
        dt_str = datetime.datetime.fromtimestamp(t).strftime('%H:%M')
        bias = "BULL GREEN" if c > o else "BEAR RED" if c < o else "DOJI"
        print(f"{dt_str} | {o:.2f}  | {h:.2f}  | {l:.2f}  | {c:.2f}  | {v:<6} | {bias}")

    return {
        'wti_ltp': ltp,
        'mcx_ltp': mcx_ltp,
        'usd_inr': usd_inr,
        'ema9': ema9 * usd_inr,
        'ema21': ema21 * usd_inr,
        'rsi': rsi14,
        'trend': trend,
        'high': mcx_high,
        'low': mcx_low
    }

if __name__ == '__main__':
    res = analyze_crude()
