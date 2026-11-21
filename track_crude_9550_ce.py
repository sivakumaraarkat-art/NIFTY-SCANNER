import sys
import os
from pathlib import Path
from datetime import datetime

# UTF-8 encoding fix for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scanners.options_data_provider import get_kite_client

def track_exact_crude_position():
    ENTRY_PRICE = 282.0
    USER_SL = 270.0        # User's current SL
    REC_TIGHT_SL = 255.0   # Recommended Intraday SL
    REC_SWING_SL = 235.0   # Recommended Swing SL
    HARD_SL = 197.0        # -30% Structural SL

    T1_PRICE = 365.0       # +30% (+₹8,300 profit)
    T2_PRICE = 420.0       # +50% (+₹13,800 profit)
    T3_PRICE = 510.0       # +80% (+₹22,800 profit)
    LOT_QTY = 100          # 1 standard MCX lot
    CAPITAL_INVESTED = ENTRY_PRICE * LOT_QTY # ₹28,200

    print("=" * 75)
    print("🛢️  MCX CRUDE OIL 9550 CE (17-NOV EXPIRY) — POSITION & PRICE CHECK")
    print("=" * 75)
    print(f"• Bought Price:     ₹{ENTRY_PRICE:.2f}")
    print(f"• Quantity:         {LOT_QTY} (1 Standard Lot)")
    print(f"• Capital Invested: ₹{CAPITAL_INVESTED:,.2f}")
    print(f"• Your SL:          ₹{USER_SL:.2f} (Buffer: {ENTRY_PRICE - USER_SL:.1f} pts / ₹{(ENTRY_PRICE - USER_SL)*LOT_QTY:,.0f} risk)")
    print(f"• Recommended SL:   ₹{REC_SWING_SL:.2f} (Buffer: {ENTRY_PRICE - REC_SWING_SL:.1f} pts / ₹{(ENTRY_PRICE - REC_SWING_SL)*LOT_QTY:,.0f} risk)")
    print("-" * 75)

    kite = get_kite_client()
    if not kite:
        print("❌ Kite client initialization failed. Please verify credentials or token.")
        return

    try:
        instruments = kite.instruments("MCX")

        # 1. Fetch Underlying Future Price
        futures = [
            i for i in instruments
            if "CRUDEOIL" in i.get("name", "").upper()
            and i.get("instrument_type") == "FUT"
        ]
        futures.sort(key=lambda x: str(x.get("expiry", "")))
        if futures:
            near_fut = futures[0]
            fut_sym = f"MCX:{near_fut['tradingsymbol']}"
            q_fut = kite.quote([fut_sym])
            if fut_sym in q_fut:
                f_data = q_fut[fut_sym]
                f_ltp = f_data.get("last_price", 0.0)
                f_ohlc = f_data.get("ohlc", {})
                print(f"📌 Underlying Future: {near_fut['tradingsymbol']}")
                print(f"   Expiry: {near_fut.get('expiry')} | LTP: ₹{f_ltp:,.2f} ({f_data.get('net_change', 0.0):+.2f})")
                print(f"   Day Range: Low ₹{f_ohlc.get('low', 0.0):,.2f} — High ₹{f_ohlc.get('high', 0.0):,.2f}")
                print("-" * 75)

        # 2. Find 9550 CE Option Contracts
        target_strike = 9550.0
        crude_opts = [
            i for i in instruments
            if "CRUDEOIL" in i.get("name", "").upper()
            and i.get("instrument_type") == "CE"
            and abs(float(i.get("strike", 0.0)) - target_strike) < 5.0
        ]

        if not crude_opts:
            print("⚠️ No exact 9550 CE contract found. Checking available nearby CE strikes:")
            nearby_opts = [
                i for i in instruments
                if "CRUDEOIL" in i.get("name", "").upper()
                and i.get("instrument_type") == "CE"
            ]
            nearby_opts.sort(key=lambda x: (str(x.get("expiry")), float(x.get("strike", 0))))
            for o in nearby_opts[:8]:
                print(f"   - {o['tradingsymbol']} | Strike: {o.get('strike')} | Expiry: {o.get('expiry')}")
            return

        crude_opts.sort(key=lambda x: str(x.get("expiry", "")))

        # Pick 17-Nov expiry or first available
        active_opt = crude_opts[0]
        for opt in crude_opts:
            exp_str = str(opt.get("expiry", "")).upper()
            if "17" in exp_str or "NOV" in exp_str:
                active_opt = opt
                break

        sym = f"MCX:{active_opt['tradingsymbol']}"
        q = kite.quote([sym])
        if sym not in q:
            print(f"⚠️ Quote unavailable for {sym}")
            return

        data = q[sym]
        ltp = data.get("last_price", 0.0)
        ohlc = data.get("ohlc", {})
        net_change = data.get("net_change", 0.0)
        depth = data.get("depth", {})
        best_bid = depth.get("buy", [{}])[0].get("price", 0.0) if depth.get("buy") else 0.0
        best_ask = depth.get("sell", [{}])[0].get("price", 0.0) if depth.get("sell") else 0.0

        pnl_pts = ltp - ENTRY_PRICE
        pnl_pct = (pnl_pts / ENTRY_PRICE) * 100.0
        pnl_rupees = pnl_pts * LOT_QTY
        current_value = ltp * LOT_QTY

        print(f"📊 OPTION CONTRACT:  {active_opt['tradingsymbol']}")
        print(f"   Expiry:           {active_opt.get('expiry')} | Lot Size: {active_opt.get('lot_size')}")
        print(f"   LIVE LTP:         ₹{ltp:.2f} ({net_change:+.2f} today)")
        print(f"   Best Bid / Ask:   ₹{best_bid:.2f} / ₹{best_ask:.2f}")
        print(f"   Day Range:        Low ₹{ohlc.get('low', 0.0):.2f} — High ₹{ohlc.get('high', 0.0):.2f}")
        print(f"   Traded Volume:    {data.get('volume', 0):,} contracts | OI: {data.get('oi', 0):,}")
        print("-" * 75)
        print(f"💰 POSITION VALUE:   ₹{current_value:,.2f}")

        pnl_str = f"🟢 PROFIT: +₹{pnl_rupees:,.2f} (+{pnl_pts:.2f} pts / +{pnl_pct:.2f}%)" if pnl_pts >= 0 else f"🔴 LOSS:   -₹{abs(pnl_rupees):,.2f} ({pnl_pts:.2f} pts / {pnl_pct:.2f}%)"
        print(f"   NET P&L:          {pnl_str}")
        print("-" * 75)

        # SL and Target Verifications
        print("🎯 RISK & EXIT CHECKS:")
        if ltp <= USER_SL:
            print(f"   🚨 YOUR ₹270 SL WOULD BE HIT! Current price (₹{ltp:.2f}) is at or below ₹{USER_SL:.2f}.")
        else:
            print(f"   🛡️ Price is ₹{ltp - USER_SL:.2f} points above your ₹270 SL.")

        if ltp >= T3_PRICE:
            print(f"   🌟 TARGET 3 REACHED (₹{T3_PRICE}+)! Book full profits.")
        elif ltp >= T2_PRICE:
            print(f"   🎯 TARGET 2 REACHED (₹{T2_PRICE}+)! Trail SL to ₹365.")
        elif ltp >= T1_PRICE:
            print(f"   ✅ TARGET 1 REACHED (₹{T1_PRICE}+)! Secure 50% profit.")
        elif ltp <= REC_SWING_SL:
            print(f"   🛑 Recommended Swing SL (₹{REC_SWING_SL}) reached. Cut trade.")
        else:
            print(f"   ⏳ Position active. Distance to Target 1 (₹365): {T1_PRICE - ltp:+.2f} pts.")

        print("=" * 75)

    except Exception as e:
        print(f"❌ Error during tracking: {e}")

if __name__ == "__main__":
    track_exact_crude_position()
