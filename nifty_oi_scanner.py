import os
import time
from pathlib import Path
from datetime import date

import pandas as pd
from kiteconnect import KiteConnect
from kiteconnect.exceptions import PermissionException


# ============================================================
# CONFIGURATION
# ============================================================

API_KEY = os.getenv("KITE_API_KEY")

TOKEN_FILE = Path(__file__).with_name(".kite_access_token")

ACCESS_TOKEN = os.getenv("KITE_ACCESS_TOKEN")

if not ACCESS_TOKEN and TOKEN_FILE.exists():
    ACCESS_TOKEN = TOKEN_FILE.read_text(
        encoding="utf-8"
    ).strip()

STRIKES_EACH_SIDE = 5
STRIKE_STEP = 50
REFRESH_SECONDS = 30


# ============================================================
# VALIDATION
# ============================================================

if not API_KEY:
    print("ERROR: KITE_API_KEY is not set.")
    raise SystemExit(1)

if not ACCESS_TOKEN:
    print("ERROR: KITE_ACCESS_TOKEN is not set.")
    raise SystemExit(1)


# ============================================================
# KITE CONNECTION
# ============================================================

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)


# ============================================================
# LOGIN TEST
# ============================================================

try:

    profile = kite.profile()

    print("=" * 110)
    print("NIFTY OI + PRICE ACTION SCANNER")
    print("=" * 110)

    print("User ID :", profile["user_id"])
    print("Name    :", profile["user_name"])
    print("Status  : CONNECTED")

    print("=" * 110)

except PermissionException as exc:

    print("Authentication failed: insufficient permission for Kite market data or profile call.")
    print("Verify the API key permissions for your Kite app and generate a new access token.")
    print(exc)

    raise SystemExit(1)

except Exception as exc:

    print("Authentication failed:")
    print(exc)

    raise SystemExit(1)


# ============================================================
# DOWNLOAD INSTRUMENTS
# ============================================================

try:

    print("Downloading NFO instruments...")

    instruments = kite.instruments("NFO")

    instruments_df = pd.DataFrame(instruments)

except Exception as exc:

    print("Unable to download NFO instruments:")
    print(exc)

    raise SystemExit(1)


# ============================================================
# FILTER NIFTY OPTIONS
# ============================================================

options = instruments_df[
    (instruments_df["name"] == "NIFTY")
    &
    (instruments_df["instrument_type"].isin(["CE", "PE"]))
].copy()

options["expiry"] = pd.to_datetime(
    options["expiry"]
).dt.date


# ============================================================
# FIND EXPIRY
# ============================================================

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


# ============================================================
# PREVIOUS SNAPSHOT
# ============================================================

previous_snapshot = {}


# ============================================================
# CLASSIFICATION FUNCTION
# ============================================================

def classify_activity(
    old_ltp,
    new_ltp,
    old_oi,
    new_oi
):

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


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    try:

        # ----------------------------------------------------
        # NIFTY PRICE
        # ----------------------------------------------------

        nifty_data = kite.ltp(
            ["NSE:NIFTY 50"]
        )

        nifty_price = nifty_data[
            "NSE:NIFTY 50"
        ]["last_price"]


        # ----------------------------------------------------
        # ATM
        # ----------------------------------------------------

        atm_strike = int(
            (nifty_price + STRIKE_STEP / 2)
            // STRIKE_STEP
            * STRIKE_STEP
        )


        # ----------------------------------------------------
        # STRIKE RANGE
        # ----------------------------------------------------

        min_strike = (
            atm_strike
            - STRIKES_EACH_SIDE * STRIKE_STEP
        )

        max_strike = (
            atm_strike
            + STRIKES_EACH_SIDE * STRIKE_STEP
        )

        selected_strikes = list(
            range(
                min_strike,
                max_strike + STRIKE_STEP,
                STRIKE_STEP
            )
        )


        # ----------------------------------------------------
        # OPTION CONTRACTS
        # ----------------------------------------------------

        chain = options[
            (options["expiry"] == nearest_expiry)
            &
            (options["strike"].isin(selected_strikes))
        ].copy()


        if chain.empty:

            print("No option contracts found.")

            time.sleep(
                REFRESH_SECONDS
            )

            continue


        # ----------------------------------------------------
        # SYMBOLS
        # ----------------------------------------------------

        symbols = [
            f"NFO:{symbol}"
            for symbol in chain["tradingsymbol"]
        ]


        # ----------------------------------------------------
        # QUOTES
        # ----------------------------------------------------

        quotes = kite.quote(symbols)


        rows = []


        for _, contract in chain.iterrows():

            trading_symbol = contract[
                "tradingsymbol"
            ]

            kite_symbol = (
                f"NFO:{trading_symbol}"
            )

            quote = quotes.get(kite_symbol)

            if not quote:
                continue


            option_type = contract[
                "instrument_type"
            ]

            strike = int(
                contract["strike"]
            )

            ltp = float(
                quote.get("last_price", 0)
            )

            oi = int(
                quote.get("oi", 0)
            )

            volume = int(
                quote.get("volume", 0)
            )


            # ------------------------------------------------
            # Previous snapshot
            # ------------------------------------------------

            old_data = previous_snapshot.get(
                trading_symbol
            )


            if old_data:

                old_ltp = old_data["ltp"]
                old_oi = old_data["oi"]

                oi_change = oi - old_oi

                price_change = (
                    ltp - old_ltp
                )

                activity = classify_activity(
                    old_ltp,
                    ltp,
                    old_oi,
                    oi
                )

            else:

                old_ltp = None
                old_oi = None

                oi_change = 0
                price_change = 0

                activity = "BASELINE"


            # ------------------------------------------------
            # Save current snapshot
            # ------------------------------------------------

            previous_snapshot[
                trading_symbol
            ] = {
                "ltp": ltp,
                "oi": oi,
            }


            rows.append(
                {
                    "strike": strike,
                    "type": option_type,
                    "symbol": trading_symbol,
                    "ltp": ltp,
                    "volume": volume,
                    "oi": oi,
                    "oi_change": oi_change,
                    "price_change": price_change,
                    "activity": activity,
                }
            )


        if not rows:

            time.sleep(
                REFRESH_SECONDS
            )

            continue


        df = pd.DataFrame(rows)


        # ====================================================
        # CLEAR SCREEN
        # ====================================================

        print("\033[2J\033[H")


        print("=" * 125)
        print("NIFTY OI + PRICE ACTION SCANNER")
        print("=" * 125)

        print(
            f"NIFTY       : {nifty_price:.2f}"
        )

        print(
            f"ATM         : {atm_strike}"
        )

        print(
            f"EXPIRY      : {nearest_expiry}"
        )

        print(
            f"Refresh     : {REFRESH_SECONDS} sec"
        )

        print("=" * 125)


        # ====================================================
        # DISPLAY
        # ====================================================

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


        for _, row in df.sort_values(
            ["strike", "type"]
        ).iterrows():

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


        # ====================================================
        # PCR
        # ====================================================

        ce = df[
            df["type"] == "CE"
        ]

        pe = df[
            df["type"] == "PE"
        ]


        total_call_oi = ce["oi"].sum()
        total_put_oi = pe["oi"].sum()


        if total_call_oi > 0:

            pcr = (
                total_put_oi
                / total_call_oi
            )

        else:

            pcr = 0


        # ====================================================
        # TOTAL OI CHANGE
        # ====================================================

        call_oi_change = ce[
            "oi_change"
        ].sum()

        put_oi_change = pe[
            "oi_change"
        ].sum()


        # ====================================================
        # HIGHEST OI
        # ====================================================

        highest_call = ce.loc[
            ce["oi"].idxmax()
        ]

        highest_put = pe.loc[
            pe["oi"].idxmax()
        ]


        # ====================================================
        # SIMPLE BIAS
        # ====================================================

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


        # ====================================================
        # SUMMARY
        # ====================================================

        print()
        print("=" * 90)
        print("MARKET STRUCTURE")
        print("=" * 90)

        print(
            f"PCR                  : {pcr:.2f}"
        )

        print(
            f"Call OI Change       : "
            f"{call_oi_change:+,}"
        )

        print(
            f"Put OI Change        : "
            f"{put_oi_change:+,}"
        )

        print(
            f"Highest Call OI      : "
            f"{int(highest_call['strike'])}"
        )

        print(
            f"Highest Put OI       : "
            f"{int(highest_put['strike'])}"
        )

        print(
            f"Market Bias          : {bias}"
        )

        print("=" * 90)

        print(
            "\nIMPORTANT: Bias is analytical only. "
            "It is NOT an automatic trading signal."
        )


        # ====================================================
        # WAIT
        # ====================================================

        time.sleep(
            REFRESH_SECONDS
        )


    except KeyboardInterrupt:

        print()
        print("Scanner stopped.")

        break


    except PermissionException as exc:

        print()
        print("Scanner error: insufficient permission for Kite market data call.")
        print("Verify the API key permissions for your Kite app and regenerate the access token.")
        print(exc)

        raise SystemExit(1)

    except Exception as exc:

        print()
        print("Scanner error:")
        print(exc)

        print(
            f"Retrying in "
            f"{REFRESH_SECONDS} seconds..."
        )

        time.sleep(
            REFRESH_SECONDS
        )