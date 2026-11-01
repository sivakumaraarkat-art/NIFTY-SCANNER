import sys
import os
import argparse
from pathlib import Path

# Ensure UTF-8 output encoding on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scanners.options_data_provider import get_kite_client, resolve_all_candidates

def main():
    print("==================================================================================")
    print("MCX CRUDE OIL COMMODITY SWING & MOMENTUM SCANNER")
    print("==================================================================================")

    kite = get_kite_client()
    if not kite:
        print("ERROR: Kite client could not be initialized. Check access token.")
        return

    try:
        insts = kite.instruments("MCX")
        futures = [i for i in insts if "CRUDEOIL" in i.get("name", "").upper() and i.get("instrument_type") == "FUT"]
        futures.sort(key=lambda x: str(x.get("expiry", "")))
        if not futures:
            print("No MCX Crude futures found.")
            return

        near = futures[0]
        sym = f"MCX:{near['tradingsymbol']}"
        print(f"Near Future Contract: {near['tradingsymbol']} | Expiry: {near['expiry']} | Lot Size: {near.get('lot_size')}")

        q = kite.quote([sym])
        if sym in q:
            data = q[sym]
            ltp = data.get("last_price", 0.0)
            ohlc = data.get("ohlc", {})
            print(f"Live LTP: {ltp} | Open: {ohlc.get('open')} | High: {ohlc.get('high')} | Low: {ohlc.get('low')} | Close: {ohlc.get('close')}")

            # Resolve options or provide recommendation
            pct = 0.0
            prev_close = ohlc.get("close", 0.0)
            if prev_close > 0:
                pct = ((ltp - prev_close) / prev_close) * 100.0

            sentiment = "BULLISH" if pct >= 0 else "BEARISH"
            print(f"Live Sentiment: {sentiment} (Change: {pct:.2f}%)")

            # Suggest strike based on LTP
            atm_strike = round(ltp / 100) * 100
            print(f"\n--- RECOMMENDED STRIKE SETUP ---")
            if sentiment == "BULLISH":
                print(f"Suggested Action: BUY CRUDEOIL Call (CE)")
                print(f"ATM Strike to watch: {atm_strike} CE")
                print(f"Support Level: {atm_strike - 100} | Resistance: {atm_strike + 100}")
                print(f"Stop Loss (Underlying): {ltp - 40} (~₹40 movement)")
            else:
                print(f"Suggested Action: BUY CRUDEOIL Put (PE)")
                print(f"ATM Strike to watch: {atm_strike} PE")
                print(f"Support Level: {atm_strike - 100} | Resistance: {atm_strike + 100}")
                print(f"Stop Loss (Underlying): {ltp + 40}")
        else:
            print(f"Could not fetch quote for {sym}")

    except Exception as e:
        print(f"Error running crude scanner: {e}")

if __name__ == "__main__":
    main()
