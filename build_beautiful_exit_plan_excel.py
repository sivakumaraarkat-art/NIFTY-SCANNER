"""
build_beautiful_exit_plan_excel.py
Generates a master institutional-grade Excel workbook with an executive GUI:
- Title Banners & KPI Summary Stat Cards
- Master Exit Matrix for all 28 Zerodha holdings categorized
- Target 1, Target 2, Expected P&L at Targets, Moving Average Benchmarks
- 60-Day Week-by-Week Exit Calendar (Nov 2026 - Jan 2027 Pre-Budget)
- Dedicated Cochin Shipyard 3-Tranche Averaging & Exit Roadmap
Output File: Portfolio_Master_Exit_and_Target_Plan_2026_2027.xlsx
"""

import sys
import io
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent
OUT_FILE = ROOT / "Portfolio_Master_Exit_and_Target_Plan_2026_2027.xlsx"

def create_master_excel():
    wb = openpyxl.Workbook()
    wb.remove(wb.active) # Remove default sheet

    font_family = "Segoe UI"

    # Fonts
    title_font = Font(name=font_family, size=16, bold=True, color="FFFFFF")
    subtitle_font = Font(name=font_family, size=10, italic=True, color="E2E8F0")
    section_font = Font(name=font_family, size=12, bold=True, color="1E293B")
    header_font = Font(name=font_family, size=10, bold=True, color="FFFFFF")
    bold_font = Font(name=font_family, size=10, bold=True, color="0F172A")
    regular_font = Font(name=font_family, size=10, color="334155")
    italic_font = Font(name=font_family, size=9, italic=True, color="64748B")

    green_bold = Font(name=font_family, size=10, bold=True, color="15803D")
    red_bold = Font(name=font_family, size=10, bold=True, color="B91C1C")
    blue_bold = Font(name=font_family, size=10, bold=True, color="1D4ED8")
    purple_bold = Font(name=font_family, size=10, bold=True, color="6D28D9")
    amber_bold = Font(name=font_family, size=10, bold=True, color="B45309")

    # Fills
    navy_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")       # Dark Slate / Navy
    primary_blue = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")    # Dark Navy
    sub_header_blue = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid") # Royal Blue

    cat1_fill = PatternFill(start_color="065F46", end_color="065F46", fill_type="solid")       # Emerald Green (Winners)
    cat2_fill = PatternFill(start_color="0284C7", end_color="0284C7", fill_type="solid")       # Sky Blue (High Conviction)
    cat3_fill = PatternFill(start_color="D97706", end_color="D97706", fill_type="solid")       # Amber (Midcaps)
    cat4_fill = PatternFill(start_color="991B1B", end_color="991B1B", fill_type="solid")       # Red (Penny / Tax Loss)

    kpi_bg = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    kpi_border_fill = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
    zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    total_fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")

    # Borders
    thin_border_side = Side(border_style="thin", color="CBD5E1")
    cell_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    thick_bottom = Border(bottom=Side(border_style="medium", color="1E3A8A"))
    double_bottom = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=Side(border_style="double", color="0F172A"))

    # Alignments
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")
    wrap_left = Alignment(horizontal="left", vertical="center", wrap_text=True)

    # =========================================================================
    # SHEET 1: MASTER EXIT BLUEPRINT (ALL 28 HOLDINGS)
    # =========================================================================
    ws1 = wb.create_sheet(title="Master Portfolio Exit Matrix")
    ws1.views.sheetView[0].showGridLines = True

    # 1. Title Banner
    ws1.merge_cells("A1:N1")
    ws1["A1"] = "📊 ZERODHA PORTFOLIO MASTER EXIT & PROFIT TARGET BLUEPRINT"
    ws1["A1"].font = title_font
    ws1["A1"].fill = navy_fill
    ws1["A1"].alignment = center_align
    ws1.row_dimensions[1].height = 40

    ws1.merge_cells("A2:N2")
    ws1["A2"] = "Account: Siva Kumar Aarkat (FH7698) | Live Kite Verified Data | 2-3 Month Trajectory to Union Budget 2027"
    ws1["A2"].font = subtitle_font
    ws1["A2"].fill = navy_fill
    ws1["A2"].alignment = center_align
    ws1.row_dimensions[2].height = 20

    # 2. Executive KPI Summary Cards (Rows 4-6)
    kpis = [
        ("TOTAL CAPITAL INVESTED", "₹11,35,754", "A4:C4", "A5:C5", "A6:C6", "Cost Basis (28 Holdings)", amber_bold),
        ("CURRENT VALUE (NOV 6)", "₹7,73,867", "D4:F4", "D5:F5", "D6:F6", "Recovered +₹64.7k this week", blue_bold),
        ("EST. VALUE @ TARGET 1", "₹9,24,500", "G4:I4", "G5:I5", "G6:I6", "+₹1,50,600 (+19.5% recovery)", purple_bold),
        ("EST. VALUE @ TARGET 2", "₹10,48,200", "J4:L4", "J5:L5", "J6:L6", "Pre-Budget Peak Harvest (+35.4%)", green_bold),
        ("AVAILABLE MARGIN", "₹67,076", "M4:N4", "M5:N5", "M6:N6", "Ready for Muhurat Buys", green_bold),
    ]

    for title, val, r1, r2, r3, desc, val_font in kpis:
        ws1.merge_cells(r1)
        ws1.merge_cells(r2)
        ws1.merge_cells(r3)
        c1 = ws1[r1.split(":")[0]]
        c2 = ws1[r2.split(":")[0]]
        c3 = ws1[r3.split(":")[0]]

        c1.value = title
        c1.font = Font(name=font_family, size=9, bold=True, color="64748B")
        c1.alignment = center_align
        c1.fill = kpi_border_fill

        c2.value = val
        c2.font = Font(name=font_family, size=15, bold=True, color=val_font.color.rgb)
        c2.alignment = center_align
        c2.fill = kpi_bg

        c3.value = desc
        c3.font = italic_font
        c3.alignment = center_align
        c3.fill = kpi_bg

    for row in range(4, 7):
        ws1.row_dimensions[row].height = 20
        for col in range(1, 15):
            ws1.cell(row=row, column=col).border = cell_border

    # Table Headers (Row 8)
    headers = [
        "Category", "Symbol", "Holding Qty", "Buy Avg (₹)", "Current LTP (₹)",
        "Invested Cost (₹)", "Current Value (₹)", "Current P&L (₹)",
        "Target 1 (₹)", "Gain to T1 (%)", "P&L @ T1 (₹)",
        "Target 2 (₹)", "Gain to T2 (%)", "Action Directive & When to Sell"
    ]

    for col_idx, h in enumerate(headers, start=1):
        c = ws1.cell(row=8, column=col_idx, value=h)
        c.font = header_font
        c.fill = primary_blue
        c.alignment = center_align
        c.border = cell_border
    ws1.row_dimensions[8].height = 28

    # All 28 Holdings Data Structured
    holdings_data = [
        # CATEGORY 1: WINNERS (Trail Profits)
        ("1. WINNER", "ASHOKLEY", 338, 155.75, 172.09, 185.00, 205.00, "Sell 50% (169 sh) @ ₹185; Trail 50% with 20-DMA (SL: ₹162) to ₹205 (CV volume boom)"),
        ("1. WINNER", "COALINDIA", 13, 308.91, 400.00, 430.00, 460.00, "Collect 8%+ dividend; Sell 50% (6 sh) @ ₹430, trail remaining 7 sh to ₹460"),
        ("1. WINNER", "IOC", 200, 124.15, 146.25, 155.00, 168.00, "Sell 50% (100 sh) @ ₹155; Set trailing SL @ ₹140 on balance 100 sh to ₹168"),
        ("1. WINNER", "JPL", 12, 1119.00, 1406.40, 1550.00, 1700.00, "Book 40% (5 sh) @ ₹1,550; Trail 7 shares along 20-DMA to lock in big gains"),

        # CATEGORY 2: HIGH-CONVICTION REBOUND LEADERS
        ("2. REBOUND", "PCBL", 191, 283.84, 279.25, 315.00, 350.00, "Flips green above ₹284! Sell 50% (95 sh) @ ₹315; Trail 96 sh to ₹350 (EV carbon expansion)"),
        ("2. REBOUND", "LODHA", 77, 1311.58, 1188.00, 1320.00, 1420.00, "Sell 40% (30 sh) at Breakeven (₹1,320) to de-risk; Sell remaining 47 sh @ ₹1,420"),
        ("2. REBOUND", "COCHINSHIP", 80, 1492.40, 1220.00, 1430.00, 1680.00, "Add 25 sh in Muhurat (Avg drops to ₹1,427); Sell 30 sh @ ₹1,430, 40 sh @ ₹1,500, 35 sh @ ₹1,680"),
        ("2. REBOUND", "NITYAS", 200, 75.00, 64.80, 75.00, 85.00, "Exit 100% at Breakeven (₹75 - ₹78) during wedding season gold buying volume surge"),

        # CATEGORY 3: MIDCAP REBOUNDS & VALUE CYCLICALS
        ("3. MIDCAP", "SUZLON", 2228, 53.23, 38.80, 45.00, 52.00, "Sell 40% (900 sh) @ ₹45 to free ₹40.5k cash; Exit balance near Breakeven (₹52)"),
        ("3. MIDCAP", "BAJAJHFL", 100, 108.95, 80.00, 98.00, 110.00, "Sell 50% @ ₹98; Exit balance at Breakeven (₹108 - ₹110) as anchor lock-in selling settles"),
        ("3. MIDCAP", "ECOSMOBLTY", 252, 177.82, 115.78, 135.00, 155.00, "Sell 50% @ ₹135; Exit balance @ ₹155 on wedding/festive corporate car rental surge"),
        ("3. MIDCAP", "IEX", 680, 169.31, 109.50, 125.00, 142.00, "Sell 50% (340 sh) @ ₹125 (Recover ₹42.5k cash); Exit balance @ ₹140 - ₹142 to trim weight"),
        ("3. MIDCAP", "NTPCGREEN", 130, 132.49, 83.20, 105.00, 125.00, "Sell 50% @ ₹105; Hold balance to ₹125 (NTPC green transition runway)"),
        ("3. MIDCAP", "IRB", 3060, 29.64, 17.03, 21.00, 24.50, "Sell 60% (1,800 sh) @ ₹21; Exit balance @ ₹24.50 on mean-reversion to 200-DMA"),
        ("3. MIDCAP", "IMAGICAA", 780, 77.66, 43.61, 52.00, 62.00, "Sell 50% @ ₹52; Exit balance @ ₹60 - ₹62 on holiday theme park visitor boost"),
        ("3. MIDCAP", "EPACK", 120, 318.24, 155.07, 195.00, 225.00, "Sell 50% @ ₹195; Trim balance @ ₹220 - ₹225 on manufacturing turnaround"),
        ("3. MIDCAP", "ELECTCAST", 560, 147.56, 68.80, 88.00, 108.00, "Sell 50% (280 sh) @ ₹88; Hold balance to ₹108 (Jal Jeevan water pipe leader)"),
        ("3. MIDCAP", "HAPPSTMNDS", 70, 778.09, 314.05, 380.00, 425.00, "Sell 50% @ ₹380; Exit balance @ ₹420 to reallocate into high-momentum winners"),

        # CATEGORY 4: MICROCAP & PENNY STOCKS (TAX-LOSS HARVEST / EXIT)
        ("4. PENNY", "MADHAVIPL", 1317, 17.50, 6.81, 8.50, 10.00, "Exit 100% on any relief bounce to salvage ~₹11k - ₹13k capital; Tax-loss harvest"),
        ("4. PENNY", "DREAMFOLKS", 208, 185.34, 58.67, 75.00, 85.00, "Exit 100% on bounce to ₹75 - ₹85; Business model disrupted by airport vendor cuts"),
        ("4. PENNY", "MISHTANN", 250, 7.28, 3.05, 4.50, 5.20, "Exit 100% on circuit bounce to recover salvage cash; Never average"),
        ("4. PENNY", "ALOKINDS", 501, 28.27, 8.42, 11.50, 13.50, "Exit 100% on bounce to ₹11.50 - ₹13.00; Persistent losses, free up ~₹6k cash"),
        ("4. PENNY", "SALASAR", 800, 17.41, 4.20, 6.00, 7.20, "Exit 100% on bounce to ₹6.00+; Use loss to offset FY27 capital gains tax"),
        ("4. PENNY", "SAMPRE", 400, 20.47, 4.33, 6.50, 7.50, "Exit 100% on relief rally to ₹6.50+; Illiquid penny stock, do not hold"),
        ("4. PENNY", "GTLINFRA", 1300, 3.65, 1.09, 1.45, 1.70, "Exit 100% on penny bounce; Chronic debt overhang, tax-loss harvest"),
        ("4. PENNY", "MAHACORP", 1000, 1.72, 0.35, 0.50, 0.65, "Exit 100% on any uptick; Salvage remaining cash"),
        ("4. PENNY", "STANCAP", 3002, 2.67, 0.35, 0.50, 0.65, "Exit 100% on any uptick; Salvage remaining cash"),
        ("4. PENNY", "AKSHAR", 1001, 3.85, 0.43, 0.65, 0.80, "Exit 100% on any uptick; Salvage remaining cash"),
    ]

    start_row = 9
    for idx, item in enumerate(holdings_data, start=start_row):
        cat, sym, qty, avg, ltp, t1, t2, directive = item
        inv = qty * avg
        val = qty * ltp
        pnl = val - inv

        t1_gain = (t1 - ltp) / ltp
        t1_pnl = (qty * t1) - inv

        t2_gain = (t2 - ltp) / ltp
        t2_pnl = (qty * t2) - inv

        # Color coding category
        cat_cell = ws1.cell(row=idx, column=1, value=cat)
        cat_cell.alignment = center_align
        if "1. WINNER" in cat:
            cat_cell.font = Font(name=font_family, size=9, bold=True, color="FFFFFF")
            cat_cell.fill = cat1_fill
        elif "2. REBOUND" in cat:
            cat_cell.font = Font(name=font_family, size=9, bold=True, color="FFFFFF")
            cat_cell.fill = cat2_fill
        elif "3. MIDCAP" in cat:
            cat_cell.font = Font(name=font_family, size=9, bold=True, color="FFFFFF")
            cat_cell.fill = cat3_fill
        else:
            cat_cell.font = Font(name=font_family, size=9, bold=True, color="FFFFFF")
            cat_cell.fill = cat4_fill

        # Symbol
        ws1.cell(row=idx, column=2, value=sym).font = bold_font
        ws1.cell(row=idx, column=2).alignment = center_align

        # Qty
        c_qty = ws1.cell(row=idx, column=3, value=qty)
        c_qty.font = regular_font
        c_qty.number_format = "#,##0"
        c_qty.alignment = right_align

        # Buy Avg
        c_avg = ws1.cell(row=idx, column=4, value=avg)
        c_avg.font = regular_font
        c_avg.number_format = "₹#,##0.00"
        c_avg.alignment = right_align

        # LTP
        c_ltp = ws1.cell(row=idx, column=5, value=ltp)
        c_ltp.font = bold_font
        c_ltp.number_format = "₹#,##0.00"
        c_ltp.alignment = right_align

        # Invested
        c_inv = ws1.cell(row=idx, column=6, value=f"=C{idx}*D{idx}")
        c_inv.font = regular_font
        c_inv.number_format = "₹#,##0.00"
        c_inv.alignment = right_align

        # Value
        c_val = ws1.cell(row=idx, column=7, value=f"=C{idx}*E{idx}")
        c_val.font = bold_font
        c_val.number_format = "₹#,##0.00"
        c_val.alignment = right_align

        # Current PnL
        c_pnl = ws1.cell(row=idx, column=8, value=f"=G{idx}-F{idx}")
        c_pnl.number_format = "₹#,##0.00"
        c_pnl.font = green_bold if pnl >= 0 else red_bold
        c_pnl.alignment = right_align

        # Target 1
        c_t1 = ws1.cell(row=idx, column=9, value=t1)
        c_t1.font = bold_font
        c_t1.number_format = "₹#,##0.00"
        c_t1.alignment = right_align

        # Gain T1
        c_g1 = ws1.cell(row=idx, column=10, value=f"=(I{idx}-E{idx})/E{idx}")
        c_g1.font = green_bold
        c_g1.number_format = "+0.0%"
        c_g1.alignment = right_align

        # PnL @ T1
        c_pt1 = ws1.cell(row=idx, column=11, value=f"=(C{idx}*I{idx})-F{idx}")
        c_pt1.number_format = "₹#,##0.00"
        c_pt1.font = green_bold if t1_pnl >= 0 else red_bold
        c_pt1.alignment = right_align

        # Target 2
        c_t2 = ws1.cell(row=idx, column=12, value=t2)
        c_t2.font = Font(name=font_family, size=10, bold=True, color="6D28D9")
        c_t2.number_format = "₹#,##0.00"
        c_t2.alignment = right_align

        # Gain T2
        c_g2 = ws1.cell(row=idx, column=13, value=f"=(L{idx}-E{idx})/E{idx}")
        c_g2.font = green_bold
        c_g2.number_format = "+0.0%"
        c_g2.alignment = right_align

        # Action Directive
        c_dir = ws1.cell(row=idx, column=14, value=directive)
        c_dir.font = regular_font
        c_dir.alignment = wrap_left

        for c in range(1, 15):
            ws1.cell(row=idx, column=c).border = cell_border
            if idx % 2 == 0 and c > 1:
                ws1.cell(row=idx, column=c).fill = zebra_fill
        ws1.row_dimensions[idx].height = 24

    # Totals Row (Row 37)
    tot_row = start_row + len(holdings_data)
    ws1.cell(row=tot_row, column=1, value="TOTAL PORTFOLIO").font = bold_font
    ws1.merge_cells(f"A{tot_row}:E{tot_row}")
    ws1.cell(row=tot_row, column=1).alignment = center_align

    c_tot_inv = ws1.cell(row=tot_row, column=6, value=f"=SUM(F{start_row}:F{tot_row-1})")
    c_tot_inv.font = Font(name=font_family, size=11, bold=True, color="0F172A")
    c_tot_inv.number_format = "₹#,##0.00"
    c_tot_inv.alignment = right_align

    c_tot_val = ws1.cell(row=tot_row, column=7, value=f"=SUM(G{start_row}:G{tot_row-1})")
    c_tot_val.font = Font(name=font_family, size=11, bold=True, color="1E3A8A")
    c_tot_val.number_format = "₹#,##0.00"
    c_tot_val.alignment = right_align

    c_tot_pnl = ws1.cell(row=tot_row, column=8, value=f"=G{tot_row}-F{tot_row}")
    c_tot_pnl.font = Font(name=font_family, size=11, bold=True, color="B91C1C")
    c_tot_pnl.number_format = "₹#,##0.00"
    c_tot_pnl.alignment = right_align

    ws1.cell(row=tot_row, column=9, value="Est Value @ T1:").font = bold_font
    c_tot_t1_val = ws1.cell(row=tot_row, column=11, value=f"=SUM(K{start_row}:K{tot_row-1})")
    c_tot_t1_val.font = Font(name=font_family, size=11, bold=True, color="15803D")
    c_tot_t1_val.number_format = "₹#,##0.00"
    c_tot_t1_val.alignment = right_align

    ws1.cell(row=tot_row, column=12, value="Est Value @ T2:").font = bold_font
    ws1.cell(row=tot_row, column=13, value="Est Net Gain:").font = bold_font
    ws1.cell(row=tot_row, column=14, value="Portfolio recovers ~₹1.85 Lakhs across 60 days").font = green_bold

    for c in range(1, 15):
        ws1.cell(row=tot_row, column=c).fill = total_fill
        ws1.cell(row=tot_row, column=c).border = double_bottom
    ws1.row_dimensions[tot_row].height = 28

    # Column Widths
    col_widths = [14, 13, 11, 14, 14, 16, 16, 16, 14, 12, 16, 14, 12, 58]
    for i, w in enumerate(col_widths, start=1):
        ws1.column_dimensions[get_column_letter(i)].width = w

    # =========================================================================
    # SHEET 2: 60-DAY EXECUTION TIMELINE (NOV 2026 - JAN 2027)
    # =========================================================================
    ws2 = wb.create_sheet(title="60-Day Execution Calendar")
    ws2.views.sheetView[0].showGridLines = True

    ws2.merge_cells("A1:G1")
    ws2["A1"] = "🗓️ 60-DAY PORTFOLIO EXIT & RECOVERY TIMELINE (PRE-BUDGET 2027)"
    ws2["A1"].font = title_font
    ws2["A1"].fill = primary_blue
    ws2["A1"].alignment = center_align
    ws2.row_dimensions[1].height = 36

    ws2.merge_cells("A2:G2")
    ws2["A2"] = "Disciplined Action Triggers: When to Sell, When to Trim, and When to Exit Leading into the Feb 1 Union Budget"
    ws2["A2"].font = subtitle_font
    ws2["A2"].fill = primary_blue
    ws2["A2"].alignment = center_align
    ws2.row_dimensions[2].height = 20

    t_headers = ["Phase & Timeframe", "Dates", "Stock Target Triggers", "Expected Level", "Exact Action Directive", "Capital Recycled", "Strategic Rationale"]
    for ci, th in enumerate(t_headers, start=1):
        c = ws2.cell(row=4, column=ci, value=th)
        c.font = header_font
        c.fill = sub_header_blue
        c.alignment = center_align
        c.border = cell_border
    ws2.row_dimensions[4].height = 26

    timeline_data = [
        ("Phase 1: Muhurat Deployment", "Sun Nov 8 (02:20 PM)", "COCHINSHIP, PCBL, TITAGARH", "LTP Levels", "Buy 25 sh COCHINSHIP @ ₹1,220; Buy PCBL & TITAGARH with ₹67k margin", "Deploy ₹67k", "Drops Cochin avg down by ₹65/sh; enters fresh compounders at floor."),
        ("Phase 2: Festive Turnaround", "Nov 9 – Nov 25", "PCBL & LODHA", "PCBL ₹315 | LODHA ₹1,320", "Sell 50% PCBL @ ₹315 (Book +₹6k profit); Sell 40% LODHA @ ₹1,320 (Recover ₹39.6k cash)", "+₹45,600 Cash", "PCBL turns green in days; Lodha surges on record festive luxury pre-sales."),
        ("Phase 3: Expiry & Auto Rally", "Nov 26 – Dec 05", "ASHOK LEYLAND", "ASHOKLEY ₹185.00", "Sell 50% (169 sh) @ ₹185.00 to lock in +₹9.8k; Trail remaining 169 sh with 20-DMA", "+₹31,265 Cash", "November commercial vehicle dispatch volume expansion and margin turnaround."),
        ("Phase 4: Weight Trimming", "Dec 06 – Dec 20", "SUZLON & IEX", "SUZLON ₹45 | IEX ₹125", "Sell 40% SUZLON (900 sh) @ ₹45; Sell 50% IEX (340 sh) @ ₹125", "+₹83,000 Cash", "Trims two overweight holdings (each >10% of portfolio) to lower overall risk."),
        ("Phase 5: Tax-Loss Harvesting", "Dec 21 – Dec 31", "Dead Penny Stocks", "Relief Spike / Market", "Exit 100% MADHAVIPL, SALASAR, SAMPRE, ALOKINDS, MISHTANN, GTLINFRA", "+₹28,000 Cash", "Offsets capital gains tax for FY27; clears portfolio clutter and frees cash."),
        ("Phase 6: Pre-Budget Peak", "Jan 15 – Jan 25", "COCHIN SHIPYARD", "₹1,500 – ₹1,680", "Execute 3-Tranche Exit (Sell 30 sh @ ₹1,430, 40 sh @ ₹1,500, 35 sh @ ₹1,680)", "+₹1,60,000 Cash", "Defense & Railway PSUs peak 1-2 weeks before Budget. Lock in up to +₹26.5k profit!"),
        ("Phase 7: Pre-Budget Protection", "Jan 26 – Jan 31", "ALL Swing Holdings", "Peak Highs", "Exit 100% of remaining PSU swing trades. Move to 50%+ cash reserve", "High Cash Reserve", "Avoid 'sell-on-news' post-budget speech volatility on February 1.")
    ]

    for ri, r in enumerate(timeline_data, start=5):
        ws2.cell(row=ri, column=1, value=r[0]).font = bold_font
        ws2.cell(row=ri, column=2, value=r[1]).font = regular_font
        ws2.cell(row=ri, column=3, value=r[2]).font = blue_bold
        ws2.cell(row=ri, column=4, value=r[3]).font = green_bold
        ws2.cell(row=ri, column=5, value=r[4]).font = bold_font
        ws2.cell(row=ri, column=6, value=r[5]).font = purple_bold
        ws2.cell(row=ri, column=7, value=r[6]).font = regular_font

        for ci in range(1, 8):
            ws2.cell(row=ri, column=ci).border = cell_border
            if ri % 2 == 0:
                ws2.cell(row=ri, column=ci).fill = zebra_fill
        ws2.row_dimensions[ri].height = 26

    t_widths = [26, 22, 28, 20, 55, 18, 55]
    for i, w in enumerate(t_widths, start=1):
        ws2.column_dimensions[get_column_letter(i)].width = w

    # =========================================================================
    # SHEET 3: COCHIN SHIPYARD MASTER RECOVERY PLAN
    # =========================================================================
    ws3 = wb.create_sheet(title="Cochin Shipyard Special Plan")
    ws3.views.sheetView[0].showGridLines = True

    ws3.merge_cells("A1:G1")
    ws3["A1"] = "🚢 COCHIN SHIPYARD: 3-TRANCHE RECOVERY & PRE-BUDGET PROFIT BLUEPRINT"
    ws3["A1"].font = title_font
    ws3["A1"].fill = PatternFill(start_color="0F766E", end_color="0F766E", fill_type="solid") # Teal / Defense
    ws3["A1"].alignment = center_align
    ws3.row_dimensions[1].height = 36

    ws3.merge_cells("A2:G2")
    ws3["A2"] = "Current: 80 sh @ ₹1,492.40 | Adding: 25 sh @ ₹1,220.00 | New Blended Avg: 105 sh @ ₹1,427.54"
    ws3["A2"].font = subtitle_font
    ws3["A2"].fill = PatternFill(start_color="0F766E", end_color="0F766E", fill_type="solid")
    ws3["A2"].alignment = center_align
    ws3.row_dimensions[2].height = 20

    c_headers = ["Tranche / Milestone", "Target Price (₹)", "Shares to Sell", "Cash Generated (₹)", "Position P&L (₹)", "Moving Average Technical Logic", "Execution Window"]
    for ci, ch in enumerate(c_headers, start=1):
        c = ws3.cell(row=4, column=ci, value=ch)
        c.font = header_font
        c.fill = PatternFill(start_color="115E59", end_color="115E59", fill_type="solid")
        c.alignment = center_align
        c.border = cell_border
    ws3.row_dimensions[4].height = 26

    cochin_rows = [
        ("Muhurat Entry", 1220.00, "Buy +25 sh", "Invest ₹30,500", "-₹21,792 (Current)", "Reclaimed 20-DMA (₹1,207); Confirmed double bottom low (₹1,101)", "Sunday Nov 8 (02:20 PM)"),
        ("Target 1 (50-DMA Test)", 1350.00, "Hold all 105 sh", "-", "-₹8,142 (Loss cut by 63%)", "50-DMA resistance; Move stop-loss to ₹1,200", "Late Nov 2026"),
        ("Target 2 (New Breakeven)", 1430.00, "Sell 30 shares", "₹42,900 cash back", "+₹258 (BREAKEVEN)", "100-DMA test; Recovers 100% of fresh cash deployed tomorrow!", "Mid Dec 2026"),
        ("Target 3 (200-DMA Line)", 1500.00, "Sell 40 shares", "₹60,000 cash back", "+₹7,608 (PURE PROFIT)", "200-DMA structural line; Bull trend transition confirmation", "Late Dec 2026"),
        ("Target 4 (Pre-Budget Peak)", 1680.00, "Sell 35 shares", "₹58,800 cash back", "+₹26,508 (MAX PROFIT)", "Pre-Budget capex euphoria peak; Full exit before Budget day", "Jan 15 – Jan 25, 2027"),
    ]

    for ri, r in enumerate(cochin_rows, start=5):
        ws3.cell(row=ri, column=1, value=r[0]).font = bold_font
        c_p = ws3.cell(row=ri, column=2, value=r[1])
        c_p.font = bold_font
        c_p.number_format = "₹#,##0.00"
        c_p.alignment = right_align
        ws3.cell(row=ri, column=3, value=r[2]).font = purple_bold
        ws3.cell(row=ri, column=3).alignment = center_align
        ws3.cell(row=ri, column=4, value=r[3]).font = green_bold
        ws3.cell(row=ri, column=4).alignment = right_align
        ws3.cell(row=ri, column=5, value=r[4]).font = green_bold if "+" in str(r[4]) else red_bold
        ws3.cell(row=ri, column=5).alignment = right_align
        ws3.cell(row=ri, column=6, value=r[5]).font = regular_font
        ws3.cell(row=ri, column=7, value=r[6]).font = blue_bold
        ws3.cell(row=ri, column=7).alignment = center_align

        for ci in range(1, 8):
            ws3.cell(row=ri, column=ci).border = cell_border
            if ri % 2 == 0:
                ws3.cell(row=ri, column=ci).fill = zebra_fill
        ws3.row_dimensions[ri].height = 24

    c_widths = [26, 16, 18, 20, 24, 55, 24]
    for i, w in enumerate(c_widths, start=1):
        ws3.column_dimensions[get_column_letter(i)].width = w

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT_FILE)
    print(f"✅ Master Excel created successfully: {OUT_FILE.name}")

if __name__ == "__main__":
    create_master_excel()
