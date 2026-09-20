"""
STOCK SWING V1
NSE Equity Universe Loader

Purpose:
- Load NSE equity instruments from Zerodha.
- Keep only normal NSE equity (EQ) instruments.
- Remove duplicates.
- Apply basic symbol/data-quality filters.
- Return a clean candidate universe.

IMPORTANT:
This module does NOT determine liquidity by itself.
Liquidity ranking will be performed in the next stage using
historical traded-value data.
"""

from __future__ import annotations

import pandas as pd

NON_STOCK_NAME_MARKERS = (
    "ETF",
    "EXCHANGE TRADED FUND",
    "FUND",
    "MUTUAL FUND",
    "INDEX FUND",
    "TRUST",
    "REAL ESTATE INVESTMENT TRUST",
    "REIT",
    "INVIT",
    "INFRASTRUCTURE INVESTMENT TRUST",
    "GOVERNMENT SECURITY",
    "GOVERNMENT BOND",
    "TREASURY",
    "SOVEREIGN GOLD",
    "BOND",
    "DEBENTURE",
)


def _keep_stock_candidates(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Remove known non-stock instruments from the NSE EQ dump."""

    symbol = dataframe["tradingsymbol"]
    name = (
        dataframe.get(
            "name",
            pd.Series("", index=dataframe.index),
        )
        .fillna("")
        .astype(str)
        .str.upper()
    )

    non_stock_symbol = symbol.str.contains(
        "-",
        regex=False,
        na=False,
    )
    non_stock_symbol |= symbol.str.contains(
        "BEES|ETF|GILT|GSEC|SGB",
        regex=True,
        na=False,
    )
    non_stock_symbol |= symbol.str.endswith(
        "NAV",
        na=False,
    )
    non_stock_name = name.apply(
        lambda value: any(marker in value for marker in NON_STOCK_NAME_MARKERS)
    )

    return dataframe[~(non_stock_symbol | non_stock_name)].copy()


def load_nse_equity_universe(kite, settings) -> list[dict]:
    """
    Load and clean the NSE equity universe from Zerodha.

    Returns:
        List of dictionaries containing:
        tradingsymbol, instrument_token, exchange,
        segment, instrument_type, tick_size, lot_size.
    """

    print("Loading NSE equity instruments from Zerodha...")

    instruments = kite.instruments("NSE")

    if not instruments:
        raise RuntimeError("Zerodha returned an empty NSE instrument list.")

    df = pd.DataFrame(instruments)
    raw_instrument_count = len(df)

    required_columns = {
        "instrument_token",
        "tradingsymbol",
        "exchange",
        "segment",
        "instrument_type",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise RuntimeError(
            f"NSE instrument response is missing columns: {sorted(missing)}"
        )

    # ---------------------------------------------------------
    # 1. Keep only NSE equity instruments
    # ---------------------------------------------------------
    df = df[
        (df["exchange"] == "NSE")
        & (df["segment"] == "NSE")
        & (df["instrument_type"] == "EQ")
    ].copy()

    # ---------------------------------------------------------
    # 2. Remove invalid symbols
    # ---------------------------------------------------------
    df["tradingsymbol"] = df["tradingsymbol"].astype(str).str.strip().str.upper()

    df = df[
        df["tradingsymbol"].notna()
        & (df["tradingsymbol"] != "")
        & (df["tradingsymbol"] != "NAN")
    ]

    # ---------------------------------------------------------
    # 3. Remove known non-stock instruments. Zerodha's EQ segment also
    # contains ETFs, bonds, SGBs, REITs, and other securities.
    # ---------------------------------------------------------
    df = _keep_stock_candidates(df)

    # ---------------------------------------------------------
    # 4. Remove duplicate symbols
    # ---------------------------------------------------------
    df = df.drop_duplicates(
        subset=["tradingsymbol"],
        keep="first",
    )

    # ---------------------------------------------------------
    # 5. Basic quality exclusions
    #
    # We are NOT trying to decide liquidity here.
    # That comes in Step 9B.
    # ---------------------------------------------------------
    excluded_symbols = {
        "NIFTY",
        "BANKNIFTY",
        "FINNIFTY",
        "MIDCPNIFTY",
    }

    df = df[~df["tradingsymbol"].isin(excluded_symbols)]

    # ---------------------------------------------------------
    # 6. Sort for deterministic processing
    # ---------------------------------------------------------
    df = df.sort_values("tradingsymbol").reset_index(drop=True)

    # ---------------------------------------------------------
    # 7. Select fields required by downstream modules
    # ---------------------------------------------------------
    output_columns = [
        "instrument_token",
        "tradingsymbol",
        "exchange",
        "segment",
        "instrument_type",
    ]

    optional_columns = [
        "tick_size",
        "lot_size",
        "name",
    ]

    selected_columns = [
        column for column in output_columns + optional_columns if column in df.columns
    ]

    result = df[selected_columns].to_dict(orient="records")

    print(f"Raw NSE instruments received: " f"{raw_instrument_count}.")
    print(f"Stock candidates prepared: " f"{len(result)} symbols.")

    return result
