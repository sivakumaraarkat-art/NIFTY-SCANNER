"""
check_portfolio_10d_pnl.py
Calculates exact daily and cumulative 10-day profit & loss (P&L)
for your Zerodha equity holdings by querying live holdings and
historical daily closing prices directly from Kite Connect API.
"""

import sys
import io
from pathlib import Path
from datetime import datetime, timedelta

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent

try:
    from kiteconnect import KiteConnect
    token_file = ROOT / ".kite_access_token"
    key_file = ROOT / ".kite_api_key"

    if not token_file.exists() or not key_file.exists():
        print("❌ Kite token or API key file missing in project root.")
        sys.exit(1)

    access_token = token_file.read_text(encoding="utf-8").strip()
    api_key = key_file.read_text(encoding="utf-8").strip()

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

    profile = kite.profile()
    user_name = profile.get("user_name", "N/A")
    user_id = profile.get("user_id", "N/A")

    print("=" * 85)
    print(f"📊 ZERODHA PORTFOLIO 10-DAY P&L AUDIT | Account: {user_name} ({user_id})")
    print("=" * 85)

    holdings = kite.holdings()
    if not holdings:
        print("⚠️ No equity holdings found in this Zerodha account.")
        sys.exit(0)

    # Filter out holdings with qty = 0
    active_holdings = [h for h in holdings if (h.get("quantity", 0) + h.get("t1_quantity", 0)) > 0]
    total_holdings_count = len(active_holdings)
    print(f"[*] Found {total_holdings_count} active equity holdings in your portfolio.\n")

    # Overall Summary
    total_invested = sum((h.get("quantity", 0) + h.get("t1_quantity", 0)) * h.get("average_price", 0.0) for h in active_holdings)
    current_value = sum((h.get("quantity", 0) + h.get("t1_quantity", 0)) * h.get("last_price", 0.0) for h in active_holdings)
    overall_pnl = current_value - total_invested
    overall_pnl_pct = (overall_pnl / total_invested * 100) if total_invested > 0 else 0.0

    print("💼 OVERALL PORTFOLIO SNAPSHOT:")
    print(f"   • Total Invested Capital : ₹{total_invested:,.2f}")
    print(f"   • Current Portfolio Value: ₹{current_value:,.2f}")
    print(f"   • All-Time Unrealized P&L: ₹{overall_pnl:+,.2f} ({overall_pnl_pct:+.2f}%)")
    print("=" * 85)

    # Fetch daily historical candles for the last 25 calendar days (to capture 10+ trading days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=28)

    print("\n⏳ Fetching 10-day daily closing bars for each holding from Zerodha...")

    stock_daily_data = {}
    trading_dates = set()

    for h in active_holdings:
        sym = h.get("tradingsymbol")
        inst_token = h.get("instrument_token")
        qty = h.get("quantity", 0) + h.get("t1_quantity", 0)
        avg_price = h.get("average_price", 0.0)
        ltp = h.get("last_price", 0.0)

        daily_closes = {}
        try:
            candles = kite.historical_data(inst_token, start_date, end_date, "day")
            for c in candles:
                d_str = c["date"].strftime("%Y-%m-%d")
                daily_closes[d_str] = c["close"]
                trading_dates.add(d_str)
        except Exception as e:
            pass

        stock_daily_data[sym] = {
            "qty": qty,
            "avg_price": avg_price,
            "ltp": ltp,
            "daily_closes": daily_closes
        }

    sorted_dates = sorted(list(trading_dates))
    # Target last 10 trading days
    if len(sorted_dates) > 10:
        target_dates = sorted_dates[-10:]
    else:
        target_dates = sorted_dates

    # Calculate portfolio value on each date
    daily_portfolio_values = {}
    for d in sorted_dates:
        val = 0.0
        for sym, d_info in stock_daily_data.items():
            qty = d_info["qty"]
            close = d_info["daily_closes"].get(d, d_info["ltp"])
            val += qty * close
        daily_portfolio_values[d] = val

    print("\n" + "=" * 85)
    print("📅 LAST 10 SESSIONS: DAY-BY-DAY PORTFOLIO VALUE & P&L MOVEMENT")
    print("=" * 85)
    print(f"{'#':3} | {'TRADING DATE':14} | {'PORTFOLIO VALUE':18} | {'DAY-OVER-DAY P&L (₹)':22} | {'DAY CHG (%)':12}")
    print("-" * 85)

    ten_day_start_val = None
    row_num = 1

    for idx, d in enumerate(sorted_dates):
        curr_val = daily_portfolio_values[d]
        if d in target_dates:
            prev_date = sorted_dates[idx - 1] if idx > 0 else None
            prev_val = daily_portfolio_values.get(prev_date, curr_val) if prev_date else curr_val

            if ten_day_start_val is None:
                ten_day_start_val = prev_val

            dod_pnl = curr_val - prev_val
            dod_pct = (dod_pnl / prev_val * 100) if prev_val > 0 else 0.0
            sign = "+" if dod_pnl >= 0 else ""
            print(f"{row_num:<3} | {d:14} | ₹{curr_val:15,.2f} | {sign}₹{dod_pnl:18,.2f} | {sign}{dod_pct:9.2f}%")
            row_num += 1

    # Net 10-Day Change
    if ten_day_start_val is not None and target_dates:
        latest_val = daily_portfolio_values[target_dates[-1]]
        net_10d_pnl = latest_val - ten_day_start_val
        net_10d_pct = (net_10d_pnl / ten_day_start_val * 100) if ten_day_start_val > 0 else 0.0
        sign_10d = "+" if net_10d_pnl >= 0 else ""

        print("-" * 85)
        print(f"⭐ 10-DAY NET PORTFOLIO P&L : {sign_10d}₹{net_10d_pnl:,.2f} ({sign_10d}{net_10d_pct:.2f}%)")
        print(f"   (From {target_dates[0]} opening baseline ₹{ten_day_start_val:,.2f} → {target_dates[-1]} close ₹{latest_val:,.2f})")
    print("=" * 85)

    # Top Gainers and Losers across the 10 days
    perf_list = []
    if len(target_dates) >= 2:
        t_first = target_dates[0]
        t_last = target_dates[-1]
        for sym, d_info in stock_daily_data.items():
            qty = d_info["qty"]
            p_start = d_info["daily_closes"].get(t_first, d_info["avg_price"])
            p_end = d_info["daily_closes"].get(t_last, d_info["ltp"])
            chg_inr = (p_end - p_start) * qty
            chg_pct = ((p_end - p_start) / p_start * 100) if p_start > 0 else 0.0
            perf_list.append((sym, qty, p_start, p_end, chg_inr, chg_pct))

    if perf_list:
        perf_list.sort(key=lambda x: x[4], reverse=True)
        print("\n🏆 TOP 5 GAINERS IN YOUR PORTFOLIO (LAST 10 SESSIONS):")
        for sym, qty, p_start, p_end, chg_inr, chg_pct in perf_list[:5]:
            if chg_inr > 0:
                print(f"   ▲ {sym:<12} : +₹{chg_inr:9,.2f} ({chg_pct:+6.2f}%) | ₹{p_start:,.2f} → ₹{p_end:,.2f} ({qty} shares)")

        perf_list.sort(key=lambda x: x[4])
        print("\n📉 TOP 5 DRAGGERS / LOSSES IN YOUR PORTFOLIO (LAST 10 SESSIONS):")
        for sym, qty, p_start, p_end, chg_inr, chg_pct in perf_list[:5]:
            if chg_inr < 0:
                print(f"   ▼ {sym:<12} : -₹{abs(chg_inr):9,.2f} ({chg_pct:+6.2f}%) | ₹{p_start:,.2f} → ₹{p_end:,.2f} ({qty} shares)")

    print("\n" + "=" * 85)

except Exception as e:
    import traceback
    print(f"❌ Error during 10-day portfolio audit: {e}")
    traceback.print_exc()
