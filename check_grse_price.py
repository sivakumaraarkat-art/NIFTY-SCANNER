"""Check exact latest close / live quote for GRSE, COCHINSHIP, MAZDOCK."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scanners.options_data_provider import get_kite_client

def main():
    kite = get_kite_client()
    symbols = ["NSE:GRSE", "NSE:COCHINSHIP", "NSE:MAZDOCK", "NSE:MUTHOOTFIN"]
    if kite:
        try:
            q = kite.quote(symbols)
            print("=" * 70)
            print("NSE DEFENSE & TOP MOMENTUM STOCKS -- LATEST QUOTE SNAPSHOT")
            print("=" * 70)
            for s in symbols:
                d = q.get(s, {})
                ltp = d.get("last_price", 0.0)
                ohlc = d.get("ohlc", {})
                close_p = ohlc.get("close", ltp)
                chg = ltp - close_p
                pct = (chg / close_p * 100) if close_p else 0.0
                print(f"{s:<16}: Rs.{ltp:<8.2f} (Change: {chg:+.2f} / {pct:+.2f}%)")
                print(f"  Day Range: Low: Rs.{ohlc.get('low', 0):.2f} - High: Rs.{ohlc.get('high', 0):.2f} | Open: Rs.{ohlc.get('open', 0):.2f}")
            print("=" * 70)
            return
        except Exception as e:
            print(f"Kite error: {e}")

if __name__ == "__main__":
    main()
