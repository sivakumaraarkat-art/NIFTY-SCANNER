"""Check exact live quote, P&L, and risk-reward for user's CRUDEOIL 8750 PE."""
import sys
import os
from pathlib import Path
from datetime import date

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scanners.options_data_provider import get_kite_client

def main():
    kite = get_kite_client()
    if not kite:
        print("[!] Kite client could not be initialized.")
        return

    try:
        mcx_instruments = kite.instruments("MCX")
        today = date.today()
        # Find 8750 PE
        pe_opts = [
            i for i in mcx_instruments
            if "CRUDEOIL" in i.get("name", "").upper()
            and i.get("instrument_type") == "PE"
            and abs(float(i.get("strike", 0)) - 8750.0) < 5
            and i.get("expiry") and i["expiry"] >= today
        ]
        pe_opts.sort(key=lambda x: str(x.get("expiry", "")))

        # Find near future
        futures = [
            i for i in mcx_instruments
            if "CRUDEOIL" in i.get("name", "").upper() and i.get("instrument_type") == "FUT"
        ]
        futures.sort(key=lambda x: str(x.get("expiry", "")))
        near_fut = futures[0] if futures else None

        fut_sym = f"MCX:{near_fut['tradingsymbol']}" if near_fut else None
        target_opt = pe_opts[0] if pe_opts else None
        opt_sym = f"MCX:{target_opt['tradingsymbol']}" if target_opt else None

        keys = [k for k in [fut_sym, opt_sym] if k]
        quotes = kite.quote(keys)

        print("=" * 80)
        print("CRUDE OIL 8750 PE POSITION AUDIT")
        print("=" * 80)

        fut_ltp = 0.0
        if fut_sym and fut_sym in quotes:
            qd = quotes[fut_sym]
            fut_ltp = qd.get("last_price", 0.0)
            ohlc = qd.get("ohlc", {})
            print(f"Underlying Crude Future: {near_fut['tradingsymbol']}")
            print(f"  Future LTP:    Rs.{fut_ltp:,.2f} (Day Low: Rs.{ohlc.get('low', 0):,.2f} | Day High: Rs.{ohlc.get('high', 0):,.2f})")

        if opt_sym and opt_sym in quotes:
            od = quotes[opt_sym]
            ltp = od.get("last_price", 0.0)
            ohlc = od.get("ohlc", {})
            depth = od.get("depth", {})
            buy_p = depth.get("buy", [{}])[0].get("price", 0.0)
            sell_p = depth.get("sell", [{}])[0].get("price", 0.0)

            entry = 226.80
            lot_size = target_opt.get("lot_size", 100)
            diff = ltp - entry
            pnl = diff * lot_size
            pct = (diff / entry) * 100.0

            print(f"\nOption Contract: {target_opt['tradingsymbol']} (Expiry: {target_opt.get('expiry')})")
            print(f"  Your Entry Price:  Rs.{entry:.2f}")
            print(f"  Current Live LTP:  Rs.{ltp:.2f} (Bid: Rs.{buy_p:.2f} / Ask: Rs.{sell_p:.2f})")
            print(f"  Day Range:         Low: Rs.{ohlc.get('low', 0):.2f} - High: Rs.{ohlc.get('high', 0):.2f}")

            status_badge = "[PROFIT]" if pnl >= 0 else "[LOSS]"
            print(f"\nLive P&L Status:   {status_badge} Rs.{pnl:+,.2f} ({pct:+.2f}%)")
            print("=" * 80)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
