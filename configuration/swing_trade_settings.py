import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    zerodha_api_key: str
    access_token_file: Path
    telegram_bot_token: str
    telegram_chat_id: str
    initial_capital: float
    risk_per_trade: float
    minimum_risk_reward: float
    minimum_candidate_score: float
    signal_only: bool
    history_days: int
    max_symbols: int
    max_historical_download_symbols: int
    request_delay_seconds: float
    data_cache_dir: Path
    controlled_universe_size: int
    minimum_stock_price: float
    maximum_stock_price: float


def load_settings():
    default_token_path = (PROJECT_ROOT.parent / ".kite_access_token").resolve()
    token_value = os.getenv(
        "ZERODHA_ACCESS_TOKEN_FILE", str(default_token_path)
    ).strip()
    token = Path(token_value).expanduser()
    if not token.is_absolute():
        token = (PROJECT_ROOT / token).resolve()
    cache = PROJECT_ROOT / os.getenv(
        "MARKET_DATA_CACHE_DIR", "database/market_data_cache"
    )
    return Settings(
        os.getenv("ZERODHA_API_KEY", "").strip(),
        token,
        os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        os.getenv("TELEGRAM_CHAT_ID", "").strip(),
        float(os.getenv("INITIAL_CAPITAL", "100000")),
        float(os.getenv("RISK_PER_TRADE", "0.01")),
        float(os.getenv("MINIMUM_RISK_REWARD", "2.0")),
        float(os.getenv("MINIMUM_CANDIDATE_SCORE", "80")),
        os.getenv("SIGNAL_ONLY", "true").lower() == "true",
        int(os.getenv("HISTORY_DAYS", "220")),
        int(os.getenv("MAX_UNIVERSE_SYMBOLS", "300")),
        int(os.getenv("MAX_HISTORICAL_DOWNLOAD_SYMBOLS", "300")),
        float(os.getenv("ZERODHA_REQUEST_DELAY_SECONDS", "0.35")),
        cache,
        int(os.getenv("CONTROLLED_UNIVERSE_SIZE", "300")),
        float(os.getenv("MINIMUM_STOCK_PRICE", "0")),
        float(os.getenv("MAXIMUM_STOCK_PRICE", "999999")),
    )
