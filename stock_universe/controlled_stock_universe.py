"""Select an explicit, validated controlled stock universe."""

from __future__ import annotations


def parse_controlled_symbols(value: str) -> list[str]:
    """Parse a reproducible comma-separated symbol source."""

    symbols = []
    seen = set()

    for raw_symbol in value.split(","):
        symbol = raw_symbol.strip().upper()
        if symbol and symbol not in seen:
            seen.add(symbol)
            symbols.append(symbol)

    return symbols


def select_controlled_universe(
    stock_candidates: list[dict],
    controlled_symbols: list[str],
    maximum_size: int,
) -> list[dict]:
    """Validate and select an explicit symbol list from stock candidates.

    The input list is the source of ordering and membership. No liquidity
    ranking or arbitrary alphabetical selection happens here.
    """

    maximum_size = int(maximum_size)
    if maximum_size < 1:
        raise ValueError("maximum_size must be at least 1")

    candidates_by_symbol = {
        str(candidate.get("tradingsymbol", "")).strip().upper(): candidate
        for candidate in stock_candidates
        if str(candidate.get("tradingsymbol", "")).strip()
    }

    requested_symbols = parse_controlled_symbols(",".join(controlled_symbols))
    unknown_symbols = [
        symbol for symbol in requested_symbols if symbol not in candidates_by_symbol
    ]

    if unknown_symbols:
        raise ValueError(
            "Controlled universe contains symbols outside the validated "
            f"NSE company-equity universe: {', '.join(unknown_symbols)}"
        )

    return [candidates_by_symbol[symbol] for symbol in requested_symbols[:maximum_size]]
