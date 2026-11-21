import sys
sys.path.insert(0, "src/scanners")
from options_data_provider import (
    get_kite_client, get_nfo_instruments, resolve_option_candidate
)

print("=" * 80)
print("HISTORICAL BACKTEST - OPTION RESOLUTION & SL/TARGET LOGIC")
print("=" * 80)

kite = get_kite_client()
if not kite:
    print("No Kite connection")
    sys.exit(1)

print("Connected to Kite")

instruments = get_nfo_instruments(kite)
print("Loaded " + str(len(instruments)) + " instruments")

test_symbols = ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "BAJFINANCE", "MARUTI", "SBIN", "NIFTY", "BANKNIFTY"]

print("\nFetching live spot data...")

for symbol in test_symbols:
    try:
        if symbol == "NIFTY":
            spot_key = "NSE:NIFTY 50"
        elif symbol == "BANKNIFTY":
            spot_key = "NSE:NIFTY BANK"
        else:
            spot_key = "NSE:" + symbol

        quote = kite.quote([spot_key])
        if spot_key not in quote:
            print("  " + symbol + ": No quote")
            continue
        spot_price = quote[spot_key]["last_price"]

        print("\n--- " + symbol + " (Spot: " + str(spot_price) + ") ---")

        # Test BULLISH (CE) - Intraday
        candidate = resolve_option_candidate(kite, instruments, symbol, "BULLISH", is_btst=False, sentiment_score=85)
        if candidate:
            print("  INTRADAY CE: " + candidate["option_symbol"] + " @ " + str(candidate["ltp"]) + " | SL: " + str(candidate["powerful_sl"]) + " (" + str(candidate["sl_risk_pct"]) + "%) | T1: " + str(candidate["t1"]) + " | T2: " + str(candidate["t2"]) + " | Delta: " + str(candidate["delta"]) + " | IV: " + str(candidate["iv"]) + "% | Spread: " + str(candidate["spread_pct"]) + "%")
        else:
            print("  INTRADAY CE: REJECTED")

        # Test BEARISH (PE) - Intraday
        candidate = resolve_option_candidate(kite, instruments, symbol, "BEARISH", is_btst=False, sentiment_score=85)
        if candidate:
            print("  INTRADAY PE: " + candidate["option_symbol"] + " @ " + str(candidate["ltp"]) + " | SL: " + str(candidate["powerful_sl"]) + " (" + str(candidate["sl_risk_pct"]) + "%) | T1: " + str(candidate["t1"]) + " | T2: " + str(candidate["t2"]) + " | Delta: " + str(candidate["delta"]) + " | IV: " + str(candidate["iv"]) + "% | Spread: " + str(candidate["spread_pct"]) + "%")
        else:
            print("  INTRADAY PE: REJECTED")

        # Test BTST BULLISH (CE)
        candidate = resolve_option_candidate(kite, instruments, symbol, "BULLISH", is_btst=True, sentiment_score=85)
        if candidate:
            print("  BTST CE: " + candidate["option_symbol"] + " @ " + str(candidate["ltp"]) + " | SL: " + str(candidate["powerful_sl"]) + " (" + str(candidate["sl_risk_pct"]) + "%) | T1: " + str(candidate["t1"]) + " | T2: " + str(candidate["t2"]) + " | Delta: " + str(candidate["delta"]) + " | IV: " + str(candidate["iv"]) + "% | Spread: " + str(candidate["spread_pct"]) + "%")
        else:
            print("  BTST CE: REJECTED")

        # Test BTST BEARISH (PE)
        candidate = resolve_option_candidate(kite, instruments, symbol, "BEARISH", is_btst=True, sentiment_score=85)
        if candidate:
            print("  BTST PE: " + candidate["option_symbol"] + " @ " + str(candidate["ltp"]) + " | SL: " + str(candidate["powerful_sl"]) + " (" + str(candidate["sl_risk_pct"]) + "%) | T1: " + str(candidate["t1"]) + " | T2: " + str(candidate["t2"]) + " | Delta: " + str(candidate["delta"]) + " | IV: " + str(candidate["iv"]) + "% | Spread: " + str(candidate["spread_pct"]) + "%")
        else:
            print("  BTST PE: REJECTED")

    except Exception as e:
        print("  Error for " + symbol + ": " + str(e))

print("\n" + "=" * 80)
print("BACKTEST COMPLETE")
print("=" * 80)