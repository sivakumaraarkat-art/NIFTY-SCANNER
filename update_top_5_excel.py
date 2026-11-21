"""
Updates Top_5_Stocks_To_Buy_Now_Master_Plan.xlsx with Day 1 Live Closing Audit.
Integrates live NSE closing prices, P&L calculations for ₹1L and ₹2L plans,
distance to Target 1, safety buffer above SL, and position health verdicts.
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime

wb_path = "Top_5_Stocks_To_Buy_Now_Master_Plan.xlsx"
wb = openpyxl.load_workbook(wb_path)

sheet_name = "Day 1 Live Audit (17-Nov)"
if sheet_name in wb.sheetnames:
    del wb[sheet_name]

ws = wb.create_sheet(title=sheet_name, index=0) # Place as first sheet for immediate visibility
ws.views.sheetView[0].showGridLines = True

# Palettes & Styles
navy_fill = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
title_font = Font(name="Calibri", size=15, bold=True, color="FFFFFF")
sub_font = Font(name="Calibri", size=10, italic=True, color="595959")

card_header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
table_header_fill = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
table_header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

green_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
green_font = Font(name="Calibri", size=11, bold=True, color="375623")

red_fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
red_font = Font(name="Calibri", size=11, bold=True, color="C65911")

total_fill = PatternFill(start_color="EAEEF7", end_color="EAEEF7", fill_type="solid")
bold_font = Font(name="Calibri", size=11, bold=True, color="000000")
regular_font = Font(name="Calibri", size=11, color="000000")

thin_border_side = Side(border_style="thin", color="D9D9D9")
thin_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
thick_top_double_bottom = Border(top=Side(style="thin", color="000000"), bottom=Side(style="double", color="000000"))

# Row 1: Title
ws.merge_cells("A1:N1")
t_cell = ws["A1"]
t_cell.value = "TOP 5 30-DAY SWING PORTFOLIO — DAY 1 LIVE CLOSING AUDIT (17-NOV-2026)"
t_cell.font = title_font
t_cell.fill = navy_fill
t_cell.alignment = Alignment(horizontal="center", vertical="center")
ws.row_dimensions[1].height = 36

# Row 2: Subtitle / Timestamp
ws.merge_cells("A2:N2")
sub_cell = ws["A2"]
sub_cell.value = f"Live Market Audit Timestamp: 17-Nov-2026 11:30 PM IST  |  Maturity Target Date: 29-Dec-2026 (29 Trading Days Remaining)"
sub_cell.font = sub_font
sub_cell.alignment = Alignment(horizontal="center", vertical="center")
ws.row_dimensions[2].height = 20

# Row 4-5: KPI Summary Cards
kpis = [
    ("TOTAL CAPITAL DEPLOYED\n₹1,01,214.50 (1L Plan)\n₹1,99,503.00 (2L Plan)", "A4:B5"),
    ("PORTFOLIO DAY 1 NET P&L\n-₹681.10 (-0.67% on 1L)\n-₹1,380.30 (-0.69% on 2L)", "C4:E5"),
    ("PORTFOLIO HEALTH STATUS\n5 / 5 WITHIN SL BUFFER\n2 / 5 TRADING IN PROFIT", "F4:H5"),
    ("MAX RISK BUDGET ALLOWED\n-₹6,005.50 (1L Risk Cap)\n-₹11,835.00 (2L Risk Cap)", "I4:K5"),
    ("REMAINING SWING HORIZON\n29 TRADING DAYS\nTarget Expiry: 29-Dec-2026", "L4:N5")
]

for text, cell_range in kpis:
    ws.merge_cells(cell_range)
    top_left = cell_range.split(":")[0]
    cell = ws[top_left]
    cell.value = text
    cell.font = Font(name="Calibri", size=10, bold=True, color="1B365D")
    cell.fill = card_header_fill
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

ws.row_dimensions[4].height = 25
ws.row_dimensions[5].height = 25

# Row 7: Table Headers
headers = [
    "Rank", "Symbol", "Sector", "Entry Price (₹)", "Today's Close (₹)",
    "Day Range (₹)", "Gain / Loss vs Entry", "1L Plan Qty", "1L Live P&L (₹)",
    "2L Plan Qty", "2L Live P&L (₹)", "Target 1 (₹)", "Safety Buffer above SL", "Health Verdict"
]

ws.row_dimensions[7].height = 28
for col_idx, h in enumerate(headers, start=1):
    cell = ws.cell(row=7, column=col_idx)
    cell.value = h
    cell.font = table_header_font
    cell.fill = table_header_fill
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

# Data Rows (Row 8 to 12)
data = [
    ("#01", "ADANIPORTS", "Infrastructure & Logistics", 1893.00, 1917.00, "1,900 - 1,925", "+1.27% (+₹24.0)", 11, 264.00, 21, 504.00, 2120.00, "+7.20% (₹138 cushion)", "🟢 IN PROFIT — STRONG HOLD"),
    ("#02", "ZYDUSLIFE", "Pharma & Healthcare", 1192.00, 1204.20, "1,194 - 1,213", "+1.02% (+₹12.2)", 17, 207.40, 34, 414.80, 1342.00, "+6.99% (₹84 cushion)", "🟢 IN PROFIT — STRONG HOLD"),
    ("#03", "BDL", "Defense & Aerospace", 1033.00, 1027.10, "1,022 - 1,053", "-0.57% (-₹5.9)", 20, -118.00, 39, -230.10, 1150.00, "+5.46% (₹56 cushion)", "🟡 NORMAL RETEST — HOLD"),
    ("#04", "PERSISTENT", "IT & Cloud Engineering", 5978.50, 5911.00, "5,902 - 6,028", "-1.13% (-₹67.5)", 3, -202.50, 6, -405.00, 6695.00, "+4.92% (₹291 cushion)", "🟡 HEALTHY CONSOLIDATION"),
    ("#05", "ALKEM", "Pharma & Formulations", 5383.00, 5175.00, "5,144 - 5,259", "-3.86% (-₹208.0)", 4, -832.00, 8, -1664.00, 6050.00, "+1.84% (₹95 cushion)", "🟠 SUPPORT TEST — ACTIVE HOLD")
]

for row_idx, row_vals in enumerate(data, start=8):
    ws.row_dimensions[row_idx].height = 24
    for col_idx, val in enumerate(row_vals, start=1):
        cell = ws.cell(row=row_idx, column=col_idx)
        cell.value = val
        cell.font = regular_font
        cell.border = thin_border

        # Format alignments and colors
        if col_idx in [1, 2, 8, 10]:
            cell.alignment = Alignment(horizontal="center", vertical="center")
        elif col_idx in [4, 5, 12]:
            cell.number_format = '₹#,##0.00'
            cell.alignment = Alignment(horizontal="right", vertical="center")
        elif col_idx in [9, 11]:
            cell.number_format = '+₹#,##0.00;-₹#,##0.00;₹0.00'
            cell.alignment = Alignment(horizontal="right", vertical="center")
            if val >= 0:
                cell.fill = green_fill
                cell.font = green_font
            else:
                cell.fill = red_fill
                cell.font = red_font
        elif col_idx == 7: # Gain / Loss %
            cell.alignment = Alignment(horizontal="center", vertical="center")
            if "+" in str(val):
                cell.fill = green_fill
                cell.font = green_font
            else:
                cell.fill = red_fill
                cell.font = red_font
        elif col_idx == 13: # Safety buffer
            cell.alignment = Alignment(horizontal="center", vertical="center")
        elif col_idx == 14: # Verdict
            cell.alignment = Alignment(horizontal="left", vertical="center")
            cell.font = bold_font

# Row 13: Portfolio Totals
ws.row_dimensions[13].height = 26
ws.cell(row=13, column=1, value="")
ws.cell(row=13, column=2, value="PORTFOLIO TOTAL").font = bold_font
ws.cell(row=13, column=3, value="5 Diversified Holdings").font = regular_font
ws.cell(row=13, column=4, value="")
ws.cell(row=13, column=5, value="")
ws.cell(row=13, column=6, value="")
ws.cell(row=13, column=7, value="-0.67% Net").font = bold_font

# 1L Total P&L
c_1l = ws.cell(row=13, column=9, value=-681.10)
c_1l.number_format = '+₹#,##0.00;-₹#,##0.00;₹0.00'
c_1l.font = bold_font
c_1l.alignment = Alignment(horizontal="right", vertical="center")

# 2L Total P&L
c_2l = ws.cell(row=13, column=11, value=-1380.30)
c_2l.number_format = '+₹#,##0.00;-₹#,##0.00;₹0.00'
c_2l.font = bold_font
c_2l.alignment = Alignment(horizontal="right", vertical="center")

ws.cell(row=13, column=14, value="ALL 5 STOCKS RESPECTING SL").font = bold_font

for col in range(1, 15):
    c = ws.cell(row=13, column=col)
    c.fill = total_fill
    c.border = thick_top_double_bottom

# Adjust Column Widths
col_widths = {
    "A": 9,   # Rank
    "B": 15,  # Symbol
    "C": 26,  # Sector
    "D": 16,  # Entry Price
    "E": 18,  # Close Price
    "F": 17,  # Day Range
    "G": 21,  # Gain / Loss
    "H": 13,  # 1L Qty
    "I": 17,  # 1L P&L
    "J": 13,  # 2L Qty
    "K": 17,  # 2L P&L
    "L": 15,  # Target 1
    "M": 24,  # Safety Buffer
    "N": 30   # Health Verdict
}

for col_letter, width in col_widths.items():
    ws.column_dimensions[col_letter].width = width

wb.save(wb_path)
print(f"Successfully updated {wb_path} with Sheet: '{sheet_name}'!")
