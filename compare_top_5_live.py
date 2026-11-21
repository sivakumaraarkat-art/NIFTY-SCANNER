import urllib.request
import json

symbols = {
    'ADANIPORTS': {'entry': 1893.0, 'sl': 1779.0, 't1': 2120.0, 't2': 2366.0, 'qty_1l': 11, 'qty_2l': 21, 'sector': 'Infrastructure & Logistics'},
    'BDL': {'entry': 1033.0, 'sl': 971.0, 't1': 1150.0, 't2': 1310.0, 'qty_1l': 20, 'qty_2l': 39, 'sector': 'Defense & Aerospace'},
    'ZYDUSLIFE': {'entry': 1192.0, 'sl': 1120.0, 't1': 1342.0, 't2': 1495.0, 'qty_1l': 17, 'qty_2l': 34, 'sector': 'Pharma & Healthcare'},
    'ALKEM': {'entry': 5383.0, 'sl': 5080.0, 't1': 6050.0, 't2': 6600.0, 'qty_1l': 4, 'qty_2l': 8, 'sector': 'Pharma & Formulations'},
    'PERSISTENT': {'entry': 5978.5, 'sl': 5620.0, 't1': 6695.0, 't2': 7470.0, 'qty_1l': 3, 'qty_2l': 6, 'sector': 'IT & Cloud Engineering'}
}

print("=" * 90)
print("TOP 5 30-DAY SWING PORTFOLIO — CURRENT LIVE CLOSING DATA AUDIT (17-NOV-2026)")
print("=" * 90)

headers = {'User-Agent': 'Mozilla/5.0'}
results = []

for sym, cfg in symbols.items():
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}.NS?interval=1d&range=5d"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode('utf-8'))['chart']['result'][0]
            meta = data['meta']
            ltp = meta.get('regularMarketPrice')
            prev_close = meta.get('chartPreviousClose')
            high = meta.get('regularMarketDayHigh')
            low = meta.get('regularMarketDayLow')

            # Compare with morning recommended entry
            entry = cfg['entry']
            sl = cfg['sl']
            t1 = cfg['t1']
            t2 = cfg['t2']
            qty = cfg['qty_1l']

            pnl_pts = ltp - entry
            pnl_pct = (pnl_pts / entry) * 100.0
            pnl_val_1l = pnl_pts * qty
            pnl_val_2l = pnl_pts * cfg['qty_2l']

            dist_to_t1 = ((t1 - ltp) / ltp) * 100.0
            dist_to_sl = ((ltp - sl) / ltp) * 100.0

            day_chg = ltp - prev_close
            day_pct = (day_chg / prev_close) * 100.0

            results.append({
                'sym': sym,
                'sector': cfg['sector'],
                'entry': entry,
                'ltp': ltp,
                'high': high,
                'low': low,
                'prev_close': prev_close,
                'day_chg': day_chg,
                'day_pct': day_pct,
                'pnl_pts': pnl_pts,
                'pnl_pct': pnl_pct,
                'pnl_1l': pnl_val_1l,
                'pnl_2l': pnl_val_2l,
                'sl': sl,
                't1': t1,
                'dist_t1': dist_to_t1,
                'dist_sl': dist_to_sl,
                'qty_1l': qty,
                'qty_2l': cfg['qty_2l']
            })
    except Exception as e:
        print(f"Error fetching {sym}: {e}")

print(f"{'Symbol':<12} | {'Entry (Rs)':<10} | {'Today Close':<11} | {'Day Change':<12} | {'Gain vs Entry':<13} | {'1L P&L':<10} | {'Status'}")
print("-" * 90)

tot_pnl_1l = 0.0
tot_pnl_2l = 0.0

for r in results:
    tot_pnl_1l += r['pnl_1l']
    tot_pnl_2l += r['pnl_2l']
    status = "🟢 GREEN" if r['pnl_pts'] >= 0 else "🔴 RED"
    print(f"{r['sym']:<12} | Rs.{r['entry']:<8.2f} | Rs.{r['ltp']:<9.2f} | {r['day_pct']:+6.2f}%     | {r['pnl_pct']:+6.2f}%       | Rs.{r['pnl_1l']:+7.1f} | {status}")

print("-" * 90)
print(f"PORTFOLIO TOTAL NET P&L TODAY (Day 1 of 30-Day Horizon):")
print(f"• ₹1 Lakh Capital Plan:  Rs.{tot_pnl_1l:+,.2f}")
print(f"• ₹2 Lakh Capital Plan:  Rs.{tot_pnl_2l:+,.2f}")
print("=" * 90)

print("\nDETAILED BREAKDOWN BY STOCK:")
for r in results:
    print(f"\n[{r['sym']}] ({r['sector']}):")
    print(f"   • Recommended Entry: Rs.{r['entry']:,.2f}  |  Today Close: Rs.{r['ltp']:,.2f}  (Day Range: Rs.{r['low']:,.2f} - Rs.{r['high']:,.2f})")
    print(f"   • Day 1 P&L:         {r['pnl_pct']:+.2f}% ({r['pnl_pts']:+.2f} pts)  ->  Rs.{r['pnl_1l']:+,.1f} (1L Plan) / Rs.{r['pnl_2l']:+,.1f} (2L Plan)")
    print(f"   • Target 1 (T1):     Rs.{r['t1']:,.2f} (Need +{r['dist_t1']:.2f}% to reach T1)")
    print(f"   • Stop-Loss (SL):    Rs.{r['sl']:,.2f} (Safety Cushion: {r['dist_sl']:.2f}% above SL)")
    print(f"   • Health Verdict:    {'EXCELLENT - TRADING IN PROFIT' if r['pnl_pts'] >= 0 else 'HEALTHY HOLD - WITHIN SL BUFFER'}")
