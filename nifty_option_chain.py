import os
from pathlib import Path
from datetime import date

import pandas as pd
from kiteconnect import KiteConnect


# ============================================================
# CONFIGURATION
# ============================================================

API_KEY = os.getenv("KITE_API_KEY", "oob3ajmzaoxi6hvy")

TOKEN_FILE = Path(__file__).with_name(".kite_access_token")

if TOKEN_FILE.exists():
    ACCESS_TOKEN = TOKEN_FILE.read_text(
        encoding="utf-8"
    ).strip()
else:
    ACCESS_TOKEN = os.getenv("KITE_ACCESS_TOKEN")


# Number of strikes above and below ATM
STRIKES_EACH_SIDE = 5

# NIFTY strike interval
STRIKE_STEP = 50


# ============================================================
# VALIDATE CONFIGURATION
# ============================================================

if not API_KEY:
    print("ERROR: KITE_API_KEY is not set.")
    raise SystemExit(1)

if not ACCESS_TOKEN:
    print("ERROR: KITE_ACCESS_TOKEN is not set.")
    raise SystemExit(1)


# ============================================================
# CONNECT TO ZERODHA
# ============================================================

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)


# ============================================================
# VERIFY LOGIN
# ============================================================

try:

    profile = kite.profile()

    print()
    print("=" * 100)
    print("ZERODHA CONNECTION")
    print("=" * 100)
    print("User ID :", profile["user_id"])
    print("Name    :", profile["user_name"])
    print("Status  : CONNECTED")
    print("=" * 100)

except Exception as exc:

    print("Authentication failed:")
    print(exc)

    raise SystemExit(1)


# ============================================================
# GET NIFTY SPOT
# ============================================================

try:

    nifty_data = kite.ltp(["NSE:NIFTY 50"])

    nifty_price = nifty_data["NSE:NIFTY 50"]["last_price"]

    print()
    print(f"NIFTY SPOT : {nifty_price:.2f}")

except Exception as exc:

    print("Unable to get NIFTY price:")
    print(exc)

    raise SystemExit(1)


# ============================================================
# CALCULATE ATM
# ============================================================

atm_strike = int(
    (nifty_price + STRIKE_STEP / 2) // STRIKE_STEP
    * STRIKE_STEP
)

print(f"ATM STRIKE : {atm_strike}")


# ============================================================
# DOWNLOAD NFO INSTRUMENTS
# ============================================================

try:

    print()
    print("Downloading NFO instruments...")

    instruments = kite.instruments("NFO")

    instruments_df = pd.DataFrame(instruments)

    print(
        f"Total NFO instruments : "
        f"{len(instruments_df)}"
    )

except Exception as exc:

    print("Unable to download NFO instruments:")
    print(exc)

    raise SystemExit(1)


# ============================================================
# PREPARE NIFTY OPTION DATA
# ============================================================

options = instruments_df[
    (instruments_df["name"] == "NIFTY")
    &
    (instruments_df["instrument_type"].isin(["CE", "PE"]))
].copy()


# Convert expiry to date
options["expiry"] = pd.to_datetime(
    options["expiry"]
).dt.date


# ============================================================
# FIND NEAREST FUTURE EXPIRY
# ============================================================

today = date.today()

future_expiries = sorted(
    expiry
    for expiry in options["expiry"].unique()
    if expiry >= today
)

if not future_expiries:

    print("No future NIFTY expiry found.")
    raise SystemExit(1)


nearest_expiry = future_expiries[0]

print(f"EXPIRY      : {nearest_expiry}")


# ============================================================
# CREATE STRIKE RANGE
# ============================================================

min_strike = atm_strike - (
    STRIKES_EACH_SIDE * STRIKE_STEP
)

max_strike = atm_strike + (
    STRIKES_EACH_SIDE * STRIKE_STEP
)


selected_strikes = list(
    range(
        min_strike,
        max_strike + STRIKE_STEP,
        STRIKE_STEP
    )
)


print(
    f"STRIKES     : "
    f"{min_strike} - {max_strike}"
)


# ============================================================
# FILTER OPTION CONTRACTS
# ============================================================

chain = options[
    (options["expiry"] == nearest_expiry)
    &
    (options["strike"].isin(selected_strikes))
].copy()


if chain.empty:

    print("No NIFTY option contracts found.")
    raise SystemExit(1)


# ============================================================
# CREATE SYMBOL LIST
# ============================================================

symbols = [
    f"NFO:{symbol}"
    for symbol in chain["tradingsymbol"]
]


# ============================================================
# GET OPTION QUOTES
# ============================================================

try:

    print()
    print("Getting option-chain market data...")

    quotes = kite.quote(symbols)

except Exception as exc:

    print()
    print("Option market-data request failed:")
    print(exc)

    raise SystemExit(1)


# ============================================================
# BUILD OPTION CHAIN TABLE
# ============================================================

rows = []


for _, contract in chain.iterrows():

    trading_symbol = contract["tradingsymbol"]

    kite_symbol = f"NFO:{trading_symbol}"

    quote = quotes.get(kite_symbol)

    if not quote:
        continue

    option_type = contract["instrument_type"]

    ltp = quote.get("last_price", 0)
    volume = quote.get("volume", 0)
    oi = quote.get("oi", 0)

    rows.append(
        {
            "strike": int(contract["strike"]),
            "type": option_type,
            "symbol": trading_symbol,
            "ltp": ltp,
            "volume": volume,
            "oi": oi,
            "instrument_token":
                contract["instrument_token"],
        }
    )


if not rows:

    print("No option quotes returned.")
    raise SystemExit(1)


chain_df = pd.DataFrame(rows)


# ============================================================
# SEPARATE CE / PE
# ============================================================

ce_df = chain_df[
    chain_df["type"] == "CE"
].copy()

pe_df = chain_df[
    chain_df["type"] == "PE"
].copy()


# ============================================================
# COMBINE CE + PE BY STRIKE
# ============================================================

ce_display = ce_df[
    ["strike", "ltp", "volume", "oi"]
].rename(
    columns={
        "ltp": "ce_ltp",
        "volume": "ce_volume",
        "oi": "ce_oi",
    }
)


pe_display = pe_df[
    ["strike", "ltp", "volume", "oi"]
].rename(
    columns={
        "ltp": "pe_ltp",
        "volume": "pe_volume",
        "oi": "pe_oi",
    }
)


option_chain = pd.merge(
    ce_display,
    pe_display,
    on="strike",
    how="outer"
)


option_chain = option_chain.sort_values(
    "strike"
).reset_index(drop=True)


# ============================================================
# DISPLAY OPTION CHAIN
# ============================================================

print()
print()
print("=" * 110)
print("NIFTY OPTION CHAIN")
print("=" * 110)

print(
    f"{'CE OI':>14} "
    f"{'CE VOL':>12} "
    f"{'CE LTP':>10} "
    f"{'STRIKE':>8} "
    f"{'PE LTP':>10} "
    f"{'PE VOL':>12} "
    f"{'PE OI':>14}"
)

print("-" * 110)


for _, row in option_chain.iterrows():

    print(
        f"{int(row['ce_oi']):>14,} "
        f"{int(row['ce_volume']):>12,} "
        f"{row['ce_ltp']:>10.2f} "
        f"{int(row['strike']):>8} "
        f"{row['pe_ltp']:>10.2f} "
        f"{int(row['pe_volume']):>12,} "
        f"{int(row['pe_oi']):>14,}"
    )


print("=" * 110)


# ============================================================
# TOTAL OI
# ============================================================

total_call_oi = ce_df["oi"].sum()
total_put_oi = pe_df["oi"].sum()


# ============================================================
# PCR
# ============================================================

if total_call_oi > 0:

    pcr = total_put_oi / total_call_oi

else:

    pcr = 0


# ============================================================
# HIGHEST CALL OI
# ============================================================

highest_call = ce_df.loc[
    ce_df["oi"].idxmax()
]


# ============================================================
# HIGHEST PUT OI
# ============================================================

highest_put = pe_df.loc[
    pe_df["oi"].idxmax()
]


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 70)
print("OPTION-CHAIN SUMMARY")
print("=" * 70)

print(
    f"NIFTY SPOT       : {nifty_price:.2f}"
)

print(
    f"ATM STRIKE       : {atm_strike}"
)

print(
    f"EXPIRY           : {nearest_expiry}"
)

print(
    f"TOTAL CALL OI    : {total_call_oi:,.0f}"
)

print(
    f"TOTAL PUT OI     : {total_put_oi:,.0f}"
)

print(
    f"PCR              : {pcr:.2f}"
)

print(
    f"HIGHEST CALL OI  : "
    f"{int(highest_call['strike'])} CE "
    f"({int(highest_call['oi']):,})"
)

print(
    f"HIGHEST PUT OI   : "
    f"{int(highest_put['strike'])} PE "
    f"({int(highest_put['oi']):,})"
)

print("=" * 70)


# ============================================================
# BASIC INTERPRETATION
# ============================================================

print()
print("INITIAL MARKET STRUCTURE")
print("-" * 70)

print(
    f"Potential Resistance : "
    f"{int(highest_call['strike'])}"
)

print(
    f"Potential Support    : "
    f"{int(highest_put['strike'])}"
)

print(
    f"PCR                  : "
    f"{pcr:.2f}"
)

print()
print(
    "NOTE: This is option-chain analysis only. "
    "It is NOT a BUY CE / BUY PE signal."
)
print("=" * 70)