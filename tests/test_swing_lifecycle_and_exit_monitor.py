"""
Unit tests for 7-to-10 day Swing Trade Lifecycle, Registry, Exit Monitor, and Audit.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
try:
    import pytest
except ImportError:
    class _DummyPytest:
        @staticmethod
        def fixture(*args, **kwargs):
            def decorator(func):
                return func
            return decorator
    pytest = _DummyPytest()

from trade_selection.active_swing_trade_registry import (
    register_swing_candidates,
    close_swing_trade,
    load_active_trades,
    load_closed_trades,
    calculate_business_days_ahead,
    calculate_trading_days_elapsed,
    ACTIVE_TRADES_FILE,
    CLOSED_TRADES_FILE,
)
from src.scanners.swing_trade_exit_monitor import evaluate_swing_exit
from telegram_alerts.swing_trade_alert_sender import resolve_telegram_credentials


@pytest.fixture(autouse=True)
def clean_test_trades(tmp_path, monkeypatch):
    """Use a temporary directory for trade databases during tests."""
    test_active = tmp_path / "active_swing_trades.json"
    test_closed = tmp_path / "closed_swing_trades.json"
    monkeypatch.setattr("trade_selection.active_swing_trade_registry.ACTIVE_TRADES_FILE", test_active)
    monkeypatch.setattr("trade_selection.active_swing_trade_registry.CLOSED_TRADES_FILE", test_closed)
    monkeypatch.setattr("trade_selection.active_swing_trade_registry.DB_DIR", tmp_path)


def test_calculate_business_days_ahead():
    # Monday
    mon = datetime(2026, 11, 2)
    ten_days_later = calculate_business_days_ahead(mon, 10)
    # Mon 2 -> Mon 16 is 10 business days
    assert ten_days_later.weekday() < 5
    assert (ten_days_later - mon).days >= 14  # At least 14 calendar days due to weekends


def test_calculate_trading_days_elapsed():
    entry_date = "2026-11-02"  # Monday
    check_date = datetime(2026, 11, 6)  # Friday (4 trading days later)
    elapsed = calculate_trading_days_elapsed(entry_date, check_date)
    assert elapsed == 4


def test_register_and_close_swing_candidate():
    candidate = {
        "symbol": "TATACHEM",
        "setup": "TECHNICAL SWING WATCH",
        "entry": 1000.0,
        "stop_loss": 965.0,  # -3.5%
        "target_1": 1060.0,  # +6.0%
        "target_2": 1100.0,  # +10.0%
        "quantity": 100,
        "capital_required": 100000.0,
        "score": 88,
        "predictive_outlook": "🚀 HIGH CONVICTION TAILWIND",
    }

    # 1. Register candidate
    registered = register_swing_candidates([candidate], max_holding_days=10)
    assert len(registered) == 1
    trade = registered[0]
    assert trade["symbol"] == "TATACHEM"
    assert trade["entry_price"] == 1000.0
    assert trade["status"] == "OPEN"

    # 2. Duplicate registration prevention
    dup = register_swing_candidates([candidate], max_holding_days=10)
    assert len(dup) == 0

    # 3. Close trade at Target 1 (+6.0% return)
    trade_id = trade["trade_id"]
    closed = close_swing_trade(
        trade_id=trade_id,
        exit_price=1060.0,
        exit_reason="TARGET 1 HIT (+5.5%+) 🎯",
        exit_date="2026-11-08",
    )
    assert closed is not None
    assert closed["return_pct"] == 6.0
    assert closed["pnl_amount"] == 6000.0
    assert closed["status"] == "CLOSED"

    # Verify active list is now empty and closed list has 1
    assert len(load_active_trades()) == 0
    assert len(load_closed_trades()) == 1


def test_evaluate_exit_target_hit():
    trade = {
        "symbol": "RELIANCE",
        "entry_price": 2500.0,
        "stop_loss": 2410.0,
        "target_1": 2650.0,
        "target_2": 2750.0,
        "max_holding_days": 10,
        "entry_date": datetime.now().strftime("%Y-%m-%d"),
    }
    quote = {"ltp": 2660.0, "high": 2670.0, "low": 2490.0}
    should_exit, exit_p, reason = evaluate_swing_exit(trade, quote, check_emergency_news=False)
    assert should_exit is True
    assert "TARGET 1" in reason
    assert exit_p == 2650.0


def test_evaluate_exit_stop_loss_hit():
    trade = {
        "symbol": "INFY",
        "entry_price": 1800.0,
        "stop_loss": 1735.0,
        "target_1": 1910.0,
        "target_2": 1980.0,
        "max_holding_days": 10,
        "entry_date": datetime.now().strftime("%Y-%m-%d"),
    }
    quote = {"ltp": 1730.0, "high": 1805.0, "low": 1728.0}
    should_exit, exit_p, reason = evaluate_swing_exit(trade, quote, check_emergency_news=False)
    assert should_exit is True
    assert "STOP LOSS" in reason
    assert exit_p == 1735.0


def test_evaluate_exit_10_day_time_horizon():
    # Trade entered 15 calendar days ago (approx 11 trading days)
    past_date = (datetime.now() - timedelta(days=16)).strftime("%Y-%m-%d")
    trade = {
        "symbol": "WIPRO",
        "entry_price": 500.0,
        "stop_loss": 480.0,
        "target_1": 535.0,
        "target_2": 555.0,
        "max_holding_days": 10,
        "entry_date": past_date,
    }
    quote = {"ltp": 512.0, "high": 515.0, "low": 498.0}
    should_exit, exit_p, reason = evaluate_swing_exit(trade, quote, check_emergency_news=False)
    assert should_exit is True
    assert "10-DAY TIME HORIZON" in reason
    assert exit_p == 512.0


def test_resolve_telegram_credentials_prefers_portfolio_bot(monkeypatch):
    monkeypatch.setenv("PORTFOLIO_TELEGRAM_BOT_TOKEN", "test_port_token_123")
    monkeypatch.setenv("PORTFOLIO_TELEGRAM_CHAT_ID", "test_port_chat_456")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_std_token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test_std_chat")

    token, chat_id = resolve_telegram_credentials()
    assert token == "test_port_token_123"
    assert chat_id == "test_port_chat_456"
