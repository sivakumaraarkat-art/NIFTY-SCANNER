"""Refresh the Zerodha portfolio recovery workbook once per week."""

from datetime import date, timedelta
from pathlib import Path
import shutil
import time

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from configuration.swing_trade_settings import load_settings
from zerodha_market_data.zerodha_connection import create_zerodha_client

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "portfolio_recovery_plan.xlsx"
HISTORY_DIR = ROOT / "portfolio_history"
CURRENCY = "INR #,##0.00;[Red]-INR #,##0.00"
NAVY, DARK, WHITE = "1F4E78", "17365D", "FFFFFF"
RED, YELLOW, GREEN = "FCE4D6", "FFF2CC", "E2F0D9"
THIN = Side(style="thin", color="D9E1F2")


def archive_previous_workbook():
    """Archive the last report and return its path, if one exists."""
    if not OUTPUT.exists():
        return None
    HISTORY_DIR.mkdir(exist_ok=True)
    archived = HISTORY_DIR / f"portfolio_recovery_plan_{date.today().isoformat()}.xlsx"
    suffix = 2
    while archived.exists():
        archived = (
            HISTORY_DIR
            / f"portfolio_recovery_plan_{date.today().isoformat()}_{suffix}.xlsx"
        )
        suffix += 1
    shutil.copy2(OUTPUT, archived)
    return archived


def load_previous_records(path):
    """Read the prior Portfolio Review sheet into a symbol-keyed mapping."""
    if not path or not path.exists():
        return {}
    workbook = load_workbook(path, data_only=True, read_only=True)
    sheet = workbook["Portfolio Review"]
    records = {}
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        records[str(row[0]).strip().upper()] = {
            "quantity": row[1] or 0,
            "average": row[2] or 0,
            "current": row[3] or 0,
            "pnl": row[4] or 0,
            "pnl_pct": (row[5] or 0) * 100,
            "trend": row[8] or "UNKNOWN",
            "action": row[9] or "",
        }
    workbook.close()
    return records


def trend_for(kite, holding):
    token = holding.get("instrument_token")
    if not token:
        return "UNKNOWN"
    try:
        candles = kite.historical_data(
            token,
            (date.today() - timedelta(days=130)).isoformat(),
            date.today().isoformat(),
            "day",
            continuous=False,
            oi=False,
        )
        closes = [float(item["close"]) for item in candles]
        if len(closes) < 55:
            return "UNKNOWN"
        current = closes[-1]
        sma20 = sum(closes[-20:]) / 20
        sma50 = sum(closes[-50:]) / 50
        if current > sma20 > sma50:
            return "UP"
        if current < sma20 < sma50:
            return "DOWN"
        return "MIXED"
    except Exception as exc:
        print(f"WARNING: trend unavailable for {holding.get('tradingsymbol')}: {exc}")
        return "UNKNOWN"


def classify(pnl_pct, trend, symbol):
    high_risk = {"AKSHAR", "DELTACORP", "GTLINFRA", "MAHACORP", "SALASAR", "STANCAP"}
    add_levels = {
        "ASHOKLEY": "Above INR 171",
        "COALINDIA": "INR 410-417; support must hold",
        "IOC": "Above INR 136-139",
        "PCBL": "Above INR 322-324",
    }
    if symbol in high_risk or pnl_pct <= -60:
        return (
            "Exit review / no averaging",
            "Deep loss or high-risk position; review for gradual exit.",
            "Do not average",
        )
    if pnl_pct <= -35 and trend == "DOWN":
        return (
            "Reduce / no averaging",
            "Large loss with a continuing downtrend; reduce exposure.",
            "Do not average",
        )
    if symbol in add_levels:
        return (
            "Hold / gradual add",
            "Add in stages only after this price confirmation and a valid investment thesis.",
            add_levels[symbol],
        )
    if trend == "DOWN":
        return (
            "Hold / wait",
            "Hold only if the investment thesis remains valid; wait for trend recovery.",
            "Above 20-day and 50-day averages",
        )
    return (
        "Hold / wait",
        "Hold and review fundamentals, liquidity, news, and trend monthly.",
        "Only after confirmation",
    )


def style_header(ws, row, headers):
    for column, value in enumerate(headers, 1):
        cell = ws.cell(row, column, value)
        cell.font = Font(bold=True, color=WHITE)
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )


def build_workbook(records, previous_records, archived_path):
    wb = Workbook()
    summary = wb.active
    summary.title = "Summary"
    review = wb.create_sheet("Portfolio Review")
    average = wb.create_sheet("Averaging Calculator")
    plan = wb.create_sheet("Recovery Plan")
    diff = wb.create_sheet("Week-over-Week Diff")

    summary["A1"] = "Portfolio Recovery Summary"
    summary.merge_cells("A1:D1")
    summary["A1"].font = Font(size=16, bold=True, color=WHITE)
    summary["A1"].fill = PatternFill("solid", fgColor=NAVY)
    summary_rows = [
        ("Refresh date", date.today().isoformat()),
        ("Total holdings", f"=COUNTA('Portfolio Review'!A2:A{len(records)+1})"),
        ("Total invested", f"=SUM('Portfolio Review'!G2:G{len(records)+1})"),
        ("Current value", f"=SUM('Portfolio Review'!H2:H{len(records)+1})"),
        ("Total profit / loss", f"=SUM('Portfolio Review'!E2:E{len(records)+1})"),
        ("Recovery needed", "=B7/B5"),
        ("Cost-to-cost target", "=B5"),
    ]
    for row, (label, value) in enumerate(summary_rows, 3):
        summary.cell(row, 1, label).font = Font(bold=True)
        summary.cell(row, 2, value)
    for cell in ("B5", "B6", "B7", "B9"):
        summary[cell].number_format = CURRENCY
    summary["B8"].number_format = "0.00%"
    summary["A11"] = (
        "Use the Recovery Plan and Averaging Calculator sheets. This is a decision framework, not a guaranteed return."
    )
    summary.merge_cells("A11:D12")
    summary["A11"].alignment = Alignment(wrap_text=True, vertical="top")

    headers = [
        "Stock",
        "Quantity",
        "Average Price",
        "Current Price",
        "Profit / Loss",
        "Profit / Loss %",
        "Invested",
        "Current Value",
        "Trend",
        "Action",
        "Comment",
        "Review / Add Level",
    ]
    style_header(review, 1, headers)
    for row, item in enumerate(records, 2):
        values = [
            item["symbol"],
            item["quantity"],
            item["average"],
            item["current"],
            item["pnl"],
            item["pnl_pct"] / 100,
            item["invested"],
            item["value"],
            item["trend"],
            item["action"],
            item["comment"],
            item["level"],
        ]
        for column, value in enumerate(values, 1):
            cell = review.cell(row, column, value)
            cell.border = Border(bottom=THIN)
            cell.alignment = Alignment(vertical="top", wrap_text=column >= 10)
        for column in (3, 4, 5, 7, 8):
            review.cell(row, column).number_format = CURRENCY
        review.cell(row, 6).number_format = "0.00%"
        action = item["action"]
        review.cell(row, 10).fill = PatternFill(
            "solid",
            fgColor=(
                RED if "Exit" in action else YELLOW if "Reduce" in action else GREEN
            ),
        )
    review.freeze_panes = "A2"
    review.auto_filter.ref = f"A1:L{len(records)+1}"

    average_headers = [
        "Stock",
        "Existing Qty",
        "Existing Avg Price",
        "Current Price",
        "Existing Investment",
        "Extra Shares (input)",
        "Buy Price (input)",
        "New Total Qty",
        "New Average Price",
        "Recovery to Original Avg",
    ]
    style_header(average, 1, average_headers)
    average["A2"] = (
        "Enter extra shares and buy price in the yellow cells. Formulas calculate the new average price."
    )
    average.merge_cells("A2:J2")
    average["A2"].alignment = Alignment(wrap_text=True)
    for source_row, item in enumerate(records, 3):
        average.cell(source_row, 1, item["symbol"])
        average.cell(source_row, 2, item["quantity"])
        average.cell(source_row, 3, item["average"])
        average.cell(source_row, 4, item["current"])
        average.cell(source_row, 5, f"=B{source_row}*C{source_row}")
        average.cell(source_row, 6, 0)
        average.cell(source_row, 7, f"=D{source_row}")
        average.cell(source_row, 8, f"=B{source_row}+F{source_row}")
        average.cell(
            source_row,
            9,
            f"=IF(H{source_row}=0,0,(B{source_row}*C{source_row}+F{source_row}*G{source_row})/H{source_row})",
        )
        average.cell(
            source_row, 10, f"=IF(D{source_row}=0,0,(C{source_row}/D{source_row})-1)"
        )
        for column in (3, 4, 5, 7, 9):
            average.cell(source_row, column).number_format = CURRENCY
        average.cell(source_row, 10).number_format = "0.00%"
        average.cell(source_row, 6).fill = PatternFill("solid", fgColor=YELLOW)
        average.cell(source_row, 7).fill = PatternFill("solid", fgColor=YELLOW)
    average.freeze_panes = "A3"
    average.auto_filter.ref = f"A1:J{len(records)+2}"

    plan["A1"] = "Portfolio Recovery Plan"
    plan.merge_cells("A1:F1")
    plan["A1"].font = Font(size=18, bold=True, color=WHITE)
    plan["A1"].fill = PatternFill("solid", fgColor=NAVY)
    plan["A2"] = (
        "Protect remaining capital first; rebuild toward the original invested amount through stronger, confirmed positions."
    )
    plan.merge_cells("A2:F2")
    plan["A2"].alignment = Alignment(wrap_text=True)
    plan["A4"] = "Original invested amount"
    plan["B4"] = "='Summary'!B5"
    plan["A5"] = "Current portfolio value"
    plan["B5"] = "='Summary'!B6"
    plan["A6"] = "Current loss"
    plan["B6"] = "='Summary'!B7"
    plan["A7"] = "Recovery needed"
    plan["B7"] = "='Summary'!B8"
    plan["A8"] = "Cost-to-cost target"
    plan["B8"] = "='Summary'!B9"
    for row in range(4, 9):
        plan.cell(row, 1).font = Font(bold=True)
        plan.cell(row, 2).number_format = "0.00%" if row == 7 else CURRENCY
    plan["A10"] = "Milestone"
    plan["B10"] = "Portfolio target"
    plan["C10"] = "Purpose"
    plan["D10"] = "Status"
    style_header(
        plan, 10, ["Milestone", "Portfolio target", "Purpose", "Status", "", ""]
    )
    for row, (label, gain, purpose) in enumerate(
        [
            ("Stabilize", 0.05, "Stop further deterioration"),
            ("First recovery", 0.10, "Confirm discipline"),
            ("Mid recovery", 0.25, "Rebuild through stronger holdings"),
            ("Advanced recovery", 0.40, "Approach original capital"),
            ("Cost-to-cost", 0.4998, "Reach original invested amount"),
        ],
        11,
    ):
        plan.cell(row, 1, label)
        plan.cell(row, 2, f"='Summary'!B6*(1+{gain})")
        plan.cell(row, 2).number_format = CURRENCY
        plan.cell(row, 3, purpose)
        plan.cell(row, 4, "Not reached")
    plan["A18"] = "Rules"
    plan["A18"].font = Font(bold=True, color=WHITE)
    plan["A18"].fill = PatternFill("solid", fgColor=DARK)
    plan.merge_cells("A18:F18")
    rules = [
        "Do not average solely because a stock is below the original purchase price.",
        "Use staged buying only after price reclaims both the 20-day and 50-day trend averages.",
        "Keep approximately 8-10 holdings and limit each position to about 5%-8%.",
        "Review fundamentals, liquidity, news, and trend monthly.",
        "Recovery is not guaranteed; review decisions with a qualified financial adviser.",
    ]
    for row, text in enumerate(rules, 19):
        plan.cell(row, 1, f"{row-18}. {text}")
        plan.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
        plan.cell(row, 1).alignment = Alignment(wrap_text=True)

    diff["A1"] = "Week-over-Week Portfolio Diff"
    diff.merge_cells("A1:J1")
    diff["A1"].font = Font(size=16, bold=True, color=WHITE)
    diff["A1"].fill = PatternFill("solid", fgColor=NAVY)
    diff["A2"] = (
        f"Previous report: {archived_path.name if archived_path else 'None available'}"
    )
    diff.merge_cells("A2:J2")
    diff["A2"].alignment = Alignment(wrap_text=True)
    diff_headers = [
        "Stock",
        "Status",
        "Qty Change",
        "Price Change",
        "P&L Change",
        "P&L % Change",
        "Previous Trend",
        "Current Trend",
        "Previous Action",
        "Current Action",
    ]
    style_header(diff, 4, diff_headers)
    current_by_symbol = {item["symbol"]: item for item in records}
    symbols = sorted(set(previous_records) | set(current_by_symbol))
    for row, symbol in enumerate(symbols, 5):
        previous = previous_records.get(symbol)
        current = current_by_symbol.get(symbol)
        if previous is None:
            values = [
                symbol,
                "Added",
                current["quantity"],
                current["current"],
                current["pnl"],
                current["pnl_pct"] / 100,
                "-",
                current["trend"],
                "-",
                current["action"],
            ]
        elif current is None:
            values = [
                symbol,
                "Removed",
                -previous["quantity"],
                -previous["current"],
                -previous["pnl"],
                -previous["pnl_pct"] / 100,
                previous["trend"],
                "-",
                previous["action"],
                "-",
            ]
        else:
            values = [
                symbol,
                "Changed",
                current["quantity"] - previous["quantity"],
                current["current"] - previous["current"],
                current["pnl"] - previous["pnl"],
                (current["pnl_pct"] - previous["pnl_pct"]) / 100,
                previous["trend"],
                current["trend"],
                previous["action"],
                current["action"],
            ]
        for column, value in enumerate(values, 1):
            cell = diff.cell(row, column, value)
            cell.border = Border(bottom=THIN)
            cell.alignment = Alignment(vertical="top", wrap_text=column >= 7)
        for column in (4, 5):
            diff.cell(row, column).number_format = CURRENCY
        diff.cell(row, 6).number_format = "0.00%"
        if values[1] == "Added":
            diff.cell(row, 2).fill = PatternFill("solid", fgColor=GREEN)
        elif values[1] == "Removed":
            diff.cell(row, 2).fill = PatternFill("solid", fgColor=RED)
        else:
            diff.cell(row, 2).fill = PatternFill("solid", fgColor=YELLOW)
    if not previous_records:
        diff["A5"] = (
            "No previous workbook was available. This sheet will populate on the next weekly run."
        )
        diff.merge_cells("A5:J5")
    diff.freeze_panes = "A5"
    diff.auto_filter.ref = f"A4:J{max(4, len(symbols) + 4)}"

    for ws in wb.worksheets:
        ws.sheet_view.showGridLines = False
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is not None:
                    cell.alignment = Alignment(
                        vertical="top", wrap_text=cell.alignment.wrap_text
                    )
        ws.freeze_panes = ws.freeze_panes or "A2"
    widths = {
        "Summary": [30, 22, 18, 18],
        "Portfolio Review": [14, 11, 16, 16, 16, 15, 17, 17, 12, 25, 58, 30],
        "Averaging Calculator": [14, 14, 18, 16, 18, 21, 18, 15, 19, 22],
        "Recovery Plan": [28, 30, 42, 20, 20, 20],
        "Week-over-Week Diff": [14, 14, 14, 16, 16, 16, 16, 16, 30, 30],
    }
    for ws in wb.worksheets:
        for column, width in enumerate(widths[ws.title], 1):
            ws.column_dimensions[get_column_letter(column)].width = width
    wb.save(OUTPUT)


def main():
    kite = create_zerodha_client(load_settings())
    holdings = kite.holdings()
    if not holdings:
        raise RuntimeError(
            "Zerodha returned no holdings; workbook was not overwritten."
        )
    archived_path = archive_previous_workbook()
    previous_records = load_previous_records(archived_path)
    records = []
    for index, holding in enumerate(holdings, 1):
        symbol = str(holding.get("tradingsymbol", "")).strip().upper()
        quantity = int(float(holding.get("quantity") or 0))
        average = float(holding.get("average_price") or 0)
        current = float(holding.get("last_price") or 0)
        pnl = float(holding.get("pnl") or 0)
        pnl_pct = ((current - average) / average * 100) if average else 0
        trend = trend_for(kite, holding)
        action, comment, level = classify(pnl_pct, trend, symbol)
        records.append(
            {
                "symbol": symbol,
                "quantity": quantity,
                "average": average,
                "current": current,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "invested": quantity * average,
                "value": quantity * current,
                "trend": trend,
                "action": action,
                "comment": comment,
                "level": level,
            }
        )
        print(f"[{index:02d}/{len(holdings)}] {symbol}: {action}")
        time.sleep(0.35)
    build_workbook(records, previous_records, archived_path)
    print(f"Saved weekly recovery workbook: {OUTPUT}")


if __name__ == "__main__":
    main()
