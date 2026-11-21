"""
track_gail_190_ce_live.py
=========================
Real-Time Live Tracker for GAIL 190 CE Option (NFO:GAIL26NOV190CE) & GAIL Cash (NSE:GAIL).
Monitors market open (09:15 AM IST), tracks live prices, bid-ask depth, volume,
OI shifts, Target progression (T1: 2x, T2: 4x, T3: 6x+), and Stop Loss alerts.
"""

import sys
import time
import argparse
from datetime import datetime, time as dtime
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent

# Load Kite credentials
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()

from kiteconnect import KiteConnect
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

CASH_SYM = "NSE:GAIL"
OPT_SYM = "NFO:GAIL26NOV190CE"
BENCH_SYM = "NSE:NIFTY 50"
LOT_SIZE = 3550
BASE_PREMIUM = 1.78
STRIKE = 190.0

# Targets & SL
TARGET_1 = 3.60   # 2.0x (Double - Free Trade Trigger)
TARGET_2 = 7.00   # 3.9x (Quadruple)
TARGET_3 = 10.50  # 5.9x (Super Boom)
STOP_LOSS_OPT = 1.10
STOP_LOSS_CASH = 187.50

def parse_args():
    parser = argparse.ArgumentParser(description="Live Tracker for GAIL 190 CE")
    parser.add_argument("--once", action="store_true", help="Print single snapshot and exit")
    parser.add_argument("--interval", type=int, default=3, help="Polling interval in seconds (default: 3s)")
    return parser.parse_args()

def display_snapshot():
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # Check market phase
    market_open = dtime(9, 15)
    market_close = dtime(15, 30)
    cur_time = now.time()

    if cur_time < dtime(9, 0):
        phase = "PRE-MARKET (WAITING FOR 09:00 PRE-OPEN / 09:15 BELL)"
    elif cur_time < market_open:
        phase = "PRE-OPEN SESSION (09:00 - 09:08 ORDER DISCOVERY)"
    elif cur_time <= market_close:
        phase = "🟢 REGULAR LIVE MARKET (CONTINUOUS TRADING)"
    else:
        phase = "🔴 POST-MARKET (MARKET CLOSED)"

    quotes = kite.quote([CASH_SYM, OPT_SYM, BENCH_SYM])
    cash_q = quotes.get(CASH_SYM, {})
    opt_q = quotes.get(OPT_SYM, {})
    nifty_q = quotes.get(BENCH_SYM, {})

    # Cash metrics
    c_ltp = cash_q.get("last_price", 190.00)
    c_ohlc = cash_q.get("ohlc", {})
    c_prev = c_ohlc.get("close", c_ltp)
    c_open = c_ohlc.get("open", c_ltp)
    c_high = c_ohlc.get("high", c_ltp)
    c_low = c_ohlc.get("low", c_ltp)
    c_vol = cash_q.get("volume", 0)
    c_chg = ((c_ltp - c_prev) / c_prev * 100) if c_prev else 0.0

    # Option metrics
    o_ltp = opt_q.get("last_price", BASE_PREMIUM)
    o_ohlc = opt_q.get("ohlc", {})
    o_prev = o_ohlc.get("close", o_ltp)
    o_open = o_ohlc.get("open", o_ltp)
    o_high = o_ohlc.get("high", o_ltp)
    o_low = o_ohlc.get("low", o_ltp)
    o_vol = opt_q.get("volume", 0)
    o_oi = opt_q.get("oi", 0)
    o_chg = ((o_ltp - o_prev) / o_prev * 100) if o_prev else 0.0

    # Payoff multiplier from base (1.78)
    multiplier = o_ltp / BASE_PREMIUM if BASE_PREMIUM > 0 else 1.0
    pnl_per_lot = (o_ltp - BASE_PREMIUM) * LOT_SIZE

    # Nifty
    n_ltp = nifty_q.get("last_price", 25227.95)
    n_prev = nifty_q.get("ohlc", {}).get("close", n_ltp)
    n_chg = ((n_ltp - n_prev) / n_prev * 100) if n_prev else 0.0

    # Distance to In-The-Money
    dist_to_itm = STRIKE - c_ltp
    status_itm = "IN-THE-MONEY (ITM) 🚀" if c_ltp >= STRIKE else f"OTM (Only ₹{dist_to_itm:.2f} to Strike 190)"

    print("=" * 95)
    print(f"🔥 GAIL 190 CE REAL-TIME LIVE TRACKER | {now_str} IST")
    print(f"📌 Phase: {phase} | NIFTY 50: {n_ltp:.2f} ({n_chg:+.2f}%)")
    print("=" * 95)

    print("\n📊 1. UNDERLYING EQUITY (NSE:GAIL)")
    print(f"   Current LTP:      ₹{c_ltp:>7.2f} ({c_chg:+.2f}%) [Prev Close: ₹{c_prev:.2f}]")
    print(f"   Today Open:       ₹{c_open:>7.2f} | High: ₹{c_high:.2f} | Low: ₹{c_low:.2f}")
    print(f"   Volume:           {c_vol:>10,d} shares | Strike Status: {status_itm}")

    print("\n🎯 2. OPTION CONTRACT (NFO:GAIL26NOV190CE)")
    print(f"   Option LTP:       ₹{o_ltp:>7.2f} ({o_chg:+.2f}%) [Prev Close: ₹{o_prev:.2f}]")
    print(f"   Today Open:       ₹{o_open:>7.2f} | High: ₹{o_high:.2f} | Low: ₹{o_low:.2f}")
    print(f"   Option Volume:    {o_vol:>10,d} contracts | Open Interest: {o_oi:>9,d} shares")
    print(f"   Lot Size:         {LOT_SIZE} shares | Investment @ Base: ₹{LOT_SIZE * BASE_PREMIUM:,.2f}")
    print(f"   Payoff Multiple:  {multiplier:>6.2f}x | P&L per Lot: {pnl_per_lot:+,.2f} INR")

    # Order Book Depth
    depth = opt_q.get("depth", {})
    buys = depth.get("buy", [])
    sells = depth.get("sell", [])
    best_bid = buys[0].get("price", 0.0) if buys else 0.0
    best_ask = sells[0].get("price", 0.0) if sells else 0.0
    bid_qty = buys[0].get("quantity", 0) if buys else 0
    ask_qty = sells[0].get("quantity", 0) if sells else 0
    print(f"   Order Book:       Best Bid: ₹{best_bid:.2f} ({bid_qty:,} qty) | Best Ask: ₹{best_ask:.2f} ({ask_qty:,} qty)")

    print("\n🎯 3. TARGET PROGRESSION & ALERTS")
    t1_status = "✅ ACHIEVED!" if o_ltp >= TARGET_1 else f"⏳ Pending ({((TARGET_1 - o_ltp)/o_ltp * 100):+.1f}% needed)"
    t2_status = "✅ ACHIEVED!" if o_ltp >= TARGET_2 else f"⏳ Pending ({((TARGET_2 - o_ltp)/o_ltp * 100):+.1f}% needed)"
    t3_status = "✅ ACHIEVED!" if o_ltp >= TARGET_3 else f"⏳ Pending ({((TARGET_3 - o_ltp)/o_ltp * 100):+.1f}% needed)"

    print(f"   [T1] 2.0x Double   (₹{TARGET_1:.2f}):  {t1_status} -> Action: Sell 50% to make trade 100% Risk-Free!")
    print(f"   [T2] 3.9x Quad     (₹{TARGET_2:.2f}):  {t2_status} -> Action: Trail stop to T1 (₹3.60)")
    print(f"   [T3] 5.9x Mega-Boom(₹{TARGET_3:.2f}): {t3_status} -> Action: Book remaining profits")
    print(f"   [SL] Stop Loss     (₹{STOP_LOSS_OPT:.2f}):  Option Hard Stop | Cash Stop: ₹{STOP_LOSS_CASH:.2f}")

    # Actionable guidance
    print("\n💡 ACTIONABLE TRADE SIGNAL:")
    if cur_time < market_open:
        mins_left = (datetime.combine(now.date(), market_open) - now).total_seconds() / 60
        print(f"   ⏸️ Market opens in {mins_left:.0f} minutes (09:15 AM).")
        print("   👀 Key Rule at Open: Check pre-open rate at 09:08 AM.")
        print("   🚀 If GAIL opens above ₹190.50, GAIL 190 CE will immediately jump toward ₹2.20 - ₹2.50!")
    elif o_ltp >= TARGET_1:
        print("   🎉 2x TARGET HIT! Book 50% profits immediately and move SL to Cost Price (₹1.78)!")
    elif o_ltp <= STOP_LOSS_OPT or c_ltp <= STOP_LOSS_CASH:
        print("   ⚠️ STOP LOSS HIT! Exit position to protect capital.")
    else:
        print("   🟢 Position in play. Watching breakout above ₹191.00 Cash for acceleration toward T1 (₹3.60).")

    print("=" * 95)

def main():
    args = parse_args()
    if args.once:
        display_snapshot()
        return

    print("Starting continuous live tracking (Press Ctrl+C to stop)...")
    try:
        while True:
            # Clear terminal or print delimiter
            print("\033[H\033[J", end="")
            display_snapshot()
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[*] Tracking stopped by user.")

if __name__ == "__main__":
    main()
