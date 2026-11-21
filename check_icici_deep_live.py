"""
check_icici_deep_live.py
Deep real-time audit of ICICI Bank Spot and 1580 CE Option contract:
- Live quotes, day range, bid-ask depth, volume
- Current position P&L and distance to target
"""

import sys
from datetime import datetime
from pathlib import Path
import numpy as np

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

    spot_sym = "NSE:ICICIBANK"
    opt_sym = "NFO:ICICIBANK26NOV1580CE"

    q = kite.quote([spot_sym, opt_sym])
    spot = q.get(spot_sym, {})
    opt = q.get(opt_sym, {})

    # Spot Data
    s_ltp = spot.get("last_price", 0.0)
    s_ohlc = spot.get("ohlc", {})
    s_open = s_ohlc.get("open", s_ltp)
    s_high = s_ohlc.get("high", s_ltp)
    s_low = s_ohlc.get("low", s_ltp)
    s_close = s_ohlc.get("close", s_ltp)
    s_vol = spot.get("volume", 0)
    s_chg = s_ltp - s_close
    s_pct = (s_chg / s_close * 100) if s_close else 0.0

    # Option Data
    o_ltp = opt.get("last_price", 0.0)
    o_ohlc = opt.get("ohlc", {})
    o_high = o_ohlc.get("high", o_ltp)
    o_low = o_ohlc.get("low", o_ltp)
    o_vol = opt.get("volume", 0)
    o_oi = opt.get("oi", 0)
    depth = opt.get("depth", {})
    buys = depth.get("buy", [])
    sells = depth.get("sell", [])
    bid = buys[0].get("price", 0.0) if buys else o_ltp
    ask = sells[0].get("price", 0.0) if sells else o_ltp
    bid_qty = buys[0].get("quantity", 0) if buys else 0
    ask_qty = sells[0].get("quantity", 0) if sells else 0

    # User Position
    pos = kite.positions().get("net", [])
    icici_pos = next((p for p in pos if p.get("tradingsymbol") == "ICICIBANK26NOV1580CE"), None)

    # Order
    orders = [o for o in kite.orders() if o.get("status") in ["OPEN", "TRIGGER PENDING"] and o.get("tradingsymbol") == "ICICIBANK26NOV1580CE"]

    print("=" * 85)
    print(f"🏦 ICICI BANK LIVE AUDIT | {spot.get('last_trade_time', 'LIVE')}")
    print("=" * 85)
    print(f"📍 ICICI BANK SPOT:  ₹{s_ltp:,.2f} | Chg: {s_chg:>+6.2f} ({s_pct:>+5.2f}%) 🟢")
    print(f"   • Day Open / High: ₹{s_open:,.2f} / ₹{s_high:,.2f}")
    print(f"   • Day Low:         ₹{s_low:,.2f}")
    print(f"   • Volume:          {s_vol:,} shares")
    print(f"   • Proximity High:  Spot is only ₹{s_high - s_ltp:.2f} ({((s_high - s_ltp)/s_ltp)*100:.2f}%) away from Day High!")
    print("-" * 85)
    print(f"🎯 OPTION CONTRACT:  ICICIBANK26NOV1580CE (Monthly Expiry: 26-Nov-2026)")
    print(f"   • Current LTP:     ₹{o_ltp:.2f}")
    print(f"   • Top Bid / Ask:   ₹{bid:.2f} ({bid_qty} qty) / ₹{ask:.2f} ({ask_qty} qty)")
    print(f"   • Option Day High: ₹{o_high:.2f} | Day Low: ₹{o_low:.2f}")
    print(f"   • Traded Volume:   {o_vol:,} contracts")
    print(f"   • Open Interest:   {o_oi:,} contracts")
    print("-" * 85)

    if icici_pos:
        qty = icici_pos.get("quantity")
        avg = icici_pos.get("average_price")
        pnl = (o_ltp - avg) * qty
        pct = ((o_ltp - avg) / avg * 100) if avg else 0.0
        emoji = "🟢" if pnl >= 0 else "🔴"
        print("💼 YOUR ACTIVE POSITION:")
        print(f"   • Quantity:        {qty} shares (1 Lot)")
        print(f"   • Buy Price:       ₹{avg:.2f}")
        print(f"   • Live Price:      ₹{o_ltp:.2f}")
        print(f"   • Running P&L:     {emoji} ₹{pnl:+,.2f} ({pct:+.2f}%)")
        print(f"   • Target (₹28.00): Only ₹{28.00 - o_ltp:.2f} away! (Target Gain: +₹{(28.00 - avg)*qty:,.2f})")

    print("-" * 85)
    print("📋 ACTIVE ORDER IN BROKER:")
    if orders:
        for o in orders:
            print(f"  • Order #{o.get('order_id')} | SELL {o.get('quantity')} @ ₹{o.get('price')} ({o.get('status')})")
    else:
        print("  • No active orders.")

    print("=" * 85)

except Exception as e:
    print(f"❌ Error: {e}")
