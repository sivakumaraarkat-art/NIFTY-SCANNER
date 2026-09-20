"""
Trend Pullback Detector

Identifies pullback buying opportunities in strong uptrends:
- Strong uptrend (price > SMA50, SMA50 rising)
- Pullback to support (SMA20 or previous consolidation)
- RSI oversold bounce (RSI dipped below 40, now recovering)
- Volume contraction during pullback, expansion on bounce
- Bullish price action (recent green candle)
"""

import pandas as pd

# Scoring weights for trend pullback strategy (total = 100)
SCORE_STRONG_UPTREND = 25  # Price > SMA50, SMA50 rising
SCORE_PULLBACK_SUPPORT = 25  # Price at/near SMA20 support
SCORE_RSI_BOUNCE = 20  # RSI oversold recovery
SCORE_VOLUME_PATTERN = 15  # Volume expansion on bounce
SCORE_BULLISH_CANDLE = 15  # Recent bullish price action

# Thresholds
RSI_OVERSOLD_LEVEL = 40  # RSI below this indicates oversold
RSI_RECOVERY_MIN = 45  # RSI must recover above this
SMA50_RISING_PERIODS = 10  # SMA50 must be rising over last 10 days


def detect_trend_pullback_setup(symbol: str, df: pd.DataFrame, settings) -> dict | None:
    """
    Detect pullback buying opportunity in strong uptrend.

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
    previous = df.iloc[-2] if len(df) >= 2 else latest

    # Required indicators
    required = [
        "close",
        "open",
        "high",
        "low",
        "volume",
        "sma20",
        "sma50",
        "rsi14",
        "atr14",
        "avg_volume20",
        "volume_ratio20",
    ]

    if latest[required].isna().any():
        return None

    score = 0
    reasons = []

    # =========================================================================
    # Criterion 1: Strong Uptrend (25 points)
    # Price above SMA50 and SMA50 is rising
    # =========================================================================
    if latest.close > latest.sma50:
        # Check if SMA50 is rising (compare current vs 10 days ago)
        if len(df) >= SMA50_RISING_PERIODS + 50:
            sma50_10d_ago = df["sma50"].iloc[-(SMA50_RISING_PERIODS + 1)]
            if pd.notna(sma50_10d_ago) and latest.sma50 > sma50_10d_ago:
                score += SCORE_STRONG_UPTREND
                reasons.append("strong uptrend: price > SMA50, SMA50 rising")

    # =========================================================================
    # Criterion 2: Pullback to Support (25 points)
    # Price pulled back to SMA20 (within 2% of SMA20)
    # =========================================================================
    distance_to_sma20 = abs(latest.close - latest.sma20) / latest.sma20
    if distance_to_sma20 <= 0.02:  # Within 2% of SMA20
        score += SCORE_PULLBACK_SUPPORT
        reasons.append("pullback to SMA20 support")
    elif latest.close > latest.sma20 and latest.close < latest.sma20 * 1.03:
        # Partial credit if just above SMA20
        score += int(SCORE_PULLBACK_SUPPORT * 0.6)
        reasons.append("near SMA20 support")

    # =========================================================================
    # Criterion 3: RSI Oversold Bounce (20 points)
    # RSI was oversold (< 40) recently and now recovering (> 45)
    # =========================================================================
    if latest.rsi14 >= RSI_RECOVERY_MIN:
        # Check if RSI was oversold in last 5 bars
        recent_rsi = df["rsi14"].tail(6).iloc[:-1]  # Last 5 bars excluding current
        was_oversold = (recent_rsi < RSI_OVERSOLD_LEVEL).any()

        if was_oversold:
            score += SCORE_RSI_BOUNCE
            reasons.append(f"RSI bounce: oversold recovery to {latest.rsi14:.0f}")

    # =========================================================================
    # Criterion 4: Volume Pattern (15 points)
    # Volume expansion on the bounce (current volume > average)
    # =========================================================================
    if latest.volume_ratio20 >= 1.2:  # 20%+ above average
        score += SCORE_VOLUME_PATTERN
        reasons.append("volume expansion on bounce")

    # =========================================================================
    # Criterion 5: Bullish Candle (15 points)
    # Latest candle is bullish (close > open)
    # =========================================================================
    if latest.close > latest.open:
        candle_size = (latest.close - latest.open) / latest.open
        if candle_size >= 0.01:  # At least 1% green candle
            score += SCORE_BULLISH_CANDLE
            reasons.append("bullish price action")

    # Only generate setup if minimum score is met
    if score < settings.minimum_candidate_score:
        return None

    # =========================================================================
    # Calculate Stop Loss (below SMA20 or recent low)
    # =========================================================================
    entry_price = float(latest.close)
    atr_value = float(latest.atr14)

    # Stop loss: below SMA20 support or 1.5× ATR, whichever is closer
    sma20_stop = float(latest.sma20) - (0.5 * atr_value)
    atr_stop = entry_price - (1.5 * atr_value)

    # Use the tighter stop (closer to entry)
    raw_stop_loss = max(sma20_stop, atr_stop)

    # Enforce risk boundaries (min 1%, max 10%)
    min_stop_loss = entry_price * 0.90
    max_stop_loss = entry_price * 0.99
    stop_loss = max(min_stop_loss, min(raw_stop_loss, max_stop_loss))

    # Validate stop loss
    if stop_loss <= 0 or stop_loss >= entry_price:
        return None

    return {
        "symbol": symbol,
        "setup": "TREND PULLBACK",
        "score": score,
        "entry": entry_price,
        "stop_loss": stop_loss,
        "reasons": reasons,
    }
