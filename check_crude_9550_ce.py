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

def inspect_crude_9550_ce():
    print("=" * 70)
    print("🔍 MCX CRUDE OIL 9550 CE POSITION AUDIT & RISK ANALYSIS")
    print("=" * 70)

    kite = get_kite_client()
    if not kite:
        print("❌ Kite client initialization failed. Please verify .kite_access_token")
        return

    try:
        instruments = kite.instruments("MCX")
        # Find 9550 CE options
        target_strike = 9550.0
        crude_opts = [
            i for i in instruments
            if "CRUDEOIL" in i.get("name", "").upper()
            and i.get("instrument_type") == "CE"
            and abs(float(i.get("strike", 0.0)) - target_strike) < 1.0
        ]

        # Find near future for underlying price benchmark
        futures = [
            i for i in instruments
            if "CRUDEOIL" in i.get("name", "").upper()
            and i.get("instrument_type") == "FUT"
        ]
        futures.sort(key=lambda x: str(x.get("expiry", "")))
        near_fut = futures[0] if futures else None

        fut_ltp = 0.0
        if near_fut:
            fut_sym = f"MCX:{near_fut['tradingsymbol']}"
            q_fut = kite.quote([fut_sym])
            if fut_sym in q_fut:
                fut_ltp = q_fut[fut_sym].get("last_price", 0.0)
                fut_ohlc = q_fut[fut_sym].get("ohlc", {})
                print(f"🛢️ Underlying Near Future: {near_fut['tradingsymbol']}")
                print(f"   Expiry: {near_fut.get('expiry')} | Lot Size: {near_fut.get('lot_size')}")
                print(f"   Future LTP: ₹{fut_ltp:,.2f} | Open: {fut_ohlc.get('open')} | High: {fut_ohlc.get('high')} | Low: {fut_ohlc.get('low')}")

        print("\n📊 Matching 9550 CE Option Contracts:")
        if not crude_opts:
            print("   ⚠️ No active 9550 CE contract found on MCX for current expiries.")
            return

        crude_opts.sort(key=lambda x: str(x.get("expiry", "")))
        symbols_to_quote = [f"MCX:{o['tradingsymbol']}" for o in crude_opts]
        quotes = kite.quote(symbols_to_quote)

        for opt in crude_opts:
            sym = f"MCX:{opt['tradingsymbol']}"
            q = quotes.get(sym, {})
            ltp = q.get("last_price", 0.0)
            vol = q.get("volume", 0)
            oi = q.get("oi", 0)
            ohlc = q.get("ohlc", {})
            lot = opt.get("lot_size", 100)

            # OTM calculation
            distance = target_strike - fut_ltp if fut_ltp > 0 else 0
            pct_otm = (distance / fut_ltp * 100.0) if fut_ltp > 0 else 0

            print("-" * 70)
            print(f"Contract: {opt['tradingsymbol']}")
            print(f"Expiry: {opt.get('expiry')} | Lot Size: {lot}")
            print(f"LTP: ₹{ltp:,.2f} | Prev Close: ₹{ohlc.get('close', 0.0):,.2f}")
            print(f"Day Range: Low ₹{ohlc.get('low', 0.0):,.2f} — High ₹{ohlc.get('high', 0.0):,.2f}")
            print(f"Volume: {vol:,} | Open Interest (OI): {oi:,}")
            print(f"Position Status: {pct_otm:+.1f}% OTM (₹{distance:,.1f} points away from underlying future)")
            print(f"Per-Lot Value: ₹{ltp * lot:,.2f} (1 pt change = ₹{lot})")

        print("\n" + "=" * 70)
        print("💡 CRITICAL TRADE MANAGEMENT RULES FOR 9550 CE:")
        print("=" * 70)
        print("1. Theta Decay: MCX Crude options undergo accelerating theta decay as expiry nears.")
        print("2. Underlying Target: For 9550 CE to gain intrinsic value, Crude Future must cross 9,550.")
        print("3. MCX Market Hours: Trades until 11:30 PM (or 11:55 PM during US Daylight Saving).")
        print("4. Risk Rule: Exit if the premium drops by 30-40% or underlying breaks major support.")
        print("=" * 70)

    except Exception as e:
        print(f"❌ Error inspecting contract: {e}")

if __name__ == "__main__":
    inspect_crude_9550_ce()
