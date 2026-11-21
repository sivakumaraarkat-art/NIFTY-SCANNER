"""
audit_and_scan_next_trade.py
1. Audits current positions and today's executed orders.
2. Checks available cash margin.
3. Scans top liquid F&O candidates for the next high-probability trade.
"""

import sys
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

    # 1. Check Positions
    positions = kite.positions().get("net", [])
    open_pos = [p for p in positions if p.get("quantity", 0) != 0]

    # 2. Check Orders
    orders = kite.orders()
    recent_orders = orders[-5:] if orders else []

    # 3. Margins
    margin_data = kite.margins().get("equity", {})
    avail_cash = margin_data.get("available", {}).get("live_balance", 0.0)

    print("=" * 85)
    print("💼 ACCOUNT & TRADE EXECUTION STATUS")
    print("=" * 85)
    if open_pos:
        for p in open_pos:
            print(f"  • Open: {p.get('tradingsymbol')} [{p.get('product')}] | Qty: {p.get('quantity')} | LTP: ₹{p.get('last_price')} | P&L: ₹{p.get('pnl'):+,.2f}")
    else:
        print("  ✅ All derivative positions are currently flat/closed!")

    print("\n📝 LAST 3 ORDERS:")
    for o in recent_orders[-3:]:
        print(f"  • [{o.get('order_timestamp')}] {o.get('status')} | {o.get('transaction_type')} {o.get('quantity')} {o.get('tradingsymbol')} @ ₹{o.get('price')} (Filled: ₹{o.get('average_price')})")

    print(f"\n💵 AVAILABLE CASH FOR NEXT TRADE: ₹{avail_cash:,.2f}")
    print("-" * 85)

    # 4. Scan Candidates for Next High-Probability Setup
    # Let's inspect live prices of high-momentum F&O stocks and their monthly options
    scan_candidates = [
        # (Spot, Opt, Type, Lot, Thesis)
        ("NSE:JUBLFOOD", "NFO:JUBLFOOD26NOV430PE", "PE", 1250, "Top Breakdown Leader (Bearish)"),
        ("NSE:COCHINSHIP", "NSE:COCHINSHIP", "EQUITY_MIS", 1, "Defense/Shipbuilding Breakout (Bullish)"),
        ("NSE:ICICIBANK", "NFO:ICICIBANK26NOV1580CE", "CE", 700, "Banking Outperformer (Bullish)"),
        ("NSE:VEDL", "NFO:VEDL26NOV260CE", "CE", 1150, "High Delivery Accumulation (Bullish)"),
        ("NSE:BEL", "NFO:BEL26NOV320CE", "CE", 1500, "Defense Sector Rally (Bullish)")
    ]

    symbols_to_quote = [c[0] for c in scan_candidates] + [c[1] for c in scan_candidates if c[1] != c[0]]
    quotes = kite.quote(symbols_to_quote)

    print("\n🎯 SCANNING FOR NEXT BEST HIGH-PROBABILITY TRADE:")
    print("=" * 85)

    for spot_sym, inst_sym, trade_type, lot, thesis in scan_candidates:
        sq = quotes.get(spot_sym, {})
        iq = quotes.get(inst_sym, {})

        spot_ltp = sq.get("last_price", 0.0)
        spot_ohlc = sq.get("ohlc", {})
        spot_prev = spot_ohlc.get("close", spot_ltp)
        spot_chg = ((spot_ltp - spot_prev) / spot_prev * 100) if spot_prev else 0.0

        inst_ltp = iq.get("last_price", 0.0)
        vol = iq.get("volume", 0)
        oi = iq.get("oi", 0)
        depth = iq.get("depth", {})
        bids = depth.get("buy", [])
        asks = depth.get("sell", [])
        bid = bids[0].get("price", 0.0) if bids else inst_ltp
        ask = asks[0].get("price", 0.0) if asks else inst_ltp

        clean_inst = inst_sym.replace("NFO:", "").replace("NSE:", "")
        clean_spot = spot_sym.replace("NSE:", "")

        # Targets & SL computation
        if "CE" in trade_type or "EQUITY" in trade_type:
            t1 = round(inst_ltp * 1.08, 2)
            t2 = round(inst_ltp * 1.15, 2)
            sl = round(inst_ltp * 0.82, 2)
        else:
            t1 = round(inst_ltp * 1.10, 2)
            t2 = round(inst_ltp * 1.20, 2)
            sl = round(inst_ltp * 0.80, 2)

        capital_req = lot * inst_ltp
        emoji = "🟢" if "CE" in trade_type or "EQUITY" in trade_type else "🔴"

        print(f"\n{emoji} [{trade_type}] {clean_inst} | Underlying: {clean_spot} @ ₹{spot_ltp:,.2f} ({spot_chg:>+5.2f}%)")
        print(f"   • Thesis:        {thesis}")
        print(f"   • Live Price:    ₹{inst_ltp:>7.2f} (Bid: ₹{bid:.2f} / Ask: ₹{ask:.2f})")
        print(f"   • Target 1:      ₹{t1:>7.2f} | Target 2: ₹{t2:>7.2f}")
        print(f"   • Powerful SL:   ₹{sl:>7.2f}")
        print(f"   • Lot / Sizing:  Lot = {lot} | Capital: ₹{capital_req:,.2f}")
        print(f"   • Liquidity:     Volume: {vol:,} | OI: {oi:,}")

    print("\n" + "=" * 85)

except Exception as e:
    print(f"❌ Error during trade scan: {e}")
