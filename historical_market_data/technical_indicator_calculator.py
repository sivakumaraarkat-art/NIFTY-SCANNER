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

    # -------------------------------------------------------------------------
    # Bollinger Bands - Volatility-based mean reversion
    # -------------------------------------------------------------------------
    bb_window = 20
    bb_std_mult = 2.0
    
    sma_bb = close.rolling(window=bb_window, min_periods=bb_window).mean()
    bb_std = close.rolling(window=bb_window, min_periods=bb_window).std()
    
    result["bb_upper"] = sma_bb + (bb_std * bb_std_mult)
    result["bb_lower"] = sma_bb - (bb_std * bb_std_mult)
    result["bb_middle"] = sma_bb
    result["bb_sma"] = sma_bb

    # -------------------------------------------------------------------------
    # MACD - Momentum indicator for trend confirmation
    # -------------------------------------------------------------------------
    # Fast and slow EMA periods
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    
    ema_fast = close.ewm(span=macd_fast, adjust=False).mean()
    ema_slow = close.ewm(span=macd_slow, adjust=False).mean()
    
    result["macd_line"] = ema_fast - ema_slow
    result["macd_signal"] = result["macd_line"].ewm(span=macd_signal, adjust=False).mean()
    result["macd_hist"] = result["macd_line"] - result["macd_signal"]

    return result


def add_intraday_indicators(
    df: pd.DataFrame, atr_period: int = 10, atr_multiplier: float = 3.0
) -> pd.DataFrame:
    """Add session VWAP and SuperTrend to chronologically ordered intraday OHLCV."""
    required_columns = {"date", "open", "high", "low", "close", "volume"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if df.empty:
        raise ValueError("Intraday data must contain at least one candle")
    if atr_period < 1 or atr_multiplier <= 0:
        raise ValueError("atr_period and atr_multiplier must be positive")

    result = df.copy()
    timestamps = pd.to_datetime(result["date"], errors="coerce")
    if timestamps.isna().any():
        raise ValueError("Intraday date column contains invalid timestamps")
    if not timestamps.is_monotonic_increasing:
        raise ValueError("Intraday candles must be in chronological order")

    high = result["high"].astype(float)
    low = result["low"].astype(float)
    close = result["close"].astype(float)
    volume = result["volume"].astype(float)

    typical_price = (high + low + close) / 3
    session = timestamps.dt.normalize()
    cumulative_value = (typical_price * volume).groupby(session, sort=False).cumsum()
    cumulative_volume = volume.groupby(session, sort=False).cumsum()
    result["intraday_vwap"] = cumulative_value / cumulative_volume.replace(0, np.nan)

    previous_close = close.shift(1)
    true_range = pd.concat(
        [high - low, (high - previous_close).abs(), (low - previous_close).abs()],
        axis=1,
    ).max(axis=1)
    atr = true_range.ewm(alpha=1 / atr_period, adjust=False).mean()
    midpoint = (high + low) / 2
    basic_upper = (midpoint + atr_multiplier * atr).to_numpy()
    basic_lower = (midpoint - atr_multiplier * atr).to_numpy()
    close_values = close.to_numpy()

    final_upper = basic_upper.copy()
    final_lower = basic_lower.copy()
    bullish = np.ones(len(result), dtype=bool)
    for index in range(1, len(result)):
        if basic_upper[index] < final_upper[index - 1] or close_values[index - 1] > final_upper[index - 1]:
            final_upper[index] = basic_upper[index]
        else:
            final_upper[index] = final_upper[index - 1]

        if basic_lower[index] > final_lower[index - 1] or close_values[index - 1] < final_lower[index - 1]:
            final_lower[index] = basic_lower[index]
        else:
            final_lower[index] = final_lower[index - 1]

        if bullish[index - 1]:
            bullish[index] = close_values[index] >= final_lower[index]
        else:
            bullish[index] = close_values[index] > final_upper[index]

    result["intraday_supertrend"] = np.where(bullish, final_lower, final_upper)
    result["intraday_trend"] = np.where(bullish, "bullish", "bearish")
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
        "bb_upper",
        "bb_lower",
        "macd_line",
        "macd_signal",
        "macd_hist",
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
