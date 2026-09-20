"""
STOCK SWING V1
Liquidity Ranking

Two-stage liquidity process:

STAGE 1 - Quote Liquidity Prefilter
-----------------------------------
Uses Zerodha quote data to quickly rank the broad NSE
stock candidate universe before requesting historical data.

This prevents thousands of historical API requests.

STAGE 2 - Historical Liquidity Validation
------------------------------------------
After historical OHLCV is downloaded for the shortlisted
stocks, calculate 20-day average traded value:

    traded_value = close × volume

This second stage provides the more reliable liquidity ranking.

IMPORTANT:
Liquidity is a universe-quality filter.
It is NOT a trading signal.
"""

from __future__ import annotations

import time
from typing import Iterable

import pandas as pd

# ---------------------------------------------------------------------------
# STAGE 1 - QUOTE LIQUIDITY PREFILTER SETTINGS
# ---------------------------------------------------------------------------

DEFAULT_QUOTE_PREFILTER_STOCKS = 300
DEFAULT_QUOTE_BATCH_SIZE = 200
# Zerodha quote endpoint limit is 1 request/second.
DEFAULT_QUOTE_REQUEST_DELAY_SECONDS = 1.10

# Minimum current/estimated traded value.
# This is only a preliminary filter.
DEFAULT_MINIMUM_QUOTE_TRADED_VALUE = 5_000_000


# ---------------------------------------------------------------------------
# STAGE 2 - HISTORICAL LIQUIDITY SETTINGS
# ---------------------------------------------------------------------------

DEFAULT_LIQUIDITY_LOOKBACK_DAYS = 20
DEFAULT_MINIMUM_AVERAGE_TRADED_VALUE = 10_000_000
DEFAULT_MAXIMUM_STOCKS = 100


# ---------------------------------------------------------------------------
# HELPER
# ---------------------------------------------------------------------------


def _chunks(items: list[str], size: int) -> Iterable[list[str]]:
    """Split a list into smaller batches."""
    for index in range(0, len(items), size):
        yield items[index : index + size]


# ---------------------------------------------------------------------------
# STAGE 1
# QUOTE-BASED LIQUIDITY PREFILTER
# ---------------------------------------------------------------------------


def prefilter_by_quote_liquidity(
    kite,
    stock_candidates: list[dict],
    maximum_stocks: int = DEFAULT_QUOTE_PREFILTER_STOCKS,
    batch_size: int = DEFAULT_QUOTE_BATCH_SIZE,
    minimum_quote_traded_value: float = DEFAULT_MINIMUM_QUOTE_TRADED_VALUE,
    request_delay_seconds: float = DEFAULT_QUOTE_REQUEST_DELAY_SECONDS,
    minimum_price: float = 0,
    maximum_price: float = 999999,
) -> list[dict]:
    """
    Quickly rank broad stock candidates using Zerodha quote data.

    This stage exists specifically to prevent historical OHLCV
    requests for thousands of stocks.

    Approximate current traded value:

        volume × average_price

    Only the top `maximum_stocks` candidates are returned.

    This is a prefilter, not the final liquidity ranking.
    """

    if not stock_candidates:
        return []

    maximum_stocks = max(1, int(maximum_stocks))
    batch_size = max(1, int(batch_size))

    symbols = []

    for candidate in stock_candidates:
        symbol = str(candidate.get("tradingsymbol", "")).strip().upper()

        if not symbol:
            continue

        symbols.append(symbol)

    # Remove duplicate symbols while preserving order.
    symbols = list(dict.fromkeys(symbols))

    print(
        f"Quote liquidity prefilter started for " f"{len(symbols)} stock candidates..."
    )

    results: list[dict] = []

    total_batches = (len(symbols) + batch_size - 1) // batch_size

    for batch_number, symbol_batch in enumerate(
        _chunks(symbols, batch_size),
        start=1,
    ):
        instruments = [f"NSE:{symbol}" for symbol in symbol_batch]

        try:
            quote_data = kite.quote(instruments)

        except Exception as exc:
            print(
                f"WARNING: quote batch {batch_number}/{total_batches} " f"failed: {exc}"
            )

            # Slow down after an API error.
            time.sleep(max(request_delay_seconds, 1.0))
            continue

        for symbol in symbol_batch:

            quote_key = f"NSE:{symbol}"
            quote = quote_data.get(quote_key)

            if not quote:
                continue

            try:
                last_price = float(quote.get("last_price") or 0)

                average_price = float(quote.get("average_price") or 0)

                volume = float(quote.get("volume") or 0)

            except (TypeError, ValueError):
                continue

            if last_price <= 0:
                continue

            if last_price < minimum_price or last_price > maximum_price:
                continue

            if volume <= 0:
                continue

            # Prefer today's average traded price.
            # Fall back to last price if average_price is unavailable.
            reference_price = average_price if average_price > 0 else last_price

            quote_traded_value = reference_price * volume

            if quote_traded_value < minimum_quote_traded_value:
                continue

            results.append(
                {
                    "symbol": symbol,
                    "last_price": last_price,
                    "average_price": average_price,
                    "volume": volume,
                    "quote_traded_value": float(quote_traded_value),
                }
            )

        # Do not hammer Zerodha.
        if batch_number < total_batches:
            time.sleep(request_delay_seconds)

        if batch_number == 1 or batch_number % 5 == 0:
            print(
                f"Quote liquidity progress: "
                f"{batch_number}/{total_batches} batches | "
                f"qualified: {len(results)}"
            )

    results.sort(
        key=lambda item: item["quote_traded_value"],
        reverse=True,
    )

    selected = results[:maximum_stocks]

    # -----------------------------------------------------------------------
    # FALLBACK: If no stocks qualify (market closed/pre-open with volume=0),
    # use the curated liquid stock universe
    # -----------------------------------------------------------------------
    if not selected:
        print(
            "WARNING: Quote liquidity prefilter returned 0 stocks.\n"
            "This typically happens when:\n"
            "  - Market is closed (after 3:30 PM IST)\n"
            "  - Running scan before market open (before 9:15 AM IST)\n"
            "  - Weekend or holiday scan\n"
            "  - Zerodha quote volume is reset to 0\n"
            "\n"
            "Falling back to established liquid stock universe..."
        )

        from .liquid_stocks_universe import get_curated_liquid_symbols

        curated_symbols = get_curated_liquid_symbols()

        # Map curated symbols to candidate dictionaries
        candidate_map = {c["tradingsymbol"]: c for c in stock_candidates}

        fallback_candidates = [
            candidate_map[symbol]
            for symbol in curated_symbols[:maximum_stocks]
            if symbol in candidate_map
        ]

        print(
            f"Using curated liquid universe: {len(fallback_candidates)} stocks.\n"
            f"Stage 2 historical liquidity will validate these against "
            f"20-day average traded value."
        )

        return fallback_candidates

    print(
        f"Quote liquidity prefilter completed: "
        f"{len(selected)} stocks selected from "
        f"{len(symbols)} candidates."
    )

    return selected


# ---------------------------------------------------------------------------
# STAGE 2
# HISTORICAL LIQUIDITY CALCULATION
# ---------------------------------------------------------------------------


def calculate_liquidity_metrics(
    symbol: str,
    dataframe: pd.DataFrame,
    lookback_days: int = DEFAULT_LIQUIDITY_LOOKBACK_DAYS,
) -> dict | None:
    """
    Calculate historical liquidity metrics using recent OHLCV data.

    Traded value:

        close × volume
    """

    required = {"close", "volume"}

    if not required.issubset(dataframe.columns):
        return None

    df = dataframe.copy()

    if len(df) < lookback_days:
        return None

    df["close"] = pd.to_numeric(
        df["close"],
        errors="coerce",
    )

    df["volume"] = pd.to_numeric(
        df["volume"],
        errors="coerce",
    )

    df = df.dropna(subset=["close", "volume"])

    if len(df) < lookback_days:
        return None

    df["traded_value"] = df["close"] * df["volume"]

    recent = df.tail(lookback_days)

    avg_traded_value = recent["traded_value"].mean()
    median_traded_value = recent["traded_value"].median()
    avg_volume = recent["volume"].mean()

    if pd.isna(avg_traded_value) or avg_traded_value <= 0:
        return None

    return {
        "symbol": symbol,
        "average_traded_value": float(avg_traded_value),
        "median_traded_value": float(median_traded_value),
        "average_volume": float(avg_volume),
        "liquidity_days": len(recent),
    }


def rank_liquid_stocks(
    market_data: dict[str, pd.DataFrame],
    minimum_average_traded_value: float = DEFAULT_MINIMUM_AVERAGE_TRADED_VALUE,
    maximum_stocks: int = DEFAULT_MAXIMUM_STOCKS,
    minimum_price: float = 0,
    maximum_price: float = 999999,
) -> list[dict]:
    """
    Return the most liquid stocks after historical analysis.

    This is the SECOND liquidity stage.

    Historical data should already have been downloaded
    only for the quote-prefiltered universe.
    """

    results = []

    for symbol, dataframe in market_data.items():

        # Apply price filter based on latest close price
        if len(dataframe) > 0:
            latest_close = float(dataframe.iloc[-1]["close"])
            if latest_close < minimum_price or latest_close > maximum_price:
                continue

        metrics = calculate_liquidity_metrics(
            symbol=symbol,
            dataframe=dataframe,
            lookback_days=DEFAULT_LIQUIDITY_LOOKBACK_DAYS,
        )

        if metrics is None:
            continue

        if metrics["average_traded_value"] < minimum_average_traded_value:
            continue

        results.append(metrics)

    results.sort(
        key=lambda item: item["average_traded_value"],
        reverse=True,
    )

    return results[:maximum_stocks]
