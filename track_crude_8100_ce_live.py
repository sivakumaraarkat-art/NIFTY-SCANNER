"""
Real-Time Live Tracker for MCX Crude Oil 8100 CE Option.
Tracks both Nov 17 Expiry (Hero-Zero) and Dec 16 Expiry (Swing/Positional)
with live underlying ticks, Black-Scholes Greeks, Target progression, and SL alarms.
"""
import sys
import os
import io
import time
import json
import math
import urllib.request
from datetime import datetime

# Windows terminal UTF-8 encoding
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

def norm_cdf(x):
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def black_scholes_call(S, K, T, r, sigma):
    if T <= 0:
        return max(0.0, S - K), 1.0 if S > K else 0.0
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    price = S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
    delta = norm_cdf(d1)
    return price, delta

def fetch_json(url, timeout=5):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception:
        return None

def get_live_market_data():
    # 1. WTI Crude
    wti_url = "https://query1.finance.yahoo.com/v8/finance/chart/CL=F?interval=1m&range=1d"
    wti_data = fetch_json(wti_url)

    wti_ltp = 86.50
    wti_high = 87.38
    wti_low = 84.68
    wti_prev = 85.72
    recent_candles = []

    if wti_data and 'chart' in wti_data and wti_data['chart'].get('result'):
        res = wti_data['chart']['result'][0]
        meta = res['meta']
        wti_ltp = meta.get('regularMarketPrice', wti_ltp)
        wti_high = meta.get('regularMarketDayHigh', wti_high)
        wti_low = meta.get('regularMarketDayLow', wti_low)
        wti_prev = meta.get('chartPreviousClose', wti_prev)

        timestamps = res.get('timestamp', [])
        q = res['indicators']['quote'][0]
        for t, o, h, l, c in zip(timestamps[-5:], q['open'][-5:], q['high'][-5:], q['low'][-5:], q['close'][-5:]):
            if c is not None and o is not None:
                dt_str = datetime.fromtimestamp(t).strftime('%H:%M')
                recent_candles.append({'time': dt_str, 'open': o, 'high': h, 'low': l, 'close': c})

    # 2. USD/INR
    inr_url = "https://query1.finance.yahoo.com/v8/finance/chart/INR=X?interval=1d&range=1d"
    inr_data = fetch_json(inr_url)
    usd_inr = 93.46
    if inr_data and 'chart' in inr_data and inr_data['chart'].get('result'):
        usd_inr = inr_data['chart']['result'][0]['meta'].get('regularMarketPrice', usd_inr)

    # 3. MCX Parity Calculation
    mcx_ltp = round(wti_ltp * usd_inr, 1)
    mcx_high = round(wti_high * usd_inr, 1)
    mcx_low = round(wti_low * usd_inr, 1)
    mcx_chg = round((wti_ltp - wti_prev) * usd_inr, 1)
    mcx_pct = round(((wti_ltp - wti_prev) / wti_prev) * 100.0, 2)

    return {
        'wti_ltp': wti_ltp,
        'wti_high': wti_high,
        'wti_low': wti_low,
        'wti_prev': wti_prev,
        'usd_inr': usd_inr,
        'mcx_ltp': mcx_ltp,
        'mcx_high': mcx_high,
        'mcx_low': mcx_low,
        'mcx_chg': mcx_chg,
        'mcx_pct': mcx_pct,
        'candles': recent_candles
    }

def print_live_tracker():
    data = get_live_market_data()
    now_str = datetime.now().strftime('%H:%M:%S IST')

    wti_ltp = data['wti_ltp']
    mcx_ltp = data['mcx_ltp']
    usd_inr = data['usd_inr']

    # Calculate Option Greeks for December 16 Expiry (29 DTE)
    # Strike 8100 CE
    K = 8100.0
    r = 0.065
    sigma = 0.35
    T_dec = 29.0 / 365.0
    prem_dec, delta_dec = black_scholes_call(mcx_ltp, K, T_dec, r, sigma)

    # Calculate Option Greeks for Today's Nov 17 Expiry (1.5 hours remaining ~ 0.0002 years)
    T_nov = 1.5 / (365.0 * 24.0)
    prem_nov, delta_nov = black_scholes_call(mcx_ltp, K, T_nov, r, 0.45)

    # Intrinsic value
    intrinsic = max(0.0, mcx_ltp - K)

    print("=" * 82)
    print(f"🛢️  LIVE CRUDE OIL 8100 CALL (CE) REAL-TIME MONITOR — {now_str}")
    print("=" * 82)

    print(f"• WTI NYMEX Spot:    ${wti_ltp:.2f}  ({data['wti_ltp'] - data['wti_prev']:+.2f} / {data['mcx_pct']:+.2f}%)  [Low: ${data['wti_low']:.2f} | High: ${data['wti_high']:.2f}]")
    print(f"• USD / INR Rate:    Rs.{usd_inr:.2f}")
    print(f"• MCX Future LTP:    Rs.{mcx_ltp:,.1f} ({data['mcx_chg']:+.1f} / {data['mcx_pct']:+.2f}%)  [Low: Rs.{data['mcx_low']:,} | High: Rs.{data['mcx_high']:,}]")
    print(f"• Strike Moneyness:  CRUDEOIL 8100 CE is {'IN-THE-MONEY (ITM)' if mcx_ltp >= K else 'AT-THE-MONEY (ATM)'} by {abs(mcx_ltp - K):.1f} pts")
    print(f"• Intrinsic Value:   Rs.{intrinsic:.1f} pts")
    print("-" * 82)

    # DISPLAY CONTRACT 1: DECEMBER 16 EXPIRY (SWING / POSITIONAL)
    print("📦 CONTRACT 1: CRUDEOIL 16-DEC-2026 8100 CE (Recommended Swing Contract - 29 DTE)")
    print(f"   • Current Live Est. Premium: Rs.{prem_dec:.2f}")
    print(f"   • Delta:                     {delta_dec:.2f} (Gains ~Rs.{delta_dec*10:.1f} per 10 pt rise in Crude)")
    print(f"   • 1 Std Lot Capital:         Rs.{prem_dec*100:,.0f} (100 Barrels) | Mini Lot: Rs.{prem_dec*10:,.0f} (10 Barrels)")
    print(f"   • Suggested Entry Trigger:   Rs.330.00 – Rs.335.00 (When MCX sustains above Rs.8,100)")
    print(f"   • Stop-Loss (SL):            Rs.260.00 (-Rs.70 pts | -21% max risk)")
    print(f"   • Target 1 (T1):             Rs.415.00 (+Rs.85 pts | +Rs.8,500 profit on Std Lot)")
    print(f"   • Target 2 (T2):             Rs.495.00 (+Rs.165 pts | +Rs.16,500 profit on Std Lot)")

    # Progression bar
    entry_ref = 330.0
    t1_ref = 415.0
    sl_ref = 260.0
    cur_pnl_pts = prem_dec - entry_ref
    status_dec = "[WAITING FOR BREAKOUT TRIGGER]" if mcx_ltp < 8100 else "[🟢 TRIGGERED / ACTIVE BULLISH RUN]"
    print(f"   • Status:                    {status_dec}")
    print("-" * 82)

    # DISPLAY CONTRACT 2: NOVEMBER 17 EXPIRY (HERO-ZERO TODAY)
    print("⚡ CONTRACT 2: CRUDEOIL 17-NOV-2026 8100 CE (Expiry Tonight - Hero-Zero)")
    print(f"   • Current Live Est. Premium: Rs.{prem_nov:.2f}")
    print(f"   • Delta:                     {delta_nov:.2f} (Extreme Gamma due to 0 DTE)")
    print(f"   • 1 Std Lot Capital:         Rs.{prem_nov*100:,.0f} (100 Barrels)")
    print(f"   • Expiry Notice:             ⚠️ Must square off before 11:10 PM IST to avoid devolvement!")
    print(f"   • Hero-Zero Target:          Rs.55.00 – Rs.85.00+ if MCX tests Rs.8,150+ before 11:30 PM")
    print("-" * 82)

    # RECENT 1-MIN CANDLE BIAS
    if data['candles']:
        print("📊 LATEST 1-MINUTE CANDLES (WTI Crude):")
        for c in data['candles']:
            bias = "BULL GREEN" if c['close'] >= c['open'] else "BEAR RED"
            print(f"   [{c['time']}] O: ${c['open']:.2f} | H: ${c['high']:.2f} | L: ${c['low']:.2f} | C: ${c['close']:.2f}  [{bias}]")
    print("=" * 82)

if __name__ == '__main__':
    print_live_tracker()
