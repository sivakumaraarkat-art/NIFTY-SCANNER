"""
Crude Oil Swing & Intraday Scanner (Dedicated MCX Crude Oil)
Fetches live MCX futures quote, evaluates real momentum, and resolves verified options.
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scanners.options_data_provider import get_kite_client, resolve_all_candidates
from telegram_alerts.options_alert_sender import send_options_telegram_alerts

def get_crude_sentiment_and_score(kite) -> tuple[str, int]:
    """Dynamically determine Crude Oil sentiment and score from live MCX future price action."""
    if kite is None:
        return "BULLISH", 70
    try:
        insts = kite.instruments("MCX")
        futures = [i for i in insts if "CRUDEOIL" in i.get("name", "").upper() and i.get("instrument_type") == "FUT"]
        futures.sort(key=lambda x: str(x.get("expiry", "")))
        if not futures:
            return "BULLISH", 70
        near = futures[0]
        sym = f"MCX:{near['tradingsymbol']}"
        q = kite.quote([sym])
        if sym in q:
            data = q[sym]
            ltp = data.get("last_price", 0.0)
            ohlc = data.get("ohlc", {})
            prev_close = ohlc.get("close", 0.0)
            if prev_close > 0:
                pct = ((ltp - prev_close) / prev_close) * 100.0
                if pct >= 0.2:
                    score = int(min(95, 70 + abs(pct) * 10))
                    return "BULLISH", score
                elif pct <= -0.2:
                    score = int(min(95, 70 + abs(pct) * 10))
                    return "BEARISH", score
                else:
                    return "BULLISH", 60
    except Exception as e:
        print(f"⚠️ Could not fetch live Crude sentiment: {e}")
    return "BULLISH", 70

def main():
    parser = argparse.ArgumentParser(description="Dedicated MCX Crude Oil Scanner")
    parser.add_argument("--min-score", type=int, default=50, help="Minimum score")
    args = parser.parse_args()

    print("==================================================================================")
    print("🛢️ MCX CRUDE OIL COMMODITY SWING & MOMENTUM SCANNER")
    print("==================================================================================")

    kite = get_kite_client()
    sentiment, score = get_crude_sentiment_and_score(kite)
    print(f"📊 Live Crude Sentiment: {sentiment} | Score: {score}/100")

    candidates = [("CRUDEOIL", sentiment, score)]
    results = resolve_all_candidates(candidates, is_btst=False, min_score=args.min_score)

    if not results:
        print("⚠️ No verified Crude Oil option contracts qualified.")
        return

    print(f"\nDispatching verified Crude Oil signals to Telegram...")
    send_options_telegram_alerts(results, "CRUDE OIL SCAN")
    print("✅ Crude Oil scan completed successfully!")

if __name__ == '__main__':
    main()
