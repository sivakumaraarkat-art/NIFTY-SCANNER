"""
check_latest_now.py
Comprehensive real-time audit:
1. Live Market Indices (Nifty 50, Bank Nifty, India VIX)
2. User's Demat Positions, Margins & P&L
3. Active GTT Orders & Order Book
4. Cloud VM latest scan triggers (11:45/11:50 AM crons)
"""

import sys
import subprocess
from pathlib import Path

# UTF-8 fix for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent

try:
    from kiteconnect import KiteConnect

    api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
    token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(token)

    print("=" * 85)
    print("⚡ LIVE MARKET & ACCOUNT AUDIT")
    print("=" * 85)

    # 1. Market Indices
    idx_symbols = ["NSE:NIFTY 50", "NSE:NIFTY BANK", "NSE:INDIA VIX"]
    idx_quotes = kite.quote(idx_symbols)

    print("\n📊 LIVE INDICES & VOLATILITY:")
    print("-" * 85)
    for sym in idx_symbols:
        q = idx_quotes.get(sym, {})
        ltp = q.get("last_price", 0.0)
        ohlc = q.get("ohlc", {})
        prev = ohlc.get("close", ltp)
        chg = ltp - prev
        pct = (chg / prev * 100) if prev else 0.0
        emoji = "🟢" if chg >= 0 else "🔴"
        print(f"  • {sym:<16} : ₹{ltp:>9.2f} | Chg: {chg:>+7.2f} ({pct:>+5.2f}%) {emoji}")

    # 2. Key Stocks Under Watch
    watch_stocks = ["NSE:COCHINSHIP", "NSE:IRB", "NSE:DIVISLAB", "NSE:DATAPATTNS", "NSE:JUBLFOOD"]
    stk_quotes = kite.quote(watch_stocks)
    print("\n🔍 WATCHLIST STOCKS LIVE STATUS:")
    print("-" * 85)
    for sym in watch_stocks:
        q = stk_quotes.get(sym, {})
        ltp = q.get("last_price", 0.0)
        ohlc = q.get("ohlc", {})
        prev = ohlc.get("close", ltp)
        high = ohlc.get("high", ltp)
        low = ohlc.get("low", ltp)
        chg = ltp - prev
        pct = (chg / prev * 100) if prev else 0.0
        emoji = "🟢" if chg >= 0 else "🔴"
        print(f"  • {sym:<16} : ₹{ltp:>9.2f} | Chg: {chg:>+7.2f} ({pct:>+5.2f}%) {emoji} | Range: ₹{low:.2f} - ₹{high:.2f}")

    # 3. User's Positions
    positions = kite.positions()
    net_pos = positions.get("net", [])
    open_pos = [p for p in net_pos if p.get("quantity", 0) != 0]

    print("\n💼 OPEN DERIVATIVE / INTRADAY POSITIONS:")
    print("-" * 85)
    if open_pos:
        for p in open_pos:
            tsym = p.get("tradingsymbol")
            qty = p.get("quantity")
            buy_val = p.get("buy_value", 0.0)
            m2m = p.get("m2m", 0.0)
            pnl = p.get("pnl", 0.0)
            ltp = p.get("last_price", 0.0)
            print(f"  • {tsym} | Qty: {qty} | LTP: ₹{ltp:.2f} | M2M: ₹{m2m:+.2f} | P&L: ₹{pnl:+.2f}")
    else:
        print("  ✅ Zero open derivative/intraday positions. All previous trades closed!")

    # 4. Cash Margins
    margins = kite.margins()
    equity_margin = margins.get("equity", {})
    available_cash = equity_margin.get("available", {}).get("live_balance", 0.0)
    net_cash = equity_margin.get("net", 0.0)
    print(f"\n💰 MARGIN AVAILABLE: Live Cash: ₹{available_cash:,.2f} | Net Margin: ₹{net_cash:,.2f}")

    # 5. Active GTT Orders
    gtts = kite.get_gtts()
    active_gtts = [g for g in gtts if g.get("status") == "active"]
    print(f"\n📋 ACTIVE GTT ORDERS ({len(active_gtts)} active):")
    print("-" * 85)
    if active_gtts:
        for g in active_gtts:
            gid = g.get("id")
            tsym = g.get("condition", {}).get("tradingsymbol")
            triggers = g.get("condition", {}).get("trigger_values", [])
            last_p = g.get("condition", {}).get("last_price", 0.0)
            print(f"  • GTT #{gid} | {tsym} | Last Price: ₹{last_p:.2f} | Triggers: {triggers}")
    else:
        print("  • No active GTT orders pending.")

    # 6. Check Cloud VM Latest Status
    KEY_PATH = Path("D:/NiftyScanner/oracle/nifty-v15.key")
    VM_HOST = "ubuntu@140.245.195.112"
    if KEY_PATH.exists():
        print("\n🌐 CLOUD VM LATEST LOGS & CRON STATUS:")
        print("-" * 85)
        ssh_cmd = [
            "ssh", "-i", str(KEY_PATH), "-o", "StrictHostKeyChecking=no",
            VM_HOST,
            "ls -lt /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/logs/ | head -n 6"
        ]
        res = subprocess.run(ssh_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
        print(res.stdout.strip())

    print("=" * 85)

except Exception as e:
    print(f"❌ Error during latest audit: {e}")
