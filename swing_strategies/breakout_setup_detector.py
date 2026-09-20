"""
Breakout Setup Detector

Identifies 20-day high breakout setups with:
- Price breaking above 20-day consolidation range
- Volume confirmation (2× average volume)
- ATR compression during consolidation (tight range)
- Strong momentum on breakout
"""

import pandas as pd

# Scoring weights for breakout strategy (total = 100)
SCORE_BREAKOUT_CONFIRMATION = 30  # Clean break above 20-day high
SCORE_VOLUME_SURGE = 25  # Volume 2× average
SCORE_ATR_COMPRESSION = 20  # Tight consolidation (low ATR)
SCORE_MOMENTUM = 15  # Strong price momentum
SCORE_TREND_ALIGNMENT = 10  # Above key moving averages

# ATR compression threshold (current ATR vs 50-day average ATR)
ATR_COMPRESSION_RATIO = 0.75  # Current ATR < 75% of 50-day avg


def detect_breakout_setup(symbol: str, df: pd.DataFrame, settings) -> dict | None:
    """
    Detect 20-day high breakout setup with volume and ATR confirmation.

    Args:
        symbol: Stock symbol
        df: DataFrame with OHLCV and technical indicators
        settings: Settings object with minimum_candidate_score

    Returns:
        Setup dictionary or None if criteria not met
    """
    if len(df) < 60:
        return None

    latest = df.iloc[-1]

    # Required indicators
    required = [
        "close",
        "high",
        "volume",
        "high20",
        "atr14",
        "avg_volume20",
        "volume_ratio20",
        "sma20",
        "sma50",
        "return_20d",
    ]

    if latest[required].isna().any():
        return None

    # Calculate 50-day ATR for compression detection
    if "atr14" in df.columns and len(df) >= 50:
        atr_50d_avg = df["atr14"].tail(50).mean()
    else:
        atr_50d_avg = latest.atr14

    score = 0
    reasons = []

    # =========================================================================
    # Criterion 1: Breakout Confirmation (30 points)
    # Price must be at or near 20-day high (within 1%)
    # =========================================================================
    if latest.close >= latest.high20 * 0.99:
        score += SCORE_BREAKOUT_CONFIRMATION
        reasons.append("breakout: price at 20-day high")

    # =========================================================================
    # Criterion 2: Volume Surge (25 points)
    # Volume must be 2× average to confirm institutional interest
    # =========================================================================
    if latest.volume_ratio20 >= 2.0:
        score += SCORE_VOLUME_SURGE
        reasons.append("volume surge: 2x average")

    # =========================================================================
    # Criterion 3: ATR Compression (20 points)
    # Prior consolidation with tight range (ATR compression)
    # =========================================================================
    if pd.notna(atr_50d_avg) and atr_50d_avg > 0:
        atr_ratio = latest.atr14 / atr_50d_avg
        if atr_ratio < ATR_COMPRESSION_RATIO:
            score += SCORE_ATR_COMPRESSION
            reasons.append(f"consolidation: tight ATR ({atr_ratio:.2f}x 50d avg)")

    # =========================================================================
    # Criterion 4: Strong Momentum (15 points)
    # Positive 20-day return shows sustained buying
    # =========================================================================
    if latest.return_20d > 0.05:  # 5%+ gain in 20 days
        score += SCORE_MOMENTUM
        reasons.append("momentum: 5%+ gain in 20 days")

    # =========================================================================
    # Criterion 5: Trend Alignment (10 points)
    # Price above moving averages suggests trend support
    # =========================================================================
    if latest.close > latest.sma20 and latest.sma20 > latest.sma50:
        score += SCORE_TREND_ALIGNMENT
        reasons.append("trend support: above MAs")

    # Only generate setup if minimum score is met
    if score < settings.minimum_candidate_score:
        return None

    # =========================================================================
    # Calculate Stop Loss (below consolidation low)
    # =========================================================================
    entry_price = float(latest.close)
    atr_value = float(latest.atr14)

    # Stop loss: below recent consolidation (2× ATR below entry)
    raw_stop_loss = entry_price - (2.0 * atr_value)

    # Enforce risk boundaries (min 1%, max 10%)
    min_stop_loss = entry_price * 0.90
    max_stop_loss = entry_price * 0.99
    stop_loss = max(min_stop_loss, min(raw_stop_loss, max_stop_loss))

    # Validate stop loss
    if stop_loss <= 0 or stop_loss >= entry_price:
        return None

    return {
        "symbol": symbol,
        "setup": "BREAKOUT (20D HIGH)",
        "score": score,
        "entry": entry_price,
        "stop_loss": stop_loss,
        "reasons": reasons,
    }
