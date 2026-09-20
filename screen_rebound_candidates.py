"""Screen complete NSE cap snapshots for 52-week-low rebound patterns."""

from datetime import date, timedelta
import csv
import time
from pathlib import Path

from openpyxl import load_workbook

from configuration.swing_trade_settings import load_settings
from zerodha_market_data.zerodha_connection import create_zerodha_client

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "nse_cap_segments"
OUTPUT = ROOT / "rebound_stock_candidates.csv"
PORTFOLIO = ROOT / "portfolio_recovery_plan.xlsx"
FILES = {
    "LARGE": "nifty100.csv",
    "MID": "nifty_midcap150.csv",
    "SMALL": "nifty_smallcap250.csv",
}


def load_symbols():
    symbols = {}
    for segment, filename in FILES.items():
        with (DATA / filename).open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                symbol = str(row.get("symbol", "")).strip().upper()
                if symbol:
                    symbols[symbol] = segment
    return symbols


def analyse(kite, instrument):
    candles = kite.historical_data(
        instrument["instrument_token"],
        (date.today() - timedelta(days=420)).isoformat(),
        date.today().isoformat(),
        "day",
        continuous=False,
        oi=False,
    )
    if len(candles) < 210:
        return None
    closes = [float(item["close"]) for item in candles]
    lows = [float(item["low"]) for item in candles]
    volumes = [float(item.get("volume") or 0) for item in candles]
    price = closes[-1]
    low52 = min(closes[-252:])
    sma20 = sum(closes[-20:]) / 20
    sma50 = sum(closes[-50:]) / 50
    sma200 = sum(closes[-200:]) / 200
    gains, losses = [], []
    for before, after in zip(closes[-15:-1], closes[-14:]):
        change = after - before
        gains.append(max(change, 0))
        losses.append(max(-change, 0))
    average_gain = sum(gains) / 14
    average_loss = sum(losses) / 14
    rsi = 100 if average_loss == 0 else 100 - (100 / (1 + average_gain / average_loss))
    five_day_return = (price / closes[-6] - 1) * 100
    recent_low = min(closes[-11:])
    recent_support = min(closes[-20:])
    prior_support = min(closes[-40:-20])
    weekly_lows = [min(lows[index : index + 5]) for index in range(0, len(lows) - 4, 5)]
    weekly_support = min(weekly_lows[-12:])
    weekly_rebound = (price / weekly_support - 1) * 100
    rebound = (price / recent_low - 1) * 100
    volume_average = sum(volumes[-21:-1]) / 20
    volume_ratio = volumes[-1] / volume_average if volume_average else 0
    from_low = (price / low52 - 1) * 100
    rising_support = (
        price > sma20 > sma50
        and recent_support > prior_support * 1.03
        and price / recent_support <= 1.10
    )
    weekly_base_rebound = (
        weekly_rebound >= 4
        and weekly_rebound <= 18
        and price >= sma20 * 0.95
        and 25 <= rsi <= 65
    )
    base_rebound = weekly_base_rebound and five_day_return >= 0
    breakdown = (
        price < sma20 < sma50
        and (five_day_return <= -3 or price <= recent_support * 1.03)
        and rsi < 45
    )
    if base_rebound:
        status = "BUY WATCH - WEEKLY BASE REBOUND"
    elif rising_support:
        status = "BUY WATCH - RISING SUPPORT"
    elif breakdown:
        status = "SELL / BREAKDOWN REVIEW"
    elif from_low <= 18 and five_day_return > 0:
        status = "WATCH - WAIT FOR REBOUND"
    else:
        return None
    return {
        "symbol": instrument["tradingsymbol"],
        "price": round(price, 2),
        "low52": round(low52, 2),
        "from_low_pct": round(from_low, 1),
        "sma20": round(sma20, 2),
        "sma50": round(sma50, 2),
        "sma200": round(sma200, 2),
        "rsi14": round(rsi, 1),
        "return_5d_pct": round(five_day_return, 1),
        "rebound_pct": round(max(rebound, weekly_rebound), 1),
        "volume_ratio": round(volume_ratio, 1),
        "support": round(weekly_support, 2),
        "sell_below": round(recent_support * 0.98, 2),
        "status": status,
    }


def main():
    kite = create_zerodha_client(load_settings())
    symbols = load_symbols()
    portfolio = (
        load_workbook(PORTFOLIO, data_only=True, read_only=True)["Portfolio Review"]
        if PORTFOLIO.exists()
        else None
    )
    held_symbols = (
        {
            str(row[0]).strip().upper()
            for row in portfolio.iter_rows(min_row=2, values_only=True)
            if row[0]
        }
        if portfolio
        else set()
    )
    symbols = {
        symbol: segment
        for symbol, segment in symbols.items()
        if symbol not in held_symbols
    }
    instruments = {item["tradingsymbol"]: item for item in kite.instruments("NSE")}
    results = []
    for index, (symbol, segment) in enumerate(symbols.items(), 1):
        instrument = instruments.get(symbol)
        if instrument:
            try:
                result = analyse(kite, instrument)
                if result:
                    result["cap_segment"] = segment
                    results.append(result)
            except Exception as exc:
                print(f"WARNING: {symbol}: {exc}")
        if index % 25 == 0:
            print(f"Progress: {index}/{len(symbols)}")
        time.sleep(0.35)
    fields = [
        "symbol",
        "cap_segment",
        "status",
        "price",
        "low52",
        "from_low_pct",
        "support",
        "sell_below",
        "sma20",
        "sma50",
        "sma200",
        "rsi14",
        "return_5d_pct",
        "rebound_pct",
        "volume_ratio",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(
            sorted(
                results,
                key=lambda item: (
                    item["cap_segment"],
                    item["status"] != "CANDIDATE",
                    -item["return_5d_pct"],
                ),
            )
        )
    print(f"Saved {len(results)} watch/candidate rows to {OUTPUT}")
    for item in results:
        print("|".join(str(item[field]) for field in fields))


if __name__ == "__main__":
    main()
