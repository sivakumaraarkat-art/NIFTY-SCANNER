"""
Swing Setup Engine

Orchestrates multiple swing trade strategy detectors:
1. Technical Swing Watch (original - trend, RSI, volume, momentum)
2. Breakout Setup (20-day high with volume confirmation)
3. Trend Pullback (pullback to support in strong uptrend)

Each detector independently scores setups and returns candidates.
"""

from .breakout_setup_detector import detect_breakout_setup
from .trend_pullback_detector import detect_trend_pullback_setup

# Scoring weights (total = 100) for Technical Swing Watch
SCORE_TREND_ALIGNMENT = 25  # Price > SMA20 > SMA50
SCORE_RSI_HEALTHY = 20  # RSI between 50-70 (healthy uptrend)
SCORE_VOLUME_SURGE = 20  # Volume 1.5x+ average
SCORE_MOMENTUM = 20  # 3%+ gain in 20 days
SCORE_BREAKOUT_PROXIMITY = 15  # Within 2% of 20-day high

# Stop loss settings
ATR_MULTIPLIER = 1.5  # Stop loss = entry - (1.5 × ATR)
MIN_RISK_PERCENT = 0.01  # Minimum 1% risk
MAX_RISK_PERCENT = 0.10  # Maximum 10% risk for swing trades


def generate_setup_candidates(frames: dict, settings) -> list[dict]:
    """
    Generate swing trade setup candidates using multiple strategies.

    Runs three independent strategy detectors:
    1. Technical Swing Watch (original scoring system)
    2. Breakout Setup (20-day high breakout detector)
    3. Trend Pullback (pullback in uptrend detector)

    Args:
        frames: Dictionary of {symbol: DataFrame with technical indicators}
        settings: Settings object with minimum_candidate_score

    Returns:
        List of setup dictionaries with entry, stop_loss, score, reasons
    """
    candidates = []

    for symbol, df in frames.items():
        detectors = [
            _detect_technical_swing_watch,
            detect_breakout_setup,
            detect_trend_pullback_setup,
        ]

        for detector in detectors:
            try:
                setup = detector(symbol, df, settings)
                if setup:
                    # Enrich setup with extra metadata for target calculator and institutional indicator
                    latest = df.iloc[-1]
                    setup["atr"] = (
                        float(latest["atr14"]) if "atr14" in df.columns else None
                    )
                    setup["high_20d"] = (
                        float(latest["high20"]) if "high20" in df.columns else None
                    )
                    setup["volume_ratio20"] = (
                        float(latest["volume_ratio20"])
                        if "volume_ratio20" in df.columns
                        else 0
                    )
                    candidates.append(setup)
            except Exception as exc:
                print(f"WARNING: {detector.__name__} failed for {symbol}: {exc}")

    return candidates


def _detect_technical_swing_watch(symbol: str, df, settings) -> dict | None:
    """
    Original technical swing watch strategy (trend + RSI + volume + momentum).
    """
    if len(df) < 60:
        return None

    latest = df.iloc[-1]

    required_indicators = [
        "sma20",
        "sma50",
        "rsi14",
        "atr14",
        "volume_ratio20",
        "return_20d",
        "high20",
    ]

    if latest[required_indicators].isna().any():
        return None

    score = 0
    reasons = []

    # Criterion 1: Trend Alignment (25 points)
    if latest.close > latest.sma20 > latest.sma50:
        score += SCORE_TREND_ALIGNMENT
        reasons.append("uptrend: price > SMA20 > SMA50")

    # Criterion 2: RSI Health (20 points)
    if 50 <= latest.rsi14 <= 70:
        score += SCORE_RSI_HEALTHY
        reasons.append("healthy RSI (50-70 range)")

    # Criterion 3: Volume Expansion (20 points)
    if latest.volume_ratio20 >= 1.5:
        score += SCORE_VOLUME_SURGE
        reasons.append("volume surge (1.5x+ average)")

    # Criterion 4: Positive Momentum (20 points)
    if latest.return_20d > 0.03:
        score += SCORE_MOMENTUM
        reasons.append("positive momentum (3%+ in 20d)")

    # Criterion 5: Breakout Proximity (15 points)
    if latest.close >= latest.high20 * 0.98:
        score += SCORE_BREAKOUT_PROXIMITY
        reasons.append("near 20-day high breakout")

    if score < settings.minimum_candidate_score:
        return None

    entry_price = float(latest.close)
    atr_value = float(latest.atr14)

    raw_stop_loss = entry_price - (ATR_MULTIPLIER * atr_value)
    min_stop_loss = entry_price * (1 - MAX_RISK_PERCENT)
    max_stop_loss = entry_price * (1 - MIN_RISK_PERCENT)

    stop_loss = max(min_stop_loss, min(raw_stop_loss, max_stop_loss))

    if stop_loss <= 0 or stop_loss >= entry_price:
        return None

    return {
        "symbol": symbol,
        "setup": "TECHNICAL SWING WATCH",
        "score": score,
        "entry": entry_price,
        "stop_loss": stop_loss,
        "reasons": reasons,
    }
