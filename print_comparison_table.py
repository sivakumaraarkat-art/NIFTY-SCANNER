import json

with open('portfolio_comparison_result.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('=== PORTFOLIO AUDIT vs MASTER EXIT PLAN ===\n')
print(f"{'Category':16} | {'Symbol':10} | {'Qty (P/Live)':12} | {'Buy Avg':8} | {'Live LTP':8} | {'P&L (₹)':10} | {'P&L%':7} | {'T1 (₹)':8} | {'Dist T1':8} | {'T2 (₹)':8} | {'Action Summary'}")
print('-' * 135)

for r in data['comparison']:
    cat = r['category'][:15] if r['category'] else ''
    sym = r['sym']
    q_str = f"{r['plan_qty']}/{r['live_qty']}"
    if not r['qty_match']:
        q_str += " ⚠️"
    avg = f"{r['live_avg']:.1f}"
    ltp = f"{r['live_ltp']:.1f}"
    pnl = f"{r['live_pnl']:+,.0f}"
    pnl_pct = f"{r['live_pnl_pct']:+5.1f}%"
    t1 = f"{r['target1']:.1f}" if r['target1'] else '-'
    t2 = f"{r['target2']:.1f}" if r['target2'] else '-'
    dt1 = f"{r['dist_t1_pct']:+5.1f}%" if r['dist_t1_pct'] is not None else '-'
    act = r['action'][:40] if r['action'] else ''

    print(f"{cat:16} | {sym:10} | {q_str:12} | {avg:>8} | {ltp:>8} | {pnl:>10} | {pnl_pct:>7} | {t1:>8} | {dt1:>8} | {t2:>8} | {act}")
