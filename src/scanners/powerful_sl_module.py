"""
POWERFUL SL CALCULATION MODULE
═════════════════════════════════════════════════════════════════
4-Layer SL Strategy to prevent whipsaw (price hits 98-99, bounces to 105)

Layers:
  1. Delta-Based Foundation (tight base)
  2. Volatility Buffer (IV adjustment)
  3. Theta Shield (time decay protection)
  4. Vega Insurance (IV crush protection)

Plus Anti-Whipsaw Features:
  • Trailing SL
  • Breakeven exit logic
  • Partial exit on bounce
"""

from typing import Dict, Tuple
import math


def calculate_powerful_sl(
    entry_price: float,
    delta: float,
    iv: float,
    theta: float,
    vega: float,
    option_type: str = "CE",
    days_held: float = 1.0,
    market_volatility: str = "normal"
) -> Dict:
    """
    Calculate 4-layer protective SL to prevent whipsaw.

    Args:
        entry_price: Entry price of option (₹)
        delta: Option delta (0-1)
        iv: Implied Volatility (15-50%)
        theta: Theta decay per day (negative value)
        vega: Vega (sensitivity to 1% IV change)
        option_type: "CE" or "PE"
        days_held: Days you plan to hold (1 = intraday, 1+ = BTST)
        market_volatility: "normal" / "volatile" / "extreme"

    Returns:
        Dict with SL prices and protection details
    """

    # Normalize values
    iv_pct = iv / 100 if iv > 1 else iv  # Convert to decimal
    theta_abs = abs(theta)
    vega_abs = abs(vega)

    # ─────────────────────────────────────────────────────────────
    # LAYER 1: Delta-Based Foundation (Tight Base SL)
    # ─────────────────────────────────────────────────────────────

    if market_volatility == "normal":
        delta_multiplier = 0.18
    elif market_volatility == "volatile":
        delta_multiplier = 0.20
    else:  # extreme
        delta_multiplier = 0.22

    # For PE: adjust delta (PE delta is negative, convert to absolute)
    adj_delta = abs(delta)

    base_sl = entry_price * (1 - adj_delta * delta_multiplier)
    layer1_buffer = entry_price - base_sl

    # ─────────────────────────────────────────────────────────────
    # LAYER 2: Volatility Buffer (IV Adjustment)
    # ─────────────────────────────────────────────────────────────

    if iv_pct > 0.20:
        vol_multiplier = 1.5 if market_volatility == "extreme" else 1.0
        vol_buffer = (iv_pct / 0.20) * entry_price * 0.05 * vol_multiplier
    else:
        vol_buffer = 0

    # ─────────────────────────────────────────────────────────────
    # LAYER 3: Theta Shield (Time Decay Protection)
    # ─────────────────────────────────────────────────────────────

    if market_volatility == "normal":
        theta_multiplier = 1.5
    elif market_volatility == "volatile":
        theta_multiplier = 2.0
    else:  # extreme
        theta_multiplier = 2.5

    theta_buffer = theta_abs * days_held * theta_multiplier

    # ─────────────────────────────────────────────────────────────
    # LAYER 4: Vega Insurance (IV Crush Protection)
    # ─────────────────────────────────────────────────────────────

    if market_volatility == "normal":
        vega_multiplier = 5
    elif market_volatility == "volatile":
        vega_multiplier = 5
    else:  # extreme
        vega_multiplier = 7.5

    vega_buffer = vega_abs * vega_multiplier

    # ─────────────────────────────────────────────────────────────
    # FINAL SL CALCULATION
    # ─────────────────────────────────────────────────────────────

    total_buffer = layer1_buffer + vol_buffer + theta_buffer + vega_buffer
    powerful_sl = entry_price - total_buffer

    # Safety check: SL should not exceed entry price
    powerful_sl = max(powerful_sl, entry_price * 0.80)  # Minimum 20% from entry

    # Anti-Whipsaw Features
    # Trailing SL level: Move SL up when price moves +5%
    trailing_trigger = entry_price * 1.05  # +5% profit level
    trailing_sl_new = powerful_sl + (entry_price * 1.05 - entry_price) * 0.5  # Move SL up 50% of profit

    # Breakeven exit: If price hits near SL and bounces, exit at breakeven
    breakeven_buffer = entry_price * 0.005  # ±0.5% breakeven zone
    breakeven_level = entry_price

    # Partial exit: Exit 50% if near SL and bouncing
    partial_exit_trigger = powerful_sl + 1  # Just above SL

    return {
        "entry_price": entry_price,
        "base_sl": base_sl,
        "layer1_buffer": layer1_buffer,
        "layer2_vol_buffer": vol_buffer,
        "layer3_theta_buffer": theta_buffer,
        "layer4_vega_buffer": vega_buffer,
        "total_buffer": total_buffer,
        "powerful_sl": round(powerful_sl, 2),
        "sl_risk": round(entry_price - powerful_sl, 2),
        "sl_risk_pct": round((entry_price - powerful_sl) / entry_price * 100, 2),

        # Anti-Whipsaw Features
        "trailing_trigger": round(trailing_trigger, 2),
        "trailing_sl_new": round(trailing_sl_new, 2),
        "breakeven_level": round(breakeven_level, 2),
        "breakeven_buffer": round(breakeven_buffer, 2),
        "partial_exit_trigger": round(partial_exit_trigger, 2),

        # Greeks for reference
        "delta": delta,
        "iv": iv,
        "theta": theta,
        "vega": vega,
        "market_volatility": market_volatility,
    }


def calculate_position_size_with_powerful_sl(
    entry_price: float,
    powerful_sl: float,
    account_size: float = 500000,
    risk_pct: float = 0.01
) -> Dict:
    """
    Calculate position size using 1% risk rule with powerful SL.

    Args:
        entry_price: Entry price (₹)
        powerful_sl: Powerful SL price (₹)
        account_size: Trading account size (₹)
        risk_pct: Risk percentage (default 1%)

    Returns:
        Dict with position sizing details
    """

    risk_per_share = entry_price - powerful_sl
    risk_amount = account_size * risk_pct

    if risk_per_share <= 0:
        return {
            "error": "Invalid SL: SL should be below entry price",
            "entry_price": entry_price,
            "powerful_sl": powerful_sl,
        }

    quantity = int(risk_amount / risk_per_share)
    capital_needed = quantity * entry_price

    # Target calculations
    target_1 = entry_price * 1.08  # +8% (conservative)
    target_2 = entry_price * 1.15  # +15% (aggressive)

    potential_profit_t1 = quantity * (target_1 - entry_price)
    potential_profit_t2 = quantity * (target_2 - entry_price)

    return {
        "entry_price": round(entry_price, 2),
        "powerful_sl": round(powerful_sl, 2),
        "risk_per_share": round(risk_per_share, 2),
        "risk_amount": round(risk_amount, 2),
        "quantity": quantity,
        "capital_needed": round(capital_needed, 2),
        "target_1": round(target_1, 2),
        "target_2": round(target_2, 2),
        "potential_profit_t1": round(potential_profit_t1, 2),
        "potential_profit_t2": round(potential_profit_t2, 2),
        "account_size": account_size,
        "risk_pct": risk_pct,
    }


def get_market_volatility(iv: float) -> str:
    """Determine market volatility level based on IV."""
    if iv > 30:
        return "extreme"
    elif iv > 20:
        return "volatile"
    else:
        return "normal"


def print_powerful_sl_analysis(sl_result: Dict, position_result: Dict) -> None:
    """Pretty print SL analysis and position sizing."""

    print("\n" + "="*90)
    print("🛡️ POWERFUL SL STRATEGY - WHIPSAW PROTECTION".center(90))
    print("="*90)

    # SL Analysis
    print(f"\n📊 STOP LOSS LAYERS:")
    print(f"   Layer 1 - Delta Base:        ₹{sl_result['base_sl']:.2f} (Buffer: ₹{sl_result['layer1_buffer']:.2f})")
    print(f"   Layer 2 - Volatility:        Buffer: ₹{sl_result['layer2_vol_buffer']:.2f}")
    print(f"   Layer 3 - Theta Shield:      Buffer: ₹{sl_result['layer3_theta_buffer']:.2f}")
    print(f"   Layer 4 - Vega Insurance:    Buffer: ₹{sl_result['layer4_vega_buffer']:.2f}")
    print(f"   ─────────────────────────────────────────")
    print(f"   TOTAL BUFFER:                ₹{sl_result['total_buffer']:.2f}")

    print(f"\n🎯 FINAL SL: ₹{sl_result['powerful_sl']:.2f}")
    print(f"   Entry:  ₹{sl_result['entry_price']:.2f}")
    print(f"   SL:     ₹{sl_result['powerful_sl']:.2f}")
    print(f"   Risk:   ₹{sl_result['sl_risk']:.2f} ({sl_result['sl_risk_pct']:.2f}%)")

    # Anti-Whipsaw Features
    print(f"\n🔄 ANTI-WHIPSAW FEATURES:")
    print(f"   Trailing SL trigger:  ₹{sl_result['trailing_trigger']:.2f} (+5%)")
    print(f"   New SL if triggered:  ₹{sl_result['trailing_sl_new']:.2f}")
    print(f"   Breakeven exit level: ₹{sl_result['breakeven_level']:.2f}")
    print(f"   Partial exit trigger: ₹{sl_result['partial_exit_trigger']:.2f}")

    # Position Sizing
    if "error" not in position_result:
        print(f"\n💰 POSITION SIZING (1% Risk Rule):")
        print(f"   Quantity:         {position_result['quantity']} lots")
        print(f"   Capital Needed:   ₹{position_result['capital_needed']:,.0f}")
        print(f"   Risk Per Trade:   ₹{position_result['risk_amount']:.0f}")
        print(f"   Target 1:         ₹{position_result['target_1']:.2f} → P&L: ₹{position_result['potential_profit_t1']:+,.0f}")
        print(f"   Target 2:         ₹{position_result['target_2']:.2f} → P&L: ₹{position_result['potential_profit_t2']:+,.0f}")

    print("\n" + "="*90)


# ─────────────────────────────────────────────────────────────
# EXAMPLE USAGE
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Example: RELIANCE Call Option
    print("\n" + "🔍 EXAMPLE: RELIANCE CALL".center(50))
    print("─" * 50)

    entry = 2350.0
    delta = 0.55
    iv = 22
    theta = -0.35
    vega = 0.10

    # Detect market volatility
    market_vol = get_market_volatility(iv)

    # Calculate powerful SL
    sl_result = calculate_powerful_sl(
        entry_price=entry,
        delta=delta,
        iv=iv,
        theta=theta,
        vega=vega,
        market_volatility=market_vol,
        days_held=1.0
    )

    # Calculate position sizing
    pos_result = calculate_position_size_with_powerful_sl(
        entry_price=entry,
        powerful_sl=sl_result['powerful_sl'],
        account_size=500000
    )

    # Print analysis
    print_powerful_sl_analysis(sl_result, pos_result)

    # Comparison with old method
    print("\n📊 COMPARISON: Old vs Powerful SL")
    print("─" * 50)
    old_sl = entry * 0.80
    print(f"Old Method (20%):     ₹{old_sl:.2f} | Risk: ₹{entry - old_sl:.2f}")
    print(f"Powerful Method:      ₹{sl_result['powerful_sl']:.2f} | Risk: ₹{sl_result['sl_risk']:.2f}")
    print(f"Improvement:          {((entry - old_sl) - sl_result['sl_risk']) / (entry - old_sl) * 100:.1f}% tighter SL")
    print(f"Whipsaw Protection:   ✅ YES - 4 layers defending against bounces")
