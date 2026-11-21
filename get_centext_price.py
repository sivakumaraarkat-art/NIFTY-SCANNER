"""
get_centext_price.py
Fetches live market quotes for both CENTEXT (Century Extrusions)
and CENTURYTEX (Century Textiles) directly from Zerodha Kite.
"""

import sys
import io
from pathlib import Path

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

    symbols = ["NSE:CENTEXT", "BSE:508136", "NSE:CENTURYTEX"]
    q = kite.quote(symbols)

    print("=" * 70)
    print("📈 LIVE ZERODHA QUOTES FOR CENTEXT & CENTURYTEX")
    print("=" * 70)

    for s in symbols:
        if s in q:
            data = q[s]
            ltp = data.get("last_price", 0.0)
            ohlc = data.get("ohlc", {})
            close = ohlc.get("close", ltp)
            chg = ((ltp - close) / close) * 100 if close else 0.0
            volume = data.get("volume", 0)
            low52 = data.get("lower_circuit_limit", "N/A")
            high52 = data.get("upper_circuit_limit", "N/A")

            print(f"\n🔍 Symbol: {s}")
            print(f"   • Last Traded Price (LTP) : ₹{ltp:.2f} ({chg:+.2f}%)")
            print(f"   • Previous Close          : ₹{close:.2f}")
            print(f"   • Open / High / Low       : ₹{ohlc.get('open')} / ₹{ohlc.get('high')} / ₹{ohlc.get('low')}")
            print(f"   • Traded Volume           : {volume:,} shares")
            print(f"   • Circuit Limits (L/U)    : ₹{low52} / ₹{high52}")
        else:
            print(f"\n⚠️ Symbol {s} not found in quote response.")

    print("\n" + "=" * 70)

except Exception as e:
    print(f"❌ Error fetching quotes: {e}")
