from src.scanners.options_data_provider import calculate_powerful_sl_engine
from src.scanners.run_options_intraday_scan_powerful_sl import (
    print_powerful_sl_results,
    get_stock_sector,
)


def test_powerful_sl_engine_buffer_range():
    """Verify intraday SL buffer allows up to 13.5% instead of being artificially choked at 10%."""
    # Volatile option with high delta and vega
    res = calculate_powerful_sl_engine(
        entry_price=100.0,
        delta=0.55,
        iv=45.0,
        theta=-2.0,
        vega=3.5,
        is_btst=False,
        days_held=0.25,
    )
    assert 8.0 <= res["sl_risk_pct"] <= 13.5
    assert res["sl_risk"] > 10.0  # Demonstrates it can exceed the old rigid 10.0 limit
    assert res["powerful_sl"] == round(100.0 - res["sl_risk"], 2)


def test_stopped_out_contract_is_banned():
    """Verify that a contract that already took a stop loss today is 100% blocked from repeat loss."""
    candidates = [
        {
            "symbol": "HDFCLIFE",
            "option_symbol": "HDFCLIFE26DEC605CE",
            "option_type": "CE",
            "score": 98,
            "ltp": 24.0,
            "sl_risk": 3.0,
            "powerful_sl": 21.0,
            "t1": 28.0,
            "t2": 31.0,
            "lot_size": 1100,
            "recommended_qty": 1,
            "sentiment_catalyst": "BULLISH",
        },
        {
            "symbol": "DABUR",
            "option_symbol": "DABUR26DEC415CE",
            "option_type": "CE",
            "score": 98,
            "ltp": 16.0,
            "sl_risk": 2.0,
            "powerful_sl": 14.0,
            "t1": 18.7,
            "t2": 20.7,
            "lot_size": 1250,
            "recommended_qty": 1,
            "sentiment_catalyst": "BULLISH",
        },
    ]

    selected = print_powerful_sl_results(
        candidates,
        max_candidates=2,
        loss_options=["HDFCLIFE26DEC605CE"],
        loss_underlying=["HDFCLIFE"],
    )

    selected_syms = [c["option_symbol"] for c in selected]
    assert "HDFCLIFE26DEC605CE" not in selected_syms
    assert "DABUR26DEC415CE" in selected_syms


def test_stopped_out_underlying_requires_elite_conviction():
    """Verify underlying stock that took a loss earlier requires Score >= 95 for re-entry."""
    candidates = [
        {
            "symbol": "HYUNDAI",
            "option_symbol": "HYUNDAI26DEC2080PE",
            "option_type": "PE",
            "score": 88,  # Below 95
            "ltp": 85.0,
            "sl_risk": 10.0,
            "powerful_sl": 75.0,
            "t1": 98.5,
            "t2": 108.5,
            "lot_size": 275,
            "recommended_qty": 1,
            "sentiment_catalyst": "BEARISH",
        },
        {
            "symbol": "OFSS",
            "option_symbol": "OFSS26DEC9500PE",
            "option_type": "PE",
            "score": 92,
            "ltp": 420.0,
            "sl_risk": 50.0,
            "powerful_sl": 370.0,
            "t1": 487.5,
            "t2": 537.5,
            "lot_size": 50,
            "recommended_qty": 1,
            "sentiment_catalyst": "BEARISH",
        },
    ]

    selected = print_powerful_sl_results(
        candidates,
        max_candidates=2,
        loss_underlying=["HYUNDAI"],
    )
    selected_underlying = [c["symbol"] for c in selected]
    assert "HYUNDAI" not in selected_underlying
    assert "OFSS" in selected_underlying


def test_sector_mapping():
    """Verify sector lookup identifies common F&O sectors correctly."""
    assert get_stock_sector("HDFCLIFE") == "LIFE_INSURANCE"
    assert get_stock_sector("ICICILIFE") == "LIFE_INSURANCE"
    assert get_stock_sector("DABUR") == "FMCG"
    assert get_stock_sector("OFSS") == "IT"
    assert get_stock_sector("UNKNOWNXYZ") is None


if __name__ == "__main__":
    test_powerful_sl_engine_buffer_range()
    test_stopped_out_contract_is_banned()
    test_stopped_out_underlying_requires_elite_conviction()
    test_sector_mapping()
    print("\n✅ ALL 4 TESTS PASSED CLEANLY!")

