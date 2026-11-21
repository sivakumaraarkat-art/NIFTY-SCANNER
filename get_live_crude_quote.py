import sys
import io
import json
import urllib.request
from datetime import datetime

# UTF-8 fix for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*'
}

def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return None

def main():
    print("=" * 75)
    print("🛢️  REAL-TIME GLOBAL & MCX CRUDE OIL PRICE CHECK")
    print("=" * 75)

    # 1. Fetch WTI and Brent from Yahoo Finance
    symbols = {
        'CL=F': 'WTI Crude Oil (NYMEX)',
        'BZ=F': 'Brent Crude Oil (ICE)',
        'INR=X': 'USD/INR Exchange Rate'
    }

    prices = {}
    for sym, name in symbols.items():
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=1d"
        data = fetch_json(url)
        if data and 'chart' in data and data['chart'].get('result'):
            meta = data['chart']['result'][0]['meta']
            ltp = meta.get('regularMarketPrice')
            prev = meta.get('chartPreviousClose')
            high = meta.get('regularMarketDayHigh')
            low = meta.get('regularMarketDayLow')
            chg = ltp - prev if ltp and prev else 0.0
            chg_pct = (chg / prev * 100.0) if prev else 0.0
            prices[sym] = {
                'name': name,
                'ltp': ltp,
                'prev': prev,
                'high': high,
                'low': low,
                'chg': chg,
                'chg_pct': chg_pct
            }
            badge = "🟢" if chg >= 0 else "🔴"
            print(f"{badge} {name:<25}: ${ltp:.2f}  ({chg:+.2f} / {chg_pct:+.2f}%)  [Low: ${low:.2f} - High: ${high:.2f}]")
        else:
            print(f"⚠️ Could not fetch {name}")

    print("-" * 75)

    # 2. Try fetching MCX Crude Oil from public Indian market feed
    mcx_urls = [
        "https://priceapi.moneycontrol.com/pricefeed/mcx/commoditycache/CRUDEOIL",
        "https://groww.in/v1/api/stocks_data/v1/commodity/CRUDEOIL",
        "https://web.stockedge.com/api/v1/commodities/crude-oil"
    ]

    mcx_found = False
    for u in mcx_urls:
        data = fetch_json(u)
        if data:
            # Parse Moneycontrol structure
            if 'data' in data:
                d = data['data']
                mcx_ltp = float(d.get('lastprice', 0) or d.get('price', 0) or 0)
                if mcx_ltp > 0:
                    mcx_found = True
                    prev = float(d.get('prev_close', 0) or mcx_ltp)
                    chg = mcx_ltp - prev
                    pct = (chg / prev * 100) if prev else 0.0
                    print(f"🇮🇳 MCX CRUDE OIL FUTURE:     ₹{mcx_ltp:,.2f}  ({chg:+.2f} / {pct:+.2f}%)")
                    print(f"   Expiry: {d.get('expiry_date', 'Near Expiry')} | High: ₹{d.get('high', 0)} | Low: ₹{d.get('low', 0)}")
                    break

    if not mcx_found and 'CL=F' in prices and 'INR=X' in prices:
        # Theoretical MCX conversion: WTI price * USDINR * conversion factor (~7.6 - 7.8 including duty)
        wti = prices['CL=F']['ltp']
        inr = prices['INR=X']['ltp'] or 84.0
        # Typical MCX Crude parity is approx WTI * 84 / barrel factor
        print("ℹ️  (MCX Direct Feed unavailable; Live NYMEX WTI & Brent displayed above)")

    print("-" * 75)
    print("📊 YOUR POSITION: CRUDE OIL 9550 CE (17-NOV EXPIRY, 1 LOT)")
    print(f"• Buy Price: ₹282.00 | Capital Invested: ₹28,200.00")
    print(f"• Your SL:   ₹270.00 (Risk: -12 pts / -₹1,200) -> ⚠️ Very tight (High noise risk)")
    print(f"• Rec SL:    ₹235.00 (Risk: -47 pts / -₹4,700) -> ✅ Safe Swing Buffer")
    print(f"• Target 1:  ₹365.00 (Gain: +83 pts / +₹8,300)")
    print("=" * 75)

if __name__ == "__main__":
    main()
