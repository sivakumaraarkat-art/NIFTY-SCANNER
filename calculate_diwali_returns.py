import sys
import io
import json
import urllib.request
from pathlib import Path
import pandas as pd

# UTF-8 fix for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*'
}

# The 10 Diwali Plan Stocks from Diwali_Muhurat_Two_Tranche_1L_Plus_1L_Plan_2026.xlsx
DIWALI_STOCKS = [
    {
        "rank": 1, "sym": "RVNL", "yahoo": "RVNL.NS", "name": "Rail Vikas Nigam Ltd",
        "t1_entry": 179.67, "t1_qty": 83, "t1_cost": 14912.61,
        "t2_entry": 168.00, "t2_qty": 89, "t2_cost": 14952.00,
        "target1": 205.00, "target2": 235.00
    },
    {
        "rank": 2, "sym": "IRFC", "yahoo": "IRFC.NS", "name": "Indian Railway Finance Corp",
        "t1_entry": 73.37, "t1_qty": 163, "t1_cost": 11959.31,
        "t2_entry": 69.50, "t2_qty": 172, "t2_cost": 11954.00,
        "target1": 82.50, "target2": 92.00
    },
    {
        "rank": 3, "sym": "TITAGARH", "yahoo": "TITAGARH.NS", "name": "Titagarh Rail Systems",
        "t1_entry": 654.15, "t1_qty": 18, "t1_cost": 11774.70,
        "t2_entry": 620.00, "t2_qty": 19, "t2_cost": 11780.00,
        "target1": 745.00, "target2": 820.00
    },
    {
        "rank": 4, "sym": "COCHINSHIP", "yahoo": "COCHINSHIP.NS", "name": "Cochin Shipyard Ltd",
        "t1_entry": 1114.20, "t1_qty": 10, "t1_cost": 11142.00,
        "t2_entry": 1070.00, "t2_qty": 11, "t2_cost": 11770.00,
        "target1": 1260.00, "target2": 1420.00
    },
    {
        "rank": 5, "sym": "APOLLO", "yahoo": "APOLLO.NS", "name": "Apollo Micro Systems / Apollo",
        "t1_entry": 398.75, "t1_qty": 25, "t1_cost": 9968.75,
        "t2_entry": 382.00, "t2_qty": 26, "t2_cost": 9932.00,
        "target1": 435.00, "target2": 465.00
    },
    {
        "rank": 6, "sym": "KAYNES", "yahoo": "KAYNES.NS", "name": "Kaynes Technology India",
        "t1_entry": 3131.00, "t1_qty": 3, "t1_cost": 9393.00,
        "t2_entry": 2980.00, "t2_qty": 3, "t2_cost": 8940.00,
        "target1": 3650.00, "target2": 4150.00
    },
    {
        "rank": 7, "sym": "RAILTEL", "yahoo": "RAILTEL.NS", "name": "RailTel Corp of India",
        "t1_entry": 222.40, "t1_qty": 40, "t1_cost": 8896.00,
        "t2_entry": 210.00, "t2_qty": 42, "t2_cost": 8820.00,
        "target1": 250.00, "target2": 275.00
    },
    {
        "rank": 8, "sym": "SUZLON", "yahoo": "SUZLON.NS", "name": "Suzlon Energy Ltd",
        "t1_entry": 33.90, "t1_qty": 206, "t1_cost": 6983.40,
        "t2_entry": 31.80, "t2_qty": 220, "t2_cost": 6996.00,
        "target1": 39.50, "target2": 45.00
    },
    {
        "rank": 9, "sym": "LODHA", "yahoo": "LODHA.NS", "name": "Macrotech Developers (Lodha)",
        "t1_entry": 1037.00, "t1_qty": 6, "t1_cost": 6222.00,
        "t2_entry": 980.00, "t2_qty": 7, "t2_cost": 6860.00,
        "target1": 1180.00, "target2": 1280.00
    },
    {
        "rank": 10, "sym": "PCBL", "yahoo": "PCBL.NS", "name": "PCBL Ltd (Phillips Carbon)",
        "t1_entry": 276.95, "t1_qty": 21, "t1_cost": 5815.95,
        "t2_entry": 260.00, "t2_qty": 23, "t2_cost": 5980.00,
        "target1": 315.00, "target2": 350.00
    }
]

def fetch_live_price(yahoo_symbol, fallback_parquet_sym):
    # Try Yahoo Finance API
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?interval=1d&range=5d"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            meta = data['chart']['result'][0]['meta']
            price = meta.get('regularMarketPrice')
            if price:
                return float(price), "Live Web"
    except Exception:
        pass

    # Fallback to local Parquet cache
    cache_file = Path(f"database/market_data_cache/NSE_{fallback_parquet_sym}_daily.parquet")
    if cache_file.exists():
        try:
            df = pd.read_parquet(cache_file)
            last_close = float(df['close'].iloc[-1])
            return last_close, "Parquet Cache"
        except Exception:
            pass

    return None, "Unavailable"

def audit_returns():
    print("=" * 105)
    print("🪔 DIWALI MUHURAT TWO-TRANCHE (1L + 1L) PORTFOLIO PERFORMANCE AUDIT")
    print("=" * 105)

    tot_t1_invested = 0.0
    tot_t1_current = 0.0

    print(f"{'STOCK':10} | {'ENTRY':8} | {'CURRENT':8} | {'RETURN %':10} | {'T1 P&L (₹)':12} | {'T1 VAL (₹)':12} | {'DATA SOURCE':12}")
    print("-" * 105)

    stock_results = []
    for item in DIWALI_STOCKS:
        sym = item['sym']
        t1_entry = item['t1_entry']
        t1_qty = item['t1_qty']
        t1_cost = item['t1_cost']

        current_price, source = fetch_live_price(item['yahoo'], sym)
        if current_price is None:
            current_price = t1_entry # Neutral fallback

        cur_val = current_price * t1_qty
        pnl_rupees = cur_val - t1_cost
        pnl_pct = ((current_price - t1_entry) / t1_entry) * 100.0

        tot_t1_invested += t1_cost
        tot_t1_current += cur_val

        badge = "+" if pnl_pct >= 0 else ""
        print(f"{sym:<10} | ₹{t1_entry:<7.2f} | ₹{current_price:<7.2f} | {badge}{pnl_pct:<8.2f}% | {badge}₹{pnl_rupees:<10.2f} | ₹{cur_val:<10.2f} | {source}")

        stock_results.append({
            "sym": sym,
            "entry": t1_entry,
            "current": current_price,
            "pnl_pct": pnl_pct,
            "pnl_rupees": pnl_rupees,
            "t1_cost": t1_cost,
            "cur_val": cur_val
        })

    print("=" * 105)
    tot_pnl = tot_t1_current - tot_t1_invested
    tot_pnl_pct = (tot_pnl / tot_t1_invested) * 100.0
    sign = "+" if tot_pnl >= 0 else ""

    print(f"💰 TOTAL TRANCHE 1 CAPITAL INVESTED: ₹{tot_t1_invested:,.2f}")
    print(f"📈 TOTAL CURRENT PORTFOLIO VALUE:   ₹{tot_t1_current:,.2f}")
    print(f"🎯 NET OVERALL RETURN:              {sign}₹{tot_pnl:,.2f} ({sign}{tot_pnl_pct:.2f}%)")
    print("=" * 105)

    # Best and worst performers
    sorted_stocks = sorted(stock_results, key=lambda x: x['pnl_pct'], reverse=True)
    best = sorted_stocks[0]
    worst = sorted_stocks[-1]
    print(f"🏆 Top Performer:   {best['sym']} ({best['pnl_pct']:+.2f}% | {best['pnl_rupees']:+,.2f} P&L)")
    print(f"🔻 Worst Performer: {worst['sym']} ({worst['pnl_pct']:+.2f}% | {worst['pnl_rupees']:+,.2f} P&L)")
    print("=" * 105)

if __name__ == "__main__":
    audit_returns()
