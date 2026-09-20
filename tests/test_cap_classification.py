import json
from datetime import date

import pytest

from stock_universe.cap_classification import (
    classify_market_cap,
    classify_symbol_by_cap_segment,
    group_by_cap_bucket,
    load_nse_cap_snapshot,
)


def test_classifies_large_mid_and_small_cap_by_market_cap_thresholds():
    assert classify_market_cap(200_000_000_000) == "LARGE"
    assert classify_market_cap(15_000_000_000) == "MID"
    assert classify_market_cap(2_000_000_000) == "SMALL"


def test_unknown_market_cap_is_handled_safely():
    assert classify_market_cap(None) == "UNKNOWN"
    assert classify_market_cap(float("nan")) == "UNKNOWN"


def test_group_by_cap_bucket_preserves_order_and_filters_unknowns():
    candidates = [
        {"tradingsymbol": "INFY", "instrument_token": 1},
        {"tradingsymbol": "M&M", "instrument_token": 2},
        {"tradingsymbol": "ABC", "instrument_token": 3},
    ]
    market_cap_by_symbol = {
        "INFY": 200_000_000_000,
        "M&M": 7_500_000_000,
        "ABC": 500_000_000,
    }

    grouped = group_by_cap_bucket(candidates, market_cap_by_symbol)

    assert grouped["LARGE"] == [{"tradingsymbol": "INFY", "instrument_token": 1}]
    assert grouped["MID"] == [{"tradingsymbol": "M&M", "instrument_token": 2}]
    assert grouped["SMALL"] == [{"tradingsymbol": "ABC", "instrument_token": 3}]
    assert grouped["UNKNOWN"] == []


def test_nse_snapshot_classifies_segments_and_unknowns(tmp_path):
    (tmp_path / "nifty100.csv").write_text("symbol\nINFY\n", encoding="utf-8")
    (tmp_path / "nifty_midcap150.csv").write_text("symbol\nDIXON\n", encoding="utf-8")
    (tmp_path / "nifty_smallcap250.csv").write_text(
        "symbol\nABCAPITAL\n", encoding="utf-8"
    )
    (tmp_path / "metadata.json").write_text(
        json.dumps({"snapshot_date": "2026-09-15", "source": "NSE"}),
        encoding="utf-8",
    )

    snapshot = load_nse_cap_snapshot(tmp_path, as_of=date(2026, 9, 15))

    assert classify_symbol_by_cap_segment("infy", snapshot) == "LARGE"
    assert classify_symbol_by_cap_segment("DIXON", snapshot) == "MID"
    assert classify_symbol_by_cap_segment("ABCAPITAL", snapshot) == "SMALL"
    assert classify_symbol_by_cap_segment("NOT_IN_SNAPSHOT", snapshot) == "UNKNOWN"


def test_nse_snapshot_duplicate_precedence_is_deterministic(tmp_path):
    (tmp_path / "nifty100.csv").write_text("symbol\nDUPLICATE\n", encoding="utf-8")
    (tmp_path / "nifty_midcap150.csv").write_text(
        "symbol\nDUPLICATE\n", encoding="utf-8"
    )
    (tmp_path / "nifty_smallcap250.csv").write_text(
        "symbol\nDUPLICATE\n", encoding="utf-8"
    )
    (tmp_path / "metadata.json").write_text(
        json.dumps({"snapshot_date": "2026-09-15"}), encoding="utf-8"
    )

    snapshot = load_nse_cap_snapshot(tmp_path, as_of=date(2026, 9, 15))

    assert snapshot["DUPLICATE"] == "LARGE"


def test_nse_snapshot_rejects_stale_metadata(tmp_path):
    for filename in ("nifty100.csv", "nifty_midcap150.csv", "nifty_smallcap250.csv"):
        (tmp_path / filename).write_text("symbol\nINFY\n", encoding="utf-8")
    (tmp_path / "metadata.json").write_text(
        json.dumps({"snapshot_date": "2026-01-01"}), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="stale"):
        load_nse_cap_snapshot(tmp_path, as_of=date(2026, 9, 15))
