"""
Risk-Reward Calculator

Evaluates trade setups for risk-reward viability:
- Minimum R:R ratio validation (e.g. 2.0:1)
- Risk-weighted trade scoring
- Expected value calculation
"""


def evaluate_risk_reward(
    entry: float,
    stop_loss: float,
    target: float,
    minimum_rr: float = 2.0,
) -> dict:
    """
    Evaluate the risk-to-reward characteristics of a trade setup.

    Args:
        entry: Planned entry price
        stop_loss: Planned stop loss price
        target: Planned primary target price
        minimum_rr: Minimum acceptable R:R ratio (default 2.0)

    Returns:
        Dictionary with rr_ratio, is_viable, risk_per_share, reward_per_share
    """
    risk = entry - stop_loss
    reward = target - entry

    if risk <= 0:
        return {
            "rr_ratio": 0.0,
            "is_viable": False,
            "risk_per_share": 0.0,
            "reward_per_share": 0.0,
            "reason": "Invalid risk (stop loss >= entry)",
        }

    if reward <= 0:
        return {
            "rr_ratio": 0.0,
            "is_viable": False,
            "risk_per_share": risk,
            "reward_per_share": 0.0,
            "reason": "Invalid reward (target <= entry)",
        }

    rr_ratio = reward / risk
    is_viable = rr_ratio >= minimum_rr

    return {
        "rr_ratio": round(rr_ratio, 2),
        "is_viable": is_viable,
        "risk_per_share": round(risk, 2),
        "reward_per_share": round(reward, 2),
        "reason": (
            "Acceptable R:R"
            if is_viable
            else f"R:R ({rr_ratio:.2f}) < minimum ({minimum_rr:.2f})"
        ),
    }
