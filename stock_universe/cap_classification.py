"""Market-cap classification helpers for a controlled stock scanner.

These helpers classify a company into one of the standard buckets used by
portfolio-scale scanners:
- LARGE: large-cap equities
- MID: mid-cap equities
- SMALL: small-cap equities
- UNKNOWN: unclassified or invalid values

The classification is intentionally based on actual market-cap value, not stock
price, because price alone is not a reliable indicator of company size.
"""

from __future__ import annotations

import csv
import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

LARGE_CAP_MINIMUM = 20_000_000_000
MID_CAP_MINIMUM = 5_000_000_000
SMALL_CAP_MINIMUM = 0

CAP_SEGMENT_FILES = {
    "LARGE": "nifty100.csv",
    "MID": "nifty_midcap150.csv",
    "SMALL": "nifty_smallcap250.csv",
}
CAP_SEGMENT_PRIORITY = ("LARGE", "MID", "SMALL")
DEFAULT_CAP_SNAPSHOT_DIR = (
    Path(__file__).resolve().parents[1] / "data" / "nse_cap_segments"
)
DEFAULT_MAX_SNAPSHOT_AGE_DAYS = int(os.getenv("NSE_CAP_MAX_AGE_DAYS", "180"))


def classify_market_cap(value: Any) -> str:
    """Return a standardized cap bucket for a numeric market-cap value."""
    try:
        market_cap = float(value)
    except (TypeError, ValueError):
        return "UNKNOWN"

    if market_cap != market_cap:
        return "UNKNOWN"

    if market_cap >= LARGE_CAP_MINIMUM:
        return "LARGE"
    if market_cap >= MID_CAP_MINIMUM:
        return "MID"
    if market_cap >= SMALL_CAP_MINIMUM:
        return "SMALL"
    return "UNKNOWN"


def _normalise_symbol(value: Any) -> str:
    return str(value or "").strip().upper()


def _parse_snapshot_date(value: Any) -> date:
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "NSE cap snapshot metadata must contain snapshot_date in YYYY-MM-DD format"
        ) from exc


def load_nse_cap_snapshot(
    snapshot_dir: str | Path | None = None,
    *,
    as_of: date | None = None,
    max_age_days: int = DEFAULT_MAX_SNAPSHOT_AGE_DAYS,
) -> dict[str, str]:
    """Load the dated NSE size-segment snapshot as ``symbol -> bucket``.

    Duplicate symbols are resolved deterministically using LARGE, then MID,
    then SMALL precedence. A snapshot older than ``max_age_days`` is rejected.
    """
    directory = Path(snapshot_dir) if snapshot_dir else DEFAULT_CAP_SNAPSHOT_DIR
    metadata_path = directory / "metadata.json"

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"Unable to read NSE cap snapshot metadata: {metadata_path}"
        ) from exc

    snapshot_date = _parse_snapshot_date(metadata.get("snapshot_date"))
    reference_date = as_of or date.today()
    max_age_days = int(max_age_days)
    age_days = (reference_date - snapshot_date).days
    if age_days < 0 or age_days > max_age_days:
        raise ValueError(
            f"NSE cap snapshot is stale: snapshot_date={snapshot_date.isoformat()}, "
            f"as_of={reference_date.isoformat()}, max_age_days={max_age_days}"
        )

    segments: dict[str, str] = {}
    for bucket in CAP_SEGMENT_PRIORITY:
        csv_path = directory / CAP_SEGMENT_FILES[bucket]
        try:
            with csv_path.open(newline="", encoding="utf-8") as handle:
                rows = csv.DictReader(handle)
                if not rows.fieldnames or not (
                    "symbol" in rows.fieldnames or "tradingsymbol" in rows.fieldnames
                ):
                    raise ValueError(
                        f"{csv_path.name} must contain a symbol or tradingsymbol column"
                    )
                symbol_column = (
                    "symbol" if "symbol" in rows.fieldnames else "tradingsymbol"
                )
                for row in rows:
                    symbol = _normalise_symbol(row.get(symbol_column))
                    if symbol and symbol not in segments:
                        segments[symbol] = bucket
        except OSError as exc:
            raise ValueError(
                f"Unable to read NSE cap segment file: {csv_path}"
            ) from exc

    return segments


def classify_symbol_by_cap_segment(
    symbol: Any,
    snapshot: dict[str, str] | None = None,
) -> str:
    """Return the NSE snapshot bucket for a symbol, or UNKNOWN."""
    normalized_symbol = _normalise_symbol(symbol)
    if not normalized_symbol:
        return "UNKNOWN"
    segment_snapshot = snapshot if snapshot is not None else load_nse_cap_snapshot()
    return segment_snapshot.get(normalized_symbol, "UNKNOWN")


def group_by_cap_bucket(
    stock_candidates: list[dict],
    market_cap_by_symbol: dict[str, Any],
) -> dict[str, list[dict]]:
    """Group candidates by large/mid/small cap while preserving list order."""
    grouped: dict[str, list[dict]] = {
        "LARGE": [],
        "MID": [],
        "SMALL": [],
        "UNKNOWN": [],
    }

    for candidate in stock_candidates:
        symbol = str(candidate.get("tradingsymbol", "")).strip().upper()
        if not symbol:
            continue

        bucket = classify_market_cap(market_cap_by_symbol.get(symbol))
        grouped.setdefault(bucket, []).append(candidate)

    return grouped
