"""
test_hero_zero_upgrade.py
═════════════════════════════════════════════════════════════════
Unit tests for Hero-Zero Quality Strike scanners & 3:50 PM Summary
"""

from datetime import datetime, date
from src.scanners.sensex_hero_zero_expiry_scanner import (
    resolve_sensex_hero_zero_candidates,
    is_sensex_expiry_day,
)
from src.scanners.nifty_hero_zero_expiry_scanner import (
    resolve_nifty_hero_zero_candidates,
    is_nifty_expiry_day,
)
from src.scanners.hero_zero_350pm_summary import (
    evaluate_candidate_performance,
)


def test_sensex_hero_zero_quality_strike_structure():
    """Verify Sensex candidate resolution provides single best candidate by default and both when requested."""
    # Test single best candidate (default mode)
    best_candidates = resolve_sensex_hero_zero_candidates(kite=None, single_best=True)
    assert len(best_candidates) == 1, f"Expected 1 best candidate, got {len(best_candidates)}"
    best = best_candidates[0]
    assert best["symbol"] == "SENSEX"
    assert best["entry_price"] > 0
    assert best["t1"] == round(best["entry_price"] * 2.0, 2), "Target 1 must be 2x (+100%)"
    assert best["t2"] == round(best["entry_price"] * 4.0, 2), "Target 2 must be 4x (+300%)"
    assert best["sl"] == round(best["entry_price"] * 0.50, 2), "Stop Loss must be 50% cap"
    assert best["lot_size"] == 20, "Sensex lot size must be 20"
    assert best["total_shares"] == best["recommended_qty"] * best["lot_size"]

    # Test strangle mode (both CE and PE)
    candidates = resolve_sensex_hero_zero_candidates(kite=None, single_best=False)
    assert len(candidates) == 2, f"Expected 2 candidates, got {len(candidates)}"

    ce = next((c for c in candidates if c["option_type"] == "CE"), None)
    pe = next((c for c in candidates if c["option_type"] == "PE"), None)

    assert ce is not None, "CE candidate missing"
    assert pe is not None, "PE candidate missing"

    for c in [ce, pe]:
        assert c["symbol"] == "SENSEX"
        assert c["entry_price"] > 0
        assert c["t1"] == round(c["entry_price"] * 2.0, 2), "Target 1 must be 2x (+100%)"
        assert c["t2"] == round(c["entry_price"] * 4.0, 2), "Target 2 must be 4x (+300%)"
        assert c["sl"] == round(c["entry_price"] * 0.50, 2), "Stop Loss must be 50% cap"
        assert c["lot_size"] == 20, "Sensex lot size must be 20"
        assert c["total_shares"] == c["recommended_qty"] * c["lot_size"]


def test_nifty_hero_zero_quality_strike_structure():
    """Verify Nifty candidate resolution provides single best candidate by default and both when requested."""
    # Test single best candidate (default mode)
    best_candidates = resolve_nifty_hero_zero_candidates(kite=None, single_best=True)
    assert len(best_candidates) == 1, f"Expected 1 best candidate, got {len(best_candidates)}"
    best = best_candidates[0]
    assert best["symbol"] == "NIFTY"
    assert best["entry_price"] > 0
    assert best["t1"] == round(best["entry_price"] * 2.0, 2), "Target 1 must be 2x (+100%)"
    assert best["t2"] == round(best["entry_price"] * 4.0, 2), "Target 2 must be 4x (+300%)"
    assert best["sl"] == round(best["entry_price"] * 0.50, 2), "Stop Loss must be 50% cap"
    assert best["lot_size"] == 65, "Nifty lot size must be 65"
    assert best["total_shares"] == best["recommended_qty"] * best["lot_size"]

    # Test strangle mode (both CE and PE)
    candidates = resolve_nifty_hero_zero_candidates(kite=None, single_best=False)
    assert len(candidates) == 2, f"Expected 2 candidates, got {len(candidates)}"

    ce = next((c for c in candidates if c["option_type"] == "CE"), None)
    pe = next((c for c in candidates if c["option_type"] == "PE"), None)

    assert ce is not None, "CE candidate missing"
    assert pe is not None, "PE candidate missing"

    for c in [ce, pe]:
        assert c["symbol"] == "NIFTY"
        assert c["entry_price"] > 0
        assert c["t1"] == round(c["entry_price"] * 2.0, 2), "Target 1 must be 2x (+100%)"
        assert c["t2"] == round(c["entry_price"] * 4.0, 2), "Target 2 must be 4x (+300%)"
        assert c["sl"] == round(c["entry_price"] * 0.50, 2), "Stop Loss must be 50% cap"
        assert c["lot_size"] == 65, "Nifty lot size must be 65"
        assert c["total_shares"] == c["recommended_qty"] * c["lot_size"]


def test_hero_zero_evaluation_target_hit():
    """Test 3:50 PM evaluation logic when Target 1 and Target 2 are hit."""
    candidate = {
        "symbol": "SENSEX",
        "option_symbol": "SENSEX26O2273400CE",
        "strike": 73400.0,
        "option_type": "CE",
        "entry_price": 30.0,
        "t1": 60.0,
        "t2": 120.0,
        "sl": 15.0,
        "lot_size": 20,
        "recommended_qty": 2,
    }

    # Mock candle data: peak reached 130 (T2 hit)
    class MockKite:
        def historical_data(self, token, from_dt, to_dt, interval):
            return [
                {"date": datetime(2026, 10, 22, 15, 0), "open": 30.0, "high": 65.0, "low": 28.0, "close": 55.0},
                {"date": datetime(2026, 10, 22, 15, 20), "open": 70.0, "high": 130.0, "low": 50.0, "close": 110.0},
                {"date": datetime(2026, 10, 22, 15, 29), "open": 10.0, "high": 12.0, "low": 0.05, "close": 0.05},
            ]

    instruments = [{"tradingsymbol": "SENSEX26O2273400CE", "instrument_token": 123456}]
    ev = evaluate_candidate_performance(candidate, MockKite(), datetime.now(), instruments)

    assert ev["t1_hit"] is True
    assert ev["t2_hit"] is True
    assert "MULTIBAGGER" in ev["outcome"]
    assert ev["peak_high"] == 130.0
    assert ev["pnl"] > 0, "Trade must be profitable when T1 and T2 hit"


def test_hero_zero_evaluation_stop_loss():
    """Test 3:50 PM evaluation logic when Stop Loss is hit."""
    candidate = {
        "symbol": "SENSEX",
        "option_symbol": "SENSEX26O2273000PE",
        "strike": 73000.0,
        "option_type": "PE",
        "entry_price": 25.0,
        "t1": 50.0,
        "t2": 100.0,
        "sl": 12.5,
        "lot_size": 20,
        "recommended_qty": 2,
    }

    class MockKiteSL:
        def historical_data(self, token, from_dt, to_dt, interval):
            return [
                {"date": datetime(2026, 10, 22, 15, 0), "open": 25.0, "high": 28.0, "low": 10.0, "close": 11.0},
            ]

    instruments = [{"tradingsymbol": "SENSEX26O2273000PE", "instrument_token": 123457}]
    ev = evaluate_candidate_performance(candidate, MockKiteSL(), datetime.now(), instruments)

    assert ev["t1_hit"] is False
    assert ev["sl_hit"] is True
    assert "STOP LOSS" in ev["outcome"]
    assert ev["pnl"] < 0, "Trade must be capped at 50% loss"
    assert ev["pnl"] == -(25.0 - 12.5) * 40  # 40 qty * 12.5 risk = -500


def test_hero_zero_chronological_sl_before_target():
    """Verify that if Stop Loss is hit first, subsequent price rises cannot trigger Target 1."""
    candidate = {
        "symbol": "SENSEX",
        "option_symbol": "SENSEX26O2273000PE",
        "strike": 73000.0,
        "option_type": "PE",
        "entry_price": 20.0,
        "t1": 40.0,
        "t2": 80.0,
        "sl": 10.0,
        "lot_size": 20,
        "recommended_qty": 2,
    }

    class MockKiteSeq:
        def historical_data(self, token, from_dt, to_dt, interval):
            return [
                # Candle 1: dips to 8.0 (SL 10.0 pierced!)
                {"date": datetime(2026, 10, 22, 15, 10), "open": 20.0, "high": 22.0, "low": 8.0, "close": 9.0},
                # Candle 2: subsequent rally to 45.0 (T1) after already being stopped out
                {"date": datetime(2026, 10, 22, 15, 20), "open": 15.0, "high": 45.0, "low": 14.0, "close": 42.0},
            ]

    instruments = [{"tradingsymbol": "SENSEX26O2273000PE", "instrument_token": 999111}]
    ev = evaluate_candidate_performance(candidate, MockKiteSeq(), datetime(2026, 10, 22, 15, 5), instruments)

    assert ev["sl_hit"] is True
    assert ev["t1_hit"] is False, "Must NOT trigger T1 if trade was already stopped out"
    assert "STOP LOSS" in ev["outcome"]
    assert ev["pnl"] == -(20.0 - 10.0) * 40


def test_hero_zero_t1_hit_runner_trailed_to_cost():
    """Verify that when T1 is hit, Lot 1 books +100% and Lot 2 trails to cost (breakeven)."""
    candidate = {
        "symbol": "NIFTY",
        "option_symbol": "NIFTY26OCT22800CE",
        "strike": 22800.0,
        "option_type": "CE",
        "entry_price": 20.0,
        "t1": 40.0,
        "t2": 80.0,
        "sl": 10.0,
        "lot_size": 65,
        "recommended_qty": 2,
    }

    class MockKiteRunner:
        def historical_data(self, token, from_dt, to_dt, interval):
            return [
                # Candle 1: surges to 45.0 (T1 hit!)
                {"date": datetime(2026, 10, 27, 15, 12), "open": 20.0, "high": 45.0, "low": 19.0, "close": 42.0},
                # Candle 2: retraces and drops below entry (trails to breakeven)
                {"date": datetime(2026, 10, 27, 15, 22), "open": 35.0, "high": 36.0, "low": 18.0, "close": 19.0},
            ]

    instruments = [{"tradingsymbol": "NIFTY26OCT22800CE", "instrument_token": 888222}]
    ev = evaluate_candidate_performance(candidate, MockKiteRunner(), datetime(2026, 10, 27, 15, 10), instruments)

    assert ev["t1_hit"] is True
    assert ev["t2_hit"] is False
    assert ev["sl_hit"] is False
    assert ev["runner_be_hit"] is True
    assert "TRAILED AT COST" in ev["outcome"]
    # Total shares = 130. Lot 1 (65) made (40 - 20) = +1300. Lot 2 exited at cost (0). Net PnL = +1300 (+50% ROI on 2600 capital)
    assert ev["pnl"] == 1300.0
    assert ev["pnl_pct"] == 50.0


if __name__ == "__main__":
    print("Running Hero-Zero test suite...")
    test_sensex_hero_zero_quality_strike_structure()
    print("  ✓ test_sensex_hero_zero_quality_strike_structure passed")
    test_nifty_hero_zero_quality_strike_structure()
    print("  ✓ test_nifty_hero_zero_quality_strike_structure passed")
    test_hero_zero_evaluation_target_hit()
    print("  ✓ test_hero_zero_evaluation_target_hit passed")
    test_hero_zero_evaluation_stop_loss()
    print("  ✓ test_hero_zero_evaluation_stop_loss passed")
    test_hero_zero_chronological_sl_before_target()
    print("  ✓ test_hero_zero_chronological_sl_before_target passed")
    test_hero_zero_t1_hit_runner_trailed_to_cost()
    print("  ✓ test_hero_zero_t1_hit_runner_trailed_to_cost passed")
    print("All 6 Hero-Zero tests passed successfully! 🎉")
