import pytest

from run_swing_trade_system import build_controlled_candidate_universe
from stock_universe.controlled_stock_universe import (
    parse_controlled_symbols,
    select_controlled_universe,
)


def test_parses_unique_symbols_in_source_order():
    assert parse_controlled_symbols(" infy, RELIANCE, infy, ,HDFCBANK ") == [
        "INFY",
        "RELIANCE",
        "HDFCBANK",
    ]


def test_selects_only_validated_symbols_in_requested_order():
    candidates = [
        {"tradingsymbol": "INFY", "instrument_token": 1},
        {"tradingsymbol": "RELIANCE", "instrument_token": 2},
    ]

    selected = select_controlled_universe(
        candidates,
        ["RELIANCE", "INFY"],
        maximum_size=1,
    )

    assert selected == [{"tradingsymbol": "RELIANCE", "instrument_token": 2}]


def test_rejects_symbols_outside_validated_universe():
    with pytest.raises(ValueError, match="outside"):
        select_controlled_universe(
            [{"tradingsymbol": "INFY"}],
            ["RELIANCE"],
            maximum_size=300,
        )
