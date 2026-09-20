from types import SimpleNamespace

import pandas as pd

import run_swing_trade_system


def test_controlled_paper_scan_preserves_cap_segments_and_signal_only(
    monkeypatch,
):
    settings = SimpleNamespace(
        controlled_universe_size=3,
        max_historical_download_symbols=3,
        minimum_stock_price=0,
        maximum_stock_price=999999,
        minimum_candidate_score=80,
        initial_capital=100000,
        risk_per_trade=0.01,
        telegram_bot_token="",
        telegram_chat_id="",
        signal_only=True,
    )
    universe = [
        {"tradingsymbol": "INFY", "instrument_token": 1},
        {"tradingsymbol": "DIXON", "instrument_token": 2},
        {"tradingsymbol": "UNMAPPED", "instrument_token": 3},
        {"tradingsymbol": "OUTSIDE", "instrument_token": 4},
    ]
    quote_symbols = []
    sent_candidates = []

    monkeypatch.setenv("CONTROLLED_SYMBOLS", "INFY,DIXON,UNMAPPED")
    monkeypatch.setattr(run_swing_trade_system, "load_settings", lambda: settings)
    monkeypatch.setattr(
        run_swing_trade_system, "create_zerodha_client", lambda settings: object()
    )
    monkeypatch.setattr(
        run_swing_trade_system, "verify_connection", lambda client: None
    )
    monkeypatch.setattr(
        run_swing_trade_system,
        "load_nse_equity_universe",
        lambda client, settings: universe,
    )
    monkeypatch.setattr(
        run_swing_trade_system,
        "load_nse_cap_snapshot",
        lambda: {"INFY": "LARGE", "DIXON": "MID"},
    )

    def fake_prefilter(kite, stock_candidates, **kwargs):
        quote_symbols.extend(
            candidate["tradingsymbol"] for candidate in stock_candidates
        )
        return [{"symbol": symbol} for symbol in quote_symbols]

    monkeypatch.setattr(
        run_swing_trade_system, "prefilter_by_quote_liquidity", fake_prefilter
    )
    monkeypatch.setattr(
        run_swing_trade_system,
        "HistoricalMarketDataDownloader",
        lambda client, settings: SimpleNamespace(
            download_universe=lambda candidates: {
                candidate["tradingsymbol"]: pd.DataFrame(
                    {"close": [100], "volume": [100]}
                )
                for candidate in candidates
            }
        ),
    )
    monkeypatch.setattr(
        run_swing_trade_system,
        "rank_liquid_stocks",
        lambda **kwargs: [{"symbol": symbol} for symbol in quote_symbols],
    )
    monkeypatch.setattr(
        run_swing_trade_system,
        "add_technical_indicators",
        lambda dataframe: dataframe,
    )
    monkeypatch.setattr(
        run_swing_trade_system,
        "generate_setup_candidates",
        lambda frames, settings: [
            {
                "symbol": symbol,
                "setup": "TEST",
                "score": 90,
                "entry": 100.0,
                "stop_loss": 95.0,
                "reasons": [],
            }
            for symbol in frames
        ],
    )
    monkeypatch.setattr(
        run_swing_trade_system,
        "rank_trade_candidates",
        lambda candidates, settings: candidates,
    )
    monkeypatch.setattr(
        run_swing_trade_system,
        "enrich_candidates_with_news",
        lambda candidates: candidates,
    )
    monkeypatch.setattr(
        run_swing_trade_system,
        "send_swing_alerts",
        lambda candidates, settings: sent_candidates.extend(candidates),
    )

    result = run_swing_trade_system.main()

    assert quote_symbols == ["INFY", "DIXON", "UNMAPPED"]
    assert [(item["symbol"], item["cap_segment"]) for item in result] == [
        ("INFY", "LARGE"),
        ("DIXON", "MID"),
        ("UNMAPPED", "UNKNOWN"),
    ]
    assert sent_candidates == result
    assert settings.signal_only is True
