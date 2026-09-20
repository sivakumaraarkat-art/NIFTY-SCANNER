"""
Stop Loss Calculator

Calculates adaptive stop loss for swing trades using:
- ATR-based volatility stops (1.5× to 2.5× ATR)
- Support level stops (recent swing lows, moving averages)
- Percentage caps (min 1%, max 10%)
"""

import pandas as pd


def calculate_adaptive_stop_loss(
    entry: float,
    atr: float,
    strategy_type: str = "DEFAULT",
    support_level: float | None = None,
    min_risk_pct: float = 0.01,
    max_risk_pct: float = 0.10,
) -> dict:
    """
    Calculate an adaptive stop loss tailored to market conditions and strategy.

    Args:
        entry: Entry price
        atr: Average True Range (14-period)
        strategy_type: 'BREAKOUT', 'PULLBACK', or 'DEFAULT'
        support_level: Known support level or moving average (optional)
        min_risk_pct: Minimum risk percentage (default 1%)
        max_risk_pct: Maximum risk percentage (default 10%)

    Returns:
        Dictionary with stop_loss, risk_per_share, risk_pct, and method
    """
    if entry <= 0:
        raise ValueError(f"Invalid entry price: {entry}")
    if atr <= 0:
        raise ValueError(f"Invalid ATR: {atr}")

    # Set ATR multiplier based on strategy type
    if strategy_type == "BREAKOUT":
        # Breakouts require a bit more breathing room below consolidation
        atr_multiplier = 2.0
    elif strategy_type == "PULLBACK":
        # Pullbacks can use tighter stops just below the support level
        atr_multiplier = 1.5
    else:
        atr_multiplier = 1.5

    # Method 1: Volatility-based stop (ATR)
    atr_stop = entry - (atr_multiplier * atr)
    method = f"{atr_multiplier}x ATR"

    # Method 2: Support-based stop (if provided)
    if support_level and support_level < entry:
        # Buffer slightly below support (0.3x ATR)
        support_stop = support_level - (0.3 * atr)
        # Choose the tighter stop between support and ATR
        if support_stop > atr_stop and support_stop < entry * (1 - min_risk_pct):
            stop_loss = support_stop
            method = "Support Level (with ATR buffer)"
        else:
            stop_loss = atr_stop
    else:
        stop_loss = atr_stop

    # Safety Clamping: Enforce strict swing risk boundaries
    min_stop = entry * (1 - max_risk_pct)  # Max risk bound (e.g. 10%)
    max_stop = entry * (1 - min_risk_pct)  # Min risk bound (e.g. 1%)

    clamped_stop = max(min_stop, min(stop_loss, max_stop))

    risk_per_share = entry - clamped_stop
    risk_pct = risk_per_share / entry

    return {
        "stop_loss": round(clamped_stop, 2),
        "risk_per_share": round(risk_per_share, 2),
        "risk_pct": round(risk_pct * 100, 2),  # In percentage (e.g. 3.5%)
        "method": method,
    }
