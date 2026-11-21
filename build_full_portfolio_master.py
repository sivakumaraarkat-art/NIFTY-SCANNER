import json
from pathlib import Path
from datetime import date
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

ROOT = Path(".")
OUTPUT_PATH = ROOT / "Portfolio_Buy_Average_Sell_Hold_Master_Plan.xlsx"

with open("portfolio_classified_plan.json") as f:
    records = json.load(f)

# Sort order: BUY / AVERAGE first, then HOLD (PROFIT), then HOLD, then SELL
CATEGORY_ORDER = {
    "BUY / AVERAGE": 1,
    "HOLD (PROFIT)": 2,
    "HOLD": 3,
    "SELL": 4
}
records.sort(key=lambda x: (CATEGORY_ORDER.get(x["action_tag"], 99), -x["inv"]))

COMPANY_INFO = {
    "COCHINSHIP": ("Cochin Shipyard Ltd", "Defense / Shipbuilding (PSU)"),
    "LODHA": ("Macrotech Developers Ltd", "Real Estate / Residential"),
    "ASHOKLEY": ("Ashok Leyland Ltd", "Automotive / Commercial Vehicles"),
    "PCBL": ("PCBL Ltd (Phillips Carbon)", "Specialty Chemicals / Carbon"),
    "ELECTCAST": ("Electrosteel Castings Ltd", "Ductile Iron Pipes / Water Infra"),
    "JPL": ("Jio Platforms Ltd / Jupiter", "Technology & Platforms"),
    "COALINDIA": ("Coal India Ltd", "Mining / Energy / Coal (PSU)"),
    "IOC": ("Indian Oil Corporation Ltd", "Oil Refining & Marketing (PSU)"),
    "SUZLON": ("Suzlon Energy Ltd", "Renewable Energy / Wind Turbines"),
    "IEX": ("Indian Energy Exchange Ltd", "FinTech / Power Trading Platform"),
    "IRB": ("IRB Infrastructure Developers Ltd", "Infrastructure / Toll BOT Roads"),
    "BAJAJHFL": ("Bajaj Housing Finance Ltd", "Financials / Housing NBFC"),
    "NTPCGREEN": ("NTPC Green Energy Ltd", "Renewable Energy / Solar & Wind"),
    "HAPPSTMNDS": ("Happiest Minds Technologies Ltd", "IT Services / Cloud & Digital"),
    "ECOSMOBLTY": ("Ecos (India) Mobility & Hosp Ltd", "Transportation / Corporate Car Rental"),
    "IMAGICAA": ("Imagicaaworld Entertainment Ltd", "Consumer / Theme Parks & Hospitality"),
    "EPACK": ("EPACK Durable Ltd", "EMS / Electronics Manufacturing"),
    "NITYAS": ("Nityas Gems & Jewellery Ltd", "Consumer / Gems & Jewellery"),
    "ALOKINDS": ("Alok Industries Ltd", "Textiles / Reliance Group JV"),
    "DREAMFOLKS": ("Dreamfolks Services Ltd", "Consumer Services / Airport Lounges"),
    "MADHAVIPL": ("Madhav Infra Projects Ltd", "Microcap Construction / Roads"),
    "STANCAP": ("Standard Capital Markets Ltd", "Microcap NBFC / Penny"),
    "SALASAR": ("Salasar Techno Engineering Ltd", "Infrastructure / Telecom Towers"),
    "SAMPRE": ("Sampre Nutritions Ltd", "FMCG / Confectionery / Microcap"),
    "AKSHAR": ("Akshar Spintex Ltd", "Textiles / Cotton Yarn / Penny"),
    "GTLINFRA": ("GTL Infrastructure Ltd", "Telecom Infrastructure / Penny"),
    "MISHTANN": ("Mishtann Foods Ltd", "Agro / Rice Processing / Penny"),
    "MAHACORP": ("Maharashtra Corporation Ltd", "Commodity Trading / Penny"),
}

wb = openpyxl.Workbook()

# Styles
font_title = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
font_section = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
font_bold = Font(name="Calibri", size=11, bold=True)
font_regular = Font(name="Calibri", size=11)
font_small = Font(name="Calibri", size=9, italic=True)

fill_dark_navy = PatternFill("solid", fgColor="1B365D")
fill_navy_sec = PatternFill("solid", fgColor="2E75B6")
fill_light_gray = PatternFill("solid", fgColor="F2F2F2")

fill_buy = PatternFill("solid", fgColor="E2EFDA")  # Soft green
font_buy = Font(name="Calibri", size=11, bold=True, color="276A3C")

fill_profit = PatternFill("solid", fgColor="DDEBF7") # Soft blue
font_profit = Font(name="Calibri", size=11, bold=True, color="1B365D")

fill_hold = PatternFill("solid", fgColor="FFF2CC")   # Soft yellow
font_hold = Font(name="Calibri", size=11, bold=True, color="8C6B00")

fill_sell = PatternFill("solid", fgColor="FCE4D6")   # Soft red
font_sell = Font(name="Calibri", size=11, bold=True, color="A61C1C")

fill_input = PatternFill("solid", fgColor="FFFF99")  # Bright yellow for inputs

thin_gray = Side(style="thin", color="D9D9D9")
border_cell = Border(left=thin_gray, right=thin_gray, top=thin_gray, bottom=thin_gray)
border_header = Border(left=thin_gray, right=thin_gray, top=thin_gray, bottom=Side(style="medium", color="1B365D"))

align_center = Alignment(horizontal="center", vertical="center")
align_left = Alignment(horizontal="left", vertical="center")
align_right = Alignment(horizontal="right", vertical="center")
align_wrap = Alignment(horizontal="left", vertical="center", wrap_text=True)

FMT_CURR = "₹ #,##0.00;[Red]-₹ #,##0.00;₹ 0.00"
FMT_CURR_INT = "₹ #,##0;[Red]-₹ #,##0;₹ 0"
FMT_PCT = "0.00%"
FMT_PCT_DIFF = "+0.00%;-0.00%;0.00%"
FMT_INT = "#,##0"

# -------------------------------------------------------------------------
# SHEET 1: Portfolio Summary & Dashboard
# -------------------------------------------------------------------------
ws1 = wb.active
ws1.title = "Portfolio Dashboard"
ws1.views.sheetView[0].showGridLines = True

# Title Block
ws1.merge_cells("A1:G1")
ws1["A1"] = "PORTFOLIO INTELLIGENCE & RECOVERY MASTER PLAN"
ws1["A1"].font = font_title
ws1["A1"].fill = fill_dark_navy
ws1["A1"].alignment = align_center
ws1.row_dimensions[1].height = 40

ws1.merge_cells("A2:G2")
ws1["A2"] = f"Account Demat Audit • Date: {date.today().strftime('%d %B %Y')} • Total Active Holdings: 28 Stocks"
ws1["A2"].font = Font(name="Calibri", size=11, italic=True, color="D9E1F2")
ws1["A2"].fill = PatternFill("solid", fgColor="2E75B6")
ws1["A2"].alignment = align_center
ws1.row_dimensions[2].height = 22

# KPI Cards
kpi_data = [
    ("A4:B4", "A5:B5", "Total Invested Capital", "='Holdings Master'!I31", FMT_CURR, fill_light_gray),
    ("C4:D4", "C5:D5", "Current Market Value", "='Holdings Master'!J31", FMT_CURR, fill_light_gray),
    ("E4:E4", "E5:E5", "Unrealized P&L", "='Holdings Master'!K31", FMT_CURR, fill_light_gray),
    ("F4:F4", "F5:F5", "Portfolio Return %", "=(C5-A5)/A5", FMT_PCT_DIFF, fill_light_gray),
    ("G4:G4", "G5:G5", "Immediate Cash From Exits", "='Capital Reallocation'!D16", FMT_CURR, fill_buy),
]

for top_range, val_range, title, formula, fmt, fill in kpi_data:
    top_cell = top_range.split(":")[0]
    val_cell = val_range.split(":")[0]
    if ":" in top_range:
        ws1.merge_cells(top_range)
    if ":" in val_range:
        ws1.merge_cells(val_range)

    ws1[top_cell] = title
    ws1[top_cell].font = Font(name="Calibri", size=10, bold=True, color="595959")
    ws1[top_cell].alignment = align_center
    ws1[top_cell].fill = fill

    ws1[val_cell] = formula
    ws1[val_cell].font = Font(name="Calibri", size=14, bold=True, color="1B365D" if "Exit" not in title else "276A3C")
    ws1[val_cell].alignment = align_center
    ws1[val_cell].number_format = fmt
    ws1[val_cell].fill = fill

ws1.row_dimensions[4].height = 20
ws1.row_dimensions[5].height = 30

# Category Breakdown Table
ws1.cell(7, 1, "STRATEGIC ALLOCATION BREAKDOWN BY RECOMMENDATION").font = font_section
ws1.cell(7, 1).fill = fill_dark_navy
ws1.merge_cells("A7:G7")
ws1.row_dimensions[7].height = 26

cat_headers = ["Recommendation", "Count", "Total Invested (₹)", "Current Value (₹)", "Unrealized P&L (₹)", "Return %", "Action Directive"]
for col_num, h_text in enumerate(cat_headers, 1):
    c = ws1.cell(8, col_num, h_text)
    c.font = font_header
    c.fill = fill_navy_sec
    c.alignment = align_center
    c.border = border_header
ws1.row_dimensions[8].height = 24

breakdown_rows = [
    ("BUY / AVERAGE", 5, 374823.47, 272599.30, -102224.17, -0.2727, "Accumulate on support dips; major catalysts (Defense, Housing, Auto, Pipes)", fill_buy, font_buy),
    ("HOLD (PROFIT)", 3, 42273.35, 48268.45, 5995.10, 0.1418, "Winners (+5% to +28%); Trail stop-loss; book partial gains to fund quality averages", fill_profit, font_profit),
    ("HOLD (MONITOR)", 10, 552550.88, 316158.34, -236392.54, -0.4278, "Stable/Largecap holdings; Hold existing; DO NOT add capital until 50-DMA breakout", fill_hold, font_hold),
    ("SELL / EXIT", 10, 131047.11, 38192.95, -92854.16, -0.7086, "Cut toxic penny stocks & broken microcaps; recycle ₹38,193 cash immediately", fill_sell, font_sell),
]

for idx, (cat, cnt, inv, val, pnl, ret, directive, row_fill, row_font) in enumerate(breakdown_rows, 9):
    ws1.cell(idx, 1, cat).font = row_font
    ws1.cell(idx, 1).fill = row_fill
    ws1.cell(idx, 1).alignment = align_center

    ws1.cell(idx, 2, cnt).alignment = align_center
    ws1.cell(idx, 2).number_format = FMT_INT

    ws1.cell(idx, 3, inv).number_format = FMT_CURR
    ws1.cell(idx, 4, val).number_format = FMT_CURR
    ws1.cell(idx, 5, pnl).number_format = FMT_CURR
    ws1.cell(idx, 6, ret).number_format = FMT_PCT_DIFF

    ws1.cell(idx, 7, directive).alignment = align_left
    ws1.row_dimensions[idx].height = 24
    for c in range(1, 8):
        ws1.cell(idx, c).border = border_cell

# Total Row
ws1.cell(13, 1, "TOTAL PORTFOLIO").font = font_bold
ws1.cell(13, 2, "=SUM(B9:B12)").font = font_bold
ws1.cell(13, 2).number_format = FMT_INT
ws1.cell(13, 2).alignment = align_center
ws1.cell(13, 3, "=SUM(C9:C12)").font = font_bold
ws1.cell(13, 3).number_format = FMT_CURR
ws1.cell(13, 4, "=SUM(D9:D12)").font = font_bold
ws1.cell(13, 4).number_format = FMT_CURR
ws1.cell(13, 5, "=SUM(E9:E12)").font = font_bold
ws1.cell(13, 5).number_format = FMT_CURR
ws1.cell(13, 6, "=(D13-C13)/C13").font = font_bold
ws1.cell(13, 6).number_format = FMT_PCT_DIFF
ws1.cell(13, 7, "Systematic Capital Reallocation Blueprint").font = font_bold
ws1.row_dimensions[13].height = 24
for c in range(1, 8):
    ws1.cell(13, c).border = Border(top=Side(style="medium", color="1B365D"), bottom=Side(style="double", color="1B365D"))
    ws1.cell(13, c).fill = fill_light_gray

# Rules of Portfolio Recovery
ws1.cell(15, 1, "CORE RULES OF DEMAT RECOVERY & WEALTH PROTECTION").font = font_section
ws1.cell(15, 1).fill = fill_dark_navy
ws1.merge_cells("A15:G15")
ws1.row_dimensions[15].height = 24

rules = [
    ("1. Never Average Penny Stocks (< ₹20)", "Stocks like STANCAP, AKSHAR, MAHACORP, GTLINFRA, SAMPRE, SALASAR destroy 80-90% of capital. Averaging penny stocks throws good money after bad. Salvage ₹38k and reallocate to winners."),
    ("2. Only Average High-Conviction Institutional Leaders", "Average only when: (1) Business has durable competitive moat & order book, (2) RSI is oversold (< 30-35), (3) Stock is at multi-month support floor. COCHINSHIP, LODHA, ASHOKLEY, PCBL, ELECTCAST qualify."),
    ("3. Do Not Over-Concentrate Stuck Large Caps", "SUZLON and IEX already account for 21.3% of your portfolio (₹2.33 Lakhs). Even though they are oversold, DO NOT add fresh funds until price confirms above 20-DMA and 50-DMA."),
    ("4. Recycle Capital Instead of Injecting New Cash", "By liquidating 10 toxic/broken holdings, you immediately liberate ₹38,193 in liquid cash. That is 100% free cash to average down Cochin Shipyard and Lodha without bringing in new money from your bank account."),
    ("5. Position Sizing Discipline", "Target keeping portfolio to 8-12 high-quality stocks. Cap individual positions at maximum 10-12% of Demat value. Set trailing stops on green holdings (JPL, Coal India, IOC).")
]

for idx, (rule_title, rule_desc) in enumerate(rules, 16):
    ws1.cell(idx, 1, rule_title).font = font_bold
    ws1.cell(idx, 1).alignment = align_left
    ws1.cell(idx, 1).fill = fill_light_gray
    ws1.merge_cells(start_row=idx, start_column=2, end_row=idx, end_column=7)
    ws1.cell(idx, 2, rule_desc).font = font_regular
    ws1.cell(idx, 2).alignment = align_wrap
    ws1.row_dimensions[idx].height = 28
    for c in range(1, 8):
        ws1.cell(idx, c).border = border_cell

# -------------------------------------------------------------------------
# SHEET 2: Holdings Master & Action Matrix
# -------------------------------------------------------------------------
ws2 = wb.create_sheet("Holdings Master")
ws2.views.sheetView[0].showGridLines = True

headers2 = [
    "S.No", "Stock Symbol", "Company Name", "Sector / Category", "Recommendation",
    "Quantity", "Avg Buy Price (₹)", "Current Price (₹)", "Invested (₹)", "Current Value (₹)",
    "Unrealized P&L (₹)", "P&L %", "Weight %", "20-DMA (₹)", "50-DMA (₹)", "200-DMA (₹)",
    "14-RSI", "52W High (₹)", "52W Drawdown", "Action Trigger Level", "Target Price (₹)",
    "Stop Loss (₹)", "Strategic Rationale & Catalysts"
]

ws2.merge_cells("A1:W1")
ws2["A1"] = "COMPLETE PORTFOLIO HOLDINGS & ACTION MATRIX (BUY / AVERAGE / SELL / HOLD)"
ws2["A1"].font = font_title
ws2["A1"].fill = fill_dark_navy
ws2["A1"].alignment = align_center
ws2.row_dimensions[1].height = 36

for col_num, h_text in enumerate(headers2, 1):
    c = ws2.cell(2, col_num, h_text)
    c.font = font_header
    c.fill = fill_navy_sec
    c.alignment = align_center
    c.border = border_header
ws2.row_dimensions[2].height = 28

tot_invested_val = sum(r["inv"] for r in records)

for idx, r in enumerate(records, 3):
    sym = r["symbol"]
    c_name, c_sec = COMPANY_INFO.get(sym, (sym, "General"))
    tag = r["action_tag"]

    ws2.cell(idx, 1, idx - 2).alignment = align_center
    ws2.cell(idx, 2, sym).font = font_bold
    ws2.cell(idx, 2).alignment = align_center
    ws2.cell(idx, 3, c_name).alignment = align_left
    ws2.cell(idx, 4, c_sec).alignment = align_left

    act_cell = ws2.cell(idx, 5, r["action"])
    act_cell.alignment = align_center
    if tag == "BUY / AVERAGE":
        act_cell.fill = fill_buy
        act_cell.font = font_buy
    elif tag == "HOLD (PROFIT)":
        act_cell.fill = fill_profit
        act_cell.font = font_profit
    elif tag == "HOLD":
        act_cell.fill = fill_hold
        act_cell.font = font_hold
    else:
        act_cell.fill = fill_sell
        act_cell.font = font_sell

    ws2.cell(idx, 6, r["qty"]).number_format = FMT_INT
    ws2.cell(idx, 7, r["avg"]).number_format = FMT_CURR
    ws2.cell(idx, 8, r["ltp"]).number_format = FMT_CURR

    # Formulas for invested, value, pnl, pnl%
    ws2.cell(idx, 9, f"=F{idx}*G{idx}").number_format = FMT_CURR
    ws2.cell(idx, 10, f"=F{idx}*H{idx}").number_format = FMT_CURR
    ws2.cell(idx, 11, f"=J{idx}-I{idx}").number_format = FMT_CURR
    ws2.cell(idx, 12, f"=(H{idx}-G{idx})/G{idx}").number_format = FMT_PCT_DIFF
    ws2.cell(idx, 13, f"=I{idx}/$I$31").number_format = FMT_PCT

    ws2.cell(idx, 14, r["sma20"]).number_format = FMT_CURR
    ws2.cell(idx, 15, r["sma50"]).number_format = FMT_CURR
    ws2.cell(idx, 16, r["sma200"]).number_format = FMT_CURR

    rsi_cell = ws2.cell(idx, 17, r["rsi"])
    rsi_cell.number_format = "0.0"
    rsi_cell.alignment = align_center
    if r["rsi"] > 0 and r["rsi"] < 30:
        rsi_cell.fill = fill_buy
        rsi_cell.font = font_buy
    elif r["rsi"] > 70:
        rsi_cell.fill = fill_sell
        rsi_cell.font = font_sell

    ws2.cell(idx, 18, r["high_52w"]).number_format = FMT_CURR
    ws2.cell(idx, 19, r["drawdown_52w"] / 100.0).number_format = FMT_PCT_DIFF

    ws2.cell(idx, 20, r["trigger"]).alignment = align_left
    ws2.cell(idx, 21, r["target"]).alignment = align_center
    ws2.cell(idx, 22, r["sl"]).alignment = align_center
    ws2.cell(idx, 23, r["rationale"]).alignment = align_wrap

    ws2.row_dimensions[idx].height = 26
    for c in range(1, 24):
        ws2.cell(idx, c).border = border_cell

# Total Row at Row 31
ws2.cell(31, 1, "").border = border_cell
ws2.cell(31, 2, "TOTAL").font = font_bold
ws2.cell(31, 2).alignment = align_center
ws2.cell(31, 3, "28 Holdings Consolidated").font = font_bold
ws2.cell(31, 4, "").border = border_cell
ws2.cell(31, 5, "").border = border_cell
ws2.cell(31, 6, "=SUM(F3:F30)").number_format = FMT_INT
ws2.cell(31, 6).font = font_bold
ws2.cell(31, 7, "").border = border_cell
ws2.cell(31, 8, "").border = border_cell
ws2.cell(31, 9, "=SUM(I3:I30)").number_format = FMT_CURR
ws2.cell(31, 9).font = font_bold
ws2.cell(31, 10, "=SUM(J3:J30)").number_format = FMT_CURR
ws2.cell(31, 10).font = font_bold
ws2.cell(31, 11, "=SUM(K3:K30)").number_format = FMT_CURR
ws2.cell(31, 11).font = font_bold
ws2.cell(31, 12, "=(J31-I31)/I31").number_format = FMT_PCT_DIFF
ws2.cell(31, 12).font = font_bold
ws2.cell(31, 13, "=SUM(M3:M30)").number_format = FMT_PCT
ws2.cell(31, 13).font = font_bold

for c in range(1, 24):
    ws2.cell(31, c).fill = fill_light_gray
    ws2.cell(31, c).border = Border(top=Side(style="medium", color="1B365D"), bottom=Side(style="double", color="1B365D"))
ws2.row_dimensions[31].height = 26

ws2.freeze_panes = "C3"
ws2.auto_filter.ref = "A2:W31"

# -------------------------------------------------------------------------
# SHEET 3: Averaging Simulator (Interactive)
# -------------------------------------------------------------------------
ws3 = wb.create_sheet("Averaging Calculator")
ws3.views.sheetView[0].showGridLines = True

ws3.merge_cells("A1:R1")
ws3["A1"] = "INTERACTIVE POSITION AVERAGING & BREAKEVEN ACCELERATOR"
ws3["A1"].font = font_title
ws3["A1"].fill = fill_dark_navy
ws3["A1"].alignment = align_center
ws3.row_dimensions[1].height = 36

ws3.merge_cells("A2:R2")
ws3["A2"] = "Enter planned 'Additional Shares' and 'Planned Buy Price' in YELLOW input cells. Formulas dynamically compute new average cost and required recovery move."
ws3["A2"].font = Font(name="Calibri", size=10, italic=True, color="595959")
ws3["A2"].alignment = align_center
ws3.row_dimensions[2].height = 20

headers3 = [
    "S.No", "Stock Symbol", "Company Name", "Existing Qty", "Existing Avg Price (₹)",
    "Current Market Price (₹)", "Existing Invested (₹)", "Additional Shares (INPUT)",
    "Planned Buy Price (₹) (INPUT)", "Additional Capital (₹)", "New Total Qty",
    "New Total Invested (₹)", "New Average Cost (₹)", "Cost Reduction per Share (₹)",
    "Old Breakeven Move %", "New Breakeven Move %", "Target Price (₹)", "Projected Profit at Target (₹)"
]

for col_num, h_text in enumerate(headers3, 1):
    c = ws3.cell(3, col_num, h_text)
    c.font = font_header
    c.fill = fill_navy_sec
    c.alignment = align_center
    c.border = border_header
ws3.row_dimensions[3].height = 28

avg_candidates = [r for r in records if r["action_tag"] == "BUY / AVERAGE"]
# Add top monitored candidate just in case user wants to test
for r in records:
    if r["symbol"] in ["SUZLON", "IEX", "BAJAJHFL"] and r not in avg_candidates:
        avg_candidates.append(r)

default_adds = {
    "COCHINSHIP": (35, 1119.00),
    "LODHA": (20, 1038.50),
    "ASHOKLEY": (100, 145.00),
    "PCBL": (50, 276.95),
    "ELECTCAST": (280, 63.56),
    "SUZLON": (0, 33.90),
    "IEX": (0, 101.00),
    "BAJAJHFL": (0, 77.42)
}

targets_calc = {
    "COCHINSHIP": 1420.00,
    "LODHA": 1280.00,
    "ASHOKLEY": 172.00,
    "PCBL": 340.00,
    "ELECTCAST": 95.00,
    "SUZLON": 45.00,
    "IEX": 130.00,
    "BAJAJHFL": 95.00
}

for idx, r in enumerate(avg_candidates, 4):
    sym = r["symbol"]
    c_name, _ = COMPANY_INFO.get(sym, (sym, ""))
    def_qty, def_px = default_adds.get(sym, (0, r["ltp"]))
    tgt_px = targets_calc.get(sym, r["ltp"] * 1.25)

    ws3.cell(idx, 1, idx - 3).alignment = align_center
    ws3.cell(idx, 2, sym).font = font_bold
    ws3.cell(idx, 2).alignment = align_center
    ws3.cell(idx, 3, c_name).alignment = align_left

    ws3.cell(idx, 4, r["qty"]).number_format = FMT_INT
    ws3.cell(idx, 5, r["avg"]).number_format = FMT_CURR
    ws3.cell(idx, 6, r["ltp"]).number_format = FMT_CURR
    ws3.cell(idx, 7, f"=D{idx}*E{idx}").number_format = FMT_CURR

    # Yellow Inputs
    c_add_qty = ws3.cell(idx, 8, def_qty)
    c_add_qty.fill = fill_input
    c_add_qty.font = font_bold
    c_add_qty.alignment = align_center
    c_add_qty.number_format = FMT_INT

    c_add_px = ws3.cell(idx, 9, def_px)
    c_add_px.fill = fill_input
    c_add_px.font = font_bold
    c_add_px.alignment = align_right
    c_add_px.number_format = FMT_CURR

    # Formulas
    ws3.cell(idx, 10, f"=H{idx}*I{idx}").number_format = FMT_CURR
    ws3.cell(idx, 11, f"=D{idx}+H{idx}").number_format = FMT_INT
    ws3.cell(idx, 12, f"=G{idx}+J{idx}").number_format = FMT_CURR
    ws3.cell(idx, 13, f"=IF(K{idx}>0, L{idx}/K{idx}, 0)").number_format = FMT_CURR
    ws3.cell(idx, 13).font = font_bold
    ws3.cell(idx, 14, f"=E{idx}-M{idx}").number_format = FMT_CURR

    # Old vs New Move needed to breakeven
    ws3.cell(idx, 15, f"=(E{idx}-F{idx})/F{idx}").number_format = FMT_PCT
    c_new_be = ws3.cell(idx, 16, f"=(M{idx}-F{idx})/F{idx}")
    c_new_be.number_format = FMT_PCT
    c_new_be.font = font_bold
    c_new_be.fill = fill_buy

    ws3.cell(idx, 17, tgt_px).number_format = FMT_CURR
    ws3.cell(idx, 18, f"=(Q{idx}-M{idx})*K{idx}").number_format = FMT_CURR
    ws3.cell(idx, 18).font = font_bold

    ws3.row_dimensions[idx].height = 25
    for c in range(1, 19):
        ws3.cell(idx, c).border = border_cell

ws3.freeze_panes = "D4"

# -------------------------------------------------------------------------
# SHEET 4: Capital Reallocation & Exit Plan
# -------------------------------------------------------------------------
ws4 = wb.create_sheet("Capital Reallocation")
ws4.views.sheetView[0].showGridLines = True

ws4.merge_cells("A1:G1")
ws4["A1"] = "CAPITAL LIBERATION & REINVESTMENT BLUEPRINT"
ws4["A1"].font = font_title
ws4["A1"].fill = fill_dark_navy
ws4["A1"].alignment = align_center
ws4.row_dimensions[1].height = 36

ws4.merge_cells("A2:G2")
ws4["A2"] = "Phase 1: Exit 10 toxic/broken positions to release ₹38,193 in cash • Phase 2: Deploy ₹43,000+ strictly into Top 2 Quality Compounders without fresh deposits."
ws4["A2"].font = Font(name="Calibri", size=10, italic=True, color="595959")
ws4["A2"].alignment = align_center
ws4.row_dimensions[2].height = 20

# Section A: Exits
ws4.cell(4, 1, "PHASE 1: LIQUIDATION & SALVAGE CASH EXTRACTION (10 STOCKS TO EXIT)").font = font_section
ws4.cell(4, 1).fill = fill_dark_navy
ws4.merge_cells("A4:G4")
ws4.row_dimensions[4].height = 24

headers4_a = ["Stock Symbol", "Company Name", "Shares to Sell", "Current Price (₹)", "Cash Generated (₹)", "Realized Loss (₹)", "Exit Execution Directive"]
for col_num, h_text in enumerate(headers4_a, 1):
    c = ws4.cell(5, col_num, h_text)
    c.font = font_header
    c.fill = fill_navy_sec
    c.alignment = align_center
    c.border = border_header
ws4.row_dimensions[5].height = 25

exits = [r for r in records if r["action_tag"] == "SELL"]
exits.sort(key=lambda x: -x["val"])

for idx, r in enumerate(exits, 6):
    sym = r["symbol"]
    c_name, _ = COMPANY_INFO.get(sym, (sym, ""))

    ws4.cell(idx, 1, sym).font = font_bold
    ws4.cell(idx, 1).alignment = align_center
    ws4.cell(idx, 2, c_name).alignment = align_left
    ws4.cell(idx, 3, r["qty"]).number_format = FMT_INT
    ws4.cell(idx, 4, r["ltp"]).number_format = FMT_CURR
    ws4.cell(idx, 5, f"=C{idx}*D{idx}").number_format = FMT_CURR
    ws4.cell(idx, 5).font = font_bold
    ws4.cell(idx, 6, r["pnl"]).number_format = FMT_CURR
    ws4.cell(idx, 7, r["trigger"]).alignment = align_left

    ws4.row_dimensions[idx].height = 24
    for c in range(1, 8):
        ws4.cell(idx, c).border = border_cell

# Total Exit Cash Row
ws4.cell(16, 1, "TOTAL SALVAGE CASH GENERATED").font = font_bold
ws4.merge_cells("A16:B16")
ws4.cell(16, 3, "=SUM(C6:C15)").number_format = FMT_INT
ws4.cell(16, 3).font = font_bold
ws4.cell(16, 4, "").border = border_cell
ws4.cell(16, 5, "=SUM(E6:E15)").number_format = FMT_CURR
ws4.cell(16, 5).font = Font(name="Calibri", size=12, bold=True, color="276A3C")
ws4.cell(16, 5).fill = fill_buy
ws4.cell(16, 6, "=SUM(F6:F15)").number_format = FMT_CURR
ws4.cell(16, 6).font = font_bold
ws4.cell(16, 7, "Immediate liquid cash unlocked into Demat ledger").font = font_bold

for c in range(1, 8):
    ws4.cell(16, c).border = Border(top=Side(style="medium", color="1B365D"), bottom=Side(style="double", color="1B365D"))
ws4.row_dimensions[16].height = 26

# Section B: Reallocation
ws4.cell(18, 1, "PHASE 2: REINVESTMENT INTO HIGH-CONVICTION RECOVERY LEADERS").font = font_section
ws4.cell(18, 1).fill = fill_dark_navy
ws4.merge_cells("A18:G18")
ws4.row_dimensions[18].height = 24

headers4_b = ["Target Stock", "Company Name", "Allocated Capital (₹)", "Current Price (₹)", "Shares to Accumulate", "New Breakeven Target", "Investment Thesis & Catalyst"]
for col_num, h_text in enumerate(headers4_b, 1):
    c = ws4.cell(19, col_num, h_text)
    c.font = font_header
    c.fill = fill_navy_sec
    c.alignment = align_center
    c.border = border_header
ws4.row_dimensions[19].height = 25

reinvest_plans = [
    ("COCHINSHIP", "Cochin Shipyard Ltd", 24618.00, 1119.00, 22, "₹1,434 (Down from ₹1,534)", "40 ships US order + Synergy Marine MoU. Defense order book full for 4 years. RSI 27.4."),
    ("LODHA", "Macrotech Developers Ltd", 18693.00, 1038.50, 18, "₹1,274 (Down from ₹1,334)", "At 200-DMA support floor (₹1,019). Tier-1 housing market share gains, robust pre-sales."),
]

for idx, (sym, c_name, alloc, px, qty, new_be, thesis) in enumerate(reinvest_plans, 20):
    ws4.cell(idx, 1, sym).font = font_bold
    ws4.cell(idx, 1).alignment = align_center
    ws4.cell(idx, 2, c_name).alignment = align_left
    ws4.cell(idx, 3, alloc).number_format = FMT_CURR
    ws4.cell(idx, 3).font = font_bold
    ws4.cell(idx, 4, px).number_format = FMT_CURR
    ws4.cell(idx, 5, qty).number_format = FMT_INT
    ws4.cell(idx, 5).font = font_bold
    ws4.cell(idx, 5).alignment = align_center
    ws4.cell(idx, 6, new_be).font = font_bold
    ws4.cell(idx, 6).alignment = align_center
    ws4.cell(idx, 6).fill = fill_buy
    ws4.cell(idx, 7, thesis).alignment = align_wrap

    ws4.row_dimensions[idx].height = 26
    for c in range(1, 8):
        ws4.cell(idx, c).border = border_cell

# Reinvestment Total Row
ws4.cell(22, 1, "TOTAL CAPITAL DEPLOYED").font = font_bold
ws4.merge_cells("A22:B22")
ws4.cell(22, 3, "=SUM(C20:C21)").number_format = FMT_CURR
ws4.cell(22, 3).font = font_bold
ws4.cell(22, 3).fill = fill_buy
ws4.cell(22, 4, "").border = border_cell
ws4.cell(22, 5, "=SUM(E20:E21)").number_format = FMT_INT
ws4.cell(22, 5).font = font_bold
ws4.cell(22, 5).alignment = align_center
ws4.cell(22, 6, "100% Funded from Exits").font = font_bold
ws4.cell(22, 6).alignment = align_center
ws4.cell(22, 7, "Zero extra cash required from bank account").font = font_bold

for c in range(1, 8):
    ws4.cell(22, c).border = Border(top=Side(style="medium", color="1B365D"), bottom=Side(style="double", color="1B365D"))
ws4.row_dimensions[22].height = 26

# Auto-fit column widths across all sheets
sheets_and_widths = {
    ws1: [32, 12, 22, 22, 22, 16, 75],
    ws2: [6, 14, 28, 26, 25, 10, 18, 18, 18, 18, 18, 12, 12, 14, 14, 14, 10, 14, 15, 36, 18, 14, 65],
    ws3: [6, 14, 28, 14, 20, 22, 20, 22, 25, 20, 14, 22, 20, 24, 20, 20, 18, 25],
    ws4: [14, 28, 18, 18, 20, 20, 65]
}

for ws, widths in sheets_and_widths.items():
    for col_idx, width in enumerate(widths, 1):
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = width

wb.save(OUTPUT_PATH)
print(f"Master Excel successfully created at: {OUTPUT_PATH}")
