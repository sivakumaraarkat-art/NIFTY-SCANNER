"""
Entry Price Calculator

Calculates recommended entry levels for swing trades:
- Breakout entry (slight buffer above breakout level to confirm)
- Pullback entry (limit order at support level)
- Market entry validation (avoid chasing overextended moves)
"""


def calculate_entry_price(
    current_price: float,
    strategy_type: str,
    high_20d: float | None = None,
    sma20: float | None = None,
    atr: float | None = None,
) -> dict:
    """
    Calculate recommended entry level and order type.

    Args:
        current_price: Current market price (latest close)
        strategy_type: 'BREAKOUT', 'PULLBACK', or 'DEFAULT'
        high_20d: 20-day high level (for breakout strategies)
        sma20: 20-day SMA level (for pullback strategies)
        atr: Current ATR

    Returns:
        Dictionary with entry_price, order_type, max_chase_price, and note
    """
    buffer = (0.1 * atr) if (atr and atr > 0) else (0.002 * current_price)

    if strategy_type == "BREAKOUT" and high_20d:
        # Breakout entry: at or slightly above 20-day high to confirm
        suggested_entry = max(current_price, high_20d + buffer)
        order_type = "BUY_STOP_LIMIT"
        max_chase = suggested_entry * 1.015  # Do not chase > 1.5% above entry
        note = "Enter upon confirmation above 20-day high"

    elif strategy_type == "PULLBACK" and sma20:
        # Pullback entry: limit order near SMA20 support
        suggested_entry = current_price
        order_type = "BUY_LIMIT"
        max_chase = suggested_entry * 1.01  # Do not chase > 1.0% above
        note = "Enter near SMA20 support level"

    else:
        # Default swing entry at current price
        suggested_entry = current_price
        order_type = "BUY_LIMIT"
        max_chase = suggested_entry * 1.01
        note = "Standard swing entry"

    return {
        "entry_price": round(suggested_entry, 2),
        "order_type": order_type,
        "max_chase_price": round(max_chase, 2),
        "note": note,
    }
