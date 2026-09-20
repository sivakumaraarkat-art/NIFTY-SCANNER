def calculate_position_size(
    capital: float, risk_fraction: float, entry: float, stop_loss: float
) -> int:
    """
    Calculate the correct position size (number of shares) based on risk percentage.

    Args:
        capital: Total trading capital
        risk_fraction: Fractional risk per trade (e.g., 0.01 for 1%)
        entry: The entry price of the trade
        stop_loss: The stop loss price

    Returns:
        Number of shares to buy
    """
    risk = capital * risk_fraction
    per_share_risk = abs(entry - stop_loss)

    if per_share_risk <= 0:
        return 0

    return int(risk // per_share_risk)
