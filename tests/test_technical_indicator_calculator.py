import pandas as pd
import numpy as np
import pytest
from historical_market_data.technical_indicator_calculator import (
    add_technical_indicators,
    validate_indicators,
)


def test_indicators_added_and_values_valid():
    """Test that all indicator columns exist and contain valid values."""
    n = 80
    dates = pd.date_range("2026-01-01", periods=n)
    # Simulate an upward trend with some volatility
    close_prices = [100.0 + i * 0.5 + (i % 3 - 1) * 0.5 for i in range(n)]
    df = pd.DataFrame(
        {
            "date": dates,
            "open": [p - 0.2 for p in close_prices],
            "high": [p + 1.0 for p in close_prices],
            "low": [p - 1.0 for p in close_prices],
            "close": close_prices,
            "volume": [100000 + i * 500 for i in range(n)],
        }
    )

    result = add_technical_indicators(df)

    expected_cols = [
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
    for col in expected_cols:
        assert col in result.columns, f"Missing column {col}"

    # Last row should have valid non-NaN values
    last_row = result.iloc[-1]
    assert not pd.isna(last_row["sma20"])
    assert not pd.isna(last_row["sma50"])
    assert not pd.isna(last_row["rsi14"])
    assert not pd.isna(last_row["atr14"])

    # RSI range check (0-100)
    assert 0 <= last_row["rsi14"] <= 100

    # ATR check (must be positive)
    assert last_row["atr14"] > 0

    # Validate function passes
    assert validate_indicators(result, "TEST") is True


def test_insufficient_data_raises_value_error():
    """Test that < 50 rows raises ValueError."""
    df = pd.DataFrame(
        {
            "open": [100] * 30,
            "high": [105] * 30,
            "low": [95] * 30,
            "close": [102] * 30,
            "volume": [1000] * 30,
        }
    )
    with pytest.raises(ValueError, match="Insufficient data"):
        add_technical_indicators(df)


def test_missing_column_raises_value_error():
    """Test that missing columns raise ValueError."""
    df = pd.DataFrame(
        {
            "open": [100] * 60,
            "high": [105] * 60,
            "low": [95] * 60,
            # missing close and volume
        }
    )
    with pytest.raises(ValueError, match="Missing required columns"):
        add_technical_indicators(df)
