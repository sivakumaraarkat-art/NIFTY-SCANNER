from types import SimpleNamespace

import pandas as pd

from zerodha_market_data.market_data_downloader import HistoricalMarketDataDownloader


def test_csv_cache_is_used_when_parquet_engine_is_unavailable(tmp_path, monkeypatch):
    settings = SimpleNamespace(
        data_cache_dir=str(tmp_path),
        request_delay_seconds=0,
        history_days=30,
    )
    downloader = HistoricalMarketDataDownloader(kite=None, settings=settings)

    dataframe = pd.DataFrame(
        [
            {
                "date": "2024-01-01",
                "open": 10.0,
                "high": 12.0,
                "low": 9.5,
                "close": 11.0,
                "volume": 1000,
            }
        ]
    )

    def parquet_unavailable(*args, **kwargs):
        raise ImportError("No parquet support")

    monkeypatch.setattr(pd.DataFrame, "to_parquet", parquet_unavailable)

    downloader._save_cache("RELIANCE", dataframe)

    csv_path = tmp_path / "NSE_RELIANCE_daily.csv"
    assert csv_path.exists()

    loaded = downloader._load_cache("RELIANCE")
    assert loaded is not None
    assert list(loaded.columns) == ["date", "open", "high", "low", "close", "volume"]
    assert loaded.iloc[0].to_dict()["close"] == 11.0
