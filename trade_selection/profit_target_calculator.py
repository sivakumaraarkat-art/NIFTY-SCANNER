"""
Profit Target Calculator

Calculates dynamic profit targets for swing trades using:
- Multi-target approach (T1, T2, T3)
- Higher risk-reward ratios for swing trades (2R, 3R, 5R)
- ATR-based targets (3× to 5× ATR)
- Resistance-based targets (optional)

Target allocation strategy:
- T1 (2.0× risk): Book 50% of position
- T2 (3.0× risk): Book 30% of position
- T3 (5.0× risk or trailing): Hold 20% of position
"""

import pandas as pd


def calculate_profit_targets(
    entry: float,
    stop_loss: float,
    atr: float | None = None,
    high_20d: float | None = None,
) -> dict:
    """
    Calculate three profit targets for a swing trade.

    Args:
        entry: Entry price
        stop_loss: Stop loss price
        atr: Current ATR (optional, for ATR-based targets)
        high_20d: 20-day high (optional, for resistance-based targets)

    Returns:
        Dictionary with target1, target2, target3, and risk_reward ratios
    """
    # Calculate risk per share
    risk = entry - stop_loss

    if risk <= 0:
        raise ValueError(f"Invalid risk: entry={entry}, stop_loss={stop_loss}")

    # =========================================================================
    # METHOD 1: Risk-Reward Multiple Targets (Primary)
    # =========================================================================
    rr_target1 = entry + (2.0 * risk)  # 2.0:1 R/R (Book 50%)
    rr_target2 = entry + (3.5 * risk)  # 3.5:1 R/R (Book 30%)
    rr_target3 = entry + (5.5 * risk)  # 5.5:1 R/R (Trail 20%)

    # =========================================================================
    # METHOD 2: ATR-Based Targets (Volatility adjusted)
    # For swing trading (1-3 weeks), swings typically move 2.5x to 5.5x ATR
    # =========================================================================
    if atr and atr > 0:
        atr_target1 = entry + (2.5 * atr)
        atr_target2 = entry + (4.0 * atr)
        atr_target3 = entry + (6.0 * atr)

        # Take the maximum so tight stops don't produce tiny unrealistically low targets
        target1 = max(rr_target1, atr_target1)
        target2 = max(rr_target2, atr_target2)
        target3 = max(rr_target3, atr_target3)
    else:
        target1 = rr_target1
        target2 = rr_target2
        target3 = rr_target3

    # =========================================================================
    # METHOD 3: Minimum Swing Trade Profit Floors
    # T1 minimum: +4.0% | T2 minimum: +8.0% | T3 minimum: +15.0%
    # =========================================================================
    target1 = max(target1, entry * 1.04)  # Minimum +4%
    target2 = max(target2, target1 * 1.04, entry * 1.08)  # Minimum +8%
    target3 = max(target3, target2 * 1.06, entry * 1.15)  # Minimum +15%

    # Calculate actual risk-reward ratios
    rr1 = (target1 - entry) / risk
    rr2 = (target2 - entry) / risk
    rr3 = (target3 - entry) / risk

    return {
        "target1": round(target1, 2),
        "target2": round(target2, 2),
        "target3": round(target3, 2),
        "risk_reward1": round(rr1, 2),
        "risk_reward2": round(rr2, 2),
        "risk_reward3": round(rr3, 2),
        "allocation": {
            "target1": "50%",  # Book half position at T1
            "target2": "30%",  # Book 30% at T2
            "target3": "20%",  # Trail remaining 20%
        },
    }


def calculate_trailing_stop(
    entry: float,
    current_price: float,
    highest_price_since_entry: float,
    atr: float,
) -> float:
    """
    Calculate trailing stop loss for remaining position after T2 hit.

    Args:
        entry: Original entry price
        current_price: Current market price
        highest_price_since_entry: Highest price reached since entry
        atr: Current ATR value

    Returns:
        Trailing stop loss price
    """
    # Trail by 2× ATR below the highest price
    trailing_stop = highest_price_since_entry - (2.0 * atr)

    # Ensure trailing stop never goes below breakeven
    trailing_stop = max(trailing_stop, entry)

    # Ensure trailing stop is below current price
    trailing_stop = min(trailing_stop, current_price * 0.98)

    return round(trailing_stop, 2)
