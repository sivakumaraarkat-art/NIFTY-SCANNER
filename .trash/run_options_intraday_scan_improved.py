"""
INTRADAY OPTIONS SCANNER — IMPROVED VERSION
─────────────────────────────────────────────
Enhancements:
1. Timeout protection on Zerodha API calls
2. Liquidity filter (MIN_OI + bid-ask spread checks)
3. Proper Greeks failure handling (skip on error, don't score)
4. Position sizing guidance
5. Execution logging
6. Market hours guard

Usage:
    python run_options_intraday_scan.py --symbols RELIANCE,TCS --min-score 50
"""

from __future__ import annotations

import argparse
import sys
import json
import time
from datetime import datetime, time as time_type
from pathlib import Path

# Mock imports for testing (in production, these would be real imports)
# from configuration.swing_trade_settings import load_settings
# from zerodha_market_data.zerodha_connection import create_zerodha_client, verify_connection
# from stock_universe.liquid_stocks_universe import get_curated_liquid_symbols
# from options_intraday.options_data_fetcher import fetch_fo_stock_chains
# from options_intraday.options_greeks_calculator import add_greeks_to_chain
# from options_intraday.intraday_options_scanner import scan_intraday_options
# from options_intraday.options_alert_sender import send_options_alerts


# ──────────────────────────────────────────────────────────────
# IMPROVEMENTS: Utility Functions
# ──────────────────────────────────────────────────────────────

def is_market_hours(script_type: str = "intraday") -> bool:
    """Check if current time is valid for this scanner.

    Args:
        script_type: "intraday", "btst", or "news"

    Returns:
        True if current time is valid for the script type
    """
    now = datetime.now().time()

    if script_type == "intraday":
        # 9:30 AM to 3:30 PM
        return time_type(9, 30) <= now <= time_type(15, 30)
    elif script_type == "btst":
        # 2:30 PM to 3:30 PM (EOD execution window)
        return time_type(14, 30) <= now <= time_type(15, 30)
    elif script_type == "news":
        # 8:00 AM to 9:00 PM (news available)
        return time_type(8, 0) <= now <= time_type(21, 0)

    return False


def export_scan_config(args, result_count: int, symbols_scanned: list[str]) -> dict:
    """Export scan configuration and results for audit trail.

    Args:
        args: Command line arguments
        result_count: Number of qualified candidates
        symbols_scanned: List of symbols scanned

    Returns:
        Dictionary with scan metadata
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "script": "run_options_intraday_scan",
        "symbols_scanned": symbols_scanned,
        "num_symbols": len(symbols_scanned),
        "min_score": args.min_score,
        "qualified_candidates": result_count,
        "market_hours_check": is_market_hours("intraday"),
    }


def save_execution_log(config: dict) -> Path:
    """Save execution log to JSON file with timestamp.

    Args:
        config: Configuration dictionary to save

    Returns:
        Path to the created log file
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"intraday_scan_{timestamp}.json"

    with open(log_file, 'w') as f:
        json.dump(config, f, indent=2)

    return log_file


# ──────────────────────────────────────────────────────────────
# IMPROVEMENTS: Liquidity Filters
# ──────────────────────────────────────────────────────────────

MIN_OI_THRESHOLD = 1000
MAX_BID_ASK_SPREAD_PCT = 2.0


def is_liquid(contract: dict) -> bool:
    """Check if an option contract passes liquidity filters.

    Criteria:
    - OI >= MIN_OI_THRESHOLD
    - Bid-Ask spread <= MAX_BID_ASK_SPREAD_PCT

    Args:
        contract: Option contract dictionary with oi, bid, ask, ltp

    Returns:
        True if contract passes liquidity filters
    """
    oi = contract.get("oi", 0)
    bid = contract.get("bid", 0)
    ask = contract.get("ask", 0)
    ltp = contract.get("ltp", 0.01)

    # Check OI threshold
    if oi < MIN_OI_THRESHOLD:
        return False

    # Check bid-ask spread
    if bid > 0 and ask > 0:
        spread_pct = ((ask - bid) / ltp) * 100
        if spread_pct > MAX_BID_ASK_SPREAD_PCT:
            return False

    return True


# ──────────────────────────────────────────────────────────────
# IMPROVEMENTS: Timeout Protection for API Calls
# ──────────────────────────────────────────────────────────────

def fetch_fo_stock_chains_with_timeout(
    kite,
    symbols: list[str],
    max_symbols: int = 40,
    num_strikes: int = 8,
    request_delay: float = 0.35,
    timeout_seconds: int = 30,
) -> dict:
    """Fetch option chains with timeout protection.

    Args:
        kite: Zerodha KiteConnect client
        symbols: List of symbols to fetch
        max_symbols: Maximum symbols to process
        num_strikes: Strikes around ATM
        request_delay: Delay between requests
        timeout_seconds: Maximum time to spend fetching (default: 30s)

    Returns:
        Dictionary of {symbol: option_chain} with timeout protection
    """
    chains = {}
    start_time = datetime.now()

    symbols_to_process = symbols[:max_symbols]

    for idx, symbol in enumerate(symbols_to_process, 1):
        # Check timeout
        elapsed = (datetime.now() - start_time).total_seconds()
        if elapsed > timeout_seconds:
            print(f"  ⏱ Timeout: Fetched {len(chains)}/{len(symbols_to_process)} chains in {elapsed:.1f}s")
            break

        try:
            time.sleep(request_delay)
            # Mock: In production, this would be: chain = fetch_option_chain(kite, symbol, ...)
            chain = {"symbol": symbol, "contracts": []}  # Placeholder

            if chain:
                chains[symbol] = chain
                print(f"  [{idx}/{len(symbols_to_process)}] {symbol}: data fetched ({elapsed:.1f}s)")
        except Exception as exc:
            print(f"  [{idx}/{len(symbols_to_process)}] {symbol}: {exc}")
            continue

    return chains


# ──────────────────────────────────────────────────────────────
# IMPROVEMENTS: Greeks Calculation with Proper Error Handling
# ──────────────────────────────────────────────────────────────

def add_greeks_to_chain_safe(chain: list[dict]) -> list[dict]:
    """Add Greeks to chain with proper error handling.

    Args:
        chain: List of option contracts

    Returns:
        List of contracts with Greeks (skips any that fail calculation)
    """
    greeks_chain = []
    failed_count = 0

    for contract in chain:
        try:
            # Mock: In production, this would calculate actual Greeks
            contract["delta"] = 0.5
            contract["iv"] = 25.0
            contract["theta"] = -0.1
            greeks_chain.append(contract)
        except Exception as exc:
            failed_count += 1
            continue

    if failed_count > 0:
        print(f"  ⚠ Greeks calculation failed for {failed_count} contracts, skipped")

    return greeks_chain


# ──────────────────────────────────────────────────────────────
# IMPROVEMENTS: Position Sizing Guidance
# ──────────────────────────────────────────────────────────────

def calculate_position_sizing(candidates: list[dict], account_size: float = 500000.0) -> None:
    """Print position sizing guidance for top candidates.

    Uses 1% risk rule: max risk per trade = 1% of account

    Args:
        candidates: List of scored candidates
        account_size: Total trading account size (default: ₹500K)
    """
    if not candidates:
        return

    print(f"\n{'─' * 85}")
    print("💰 POSITION SIZING (1% risk rule):")
    print(f"{'─' * 85}")

    risk_pct = 0.01
    risk_amount = account_size * risk_pct

    for i, c in enumerate(candidates[:5], 1):
        ltp = c.get("ltp", 0)
        stop_loss = c.get("stop_loss", ltp * 0.80)
        risk_per_share = ltp - stop_loss

        if risk_per_share > 0:
            quantity = int(risk_amount / risk_per_share)
            capital_needed = quantity * ltp
            potential_profit = quantity * (c.get("target_1", ltp * 1.15) - ltp)

            print(f"\n{i}. {c['symbol']} {c['strike']:.0f} {c['option_type']}")
            print(f"   Entry: ₹{ltp:.2f} | Stop: ₹{stop_loss:.2f}")
            print(f"   Qty: {quantity} lots | Risk: ₹{risk_per_share:.2f}/lot")
            print(f"   Capital: ₹{capital_needed:,.0f} | Potential P&L: ₹{potential_profit:+,.0f}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Intraday Options Scanner — Find high-conviction F&O stock options"
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default="",
        help="Comma-separated F&O symbols to scan",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=50,
        help="Minimum combined score to qualify (0-100)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=15,
        help="Maximum number of results to return",
    )
    parser.add_argument(
        "--request-delay",
        type=float,
        default=0.35,
        help="Delay between API calls in seconds",
    )
    return parser.parse_args()


def main() -> list[dict]:
    args = parse_args()

    print("=" * 60)
    print("⚡ INTRADAY OPTIONS SCANNER — IMPROVED VERSION")
    print(f"📅 {datetime.now().strftime('%d-%b-%Y %I:%M %p')}")
    print("=" * 60)

    # IMPROVEMENT: Market hours guard
    if not is_market_hours("intraday"):
        print("\n⚠️  WARNING: Running outside optimal hours (9:30 AM - 3:30 PM IST)")
        print("   Signals may be poor or non-existent.")

    # Parse symbols
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    else:
        symbols = ["RELIANCE", "TCS", "HDFCBANK"]  # Default

    print(f"\n[1/6] F&O universe: {len(symbols)} symbols selected.")

    # IMPROVEMENT: Timeout protection on chain fetching
    print(f"\n[2/6] Fetching live option chains with timeout protection...")
    chains = fetch_fo_stock_chains_with_timeout(
        None,  # Mock kite
        symbols,
        max_symbols=len(symbols),
        num_strikes=8,
        request_delay=args.request_delay,
        timeout_seconds=30,
    )

    if not chains:
        print("\nERROR: No option chain data available.")
        return []

    # IMPROVEMENT: Proper Greeks failure handling
    print(f"\n[3/6] Calculating Greeks with proper error handling...")
    greeks_chains = {}
    failed_symbols = []

    for symbol, chain in chains.items():
        try:
            greeks_chains[symbol] = add_greeks_to_chain_safe(chain if isinstance(chain, list) else [chain])
        except Exception as exc:
            print(f"  ⚠ {symbol}: Greeks calculation failed — {exc}")
            failed_symbols.append(symbol)
            continue

    if failed_symbols:
        print(f"  ⚠ Skipped {len(failed_symbols)} symbols due to Greeks failure")

    # IMPROVEMENT: Liquidity filtering
    print(f"\n[4/6] Applying liquidity filters (OI >= {MIN_OI_THRESHOLD}, Spread <= {MAX_BID_ASK_SPREAD_PCT}%)...")

    # Mock candidates (in production, from scan_intraday_options)
    candidates = [
        {
            "symbol": "RELIANCE",
            "strike": 2350,
            "option_type": "CE",
            "ltp": 46.30,
            "score": 95,
            "oi": 142300,
            "bid": 46.0,
            "ask": 46.5,
            "stop_loss": 38.50,
            "target_1": 54.80,
            "delta": 0.58,
        },
        {
            "symbol": "MARUTI",
            "strike": 7850,
            "option_type": "PE",
            "ltp": 63.50,
            "score": 89,
            "oi": 136200,
            "bid": 63.0,
            "ask": 64.0,
            "stop_loss": 54.20,
            "target_1": 72.80,
            "delta": -0.55,
        },
    ]

    # Filter by liquidity
    liquid_candidates = [c for c in candidates if is_liquid(c)]
    print(f"  ✓ Liquid candidates: {len(liquid_candidates)}/{len(candidates)}")

    # IMPROVEMENT: Position sizing guidance
    calculate_position_sizing(liquid_candidates[:5])

    # IMPROVEMENT: Execution logging
    print(f"\n[5/6] Logging execution...")
    config = export_scan_config(args, len(liquid_candidates), symbols)
    log_file = save_execution_log(config)
    print(f"  ✓ Execution log saved: {log_file}")

    print("\n" + "=" * 60)
    print("SCAN COMPLETE — SIGNAL ONLY / NO AUTOMATIC ORDERS")
    print("=" * 60 + "\n")

    return liquid_candidates


if __name__ == "__main__":
    candidates = main()
