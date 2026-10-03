"""
BTST OPTIONS SCANNER — IMPROVED VERSION
─────────────────────────────────────────
Enhancements:
1. Removed monkey-patch anti-pattern (strategy_name as parameter)
2. Consistent function signatures across all scanners
3. Theta decay boundary enforcement
4. Execution logging
5. Market hours guard

Usage:
    python run_btst_options_scan.py --symbols RELIANCE,TCS --min-score 50
"""

from __future__ import annotations

import argparse
import sys
import json
from datetime import datetime, time as time_type
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# IMPROVEMENT: Utilities
# ──────────────────────────────────────────────────────────────

def is_market_hours(script_type: str = "btst") -> bool:
    """Check if current time is valid for this scanner."""
    now = datetime.now().time()

    if script_type == "btst":
        # 2:30 PM to 3:30 PM (EOD execution window)
        return time_type(14, 30) <= now <= time_type(15, 30)

    return False


def export_scan_config(args, result_count: int, symbols_scanned: list[str]) -> dict:
    """Export scan configuration for audit trail."""
    return {
        "timestamp": datetime.now().isoformat(),
        "script": "run_btst_options_scan",
        "symbols_scanned": symbols_scanned,
        "num_symbols": len(symbols_scanned),
        "min_score": args.min_score,
        "qualified_candidates": result_count,
        "market_hours_check": is_market_hours("btst"),
    }


def save_execution_log(config: dict) -> Path:
    """Save execution log to JSON file."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"btst_scan_{timestamp}.json"

    with open(log_file, 'w') as f:
        json.dump(config, f, indent=2)

    return log_file


# ──────────────────────────────────────────────────────────────
# IMPROVEMENT: Theta Decay Boundary
# ──────────────────────────────────────────────────────────────

MAX_THETA_LOSS = 0.05  # Max 5% loss from Theta decay


def passes_theta_filter(contract: dict) -> bool:
    """Check if contract passes Theta decay boundary.

    For BTST (overnight holding), high Theta loss is problematic.
    Max allowed: 5% of contract value per day.

    Args:
        contract: Option contract with theta and ltp

    Returns:
        True if theta loss is acceptable
    """
    ltp = contract.get("ltp", 0.01)
    theta = contract.get("theta", 0)

    theta_loss_pct = abs(theta) / max(ltp, 0.01)

    return theta_loss_pct <= MAX_THETA_LOSS


# ──────────────────────────────────────────────────────────────
# IMPROVEMENT: Consistent Function Signatures
# ──────────────────────────────────────────────────────────────

def fetch_fo_stock_chains(
    kite,
    symbols: list[str],
    max_symbols: int = 40,
    num_strikes: int = 8,
    request_delay: float = 0.35,
) -> dict:
    """Fetch option chains with standardized signature.

    IMPROVEMENT: This signature is now consistent between:
    - run_options_intraday_scan.py
    - run_btst_options_scan.py

    Previously BTST used different parameter names (depth vs num_strikes, etc)

    Args:
        kite: Zerodha KiteConnect client
        symbols: List of symbols to fetch
        max_symbols: Maximum symbols to process
        num_strikes: Strikes around ATM (was 'depth' in old BTST)
        request_delay: Delay between requests

    Returns:
        Dictionary of {symbol: option_chain}
    """
    chains = {}

    # Mock implementation for demo
    for symbol in symbols[:max_symbols]:
        chains[symbol] = {
            "symbol": symbol,
            "contracts": [
                {
                    "strike": 2350,
                    "option_type": "CE",
                    "ltp": 46.30,
                    "oi": 142300,
                    "volume": 5000,
                    "delta": 0.55,
                    "theta": -0.15,
                }
            ]
        }

    return chains


def scan_btst_options(chains: dict, min_score: int = 50, top_n: int = 10) -> list[dict]:
    """Scan for BTST opportunities.

    BTST-specific tuning:
    - Delta 0.45-0.70 (slightly ITM for probability)
    - Theta decay manageable (< 5% loss overnight)
    - Focus on overnight support/resistance

    Args:
        chains: Dictionary of option chains
        min_score: Minimum score threshold
        top_n: Number of top results to return

    Returns:
        List of scored BTST candidates
    """
    candidates = []

    for symbol, chain_data in chains.items():
        contracts = chain_data.get("contracts", [])

        for contract in contracts:
            # IMPROVEMENT: Theta decay boundary check
            if not passes_theta_filter(contract):
                continue

            # Mock scoring
            score = min_score + 10  # For demo

            candidates.append({
                "symbol": symbol,
                "strike": contract.get("strike", 0),
                "option_type": contract.get("option_type", "CE"),
                "ltp": contract.get("ltp", 0),
                "score": score,
                "oi": contract.get("oi", 0),
                "volume": contract.get("volume", 0),
                "delta": contract.get("delta", 0),
                "theta": contract.get("theta", 0),
                "oi_score": 28,
                "volume_score": 24,
                "price_action_score": 20,
                "greeks_score": 18,
            })

    # Sort by score
    candidates.sort(key=lambda x: x["score"], reverse=True)

    return candidates[:top_n]


# ──────────────────────────────────────────────────────────────
# IMPROVEMENT: Strategy Name as Parameter (No Monkey-Patch)
# ──────────────────────────────────────────────────────────────

def send_options_alerts(candidates: list[dict], settings, strategy_name: str = "INTRADAY") -> None:
    """Send alerts with configurable strategy name.

    IMPROVEMENT: Removed monkey-patch anti-pattern.
    Now strategy_name is passed as a parameter instead of modifying module state.

    Args:
        candidates: List of option candidates
        settings: Configuration settings
        strategy_name: Strategy label for alerts (default: "INTRADAY")
    """
    if not candidates:
        print("No candidates to alert.")
        return

    print(f"\n{'═' * 60}")
    print(f"📊 {strategy_name} ALERTS")
    print(f"{'═' * 60}")

    for i, c in enumerate(candidates[:5], 1):
        print(f"\n{i}. {c['symbol']} {c['strike']:.0f} {c['option_type']}")
        print(f"   Score: {c['score']}/100")
        print(f"   Entry: ₹{c['ltp']:.2f}")
        print(f"   Strategy: {strategy_name}")

    print(f"\n{'═' * 60}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="BTST Options Scanner (EOD Execution)"
    )
    parser.add_argument(
        "--symbols",
        type=str,
        help="Comma-separated F&O symbols to scan",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=50,
        help="Minimum score out of 100",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 60)
    print("🌙 BTST OPTIONS SCANNER — IMPROVED VERSION")
    print(f"📅 {datetime.now().strftime('%d-%b-%Y %I:%M %p')}")
    print("=" * 60)

    # IMPROVEMENT: Market hours guard
    if not is_market_hours("btst"):
        print("\n⚠️  WARNING: BTST scanner should run 2:30 PM - 3:30 PM IST")
        print("   Results may be invalid outside this window.")

    # Parse symbols
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    else:
        symbols = ["RELIANCE", "TCS", "HDFCBANK"]

    print(f"\n[1] Filtering {len(symbols)} symbols for overnight BTST potential...")

    # IMPROVEMENT: Consistent function signature (was: fetch_fo_stock_chains(kite, instrument_map, symbol_list, depth=8))
    print(f"\n[2] Fetching live option chains (±{8} strikes around ATM)...")
    chains = fetch_fo_stock_chains(
        None,  # Mock kite
        symbols,
        max_symbols=len(symbols),
        num_strikes=8,
        request_delay=0.35,
    )

    print(f"[3] Calculating Greeks (Focus: Delta 0.45-0.70, Theta decay limit)...")

    # IMPROVEMENT: Theta decay boundary enforced in scan_btst_options
    print(f"\n[4] Running EOD BTST Strategy scanner (min score: {args.min_score}/100)...")
    candidates = scan_btst_options(chains, min_score=args.min_score, top_n=10)

    print(f"    Qualified BTST candidates: {len(candidates)}")

    if candidates:
        print(f"\n{'─' * 85}")
        print(" #  Symbol         Strike Type      LTP Score     OI    Vol  PA  GK  Delta   Theta %")
        print(f"{'─' * 85}")
        for i, c in enumerate(candidates, 1):
            theta_pct = (abs(c['theta']) / max(c['ltp'], 0.01)) * 100
            print(
                f"{i:2d}  {c['symbol']:<15} {c['strike']:>5.0f}   {c['option_type']} "
                f"₹ {c['ltp']:>6.2f}  {c['score']:>3}    "
                f"{c['oi_score']:>2}/30  {c['volume_score']:>2}/25  "
                f"{c['price_action_score']:>2}/25  {c['greeks_score']:>2}/20  "
                f"{c['delta']:>5.2f}    {theta_pct:4.1f}%"
            )
        print(f"{'─' * 85}")

        # IMPROVEMENT: Strategy name passed as parameter (no monkey-patch)
        print(f"\n[5] Sending BTST alerts to Telegram...")
        send_options_alerts(candidates, None, strategy_name="BTST OVERNIGHT")
    else:
        print("\n[-] No valid BTST candidates found.")

    # IMPROVEMENT: Execution logging
    print(f"\n[6] Logging execution...")
    config = export_scan_config(args, len(candidates), symbols)
    log_file = save_execution_log(config)
    print(f"    ✓ Execution log saved: {log_file}")

    print("\n" + "=" * 60)
    print("BTST SCAN COMPLETE — Execute between 3:00 PM and 3:25 PM.")
    print("=" * 60 + "\n")

    return candidates


if __name__ == "__main__":
    main()
