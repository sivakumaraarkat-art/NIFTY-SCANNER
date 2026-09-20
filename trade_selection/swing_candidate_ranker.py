"""
Swing Candidate Ranker

Ranks trade candidates and enriches them with:
- Dynamic multi-targets (T1: 1.5R, T2: 2.5R, T3: 4.0R)
- Position sizing based on capital and risk per trade
- R:R evaluation
"""

from .profit_target_calculator import calculate_profit_targets
from .position_size_calculator import calculate_position_size


def rank_trade_candidates(candidates: list[dict], settings) -> list[dict]:
    """
    Rank trade candidates and enrich with multi-targets and position sizing.

    Args:
        candidates: List of candidate dictionaries
        settings: Settings object with initial_capital, risk_per_trade, etc.

    Returns:
        Sorted list of ranked candidates (highest score first)
    """
    ranked = []

    for c in candidates:
        entry = float(c["entry"])
        stop_loss = float(c["stop_loss"])
        risk = entry - stop_loss

        if risk <= 0:
            continue

        if c["score"] < settings.minimum_candidate_score:
            continue

        min_price = getattr(settings, "minimum_stock_price", 0.0)
        max_price = getattr(settings, "maximum_stock_price", 999999.0)
        if entry < min_price or entry > max_price:
            continue

        cand = dict(c)

        # ---------------------------------------------------------------------
        # Dynamic Multi-Targets (T1: 50%, T2: 30%, T3: 20%)
        # ---------------------------------------------------------------------
        targets = calculate_profit_targets(
            entry=entry,
            stop_loss=stop_loss,
            atr=c.get("atr"),
            high_20d=c.get("high_20d"),
        )

        cand["target_1"] = targets["target1"]
        cand["target_2"] = targets["target2"]
        cand["target_3"] = targets["target3"]
        cand["risk_reward"] = targets["risk_reward1"]
        cand["risk_reward_t2"] = targets["risk_reward2"]
        cand["risk_reward_t3"] = targets["risk_reward3"]
        cand["target_allocation"] = targets["allocation"]

        # ---------------------------------------------------------------------
        # Position Sizing
        # ---------------------------------------------------------------------
        pos_size = calculate_position_size(
            capital=settings.initial_capital,
            risk_fraction=settings.risk_per_trade,
            entry=entry,
            stop_loss=stop_loss,
        )
        cand["quantity"] = pos_size
        cand["capital_required"] = round(pos_size * entry, 2)
        cand["risk_amount"] = round(pos_size * risk, 2)

        ranked.append(cand)

    # Sort primarily by score, secondarily by R:R ratio
    return sorted(
        ranked,
        key=lambda x: (x["score"], x["risk_reward"]),
        reverse=True,
    )
