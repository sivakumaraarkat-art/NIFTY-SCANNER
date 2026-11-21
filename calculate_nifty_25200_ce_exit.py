"""
calculate_nifty_25200_ce_exit.py
Calculates exact Black-Scholes Greeks, spot sensitivity, and exit plan
for user's open position: NIFTY26N0925200CE (1 Lot = 65 Qty @ ₹90.00).
Pure Python implementation (no scipy dependency).
"""

import math
import sys

# Windows UTF-8 fix
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

def norm_cdf(x):
    """Standard normal cumulative distribution function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def norm_pdf(x):
    """Standard normal probability density function."""
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)

def black_scholes_call(S, K, T, r, sigma):
    """S: Spot, K: Strike, T: Time in years, r: Risk-free rate, sigma: Volatility"""
    if T <= 0:
        return max(0.0, S - K), 1.0 if S > K else 0.0, 0.0, 0.0

    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    price = S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
    delta = norm_cdf(d1)
    gamma = norm_pdf(d1) / (S * sigma * math.sqrt(T))
    theta = -(S * norm_pdf(d1) * sigma) / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * norm_cdf(d2)
    theta_day = theta / 365.0

    return price, delta, gamma, theta_day

# Inputs for NIFTY 25200 CE
S_current = 25030.35
K = 25200.0
r = 0.065
# Time to expiry: ~1.25 calendar days (Muhurat Sunday + Monday expiry day)
T = 1.25 / 365.0

# Current market price is 92.60. Let's find implied volatility (IV)
def find_iv(target_price, S, K, T, r):
    low_iv, high_iv = 0.01, 1.50
    for _ in range(60):
        mid = (low_iv + high_iv) / 2.0
        p, _, _, _ = black_scholes_call(S, K, T, r, mid)
        if abs(p - target_price) < 0.01:
            return mid
        if p < target_price:
            low_iv = mid
        else:
            high_iv = mid
    return mid

iv = find_iv(92.60, S_current, K, T, r)
price, delta, gamma, theta_day = black_scholes_call(S_current, K, T, r, iv)

print("=" * 85)
print("🎯 NIFTY 25,200 CE (2026-11-09 Expiry) - OPTION GREEKS & PRICING DYNAMICS")
print("=" * 85)
print(f"  • Spot Price (NIFTY):   {S_current:,.2f}")
print(f"  • Option Strike:        {K:,.0f} CE  (OTM by {K - S_current:.1f} pts)")
print(f"  • User's Position:      65 Qty (1 Lot) @ Avg ₹90.00 (Invested: ₹5,850.00)")
print(f"  • Current LTP:          ₹{price:.2f} (Current Value: ₹{price*65:,.2f} | Unrealized: +₹{(price-90)*65:.2f})")
print(f"  • Implied Vol (IV):     {iv*100:.2f}%")
print(f"  • Delta:                {delta:.3f}  (Gain ~₹{delta*10:.2f}/share for every +10 pt Nifty move)")
print(f"  • Gamma:                {gamma:.5f}  (Delta accelerates as spot nears 25,200)")
print(f"  • Theta (1 Day Decay):  ₹{theta_day:.2f} / share (-₹{abs(theta_day)*65:.2f} per lot per day)")
print("=" * 85)

# Spot sensitivity table during Muhurat session
print("\n📊 EXPECTED 25,200 CE PRICE AT VARIOUS MUHURAT SPOT OPEN LEVELS:")
print("-" * 85)
print(f"{'NIFTY SPOT':<12} | {'SPOT CHG':<10} | {'THEOR. CE':<11} | {'1 LOT VALUE':<13} | {'NET P&L (₹)':<13} | {'ROI %':<8}")
print("-" * 85)

scenarios = [-80, -50, -30, 0, 30, 50, 70, 90, 110, 140, 170, 200]
for pts in scenarios:
    spot_sim = S_current + pts
    p_sim, d_sim, _, _ = black_scholes_call(spot_sim, K, T * 0.95, r, iv)
    lot_val = p_sim * 65
    net_pnl = (p_sim - 90.0) * 65
    roi = ((p_sim - 90.0) / 90.0) * 100
    tag = ""
    if pts == 0:
        tag = "<- Friday Close"
    elif pts == 70:
        tag = "<- Likely Muhurat Open (+0.28%)"
    elif pts == 110:
        tag = "<- Moderate Gap-Up (+0.44%)"
    elif pts == 140:
        tag = "<- Strong Gap-Up (+0.56%)"
    elif pts == 170:
        tag = "<- Strike Reached (25,200 ATM)"

    print(f"{spot_sim:<12,.2f} | {pts:>+6} pts   | ₹{p_sim:>8.2f}    | ₹{lot_val:>10,.2f}  | {net_pnl:>+10,.2f}    | {roi:>+6.1f}% {tag}")

print("=" * 85)
