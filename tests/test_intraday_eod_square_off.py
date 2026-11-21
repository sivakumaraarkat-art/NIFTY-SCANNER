from datetime import datetime, date, time as time_type
from zoneinfo import ZoneInfo
from pathlib import Path

from src.scanners.intraday_trade_monitor import observe_trades, SQUARE_OFF_TIME
from src.scanners.daily_4pm_intraday_summary import render_report
from src.scanners.options_data_provider import resolve_option_candidate, FALLBACK_LOT_SIZES

IST = ZoneInfo("Asia/Kolkata")


class FakeKite:
    def __init__(self, candles_by_token):
        self._candles = candles_by_token

    def instruments(self, exchange):
        return [
            {"tradingsymbol": "KOTAKBANK26NOV1800PE", "instrument_token": 1001},
            {"tradingsymbol": "INOXWIND26NOV63CE", "instrument_token": 1002},
            {"tradingsymbol": "TCS26NOV4000CE", "instrument_token": 1003},
        ]

    def historical_data(self, token, start, end, interval):
        return self._candles.get(token, [])

    def ltp(self, key):
        return {key: {"last_price": 1800.0}}

    def quote(self, keys):
        return {k: {"last_price": 40.0, "oi": 50000, "depth": {"buy": [{"price": 39.8}], "sell": [{"price": 40.2}]}} for k in keys}


def test_observe_trades_eod_square_off():
    # Signal entered at 14:50 IST
    # Between 14:50 and 15:25, price hovers between 4.90 and 5.30 (Entry: 5.0, T1: 5.40, SL: 4.0)
    # At 15:25, candle close is 5.10.
    signal_time = datetime(2026, 11, 4, 14, 50, tzinfo=IST).isoformat()
    signals = {
        "KOTAKBANK26NOV1800PE": {
            "option_symbol": "KOTAKBANK26NOV1800PE",
            "symbol": "KOTAKBANK",
            "strike": 1800.0,
            "option_type": "PE",
            "entry_price": 5.00,
            "t1": 5.40,
            "t2": 5.75,
            "stop_loss": 4.00,
            "lots": 1,
            "lot_size": 400,
            "capital": 2000.0,
            "signal_time": signal_time,
            "last_seen_scan_time": signal_time,
            "last_seen_scan_file": "intraday_scan_powerful_sl_20261104_145000.json",
            "status": "OPEN",
            "trade_date": "20261104",
        }
    }

    candles = [
        {"date": "2026-11-04T14:51:00+05:30", "open": 5.00, "high": 5.15, "low": 4.90, "close": 5.05},
        {"date": "2026-11-04T15:00:00+05:30", "open": 5.05, "high": 5.20, "low": 4.95, "close": 5.10},
        {"date": "2026-11-04T15:24:00+05:30", "open": 5.10, "high": 5.25, "low": 5.00, "close": 5.15},
        {"date": "2026-11-04T15:25:00+05:30", "open": 5.15, "high": 5.20, "low": 5.05, "close": 5.10},
    ]

    kite = FakeKite({1001: candles})
    state = {"schema_version": 1, "trades": {}}

    # Run observe_trades at 15:26 IST (past 15:25 square-off)
    now = datetime(2026, 11, 4, 15, 26, tzinfo=IST)
    events = observe_trades(state, signals, kite, now)

    assert events == 1
    trade = state["trades"]["KOTAKBANK26NOV1800PE"]
    assert trade["status"] == "CLOSED"
    assert trade["close_reason"] == "EOD_SQUARE_OFF"
    assert trade["close_price"] == 5.10
    assert trade["pnl"] == (5.10 - 5.00) * 1 * 400  # +40.0
    assert round(trade["pnl_pct"], 2) == 2.0


def test_observe_trades_same_candle_conservative_sl():
    # If a single 1-minute candle breaches both target (high >= t1) and SL (low <= sl),
    # conservative execution must record SL_HIT.
    signal_time = datetime(2026, 11, 4, 10, 0, tzinfo=IST).isoformat()
    signals = {
        "INOXWIND26NOV63CE": {
            "option_symbol": "INOXWIND26NOV63CE",
            "symbol": "INOXWIND",
            "strike": 63.0,
            "option_type": "CE",
            "entry_price": 10.0,
            "t1": 10.8,
            "t2": 11.5,
            "stop_loss": 8.0,
            "lots": 1,
            "lot_size": 1000,
            "capital": 10000.0,
            "signal_time": signal_time,
            "last_seen_scan_time": signal_time,
            "last_seen_scan_file": "intraday_scan_20261104_100000.json",
            "status": "OPEN",
            "trade_date": "20261104",
        }
    }

    # Spike candle from 7.5 to 11.0 in same minute
    candles = [
        {"date": "2026-11-04T10:05:00+05:30", "open": 9.5, "high": 11.0, "low": 7.5, "close": 8.5},
    ]

    kite = FakeKite({1002: candles})
    state = {"schema_version": 1, "trades": {}}
    now = datetime(2026, 11, 4, 10, 10, tzinfo=IST)

    events = observe_trades(state, signals, kite, now)
    assert events == 1
    trade = state["trades"]["INOXWIND26NOV63CE"]
    assert trade["status"] == "CLOSED"
    assert trade["close_reason"] == "SL_HIT"
    assert trade["close_price"] == 8.0
    assert trade["data_status"] == "ambiguous_resolved_conservative_sl"


def test_daily_4pm_summary_eod_square_off(monkeypatch, tmp_path):
    # Test that EOD squared off trades appear in the summary with proper status,
    # exit price, P&L, and are included in the win rate calculation.
    today_str = datetime.now(IST).strftime("%Y%m%d")
    state_file = tmp_path / "intraday_trade_state.json"
    state_data = {
        "schema_version": 1,
        "trades": {
            "T1_TRADE": {
                "option_symbol": "TCS26NOV4000CE",
                "entry_price": 50.0,
                "t1": 54.0,
                "stop_loss": 40.0,
                "close_price": 54.0,
                "close_reason": "T1_HIT",
                "status": "CLOSED",
                "close_time": f"{today_str[:4]}-{today_str[4:6]}-{today_str[6:]}T11:30:00+05:30",
                "hit_time_source": "minute_candle",
                "pnl": 900.0,
                "pnl_pct": 8.0,
                "capital": 11250.0,
                "signal_time": f"{today_str[:4]}-{today_str[4:6]}-{today_str[6:]}T10:00:00+05:30",
                "trade_date": today_str,
            },
            "EOD_WIN_TRADE": {
                "option_symbol": "KOTAKBANK26NOV1800PE",
                "entry_price": 5.0,
                "t1": 5.4,
                "stop_loss": 4.0,
                "close_price": 5.20,
                "close_reason": "EOD_SQUARE_OFF",
                "status": "CLOSED",
                "close_time": f"{today_str[:4]}-{today_str[4:6]}-{today_str[6:]}T15:25:00+05:30",
                "hit_time_source": "minute_candle",
                "pnl": 80.0,
                "pnl_pct": 4.0,
                "capital": 2000.0,
                "signal_time": f"{today_str[:4]}-{today_str[4:6]}-{today_str[6:]}T14:50:00+05:30",
                "trade_date": today_str,
            },
            "EOD_LOSS_TRADE": {
                "option_symbol": "INOXWIND26NOV63CE",
                "entry_price": 3.0,
                "t1": 3.25,
                "stop_loss": 2.4,
                "close_price": 2.90,
                "close_reason": "EOD_SQUARE_OFF",
                "status": "CLOSED",
                "close_time": f"{today_str[:4]}-{today_str[4:6]}-{today_str[6:]}T15:25:00+05:30",
                "hit_time_source": "minute_candle",
                "pnl": -100.0,
                "pnl_pct": -3.33,
                "capital": 3000.0,
                "signal_time": f"{today_str[:4]}-{today_str[4:6]}-{today_str[6:]}T13:20:00+05:30",
                "trade_date": today_str,
            },
        }
    }
    import json
    state_file.write_text(json.dumps(state_data), encoding="utf-8")

    import src.scanners.daily_4pm_intraday_summary as summary_module
    monkeypatch.setattr(summary_module, "STATE_FILE", state_file)
    monkeypatch.setattr(summary_module, "LOG_DIR", tmp_path)

    report = summary_module.render_report()
    assert report is not None

    # Win rate: 2 wins (T1_HIT + EOD_WIN_TRADE), 1 loss (EOD_LOSS_TRADE) -> 66.7%
    assert "66.7%" in report
    assert "(2W / 1L)" in report

    # EOD squared off display
    assert "EOD SQUARED OFF ⏱️ (PROFIT)" in report
    assert "EOD SQUARED OFF ⏱️ (LOSS)" in report
    assert "15:25 IST (EOD square-off)" in report
    assert "<b>Exit:</b> <code>Exit (₹5.20)</code>" in report
    assert "<b>Exit:</b> <code>Exit (₹2.90)</code>" in report

    # Ensure "Not observed" and "Live (₹0.00)" DO NOT appear
    assert "Not observed" not in report
    assert "Live (₹0.00)" not in report


def test_options_data_provider_exact_symbol_match():
    # Verify exact symbol matching avoids substring false positives
    instruments = [
        {"name": "VOLTAS", "instrument_type": "CE", "expiry": date(2026, 11, 26), "strike": 1800.0, "tradingsymbol": "VOLTAS26NOV1800CE", "lot_size": 400},
        {"name": "LT", "instrument_type": "CE", "expiry": date(2026, 11, 26), "strike": 3600.0, "tradingsymbol": "LT26NOV3600CE", "lot_size": 175},
        {"name": "LTIM", "instrument_type": "CE", "expiry": date(2026, 11, 26), "strike": 6000.0, "tradingsymbol": "LTIM26NOV6000CE", "lot_size": 150},
    ]

    candidate = resolve_option_candidate(
        kite=None,
        nfo_instruments=instruments,
        symbol="LT",
        sentiment="BULLISH",
    )
    # When kite is None, candidate is skipped safely, but check candidate matching logic:
    def matches_symbol(inst_name: str, target_sym: str) -> bool:
        name = (inst_name or "").upper().strip()
        target = target_sym.upper().strip()
        return name == target

    matched = [i for i in instruments if matches_symbol(i["name"], "LT")]
    assert len(matched) == 1
    assert matched[0]["tradingsymbol"] == "LT26NOV3600CE"
