"""Safe, cache-first historical market-data downloads."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {"date", "open", "high", "low", "close", "volume"}
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE_SECONDS = 2.0
DEFAULT_CACHE_MAX_AGE_HOURS = 24.0


class HistoricalMarketDataDownloader:
    """Download historical data with throttling, retries, and resume support."""

    def __init__(self, kite, settings):
        self.kite = kite
        self.settings = settings
        self.cache_dir = Path(settings.data_cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.request_delay_seconds = max(0.0, float(settings.request_delay_seconds))
        self.max_retries = DEFAULT_MAX_RETRIES
        self.backoff_base_seconds = DEFAULT_BACKOFF_BASE_SECONDS
        self.cache_max_age_hours = DEFAULT_CACHE_MAX_AGE_HOURS
        self.lookback_days = max(1, int(settings.history_days))
        self._last_request_time = 0.0

    def _cache_path(self, symbol: str) -> Path:
        safe_symbol = str(symbol).strip().upper().replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"NSE_{safe_symbol}_daily.parquet"

    def _cache_csv_path(self, symbol: str) -> Path:
        safe_symbol = str(symbol).strip().upper().replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"NSE_{safe_symbol}_daily.csv"

    def _cache_candidates(self, symbol: str) -> list[Path]:
        return [self._cache_path(symbol), self._cache_csv_path(symbol)]

    def _load_cache(
        self, symbol: str, allow_stale: bool = False
    ) -> pd.DataFrame | None:
        for path in self._cache_candidates(symbol):
            if not path.exists():
                continue
            try:
                if not allow_stale:
                    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
                    if age > timedelta(hours=self.cache_max_age_hours):
                        continue
                if path.suffix.lower() == ".csv":
                    dataframe = pd.read_csv(path, parse_dates=["date"])
                else:
                    dataframe = pd.read_parquet(path)
                if dataframe.empty or not REQUIRED_COLUMNS.issubset(dataframe.columns):
                    continue
                return dataframe
            except (OSError, ValueError, ImportError) as exc:
                print(f"WARNING: cache read failed for {symbol} ({path.name}): {exc}")
        return None

    def _save_cache(self, symbol: str, dataframe: pd.DataFrame) -> None:
        path = self._cache_path(symbol)
        csv_path = self._cache_csv_path(symbol)
        temporary_path = path.with_suffix(".tmp.parquet")
        try:
            dataframe.to_parquet(temporary_path, index=False)
            temporary_path.replace(path)
            return
        except Exception as exc:
            if temporary_path.exists():
                temporary_path.unlink()
            print(f"WARNING: parquet cache write failed for {symbol}: {exc}")

        try:
            dataframe.to_csv(csv_path, index=False)
        except Exception as csv_exc:
            print(f"WARNING: CSV cache write failed for {symbol}: {csv_exc}")

    def _wait_before_request(self) -> None:
        remaining = self.request_delay_seconds - (
            time.monotonic() - self._last_request_time
        )
        if remaining > 0:
            time.sleep(remaining)

    def _download_one(self, instrument_token: int, symbol: str) -> pd.DataFrame | None:
        to_date = datetime.now()
        from_date = to_date - timedelta(days=self.lookback_days)
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                self._wait_before_request()
                self._last_request_time = time.monotonic()
                records = self.kite.historical_data(
                    instrument_token,
                    from_date.strftime("%Y-%m-%d"),
                    to_date.strftime("%Y-%m-%d"),
                    "day",
                    continuous=False,
                    oi=False,
                )
                dataframe = pd.DataFrame(records)
                if dataframe.empty or not REQUIRED_COLUMNS.issubset(dataframe.columns):
                    print(f"WARNING: usable historical data unavailable for {symbol}.")
                    return None
                dataframe["date"] = pd.to_datetime(dataframe["date"])
                return dataframe
            except Exception as exc:
                last_exception = exc
                if attempt >= self.max_retries:
                    break
                delay = self.backoff_base_seconds * (2**attempt)
                print(
                    f"WARNING: {symbol} request failed; retry "
                    f"{attempt + 1}/{self.max_retries} in {delay:.1f}s: {exc}"
                )
                time.sleep(delay)

        print(f"ERROR: historical download failed for {symbol}: {last_exception}")
        return None

    def download_universe(
        self, stock_candidates: list[dict]
    ) -> dict[str, pd.DataFrame]:
        results: dict[str, pd.DataFrame] = {}
        processed_symbols: set[str] = set()
        total = len(stock_candidates)
        print(f"Historical data download started for {total} symbols.")

        for index, candidate in enumerate(stock_candidates, start=1):
            symbol = str(candidate.get("tradingsymbol", "")).strip().upper()
            if not symbol or symbol in processed_symbols:
                continue
            processed_symbols.add(symbol)
            token = candidate.get("instrument_token")
            if not token:
                print(f"WARNING: missing instrument token for {symbol}")
                continue

            dataframe = self._load_cache(symbol)
            if dataframe is not None:
                results[symbol] = dataframe
                print(f"[{index}/{total}] {symbol}: cache used")
                continue

            print(f"[{index}/{total}] {symbol}: downloading...")
            dataframe = self._download_one(int(token), symbol)
            if dataframe is None:
                fallback = self._load_cache(symbol, allow_stale=True)
                if fallback is not None:
                    results[symbol] = fallback
                    print(f"{symbol}: using existing fallback cache.")
                continue

            self._save_cache(symbol, dataframe)
            results[symbol] = dataframe

        print(
            f"Historical data download completed: "
            f"{len(results)}/{len(processed_symbols)} symbols available."
        )
        return results
