"""Build an Excel report from the completed rebound scan and portfolio review."""

from pathlib import Path
import csv
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent
SCAN = ROOT / "rebound_stock_candidates.csv"
PORTFOLIO = ROOT / "portfolio_recovery_plan.xlsx"
OUTPUT = ROOT / "rebound_signal_report.xlsx"
NAVY, DARK, WHITE = "1F4E78", "17365D", "FFFFFF"
RED, YELLOW, GREEN, BLUE = "FCE4D6", "FFF2CC", "E2F0D9", "D9EAF7"
THIN = Side(style="thin", color="D9E1F2")


def header(ws, row, values):
    for col, value in enumerate(values, 1):
        cell = ws.cell(row, col, value)
        cell.font = Font(bold=True, color=WHITE)
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.alignment = Alignment(horizontal="center", wrap_text=True)


def load_scan():
    with SCAN.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def add_levels(item):
    price = float(item["price"])
    support = float(item["low52"])
    buy = max(float(item["sma20"]), price * 1.03)
    sell = round(support * 0.98, 2)
    risk = buy - sell
    return (
        round(support, 2),
        round(buy, 2),
        sell,
        round(buy + 1.5 * risk, 2),
        round(buy + 2.5 * risk, 2),
    )


def main():
    scan = load_scan()
    portfolio = load_workbook(PORTFOLIO, data_only=True, read_only=True)[
        "Portfolio Review"
    ]
    held = {
        str(row[0]).strip().upper(): row
        for row in portfolio.iter_rows(min_row=2, values_only=True)
        if row[0]
    }
    rows = []
    for item in scan:
        support, buy, sell, target1, target2 = add_levels(item)
        rows.append(
            {
                **item,
                "support": support,
                "buy": buy,
                "sell": sell,
                "target1": target1,
                "target2": target2,
                "source": "Full cap scan",
            }
        )
    examples = [
        {
            "symbol": "VBL",
            "cap_segment": "LARGE",
            "status": "BUY WATCH - 52W SUPPORT REBOUND",
            "price": 409.50,
            "low52": 382.20,
            "support": 382.20,
            "buy": 418.00,
            "sell": 382.00,
            "target1": 472.00,
            "target2": 508.00,
            "sma20": 417.54,
            "sma50": 439.66,
            "sma200": 467.76,
            "rsi14": 32.2,
            "return_5d_pct": 0.9,
            "rebound_pct": 2.3,
            "volume_ratio": 0.4,
            "source": "User chart example",
        },
        {
            "symbol": "TALBROAUTO",
            "cap_segment": "UNCLASSIFIED",
            "status": "BUY WATCH - RISING SUPPORT",
            "price": 421.00,
            "low52": 224.05,
            "support": 400.00,
            "buy": 443.50,
            "sell": 400.00,
            "target1": 508.75,
            "target2": 552.25,
            "sma20": 415.55,
            "sma50": 411.99,
            "sma200": 323.10,
            "rsi14": 55.0,
            "return_5d_pct": 2.5,
            "rebound_pct": 5.0,
            "volume_ratio": 1.0,
            "source": "User chart example",
        },
    ]
    example_symbols = {item["symbol"] for item in examples}
    rows = [item for item in rows if item["symbol"] not in example_symbols]
    rows.extend(examples)
    held_symbols = set(held)
    rows = [item for item in rows if item["symbol"] not in held_symbols]
    rows = [item for item in rows if "BUY WATCH" in item["status"]]
    wb = Workbook()
    overview = wb.active
    overview.title = "Overview"
    overview["A1"] = "New Stock Support, Buy and Target Report"
    overview.merge_cells("A1:F1")
    overview["A1"].font = Font(size=16, bold=True, color=WHITE)
    overview["A1"].fill = PatternFill("solid", fgColor=NAVY)
    notes = [
        (
            "1. Find a stock",
            "Use Buy Watch. Start with the rows marked Weekly Base Rebound or Rising Support.",
        ),
        (
            "2. Wait for buy",
            "Do not buy at the current price automatically. Wait until price reaches Buy Confirmation.",
        ),
        (
            "3. Manage the trade",
            "Support is the chart base. Target 1 is the first booking level; Target 2 is the next level.",
        ),
        (
            "How targets work",
            "Target 1 = 1.5R and Target 2 = 2.5R, where R is Buy Confirmation minus the support-based risk level.",
        ),
        (
            "Scan scope",
            "New stocks only: 488 large/mid/small-cap symbols scanned; current portfolio symbols excluded.",
        ),
        (
            "Important",
            "Technical screening is not a guaranteed signal or personalized financial advice.",
        ),
    ]
    for row, (label, value) in enumerate(notes, 3):
        overview.cell(row, 1, label).font = Font(bold=True)
        overview.cell(row, 2, value)
        overview.merge_cells(start_row=row, start_column=2, end_row=row, end_column=6)
        overview.cell(row, 2).alignment = Alignment(wrap_text=True)
    watch = wb.create_sheet("Buy Watch")
    columns = [
        "Stock",
        "Cap Segment",
        "Pattern",
        "Current Price",
        "Support",
        "Buy Confirmation",
        "Target 1",
        "Target 2",
        "52W Low",
        "20D Avg",
        "50D Avg",
        "200D Avg",
        "RSI",
        "5D Return %",
        "Rebound %",
        "Source",
    ]
    header(watch, 1, columns)
    for row, item in enumerate(
        [
            x
            for x in rows
            if "BUY WATCH" in x["status"] or x["status"] in ("CANDIDATE",)
        ],
        2,
    ):
        values = [
            item["symbol"],
            item["cap_segment"],
            item["status"],
            float(item["price"]),
            item["support"],
            item["buy"],
            item["target1"],
            item["target2"],
            float(item["low52"]),
            float(item["sma20"]),
            float(item["sma50"]),
            float(item["sma200"]),
            float(item["rsi14"]),
            float(item["return_5d_pct"]),
            float(item["rebound_pct"]),
            item["source"],
        ]
        for col, value in enumerate(values, 1):
            watch.cell(row, col, value).border = Border(bottom=THIN)
            watch.cell(row, col).alignment = Alignment(vertical="top", wrap_text=True)
        watch.cell(row, 3).fill = PatternFill("solid", fgColor=GREEN)
        watch.cell(row, 5).fill = PatternFill("solid", fgColor=YELLOW)
        watch.cell(row, 6).fill = PatternFill("solid", fgColor=BLUE)
        watch.cell(row, 7).fill = PatternFill("solid", fgColor=GREEN)
        watch.cell(row, 8).fill = PatternFill("solid", fgColor=GREEN)
        for col in range(4, 13):
            watch.cell(row, col).number_format = "INR #,##0.00"
        for col in (13, 14, 15):
            watch.cell(row, col).number_format = "0.0"
    watch.auto_filter.ref = f"A1:P{max(1, watch.max_row)}"
    watch.freeze_panes = "A2"
    watch.row_dimensions[1].height = 38
    compare = wb.create_sheet("New Stock Signals")
    header(
        compare,
        1,
        [
            "Stock",
            "Cap Segment",
            "Pattern",
            "Current Price",
            "Support",
            "Buy Confirmation",
            "Target 1",
            "Target 2",
            "Comment",
        ],
    )
    for row, item in enumerate(rows, 2):
        values = [
            item["symbol"],
            item["cap_segment"],
            item["status"],
            float(item["price"]),
            item["support"],
            item["buy"],
            item["target1"],
            item["target2"],
            "New-stock candidate; review separately from current holdings.",
        ]
        for col, value in enumerate(values, 1):
            compare.cell(row, col, value).border = Border(bottom=THIN)
            compare.cell(row, col).alignment = Alignment(vertical="top", wrap_text=True)
        compare.cell(row, 3).fill = PatternFill(
            "solid", fgColor=GREEN if "BUY" in item["status"] else BLUE
        )
        compare.cell(row, 5).fill = PatternFill("solid", fgColor=YELLOW)
        compare.cell(row, 6).fill = PatternFill("solid", fgColor=BLUE)
        compare.cell(row, 7).fill = PatternFill("solid", fgColor=GREEN)
        compare.cell(row, 8).fill = PatternFill("solid", fgColor=GREEN)
        for col in (4, 5, 6, 7, 8):
            compare.cell(row, col).number_format = "INR #,##0.00"
    compare.auto_filter.ref = f"A1:I{max(1, compare.max_row)}"
    compare.freeze_panes = "A2"
    compare.row_dimensions[1].height = 38
    for ws in wb.worksheets:
        ws.sheet_view.showGridLines = False
        ws.freeze_panes = ws.freeze_panes or "A2"
    watch_widths = [15, 14, 28, 15, 15, 18, 15, 15, 15, 15, 15, 15, 10, 13, 13, 20]
    compare_widths = [15, 14, 28, 15, 15, 18, 15, 15, 52]
    for col, width in enumerate(watch_widths, 1):
        watch.column_dimensions[get_column_letter(col)].width = width
    for col, width in enumerate(compare_widths, 1):
        compare.column_dimensions[get_column_letter(col)].width = width
    overview.column_dimensions["A"].width = 28
    overview.column_dimensions["B"].width = 90
    wb.save(OUTPUT)
    print(f"Saved {OUTPUT} with {len(rows)} new-stock rows")


if __name__ == "__main__":
    main()
