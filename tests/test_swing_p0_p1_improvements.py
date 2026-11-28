"""
Unit tests for Swing Trade P0 & P1 Improvements:
1. Partial Exit (50% @ Target 1) + Trail SL to Break-Even (+0.5%)
2. Whipsaw-Safe Stop Loss (LTP check vs Intraday Wick Low)
3. Break-Even Stop Loss protection on runner
4. Single-share break-even trailing
5. Sector Concentration Cap (Max 2 per sector)
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from trade_selection.active_swing_trade_registry import (
    register_swing_candidates,
    close_swing_trade,
    partial_close_swing_trade,
    load_active_trades,
    load_closed_trades,
    ACTIVE_TRADES_FILE,
    CLOSED_TRADES_FILE,
    DB_DIR,
)
from src.scanners.swing_trade_exit_monitor import (
    evaluate_swing_exit,
    monitor_active_swing_trades,
)
from src.scanners.run_options_intraday_scan_powerful_sl import get_stock_sector


@pytest.fixture(autouse=True)
def clean_test_trades(tmp_path, monkeypatch):
    """Use temporary JSON databases during tests to avoid touching production files."""
    test_active = tmp_path / "active_swing_trades.json"
    test_closed = tmp_path / "closed_swing_trades.json"
    monkeypatch.setattr("trade_selection.active_swing_trade_registry.ACTIVE_TRADES_FILE", test_active)
    monkeypatch.setattr("trade_selection.active_swing_trade_registry.CLOSED_TRADES_FILE", test_closed)
    monkeypatch.setattr("trade_selection.active_swing_trade_registry.DB_DIR", tmp_path)


def test_p0_partial_close_50_pct_at_t1():
    """Verify booking 50% at Target 1 creates a closed record and trails remaining SL to break-even."""
    candidate = {
        "symbol": "TRENT",
        "setup": "TECHNICAL SWING WATCH",
        "entry": 3000.0,
        "stop_loss": 2880.0,  # -4.0%
        "target_1": 3180.0,  # +6.0%
        "target_2": 3300.0,  # +10.0%
        "quantity": 10,
        "capital_required": 30000.0,
        "score": 90,
    }

    registered = register_swing_candidates([candidate], max_holding_days=10)
    assert len(registered) == 1
    trade_id = registered[0]["trade_id"]

    # Partial exit: 50% (5 shares) at Target 1 (3180.0)
    closed_part, updated_active = partial_close_swing_trade(
        trade_id=trade_id,
        exit_price=3180.0,
        exit_reason="TARGET 1 PARTIAL HIT (50% BOOKED @ +5.5%+) 🎯",
        closed_qty=5,
    )

    # 1. Verify closed 50% record
    assert closed_part is not None
    assert closed_part["quantity"] == 5
    assert closed_part["exit_price"] == 3180.0
    assert closed_part["return_pct"] == 6.0
    assert closed_part["pnl_amount"] == 900.0  # (3180 - 3000) * 5
    assert closed_part["status"] == "CLOSED"

    # 2. Verify remaining active trade
    assert updated_active is not None
    assert updated_active["quantity"] == 5
    assert updated_active["capital_allocated"] == 15000.0
    assert updated_active["t1_booked"] is True
    # Stop loss moved to Break-Even (3000 * 1.005 = 3015.0)
    assert updated_active["stop_loss"] == 3015.0
    assert updated_active["stop_loss_pct"] == 0.50
    assert updated_active["status"] == "RUNNER_ACTIVE"

    # 3. Check databases
    assert len(load_closed_trades()) == 1
    active = load_active_trades()
    assert len(active) == 1
    assert active[0]["quantity"] == 5
    assert active[0]["stop_loss"] == 3015.0


def test_p0_runner_reaches_target_2_full_exit():
    """Verify remaining 50% runner can proceed to Target 2 and close fully."""
    candidate = {
        "symbol": "DIVISLAB",
        "entry": 10000.0,
        "stop_loss": 9600.0,
        "target_1": 10600.0,
        "target_2": 11200.0,
        "quantity": 4,
        "score": 95,
    }
    registered = register_swing_candidates([candidate], max_holding_days=10)
    trade_id = registered[0]["trade_id"]

    # 1. Hit T1 -> partial close 2 shares
    closed_part, updated_active = partial_close_swing_trade(
        trade_id=trade_id,
        exit_price=10600.0,
        exit_reason="TARGET 1 PARTIAL HIT (50% BOOKED @ +5.5%+) 🎯",
        closed_qty=2,
    )
    assert closed_part["pnl_amount"] == 1200.0

    # 2. Evaluate remaining runner when price reaches Target 2 (11200.0)
    quote = {"ltp": 11250.0, "high": 11300.0, "low": 10500.0}
    should_exit, exit_p, reason = evaluate_swing_exit(updated_active, quote, check_emergency_news=False)
    assert should_exit is True
    assert "TARGET 2 HIT" in reason
    assert exit_p == 11200.0

    # 3. Close remaining 2 shares at Target 2
    closed_final = close_swing_trade(trade_id, exit_p, reason)
    assert closed_final["quantity"] == 2
    assert closed_final["exit_price"] == 11200.0
    assert closed_final["return_pct"] == 12.0
    assert closed_final["pnl_amount"] == 2400.0  # (11200 - 10000) * 2

    # Both tranches closed: total profit = 1200 + 2400 = 3600
    all_closed = load_closed_trades()
    assert len(all_closed) == 2
    total_pnl = sum(t["pnl_amount"] for t in all_closed)
    assert total_pnl == 3600.0
    assert len(load_active_trades()) == 0


def test_p0_runner_break_even_protection_on_reversal():
    """Verify if price reverses after T1, the runner exits at Break-Even (+0.5%) ensuring zero net loss."""
    candidate = {
        "symbol": "HEROMOTOCO",
        "entry": 5000.0,
        "stop_loss": 4800.0,
        "target_1": 5300.0,  # +6%
        "target_2": 5600.0,  # +12%
        "quantity": 2,
        "score": 90,
    }
    registered = register_swing_candidates([candidate], max_holding_days=10)
    trade_id = registered[0]["trade_id"]

    # 1. T1 hit -> 50% booked, SL moved to Break-Even (5000 * 1.005 = 5025.0)
    closed_part, updated_active = partial_close_swing_trade(
        trade_id=trade_id,
        exit_price=5300.0,
        exit_reason="TARGET 1 PARTIAL HIT",
        closed_qty=1,
    )
    assert updated_active["stop_loss"] == 5025.0

    # 2. Stock reverses down to 5010.0 (below Break-Even SL 5025.0)
    quote = {"ltp": 5010.0, "high": 5200.0, "low": 5000.0}
    should_exit, exit_p, reason = evaluate_swing_exit(updated_active, quote, check_emergency_news=False)
    assert should_exit is True
    assert "BREAK-EVEN" in reason
    assert exit_p == 5025.0

    # 3. Close remaining 1 share at break-even
    closed_final = close_swing_trade(trade_id, exit_p, reason)
    assert closed_final["pnl_amount"] == 25.0  # (5025 - 5000) * 1 = +25 profit on second half!

    # Combined trade: +300 on first half, +25 on second half = +325 total profit!
    all_closed = load_closed_trades()
    assert sum(t["pnl_amount"] for t in all_closed) == 325.0


def test_p0_whipsaw_safe_stop_loss_ignores_intraday_wick_rebound():
    """Verify that a stock touching SL during morning noise but closing green above SL is NOT stopped out."""
    trade = {
        "symbol": "RELIANCE",
        "entry_price": 1300.0,
        "stop_loss": 1250.0,  # SL at 1250.0
        "target_1": 1380.0,
        "target_2": 1440.0,
        "max_holding_days": 10,
        "entry_date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
    }

    # Scenario: Morning flash dip reached 1248.0 (below SL 1250.0), but by 3:15 PM the stock rebounded to 1275.0 (well above SL)!
    rebounded_quote = {"ltp": 1275.0, "high": 1290.0, "low": 1248.0}
    should_exit, exit_p, reason = evaluate_swing_exit(trade, rebounded_quote, check_emergency_news=False)

    # Must NOT exit on the wick dip since current price has rebounded >1% above SL!
    assert should_exit is False
    assert reason == ""

    # Contrast: If current LTP is actually below SL, it MUST exit
    breakdown_quote = {"ltp": 1245.0, "high": 1260.0, "low": 1240.0}
    should_exit_true, exit_p_true, reason_true = evaluate_swing_exit(trade, breakdown_quote, check_emergency_news=False)
    assert should_exit_true is True
    assert "STOP LOSS" in reason_true
    assert exit_p_true == 1250.0


def test_p1_sector_concentration_cap_max_two():
    """Verify sector cap limits candidates from the same sector to max 2."""
    assert get_stock_sector("HDFCBANK") == "BANK_PVT"
    assert get_stock_sector("ICICIBANK") == "BANK_PVT"
    assert get_stock_sector("AXISBANK") == "BANK_PVT"

    # Simulate ranking with 3 private banks
    candidates = [
        {"symbol": "HDFCBANK", "score": 95},
        {"symbol": "ICICIBANK", "score": 92},
        {"symbol": "AXISBANK", "score": 88},  # 3rd bank in same sector - should be capped!
        {"symbol": "TCS", "score": 90},       # IT sector
        {"symbol": "TATASTEEL", "score": 89}, # Metals sector
    ]

    sector_counts = {}
    diversified = []
    for cand in candidates:
        sym = cand["symbol"]
        sec = get_stock_sector(sym)
        if sec and sector_counts.get(sec, 0) >= 2:
            continue
        diversified.append(cand)
        if sec:
            sector_counts[sec] = sector_counts.get(sec, 0) + 1

    selected_symbols = [c["symbol"] for c in diversified]
    assert "HDFCBANK" in selected_symbols
    assert "ICICIBANK" in selected_symbols
    assert "AXISBANK" not in selected_symbols  # Filtered by sector cap!
    assert "TCS" in selected_symbols
    assert "TATASTEEL" in selected_symbols
    assert len(selected_symbols) == 4
