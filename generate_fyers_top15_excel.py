from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

rows = [
    ["Rank", "Strategy Name", "Type", "Why it fits", "Risk Level", "Backtest Status", "Recommendation"],
    [1, "NIFTY 500 Top Gainers Intraday Basket", "Intraday basket", "Closest match to the current saved automation and strategy logic; uses momentum leaders with fixed basket risk.", "Medium", "Not validated in current FYERS backtest flow", "Primary candidate to keep"],
    [2, "Intraday Breakout Momentum Basket", "Intraday", "High-probability momentum entries when strong price expansion occurs in liquid stocks.", "Medium-High", "Likely workable with strict filters", "Strong backup option"],
    [3, "Opening Range Breakout", "Intraday", "Works well for strong first-hour momentum and high volume sessions.", "Medium", "Generally supported if rules stay simple", "Good shortlist item"],
    [4, "VWAP Reclaim / Trend Resumption", "Intraday", "Useful for continuation trades after a pullback and re-acceptance of trend.", "Medium", "Usually manageable with clear risk rules", "Good risk-controlled option"],
    [5, "Relative Strength Leaders", "Basket / momentum", "Selects top-performing names relative to market and sector, suitable for baskets.", "Medium", "Works best in liquid names", "Good basket style"],
    [6, "Pullback Continuation", "Intraday", "Better risk control than pure breakout; enters after a controlled retracement.", "Medium", "Good fit for simple automation", "Strong risk-managed option"],
    [7, "Gap-Up Continuation", "Intraday", "Useful when market opens with strong directional gaps and momentum remains intact.", "Medium-High", "Needs strict volume confirmation", "Use with stop discipline"],
    [8, "Sector Momentum Rotation", "Basket / sector", "Good when one sector leads the market and multiple names move together.", "Medium", "Works well if sector filter is simple", "Useful basket rotation"],
    [9, "High-Volume Breakout", "Intraday", "Fast-moving names with strong participation can produce clean moves.", "High", "Only for highly liquid stocks", "Use with strict liquidity filter"],
    [10, "Reversal from Support", "Intraday", "Good for lower-risk re-entry setups after a pullback to support.", "Medium", "Works when support is clear", "Good second-tier option"],
    [11, "Bullish Engulfing Trend Continuation", "Intraday", "Simple rule-based continuation setup with clear visual trigger.", "Medium", "Easy to automate if filters stay basic", "Good for controlled automation"],
    [12, "Oversold Rebound Basket", "Intraday / rebound", "Captures recovery plays after short-term selling pressure wanes.", "Medium-High", "Useful but more volatile", "Good secondary basket idea"],
    [13, "Morning Momentum Spike", "Intraday", "Best for opening session momentum; can work well with fixed targets and losses.", "Medium-High", "Useful if entry timing is strict", "Good early-session choice"],
    [14, "Trend-Following Pullback", "Intraday / trend", "Lower-noise approach than chasing all breakouts, with better risk control.", "Medium", "Suitable if trend filter is intact", "Good guardrail setup"],
    [15, "Low-Risk Breakout with Filter", "Intraday", "Best for quality over quantity; simple validation reduces false entries.", "Low-Medium", "Good operationally", "Best for disciplined execution"],
]

wb = Workbook()
ws = wb.active
ws.title = "Top15_Automations"

for row in rows:
    ws.append(row)

header_fill = PatternFill("solid", fgColor="D9EAF7")
for cell in ws[1]:
    cell.fill = header_fill
    cell.font = Font(bold=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")

for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=7):
    for cell in row:
        cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

for col in ws.columns:
    max_len = 0
    col_letter = get_column_letter(col[0].column)
    for cell in col:
        if cell.value is not None:
            max_len = max(max_len, len(str(cell.value)))
    ws.column_dimensions[col_letter].width = min(max_len + 3, 45)

ws.freeze_panes = "A2"
ws.auto_filter.ref = ws.dimensions

summary = wb.create_sheet("Summary")
summary["A1"] = "FYERS Top 15 Automation shortlist"
summary["A1"].font = Font(bold=True, size=14)
summary["A3"] = "Recommended primary setup"
summary["A3"].font = Font(bold=True)
summary["B3"] = "NIFTY 500 Top Gainers Intraday Basket"
summary["A4"] = "Best backup setups"
summary["A4"].font = Font(bold=True)
summary["B4"] = "Intraday Breakout Momentum Basket; VWAP Reclaim / Trend Resumption"
summary["A5"] = "Key caution"
summary["A5"].font = Font(bold=True)
summary["B5"] = "Avoid unsupported MTF / screener logic and do not enable launch until order-status issues are confirmed fixed"
summary["A7"] = "Status"
summary["A7"].font = Font(bold=True)
summary["B7"] = "Prepared for review"

for row in [1, 3, 4, 5, 7]:
    for col in ["A", "B"]:
        summary[f"{col}{row}"].alignment = Alignment(wrap_text=True)

summary.column_dimensions["A"].width = 24
summary.column_dimensions["B"].width = 80

file_path = "FYERS_Top15_Automations.xlsx"
wb.save(file_path)
print(f"Created workbook: {file_path}")
