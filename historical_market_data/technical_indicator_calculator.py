"""
Technical Indicator Calculator

Calculates standard technical indicators for swing trading:
- Moving Averages (SMA, EMA)
- RSI (Relative Strength Index) using Wilder's smoothing
- ATR (Average True Range) using Wilder's smoothing
- Volume metrics
- Price momentum and breakout levels
"""

import pandas as pd
import numpy as np


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add technical indicators to OHLCV dataframe.

    Args:
        df: DataFrame with columns: open, high, low, close, volume

    Returns:
        DataFrame with added indicator columns

    Raises:
        ValueError: If required columns are missing or insufficient data
    """
    # Validate input
    required_columns = {"open", "high", "low", "close", "volume"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if len(df) < 50:
        raise ValueError(f"Insufficient data: need at least 50 rows, got {len(df)}")

    # Work on a copy to avoid modifying original
    result = df.copy()

    # Convert to float for calculations
    close = result["close"].astype(float)
    high = result["high"].astype(float)
    low = result["low"].astype(float)
    volume = result["volume"].astype(float)

    # -------------------------------------------------------------------------
    # Moving Averages
    # -------------------------------------------------------------------------
    result["sma20"] = close.rolling(window=20, min_periods=20).mean()
    result["sma50"] = close.rolling(window=50, min_periods=50).mean()
    result["ema20"] = close.ewm(span=20, adjust=False).mean()

    # -------------------------------------------------------------------------
    # RSI (Relative Strength Index) - Wilder's Smoothing Method
    # -------------------------------------------------------------------------
    # Calculate price changes
    delta = close.diff()

    # Separate gains and losses
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    # Apply Wilder's smoothing (EMA with alpha=1/14)
    avg_gain = gains.ewm(alpha=1 / 14, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / 14, adjust=False).mean()

    # Calculate RS and RSI
    rs = avg_gain / avg_loss.replace(0, np.nan)
    result["rsi14"] = 100 - (100 / (1 + rs))

    # Fill initial NaN values with neutral 50
    result["rsi14"] = result["rsi14"].fillna(50.0)

    # -------------------------------------------------------------------------
    # ATR (Average True Range) - Wilder's Smoothing Method
    # -------------------------------------------------------------------------
    # Previous close for True Range calculation
    prev_close = close.shift(1)

    # True Range is the maximum of:
    # 1. High - Low
    # 2. |High - Previous Close|
    # 3. |Low - Previous Close|
    tr_components = pd.DataFrame(
        {
            "hl": high - low,
            "hc": (high - prev_close).abs(),
            "lc": (low - prev_close).abs(),
        }
    )

    true_range = tr_components.max(axis=1)

    # Apply Wilder's smoothing
    result["atr14"] = true_range.ewm(alpha=1 / 14, adjust=False).mean()

    # -------------------------------------------------------------------------
    # Volume Indicators
    # -------------------------------------------------------------------------
    result["avg_volume20"] = volume.rolling(window=20, min_periods=20).mean()

    # Volume ratio (current volume / 20-day average)
    # Replace zero averages with NaN to avoid division errors
    result["volume_ratio20"] = volume / result["avg_volume20"].replace(0, np.nan)

    # -------------------------------------------------------------------------
    # Price Momentum & Breakout Levels
    # -------------------------------------------------------------------------
    # 20-day high (for breakout detection)
    result["high20"] = high.rolling(window=20, min_periods=20).max()

    # 20-day return (momentum)
    result["return_20d"] = close.pct_change(periods=20)

    return result


def validate_indicators(df: pd.DataFrame, symbol: str = "UNKNOWN") -> bool:
    """
    Validate that indicators were calculated correctly.

    Args:
        df: DataFrame with technical indicators
        symbol: Stock symbol for error messages

    Returns:
        True if validation passes, False otherwise
    """
    required_indicators = [
        "sma20",
        "sma50",
        "ema20",
        "rsi14",
        "atr14",
        "avg_volume20",
        "volume_ratio20",
        "high20",
        "return_20d",
    ]

    # Check all columns exist
    missing = set(required_indicators) - set(df.columns)
    if missing:
        print(f"WARNING: {symbol} missing indicators: {missing}")
        return False

    # Check last row has valid values (at least some indicators)
    if len(df) > 0:
        last_row = df.iloc[-1]

        # RSI should be between 0 and 100
        if not pd.isna(last_row["rsi14"]):
            if not (0 <= last_row["rsi14"] <= 100):
                print(f"WARNING: {symbol} invalid RSI: {last_row['rsi14']:.2f}")
                return False

        # ATR should be positive
        if not pd.isna(last_row["atr14"]):
            if last_row["atr14"] <= 0:
                print(f"WARNING: {symbol} invalid ATR: {last_row['atr14']:.2f}")
                return False

    return True
