import argparse
import os
import time
from pathlib import Path
from datetime import date

import pandas as pd
from kiteconnect import KiteConnect


API_KEY = os.getenv("KITE_API_KEY") or "oob3ajmzaoxi6hvy"
TOKEN_FILE = Path(__file__).with_name(".kite_access_token")
ACCESS_TOKEN = os.getenv("KITE_ACCESS_TOKEN")

if not ACCESS_TOKEN and TOKEN_FILE.exists():
    ACCESS_TOKEN = TOKEN_FILE.read_text(encoding="utf-8").strip()


def validate_credentials():
    if not API_KEY:
        print("ERROR: KITE_API_KEY is not set.")
        raise SystemExit(1)

    if not ACCESS_TOKEN:
        print("ERROR: KITE_ACCESS_TOKEN is not set.")
        raise SystemExit(1)


def classify_activity(old_ltp, new_ltp, old_oi, new_oi):
    if old_ltp is None or old_oi is None:
        return "BASELINE"

    price_change = new_ltp - old_ltp
    oi_change = new_oi - old_oi

    if oi_change > 0 and price_change > 0:
        return "LONG BUILDUP"

    if oi_change > 0 and price_change < 0:
        return "SHORT BUILDUP"

    if oi_change < 0 and price_change > 0:
        return "SHORT COVERING"

    if oi_change < 0 and price_change < 0:
        return "LONG UNWINDING"

    return "NO CLEAR CHANGE"


def build_symbol_list(chain):
    return [f"NFO:{symbol}" for symbol in chain["tradingsymbol"]]


DEFAULT_LTP_SYMBOLS = {
    "NIFTY": "NSE:NIFTY 50",
    "BANKNIFTY": "NSE:BANKNIFTY",
    "SENSEX": "BSE:SENSEX",
}


def get_future_underlying_symbol(kite, underlying_name):
    instruments = kite.instruments("NFO")
    candidates = [
        inst
        for inst in instruments
        if inst["name"] == underlying_name and inst["instrument_type"] == "FUT"
    ]

    if not candidates:
        return None

    for inst in candidates:
        inst["expiry_date"] = pd.to_datetime(inst["expiry"]).date()

    today = date.today()
    future_expiries = sorted(
        inst["expiry_date"]
        for inst in candidates
        if inst["expiry_date"] >= today
    )

    if not future_expiries:
        return None

    nearest_expiry = future_expiries[0]
    future_symbols = [
        inst["tradingsymbol"]
        for inst in candidates
        if inst["expiry_date"] == nearest_expiry
    ]
    return future_symbols[0] if future_symbols else None


def build_ltp_candidates(underlying_name, ltp_symbol=None):
    candidates = []
    if ltp_symbol:
        candidates.append(ltp_symbol)

    default_symbol = DEFAULT_LTP_SYMBOLS.get(underlying_name.upper())
    if default_symbol:
        candidates.append(default_symbol)

    normalized_name = underlying_name.strip().upper()
    candidates.extend([
        f"NSE:{normalized_name}",
        f"NFO:{normalized_name}",
        normalized_name,
    ])

    if normalized_name == "NIFTY":
        candidates.append("NSE:NIFTY 50")

    candidates = [s for i, s in enumerate(candidates) if s and s not in candidates[:i]]
    return candidates


def get_underlying_price(kite, ltp_symbol, underlying_name):
    candidates = build_ltp_candidates(underlying_name, ltp_symbol)
    response = kite.ltp(candidates)

    for symbol in candidates:
        data = response.get(symbol)
        if isinstance(data, dict) and "last_price" in data:
            return data["last_price"], symbol

    for symbol, data in response.items():
        if isinstance(data, dict) and "last_price" in data:
            return data["last_price"], symbol

    future_symbol = get_future_underlying_symbol(kite, underlying_name)
    if future_symbol:
        future_key = f"NFO:{future_symbol}"
        response = kite.ltp([future_key])
        data = response.get(future_key)
        if isinstance(data, dict) and "last_price" in data:
            return data["last_price"], future_key

    available = ", ".join(sorted(response.keys()))
    raise ValueError(
        f"No LTP data found for {underlying_name}. Tried: {candidates}. "
        f"Received keys: {available}"
    )


def scanner_loop(
    kite,
    underlying_name,
    ltp_symbol,
    strike_step,
    strikes_each_side,
    refresh_seconds,
    title,
    instrument_type_filter=("CE", "PE"),
):
    instruments = kite.instruments("NFO")
    instruments_df = pd.DataFrame(instruments)

    options = instruments_df[
        (instruments_df["name"] == underlying_name)
        &
        (instruments_df["instrument_type"].isin(instrument_type_filter))
    ].copy()

    if options.empty:
        print(f"No {underlying_name} option instruments were found in NFO.")
        raise SystemExit(1)

    options["expiry"] = pd.to_datetime(options["expiry"]).dt.date

    today = date.today()
    future_expiries = sorted(
        expiry
        for expiry in options["expiry"].unique()
        if expiry >= today
    )

    if not future_expiries:
        print("No future expiry found.")
        raise SystemExit(1)

    nearest_expiry = future_expiries[0]
    previous_snapshot = {}

    while True:
        try:
            index_price, used_symbol = get_underlying_price(kite, ltp_symbol, underlying_name)

            atm_strike = int(
                (index_price + strike_step / 2)
                // strike_step
                * strike_step
            )

            min_strike = atm_strike - strikes_each_side * strike_step
            max_strike = atm_strike + strikes_each_side * strike_step
            selected_strikes = list(range(min_strike, max_strike + strike_step, strike_step))

            chain = options[
                (options["expiry"] == nearest_expiry)
                &
                (options["strike"].isin(selected_strikes))
            ].copy()

            if chain.empty:
                print("No option contracts found for the selected strikes.")
                time.sleep(refresh_seconds)
                continue

            symbols = build_symbol_list(chain)
            quotes = kite.quote(symbols)
            rows = []

            for _, contract in chain.iterrows():
                trading_symbol = contract["tradingsymbol"]
                kite_symbol = f"NFO:{trading_symbol}"
                quote = quotes.get(kite_symbol)

                if not quote:
                    continue

                option_type = contract["instrument_type"]
                strike = int(contract["strike"])
                ltp = float(quote.get("last_price", 0))
                oi = int(quote.get("oi", 0))
                volume = int(quote.get("volume", 0))

                old_data = previous_snapshot.get(trading_symbol)

                if old_data:
                    old_ltp = old_data["ltp"]
                    old_oi = old_data["oi"]
                    oi_change = oi - old_oi
                    price_change = ltp - old_ltp
                    activity = classify_activity(old_ltp, ltp, old_oi, oi)
                else:
                    old_ltp = None
                    old_oi = None
                    oi_change = 0
                    price_change = 0
                    activity = "BASELINE"

                previous_snapshot[trading_symbol] = {
                    "ltp": ltp,
                    "oi": oi,
                }

                rows.append({
                    "strike": strike,
                    "type": option_type,
                    "symbol": trading_symbol,
                    "ltp": ltp,
                    "volume": volume,
                    "oi": oi,
                    "oi_change": oi_change,
                    "price_change": price_change,
                    "activity": activity,
                })

            if not rows:
                time.sleep(refresh_seconds)
                continue

            df = pd.DataFrame(rows)
            ce = df[df["type"] == "CE"]
            pe = df[df["type"] == "PE"]

            print("\033[2J\033[H")
            print("=" * 125)
            print(title)
            print("=" * 125)
            print(f"INDEX       : {index_price:.2f}  ({used_symbol})")
            print(f"ATM         : {atm_strike}")
            print(f"EXPIRY      : {nearest_expiry}")
            print(f"Refresh     : {refresh_seconds} sec")
            print("=" * 125)

            print(
                f"{'TYPE':>5} "
                f"{'STRIKE':>8} "
                f"{'LTP':>10} "
                f"{'ΔLTP':>10} "
                f"{'OI':>14} "
                f"{'ΔOI':>14} "
                f"{'VOLUME':>14} "
                f"{'ACTIVITY'}"
            )
            print("-" * 125)

            for _, row in df.sort_values(["strike", "type"]).iterrows():
                print(
                    f"{row['type']:>5} "
                    f"{int(row['strike']):>8} "
                    f"{row['ltp']:>10.2f} "
                    f"{row['price_change']:>+10.2f} "
                    f"{int(row['oi']):>14,} "
                    f"{int(row['oi_change']):>+14,} "
                    f"{int(row['volume']):>14,} "
                    f"{row['activity']}"
                )

            total_call_oi = ce["oi"].sum()
            total_put_oi = pe["oi"].sum()
            pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0
            call_oi_change = ce["oi_change"].sum()
            put_oi_change = pe["oi_change"].sum()
            highest_call = ce.loc[ce["oi"].idxmax()]
            highest_put = pe.loc[pe["oi"].idxmax()]

            bullish_points = 0
            bearish_points = 0
            if pcr > 1:
                bullish_points += 1
            elif pcr < 1:
                bearish_points += 1

            if put_oi_change > 0:
                bullish_points += 1
            elif put_oi_change < 0:
                bearish_points += 1

            if call_oi_change > 0:
                bearish_points += 1
            elif call_oi_change < 0:
                bullish_points += 1

            if bullish_points > bearish_points:
                bias = "BULLISH"
            elif bearish_points > bullish_points:
                bias = "BEARISH"
            else:
                bias = "NEUTRAL"

            print()
            print("=" * 90)
            print("MARKET STRUCTURE")
            print("=" * 90)
            print(f"PCR                  : {pcr:.2f}")
            print(f"Call OI Change       : {call_oi_change:+,}")
            print(f"Put OI Change        : {put_oi_change:+,}")
            print(f"Highest Call OI      : {int(highest_call['strike'])}")
            print(f"Highest Put OI       : {int(highest_put['strike'])}")
            print(f"Market Bias          : {bias}")
            print("=" * 90)
            print(
                "\nIMPORTANT: Bias is analytical only. "
                "It is NOT an automatic trading signal."
            )
            time.sleep(refresh_seconds)

        except KeyboardInterrupt:
            print()
            print("Scanner stopped.")
            break

        except Exception as exc:
            print()
            print("Scanner error:")
            print(exc)
            print(f"Retrying in {refresh_seconds} seconds...")
            time.sleep(refresh_seconds)


def main():
    parser = argparse.ArgumentParser(description="Generic index OI + price-action scanner.")
    parser.add_argument("--index-name", default="NIFTY", help="Underlying instrument name in NFO.")
    parser.add_argument("--ltp-symbol", default="NSE:NIFTY 50", help="LTP symbol for the underlying.")
    parser.add_argument("--strike-step", type=int, default=50, help="Strike step for the index.")
    parser.add_argument("--strikes-each-side", type=int, default=5, help="Number of strikes each side of ATM.")
    parser.add_argument("--refresh-seconds", type=int, default=30, help="Polling interval in seconds.")
    args = parser.parse_args()

    validate_credentials()
    kite = KiteConnect(api_key=API_KEY)
    kite.set_access_token(ACCESS_TOKEN)

    try:
        profile = kite.profile()
        print("=" * 110)
        print(f"{args.index_name} OI + PRICE ACTION SCANNER")
        print("=" * 110)
        print("User ID :", profile["user_id"])
        print("Name    :", profile["user_name"])
        print("Status  : CONNECTED")
        print("=" * 110)
    except Exception as exc:
        print("Authentication failed:")
        print(exc)
        raise SystemExit(1)

    scanner_loop(
        kite=kite,
        underlying_name=args.index_name,
        ltp_symbol=args.ltp_symbol,
        strike_step=args.strike_step,
        strikes_each_side=args.strikes_each_side,
        refresh_seconds=args.refresh_seconds,
        title=f"{args.index_name} OI + PRICE ACTION SCANNER",
    )


if __name__ == "__main__":
    main()
