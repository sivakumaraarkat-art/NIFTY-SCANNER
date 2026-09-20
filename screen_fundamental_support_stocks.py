"""Find new large/mid/small-cap stocks near 52-week support with fundamentals.

The project does not currently fetch verified fundamentals. Populate
fundamental_snapshot.csv from a trusted source before running this script.
"""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path
import time

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Side

from configuration.swing_trade_settings import load_settings
from zerodha_market_data.zerodha_connection import create_zerodha_client

ROOT = Path(__file__).resolve().parent
CAP_DIR = ROOT / "data" / "nse_cap_segments"
FUNDAMENTALS = ROOT / "fundamental_snapshot.csv"
FUNDAMENTALS_TEMPLATE = ROOT / "fundamental_snapshot_template.csv"
OUTPUT = ROOT / "fundamental_support_candidates.xlsx"
CAP_FILES = {
    "LARGE": "nifty100.csv",
    "MID": "nifty_midcap150.csv",
    "SMALL": "nifty_smallcap250.csv",
}
REQUIRED_COLUMNS = {
    "symbol",
    "revenue_growth_3y_pct",
    "profit_growth_3y_pct",
    "roe_pct",
    "debt_to_equity",
    "promoter_pledge_pct",
}


def load_cap_symbols() -> dict[str, str]:
    symbols: dict[str, str] = {}
    for segment, filename in CAP_FILES.items():
        with (CAP_DIR / filename).open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                symbol = str(row.get("symbol", "")).strip().upper()
                if symbol:
                    symbols[symbol] = segment
    return symbols


def load_fundamentals() -> dict[str, dict[str, float]]:
    if not FUNDAMENTALS.exists():
        if FUNDAMENTALS_TEMPLATE.exists():
            FUNDAMENTALS.write_text(
                FUNDAMENTALS_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8"
            )
            print(
                f"Created {FUNDAMENTALS.name} from template. Fill it with trusted data before trading."
            )
        else:
            raise FileNotFoundError(
                f"Missing {FUNDAMENTALS.name} and template file. "
                "Create fundamental_snapshot.csv from a trusted source."
            )
    with FUNDAMENTALS.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"Fundamental snapshot is missing columns: {sorted(missing)}"
            )
        result = {}
        for row in reader:
            symbol = str(row.get("symbol", "")).strip().upper()
            if not symbol:
                continue
            values: dict[str, float] = {}
            for key in REQUIRED_COLUMNS:
                if key == "symbol":
                    continue
                raw_value = row.get(key, "")
                if raw_value is None or str(raw_value).strip() == "":
                    continue
                try:
                    values[key] = float(raw_value)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Invalid fundamental value for {symbol}: {key}={raw_value!r}"
                    ) from exc
            if not values:
                continue
            result[symbol] = values
    return result


def fundamental_grade(values: dict[str, float]) -> str:
    checks = [
        values["revenue_growth_3y_pct"] >= 8,
        values["profit_growth_3y_pct"] >= 8,
        values["roe_pct"] >= 12,
        values["debt_to_equity"] <= 1.0,
        values["promoter_pledge_pct"] <= 5,
    ]
    return "GOOD" if sum(checks) >= 4 else "REVIEW"


def analyse_chart(kite, instrument: dict) -> dict | None:
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
    price = closes[-1]
    low52 = min(closes[-252:])
    sma20 = sum(closes[-20:]) / 20
    sma50 = sum(closes[-50:]) / 50
    weekly_lows = [min(lows[i : i + 5]) for i in range(0, len(lows) - 4, 5)]
    weekly_support = min(weekly_lows[-12:])
    weekly_rebound = (price / weekly_support - 1) * 100
    five_day_return = (price / closes[-6] - 1) * 100
    recent_support = min(closes[-20:])
    buy_confirmation = max(sma20, price * 1.03)
    sell_below = recent_support * 0.98
    if not (weekly_rebound <= 18 and weekly_rebound >= 4 and five_day_return >= 0):
        return None
    risk = buy_confirmation - sell_below
    return {
        "price": round(price, 2),
        "low52": round(low52, 2),
        "support": round(weekly_support, 2),
        "buy_confirmation": round(buy_confirmation, 2),
        "sell_below": round(sell_below, 2),
        "target1": round(buy_confirmation + 1.5 * risk, 2),
        "target2": round(buy_confirmation + 2.5 * risk, 2),
        "sma20": round(sma20, 2),
        "sma50": round(sma50, 2),
        "rebound_pct": round(weekly_rebound, 1),
    }


def write_workbook(rows: list[dict]) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Fundamental Support Stocks"
    headers = [
        "Stock",
        "Cap Segment",
        "Fundamental Grade",
        "Current Price",
        "52W Support",
        "Buy Confirmation",
        "Target 1",
        "Target 2",
        "Sell Below",
        "Revenue Growth 3Y %",
        "Profit Growth 3Y %",
        "ROE %",
        "Debt / Equity",
        "Promoter Pledge %",
        "Weekly Rebound %",
    ]
    for column, value in enumerate(headers, 1):
        cell = sheet.cell(1, column, value)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E78")
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
    for row_number, item in enumerate(rows, 2):
        values = [
            item["symbol"],
            item["cap_segment"],
            item["fundamental_grade"],
            item["price"],
            item["support"],
            item["buy_confirmation"],
            item["target1"],
            item["target2"],
            item["sell_below"],
            item["revenue_growth_3y_pct"],
            item["profit_growth_3y_pct"],
            item["roe_pct"],
            item["debt_to_equity"],
            item["promoter_pledge_pct"],
            item["rebound_pct"],
        ]
        for column, value in enumerate(values, 1):
            sheet.cell(row_number, column, value).alignment = Alignment(vertical="top")
        sheet.cell(row_number, 3).fill = PatternFill("solid", fgColor="E2F0D9")
        for column in range(4, 10):
            sheet.cell(row_number, column).number_format = "INR #,##0.00"
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:O{max(1, sheet.max_row)}"
    sheet["A{0}".format(sheet.max_row + 2)] = (
        "Only stocks with a GOOD fundamental grade are included. Verify the source data before trading."
    )
    sheet["A{0}".format(sheet.max_row)].alignment = Alignment(wrap_text=True)
    for column in range(1, 16):
        sheet.column_dimensions[chr(64 + column) if column <= 26 else "A"].width = 18
    workbook.save(OUTPUT)


def main() -> None:
    fundamentals = load_fundamentals()
    if not fundamentals:
        print(
            "No fundamental data available. Populate fundamental_snapshot.csv with trusted values before trading."
        )
        return

    symbols = load_cap_symbols()
    kite = create_zerodha_client(load_settings())
    portfolio = kite.holdings()
    held_symbols = {
        str(item.get("tradingsymbol", "")).strip().upper() for item in portfolio
    }
    instruments = {item["tradingsymbol"]: item for item in kite.instruments("NSE")}
    rows = []
    for index, (symbol, segment) in enumerate(symbols.items(), 1):
        if (
            symbol in held_symbols
            or symbol not in fundamentals
            or symbol not in instruments
        ):
            continue
        fundamentals_for_symbol = fundamentals[symbol]
        if fundamental_grade(fundamentals_for_symbol) != "GOOD":
            continue
        try:
            chart = analyse_chart(kite, instruments[symbol])
            if chart:
                rows.append(
                    {
                        "symbol": symbol,
                        "cap_segment": segment,
                        "fundamental_grade": "GOOD",
                        **fundamentals_for_symbol,
                        **chart,
                    }
                )
        except Exception as exc:
            print(f"WARNING: {symbol}: {exc}")
        if index % 25 == 0:
            print(f"Progress: {index}/{len(symbols)}")
        time.sleep(0.35)
    write_workbook(rows)
    print(f"Saved {len(rows)} new fundamentally screened support stocks to {OUTPUT}")


if __name__ == "__main__":
    main()
