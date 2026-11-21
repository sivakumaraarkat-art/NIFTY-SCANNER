"""
generate_rvnl_irfc_master_plan.py
Generates a comprehensive, professional Excel workbook for RVNL and IRFC:
- Executive Dashboard & Capital Split (Interactive)
- RVNL Master Strategy (Tranches, Targets, Holding Horizon)
- IRFC Master Strategy (Tranches, Targets, Dividend Yield)
- Upcoming News Catalysts & 2026-2027 Pre-Budget Predictions
- Capital Position Sizing Matrix (50k, 1L, 2L, 5L tiers)
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from pathlib import Path

OUTPUT_FILE = Path("D:/NiftyScanner/STOCK_SWING_V1_updated/RVNL_and_IRFC_Master_Investment_and_Swing_Plan_2026.xlsx")

def create_excel():
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # -------------------------------------------------------------
    # Styling Palette
    # -------------------------------------------------------------
    font_family = "Segoe UI"

    title_font = Font(name=font_family, size=16, bold=True, color="FFFFFF")
    subtitle_font = Font(name=font_family, size=10, italic=True, color="E2E8F0")
    section_font = Font(name=font_family, size=12, bold=True, color="1E293B")
    header_font = Font(name=font_family, size=10, bold=True, color="FFFFFF")
    bold_font = Font(name=font_family, size=10, bold=True, color="0F172A")
    regular_font = Font(name=font_family, size=10, color="334155")
    green_bold_font = Font(name=font_family, size=10, bold=True, color="15803D")
    red_bold_font = Font(name=font_family, size=10, bold=True, color="B91C1C")
    blue_bold_font = Font(name=font_family, size=10, bold=True, color="1D4ED8")

    # Fills
    primary_header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid") # Dark Navy
    sub_header_fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")     # Blue
    rvnl_header_fill = PatternFill(start_color="0F766E", end_color="0F766E", fill_type="solid")    # Teal/Cyan
    irfc_header_fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")    # Royal Blue
    kpi_bg_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")         # Light Slate
    highlight_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")      # Soft Green
    warning_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")        # Soft Yellow
    danger_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")         # Soft Red
    zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    # Borders
    thin_border_side = Side(border_style="thin", color="CBD5E1")
    cell_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    thick_bottom = Border(bottom=Side(border_style="medium", color="1E3A8A"))
    double_bottom = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=Side(border_style="double", color="0F172A"))

    # Alignments
    left_align = Alignment(horizontal="left", vertical="center")
    center_align = Alignment(horizontal="center", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")
    wrap_left = Alignment(horizontal="left", vertical="center", wrap_text=True)

    # =============================================================
    # SHEET 1: EXECUTIVE DASHBOARD & CAPITAL ALLOCATION
    # =============================================================
    ws1 = wb.create_sheet(title="Executive Dashboard")
    ws1.views.sheetView[0].showGridLines = True

    # Title Banner
    ws1.merge_cells("A1:H1")
    ws1["A1"] = "RAILWAY WEALTH CREATION MASTER PLAN: RVNL & IRFC"
    ws1["A1"].font = title_font
    ws1["A1"].fill = primary_header_fill
    ws1["A1"].alignment = center_align
    ws1.row_dimensions[1].height = 36

    ws1.merge_cells("A2:H2")
    ws1["A2"] = "Strategic 52-Week Low Entry, 2-Tranche Accumulation, Pre-Budget Catalysts & Risk Roadmap | Generated 01-Nov-2026"
    ws1["A2"].font = subtitle_font
    ws1["A2"].fill = primary_header_fill
    ws1["A2"].alignment = center_align
    ws1.row_dimensions[2].height = 20

    # Executive Comparison Table
    ws1.merge_cells("A4:H4")
    ws1["A4"] = "1. EXECUTIVE COMPARISON: RVNL VS IRFC"
    ws1["A4"].font = section_font
    ws1.row_dimensions[4].height = 24

    headers_comp = ["Stock Symbol", "Company Role", "CMP (₹)", "52W High (₹)", "Correction %", "14D RSI", "Core Moat", "Strategic Verdict"]
    for col_idx, h in enumerate(headers_comp, start=1):
        c = ws1.cell(row=5, column=col_idx, value=h)
        c.font = header_font
        c.fill = sub_header_fill
        c.alignment = center_align
        c.border = cell_border
    ws1.row_dimensions[5].height = 26

    comp_rows = [
        ("RVNL", "EPC Rail Execution & Metro Projects", 193.34, 400.70, (193.34 - 400.70) / 400.70, 42.5, "₹90,000 Cr Order Backlog, Vande Bharat JV", "High-Beta Growth Leader (+25% to +42% Target Upside)"),
        ("IRFC", "100% Monopoly Railway Asset Financier", 80.43, 137.17, (80.43 - 137.17) / 137.17, 51.0, "Zero Net NPA, Sovereign Guarantee, ~3.8% Div Yield", "Low-Beta Defensive Anchor (+22% to +39% Target Upside)")
    ]

    for r_idx, r in enumerate(comp_rows, start=6):
        ws1.cell(row=r_idx, column=1, value=r[0]).font = bold_font
        ws1.cell(row=r_idx, column=2, value=r[1]).font = regular_font
        c_cmp = ws1.cell(row=r_idx, column=3, value=r[2])
        c_cmp.font = bold_font
        c_cmp.number_format = "₹#,##0.00"
        c_high = ws1.cell(row=r_idx, column=4, value=r[3])
        c_high.font = regular_font
        c_high.number_format = "₹#,##0.00"
        c_corr = ws1.cell(row=r_idx, column=5, value=r[4])
        c_corr.font = red_bold_font
        c_corr.number_format = "-0.0%"
        ws1.cell(row=r_idx, column=6, value=r[5]).font = bold_font
        ws1.cell(row=r_idx, column=7, value=r[6]).font = regular_font
        ws1.cell(row=r_idx, column=8, value=r[7]).font = green_bold_font
        for c_idx in range(1, 9):
            ws1.cell(row=r_idx, column=c_idx).border = cell_border
        ws1.row_dimensions[r_idx].height = 22

    # Capital Allocation & Interactive Calculator Section
    ws1.merge_cells("A9:H9")
    ws1["A9"] = "2. INTERACTIVE CAPITAL ALLOCATION CALCULATOR (ENTER YOUR BUDGET)"
    ws1["A9"].font = section_font
    ws1.row_dimensions[9].height = 24

    ws1.merge_cells("A10:C10")
    ws1["A10"] = "Total Capital to Invest (₹):"
    ws1["A10"].font = bold_font
    ws1["A10"].alignment = right_align

    c_cap = ws1.cell(row=10, column=4, value=100000)
    c_cap.font = Font(name=font_family, size=12, bold=True, color="1E3A8A")
    c_cap.fill = highlight_fill
    c_cap.border = cell_border
    c_cap.number_format = "₹#,##0"
    c_cap.alignment = center_align

    ws1.merge_cells("E10:H10")
    ws1["E10"] = "← Change this number to simulate ₹50,000, ₹2,00,000, ₹5,00,000 etc."
    ws1["E10"].font = Font(name=font_family, size=9, italic=True, color="64748B")

    # Table of Split
    headers_calc = ["Stock", "Recommended Weight", "Capital Allocated (₹)", "Tranche 1 (Immediate)", "Tranche 2 (Dip Reserve)", "Target 1 Profit", "Target 2 Profit", "Target 3 Profit"]
    for col_idx, h in enumerate(headers_calc, start=1):
        c = ws1.cell(row=12, column=col_idx, value=h)
        c.font = header_font
        c.fill = primary_header_fill
        c.alignment = center_align
        c.border = cell_border
    ws1.row_dimensions[12].height = 26

    # RVNL row
    ws1.cell(row=13, column=1, value="RVNL (60% Weight)").font = bold_font
    ws1.cell(row=13, column=2, value=0.60).number_format = "0%"
    c_rvnl_alloc = ws1.cell(row=13, column=3, value="=D10*B13")
    c_rvnl_alloc.number_format = "₹#,##0"
    c_rvnl_alloc.font = bold_font
    c_rvnl_t1 = ws1.cell(row=13, column=4, value="=C13*0.50")
    c_rvnl_t1.number_format = "₹#,##0"
    c_rvnl_t2 = ws1.cell(row=13, column=5, value="=C13*0.50")
    c_rvnl_t2.number_format = "₹#,##0"
    c_rvnl_p1 = ws1.cell(row=13, column=6, value="=C13*0.125") # +12.5%
    c_rvnl_p1.number_format = "₹#,##0 (+12.5%)"
    c_rvnl_p1.font = green_bold_font
    c_rvnl_p2 = ws1.cell(row=13, column=7, value="=C13*0.252") # +25.2%
    c_rvnl_p2.number_format = "₹#,##0 (+25.2%)"
    c_rvnl_p2.font = green_bold_font
    c_rvnl_p3 = ws1.cell(row=13, column=8, value="=C13*0.420") # +42.0%
    c_rvnl_p3.number_format = "₹#,##0 (+42.0%)"
    c_rvnl_p3.font = green_bold_font

    # IRFC row
    ws1.cell(row=14, column=1, value="IRFC (40% Weight)").font = bold_font
    ws1.cell(row=14, column=2, value=0.40).number_format = "0%"
    c_irfc_alloc = ws1.cell(row=14, column=3, value="=D10*B14")
    c_irfc_alloc.number_format = "₹#,##0"
    c_irfc_alloc.font = bold_font
    c_irfc_t1 = ws1.cell(row=14, column=4, value="=C14*0.60")
    c_irfc_t1.number_format = "₹#,##0"
    c_irfc_t2 = ws1.cell(row=14, column=5, value="=C14*0.40")
    c_irfc_t2.number_format = "₹#,##0"
    c_irfc_p1 = ws1.cell(row=14, column=6, value="=C14*0.104") # +10.4%
    c_irfc_p1.number_format = "₹#,##0 (+10.4%)"
    c_irfc_p1.font = green_bold_font
    c_irfc_p2 = ws1.cell(row=14, column=7, value="=C14*0.220") # +22.0%
    c_irfc_p2.number_format = "₹#,##0 (+22.0%)"
    c_irfc_p2.font = green_bold_font
    c_irfc_p3 = ws1.cell(row=14, column=8, value="=C14*0.390") # +39.0%
    c_irfc_p3.number_format = "₹#,##0 (+39.0%)"
    c_irfc_p3.font = green_bold_font

    # Total Blended Portfolio Row
    ws1.cell(row=15, column=1, value="TOTAL PORTFOLIO").font = Font(name=font_family, size=10, bold=True, color="1E3A8A")
    ws1.cell(row=15, column=2, value="=SUM(B13:B14)").number_format = "0%"
    c_tot_alloc = ws1.cell(row=15, column=3, value="=SUM(C13:C14)")
    c_tot_alloc.number_format = "₹#,##0"
    c_tot_alloc.font = bold_font
    c_tot_t1 = ws1.cell(row=15, column=4, value="=SUM(D13:D14)")
    c_tot_t1.number_format = "₹#,##0"
    c_tot_t2 = ws1.cell(row=15, column=5, value="=SUM(E13:E14)")
    c_tot_t2.number_format = "₹#,##0"
    c_tot_p1 = ws1.cell(row=15, column=6, value="=SUM(F13:F14)")
    c_tot_p1.number_format = "₹#,##0"
    c_tot_p1.font = green_bold_font
    c_tot_p2 = ws1.cell(row=15, column=7, value="=SUM(G13:G14)")
    c_tot_p2.number_format = "₹#,##0"
    c_tot_p2.font = green_bold_font
    c_tot_p3 = ws1.cell(row=15, column=8, value="=SUM(H13:H14)")
    c_tot_p3.number_format = "₹#,##0"
    c_tot_p3.font = green_bold_font

    for r in range(13, 16):
        ws1.row_dimensions[r].height = 22
        for c in range(1, 9):
            ws1.cell(row=r, column=c).border = cell_border
            if r == 15:
                ws1.cell(row=r, column=c).fill = kpi_bg_fill
                ws1.cell(row=r, column=c).border = double_bottom

    # Key Directives
    ws1.merge_cells("A17:H17")
    ws1["A17"] = "3. STRATEGIC EXECUTION RULES"
    ws1["A17"].font = section_font
    ws1.row_dimensions[17].height = 24

    rules = [
        ("Rule 1: Staggered Tranche Buying", "Deploy Tranche 1 immediately on Monday at market open (near 52-week low). Keep Tranche 2 reserved to deploy ONLY if NIFTY dips."),
        ("Rule 2: Stop-Loss Discipline", "RVNL Stop-Loss is ₹160.00 (closing basis). IRFC Stop-Loss is ₹66.00 (closing basis). Exit immediately if closing below these floors."),
        ("Rule 3: Profit De-Risking", "At Target 1 (T1), book 40% profit and move your stop-loss up to your entry price to lock in a completely risk-free trade."),
        ("Rule 4: Pre-Budget Holding Window", "Hold the remaining 60% position through December 2026 to January 2027 to capture the historic pre-budget railway rally.")
    ]
    for idx, (title, desc) in enumerate(rules, start=18):
        ws1.cell(row=idx, column=1, value=title).font = bold_font
        ws1.cell(row=idx, column=1).fill = zebra_fill
        ws1.merge_cells(start_row=idx, start_column=2, end_row=idx, end_column=8)
        ws1.cell(row=idx, column=2, value=desc).font = regular_font
        for c in range(1, 9):
            ws1.cell(row=idx, column=c).border = cell_border
        ws1.row_dimensions[idx].height = 22

    # Column dimensions for ws1
    col_widths_1 = [18, 32, 16, 16, 16, 20, 20, 36]
    for idx, w in enumerate(col_widths_1, start=1):
        ws1.column_dimensions[get_column_letter(idx)].width = w

    # =============================================================
    # SHEET 2: RVNL MASTER STRATEGY
    # =============================================================
    ws2 = wb.create_sheet(title="RVNL Strategy")
    ws2.views.sheetView[0].showGridLines = True

    # Title
    ws2.merge_cells("A1:G1")
    ws2["A1"] = "RAIL VIKAS NIGAM LIMITED (NSE: RVNL) — MASTER TRADING BLUEPRINT"
    ws2["A1"].font = title_font
    ws2["A1"].fill = rvnl_header_fill
    ws2["A1"].alignment = center_align
    ws2.row_dimensions[1].height = 36

    ws2.merge_cells("A2:G2")
    ws2["A2"] = "LTP: ₹193.34 | 52W High: ₹400.70 | 52W Low: ₹177.86 | Rebound from Low: +8.7% | RSI: 42.5"
    ws2["A2"].font = subtitle_font
    ws2["A2"].fill = rvnl_header_fill
    ws2["A2"].alignment = center_align
    ws2.row_dimensions[2].height = 20

    # Technical Overview Table
    ws2.merge_cells("A4:G4")
    ws2["A4"] = "1. TECHNICAL BENCHMARKS & DOWNSIDE FLOORS"
    ws2["A4"].font = section_font
    ws2.row_dimensions[4].height = 24

    headers_tech_rvnl = ["Indicator / Level", "Value (₹)", "Status / Interpretation", "Strategic Takeaway", "Probability", "Action Directive", "Notes"]
    for c_idx, h in enumerate(headers_tech_rvnl, start=1):
        c = ws2.cell(row=5, column=c_idx, value=h)
        c.font = header_font
        c.fill = rvnl_header_fill
        c.alignment = center_align
        c.border = cell_border
    ws2.row_dimensions[5].height = 26

    tech_rvnl_rows = [
        ("Current Market Price (LTP)", "₹193.34", "Rebounded from 52W Low (₹177.86)", "Double bottom accumulation zone", "100%", "Buy Tranche 1", "Up +8.7% from recent low"),
        ("Immediate Downside Floor", "₹175.00 – ₹177.00", "52-Week Low Shelf", "Strong institutional support base", "80% holds", "Accumulate", "Highest volume node"),
        ("Worst-Case Macro Floor", "₹162.00 – ₹165.00", "Pre-Breakout Base (Late 2023)", "Extreme oversold capitulation limit", "20% risk", "Average Down (Tranche 2)", "Maximum downside cap"),
        ("20-Day SMA", "₹190.72", "Immediate Resistance", "First overhead hurdle", "High breakout", "Target 1 Area", "Retest expected within 2 weeks"),
        ("50-Day SMA", "₹202.49", "Intermediate Resistance", "Key trend reversal confirmation", "High breakout", "Target 1 Cap", "Profit taking shelf"),
        ("100-Day SMA", "₹217.02", "Major Resistance", "Trend transition boundary", "Medium", "Target 2 Area", "1 to 2 month swing target"),
        ("200-Day SMA", "₹255.02", "Long-Term Structural Line", "Full valuation mean reversion", "Target T3", "Target 3 Area", "Pre-Budget 2027 Target")
    ]
    for r_idx, r in enumerate(tech_rvnl_rows, start=6):
        ws2.cell(row=r_idx, column=1, value=r[0]).font = bold_font
        ws2.cell(row=r_idx, column=2, value=r[1]).font = bold_font
        ws2.cell(row=r_idx, column=3, value=r[2]).font = regular_font
        ws2.cell(row=r_idx, column=4, value=r[3]).font = regular_font
        ws2.cell(row=r_idx, column=5, value=r[4]).font = regular_font
        ws2.cell(row=r_idx, column=6, value=r[5]).font = green_bold_font
        ws2.cell(row=r_idx, column=7, value=r[6]).font = regular_font
        for c in range(1, 8):
            ws2.cell(row=r_idx, column=c).border = cell_border
        ws2.row_dimensions[r_idx].height = 20

    # Tranche Buy Plan
    ws2.merge_cells("A15:G15")
    ws2["A15"] = "2. TWO-TRANCHE ACCUMULATION PLAN"
    ws2["A15"].font = section_font
    ws2.row_dimensions[15].height = 24

    headers_tranche = ["Tranche", "Allocation %", "Target Price Zone (₹)", "Order Type", "Execution Trigger", "Expected Blended Cost", "Max Risk to Stop-Loss"]
    for c_idx, h in enumerate(headers_tranche, start=1):
        c = ws2.cell(row=16, column=c_idx, value=h)
        c.font = header_font
        c.fill = rvnl_header_fill
        c.alignment = center_align
        c.border = cell_border
    ws2.row_dimensions[16].height = 26

    tranches_rvnl = [
        ("Tranche 1 (Immediate)", "50%", "₹178.00 – ₹181.00", "Limit / Market Open", "Current 52-week low bounce", "₹179.67", "10.9% to ₹160 SL"),
        ("Tranche 2 (Dip Reserve)", "50%", "₹168.00 – ₹172.00", "GTT / Limit Order", "Deploy only if market pulls back", "₹174.50 Average", "8.3% to ₹160 SL")
    ]
    for r_idx, r in enumerate(tranches_rvnl, start=17):
        for c_idx, val in enumerate(r, start=1):
            c = ws2.cell(row=r_idx, column=c_idx, value=val)
            c.font = bold_font if c_idx in [1, 2, 3, 6] else regular_font
            c.border = cell_border
        ws2.row_dimensions[r_idx].height = 22

    # Target Roadmap
    ws2.merge_cells("A21:G21")
    ws2["A21"] = "3. MULTI-STAGE PROFIT TARGET ROADMAP"
    ws2["A21"].font = section_font
    ws2.row_dimensions[21].height = 24

    headers_target = ["Target Tier", "Price Target (₹)", "Expected Return %", "Holding Horizon", "Risk-to-Reward Ratio", "Trading Action", "Catalyst Anchor"]
    for c_idx, h in enumerate(headers_target, start=1):
        c = ws2.cell(row=22, column=c_idx, value=h)
        c.font = header_font
        c.fill = rvnl_header_fill
        c.alignment = center_align
        c.border = cell_border
    ws2.row_dimensions[22].height = 26

    targets_rvnl = [
        ("Target 1 (Fast Swing)", "₹202.00", "+12.5% to +15.8%", "2 to 3 Weeks", "1 : 1.5", "Book 40% Profit; Move SL to Cost", "20/50 SMA Reversion + Q2 Results"),
        ("Target 2 (Swing Peak)", "₹225.00", "+25.2% to +28.9%", "1 to 2 Months", "1 : 3.0", "Book 30% Profit; Trail with 20 SMA", "Kavach Orders + Vande Bharat Sleeper"),
        ("Target 3 (Positional / Pre-Budget)", "₹255.00", "+42.0% to +46.1%", "2 to 4 Months", "1 : 5.0", "Trail Remaining 30% to Budget Week", "Pre-Budget Rally + Railway Capex Expansion")
    ]
    for r_idx, r in enumerate(targets_rvnl, start=23):
        for c_idx, val in enumerate(r, start=1):
            c = ws2.cell(row=r_idx, column=c_idx, value=val)
            c.font = green_bold_font if c_idx == 3 else (bold_font if c_idx in [1, 2] else regular_font)
            c.border = cell_border
        ws2.row_dimensions[r_idx].height = 22

    # Column widths for ws2
    col_widths_2 = [24, 20, 24, 28, 16, 26, 32]
    for idx, w in enumerate(col_widths_2, start=1):
        ws2.column_dimensions[get_column_letter(idx)].width = w

    # =============================================================
    # SHEET 3: IRFC MASTER STRATEGY
    # =============================================================
    ws3 = wb.create_sheet(title="IRFC Strategy")
    ws3.views.sheetView[0].showGridLines = True

    # Title
    ws3.merge_cells("A1:G1")
    ws3["A1"] = "INDIAN RAILWAY FINANCE CORPORATION (NSE: IRFC) — MASTER BLUEPRINT"
    ws3["A1"].font = title_font
    ws3["A1"].fill = irfc_header_fill
    ws3["A1"].alignment = center_align
    ws3.row_dimensions[1].height = 36

    ws3.merge_cells("A2:G2")
    ws3["A2"] = "LTP: ₹80.43 | 52W High: ₹137.17 | 52W Low: ₹73.05 | Rebound from Low: +10.1% | Div Yield: ~3.8% | Zero NPA"
    ws3["A2"].font = subtitle_font
    ws3["A2"].fill = irfc_header_fill
    ws3["A2"].alignment = center_align
    ws3.row_dimensions[2].height = 20

    # Technical Overview Table
    ws3.merge_cells("A4:G4")
    ws3["A4"] = "1. TECHNICAL BENCHMARKS & DOWNSIDE FLOORS"
    ws3["A4"].font = section_font
    ws3.row_dimensions[4].height = 24

    for c_idx, h in enumerate(headers_tech_rvnl, start=1):
        c = ws3.cell(row=5, column=c_idx, value=h)
        c.font = header_font
        c.fill = irfc_header_fill
        c.alignment = center_align
        c.border = cell_border
    ws3.row_dimensions[5].height = 26

    tech_irfc_rows = [
        ("Current Market Price (LTP)", "₹80.43", "Rebounded +10.1% from ₹73.05 Low", "Bounced sharply off support", "100%", "Buy Tranche 1 (60%)", "Highest dividend yield support shelf"),
        ("Immediate Downside Floor", "₹74.00 – ₹76.00", "Support Shelf", "Strong demand floor on pullbacks", "85% holds", "Tranche 2 Dip Buy", "38M shares traded on Oct 30"),
        ("Worst-Case Macro Floor", "₹67.00 – ₹69.00", "Structural Base", "Unprecedented value floor", "15% risk", "Final Accumulation", "Maximum downside risk < 6%"),
        ("20-Day SMA", "₹76.56", "Immediate Resistance", "First overhead test", "High", "Short-term hurdle", "1 to 2 week test"),
        ("50-Day SMA", "₹79.92", "Intermediate Resistance", "Key mean-reversion level", "High", "Target 1 Level", "Target 1 area (₹81.00)"),
        ("100-Day SMA", "₹85.40", "Major Resistance", "Trend transition line", "Medium-High", "Target 2 Level", "Target 2 area (₹90.00)"),
        ("200-Day SMA", "₹95.13", "Long-Term Structural Line", "Long-term mean valuation", "Target T3", "Target 3 Level", "Pre-Budget Target (₹98 – ₹102)")
    ]
    for r_idx, r in enumerate(tech_irfc_rows, start=6):
        ws3.cell(row=r_idx, column=1, value=r[0]).font = bold_font
        ws3.cell(row=r_idx, column=2, value=r[1]).font = bold_font
        ws3.cell(row=r_idx, column=3, value=r[2]).font = regular_font
        ws3.cell(row=r_idx, column=4, value=r[3]).font = regular_font
        ws3.cell(row=r_idx, column=5, value=r[4]).font = regular_font
        ws3.cell(row=r_idx, column=6, value=r[5]).font = green_bold_font
        ws3.cell(row=r_idx, column=7, value=r[6]).font = regular_font
        for c in range(1, 8):
            ws3.cell(row=r_idx, column=c).border = cell_border
        ws3.row_dimensions[r_idx].height = 20

    # Tranche Buy Plan
    ws3.merge_cells("A15:G15")
    ws3["A15"] = "2. TWO-TRANCHE ACCUMULATION PLAN"
    ws3["A15"].font = section_font
    ws3.row_dimensions[15].height = 24

    for c_idx, h in enumerate(headers_tranche, start=1):
        c = ws3.cell(row=16, column=c_idx, value=h)
        c.font = header_font
        c.fill = irfc_header_fill
        c.alignment = center_align
        c.border = cell_border
    ws3.row_dimensions[16].height = 26

    tranches_irfc = [
        ("Tranche 1 (Immediate)", "60%", "₹72.50 – ₹73.80", "Limit / Market Open", "Current 52-week low floor", "₹73.37", "10.0% to ₹66 SL"),
        ("Tranche 2 (Dip Reserve)", "40%", "₹69.00 – ₹70.50", "GTT / Limit Order", "Deploy only if market pulls back", "₹72.00 Average", "8.3% to ₹66 SL")
    ]
    for r_idx, r in enumerate(tranches_irfc, start=17):
        for c_idx, val in enumerate(r, start=1):
            c = ws3.cell(row=r_idx, column=c_idx, value=val)
            c.font = bold_font if c_idx in [1, 2, 3, 6] else regular_font
            c.border = cell_border
        ws3.row_dimensions[r_idx].height = 22

    # Target Roadmap
    ws3.merge_cells("A21:G21")
    ws3["A21"] = "3. MULTI-STAGE PROFIT TARGET ROADMAP"
    ws3["A21"].font = section_font
    ws3.row_dimensions[21].height = 24

    for c_idx, h in enumerate(headers_target, start=1):
        c = ws3.cell(row=22, column=c_idx, value=h)
        c.font = header_font
        c.fill = irfc_header_fill
        c.alignment = center_align
        c.border = cell_border
    ws3.row_dimensions[22].height = 26

    targets_irfc = [
        ("Target 1 (Short-Term)", "₹81.00", "+10.4% to +12.5%", "2 to 4 Weeks", "1 : 1.3", "Book 30% Profit; Move SL to Cost", "50-Day SMA Reversion + Dividend Credit"),
        ("Target 2 (Swing Target)", "₹90.00", "+22.0% to +25.0%", "1 to 2 Months", "1 : 2.7", "Book 40% Profit; Trail Stop-Loss", "AUM Growth to ₹5 Lakh Cr + Rate Cut Hopes"),
        ("Target 3 (Positional / Pre-Budget)", "₹102.00", "+39.0% to +41.6%", "2 to 4 Months", "1 : 4.8", "Hold for Union Budget 2027 Capex", "Annual Capex Boost + Sovereign Backing")
    ]
    for r_idx, r in enumerate(targets_irfc, start=23):
        for c_idx, val in enumerate(r, start=1):
            c = ws3.cell(row=r_idx, column=c_idx, value=val)
            c.font = green_bold_font if c_idx == 3 else (bold_font if c_idx in [1, 2] else regular_font)
            c.border = cell_border
        ws3.row_dimensions[r_idx].height = 22

    for idx, w in enumerate(col_widths_2, start=1):
        ws3.column_dimensions[get_column_letter(idx)].width = w

    # =============================================================
    # SHEET 4: NEWS CATALYSTS & FUTURE PREDICTIONS
    # =============================================================
    ws4 = wb.create_sheet(title="News & Predictions")
    ws4.views.sheetView[0].showGridLines = True

    # Title
    ws4.merge_cells("A1:G1")
    ws4["A1"] = "UPCOMING NEWS, PREDICTIVE CATALYSTS & STRATEGIC BLUEPRINT (2026–2027)"
    ws4["A1"].font = title_font
    ws4["A1"].fill = primary_header_fill
    ws4["A1"].alignment = center_align
    ws4.row_dimensions[1].height = 36

    ws4.merge_cells("A2:G2")
    ws4["A2"] = "Forward-Looking Catalyst Timeline: Board Meetings, Order Tenders, Vande Bharat Sleeper, and Pre-Budget Seasonality"
    ws4["A2"].font = subtitle_font
    ws4["A2"].fill = primary_header_fill
    ws4["A2"].alignment = center_align
    ws4.row_dimensions[2].height = 20

    headers_news = ["Timeline / Date", "Stock Impacted", "Catalyst / News Event", "Expected Announcement Details", "Probability", "Predicted Price Impact", "Strategic Action"]
    for c_idx, h in enumerate(headers_news, start=1):
        c = ws4.cell(row=4, column=c_idx, value=h)
        c.font = header_font
        c.fill = sub_header_fill
        c.alignment = center_align
        c.border = cell_border
    ws4.row_dimensions[4].height = 26

    news_data = [
        ("Mid-November 2026", "RVNL", "Q2 FY27 Earnings Board Meeting", "Expected revenue ~₹5,400 Cr; EBITDA margins steady at 6.0%. Interim dividend possibility.", "95%", "+5% to +8% Relief Rally", "Accumulate ahead of results at 52W low"),
        ("Late November 2026", "RVNL", "Vande Bharat Sleeper Commercial Trials", "First prototype commercial run between Delhi and Patna/Mumbai. Joint execution with Russia's TMH.", "90%", "+7% to +10% Sentiment Surge", "Hold for Target 1 (₹202)"),
        ("Late November 2026", "IRFC", "Interim Dividend Payout (₹1.15/share)", "Cash payout credited to demat-linked bank accounts for eligible shareholders (Record Date Oct 23).", "100%", "Dividend Yield Floor (3.8%)", "Reinvest dividend cash into RVNL"),
        ("Early December 2026", "RVNL & IRFC", "Cabinet Approval for High-Density Corridors", "CCEA sanction for 7 new railway multi-tracking projects worth ~₹24,000 Crore.", "85%", "+6% to +12% Sector Momentum", "Hold positions; trail stops"),
        ("Mid-December 2026", "RVNL", "Mega Kavach Safety Tender Allocations", "Ministry of Railways awarding Kavach 4.0 safety bids (~₹8,000 Cr) across 10,000 km tracks.", "80%", "+10% to +15% Order Book Boost", "Target 2 (₹225) reachable"),
        ("Dec 2026 – Jan 2027", "RVNL & IRFC", "Historic Pre-Budget Railway Rally", "Annual seasonal phenomenon: Railway stocks historically rally 20% to 45% ahead of Feb 1 Budget.", "85%", "+20% to +35% Broad Wave", "Do NOT sell early; trail stop-loss"),
        ("February 1, 2027", "RVNL & IRFC", "Union Budget 2027 Railway Capex", "Expected Gross Budgetary Support (GBS) of ₹2.75–3.00 Lakh Crore for Indian Railways.", "90%", "+15% to +25% Final Run", "Book Target 3 profits on Budget Day")
    ]

    for r_idx, r in enumerate(news_data, start=5):
        for c_idx, val in enumerate(r, start=1):
            c = ws4.cell(row=r_idx, column=c_idx, value=val)
            if c_idx == 1:
                c.font = bold_font
            elif c_idx == 2:
                c.font = blue_bold_font
            elif c_idx == 6:
                c.font = green_bold_font
            else:
                c.font = regular_font
            c.border = cell_border
        ws4.row_dimensions[r_idx].height = 24

    col_widths_4 = [20, 16, 28, 38, 14, 24, 28]
    for idx, w in enumerate(col_widths_4, start=1):
        ws4.column_dimensions[get_column_letter(idx)].width = w

    # =============================================================
    # SHEET 5: POSITION SIZING SIMULATOR
    # =============================================================
    ws5 = wb.create_sheet(title="Position Sizing Matrix")
    ws5.views.sheetView[0].showGridLines = True

    # Title
    ws5.merge_cells("A1:H1")
    ws5["A1"] = "READY-MADE CAPITAL ALLOCATION & POSITION SIZING MATRIX"
    ws5["A1"].font = title_font
    ws5["A1"].fill = primary_header_fill
    ws5["A1"].alignment = center_align
    ws5.row_dimensions[1].height = 36

    ws5.merge_cells("A2:H2")
    ws5["A2"] = "Exact Share Quantities, Tranche Splits, and Profit Projections for ₹50,000, ₹1,00,000, ₹2,00,000, and ₹5,00,000 Portfolios"
    ws5["A2"].font = subtitle_font
    ws5["A2"].fill = primary_header_fill
    ws5["A2"].alignment = center_align
    ws5.row_dimensions[2].height = 20

    headers_sim = ["Capital Tier", "Stock Symbol", "Total Qty (Shares)", "Tranche 1 Qty", "Tranche 2 Qty", "T1 Profit (₹)", "T2 Profit (₹)", "T3 Profit (₹)"]
    for c_idx, h in enumerate(headers_sim, start=1):
        c = ws5.cell(row=4, column=c_idx, value=h)
        c.font = header_font
        c.fill = primary_header_fill
        c.alignment = center_align
        c.border = cell_border
    ws5.row_dimensions[4].height = 26

    tiers = [
        # (Tier, Symbol, Qty, T1 Qty, T2 Qty, T1 Profit, T2 Profit, T3 Profit)
        ("₹50,000 Total", "RVNL (₹30,000)", 167, 84, 83, 3729, 7570, 12580),
        ("₹50,000 Total", "IRFC (₹20,000)", 273, 164, 109, 2083, 4540, 7816),
        ("₹1,00,000 Total", "RVNL (₹60,000)", 334, 167, 167, 7458, 15140, 25160),
        ("₹1,00,000 Total", "IRFC (₹40,000)", 545, 327, 218, 4158, 9063, 15602),
        ("₹2,00,000 Total", "RVNL (₹1,20,000)", 668, 334, 334, 14916, 30280, 50320),
        ("₹2,00,000 Total", "IRFC (₹80,000)", 1090, 654, 436, 8316, 18126, 31204),
        ("₹5,00,000 Total", "RVNL (₹3,00,000)", 1670, 835, 835, 37290, 75700, 125800),
        ("₹5,00,000 Total", "IRFC (₹2,00,000)", 2725, 1635, 1090, 20790, 45315, 78010)
    ]

    for r_idx, r in enumerate(tiers, start=5):
        ws5.cell(row=r_idx, column=1, value=r[0]).font = bold_font
        ws5.cell(row=r_idx, column=2, value=r[1]).font = blue_bold_font if "IRFC" in r[1] else Font(name=font_family, size=10, bold=True, color="0F766E")
        ws5.cell(row=r_idx, column=3, value=r[2]).font = bold_font
        ws5.cell(row=r_idx, column=4, value=r[3]).font = regular_font
        ws5.cell(row=r_idx, column=5, value=r[4]).font = regular_font

        c6 = ws5.cell(row=r_idx, column=6, value=r[5])
        c6.font = green_bold_font
        c6.number_format = "₹#,##0"

        c7 = ws5.cell(row=r_idx, column=7, value=r[6])
        c7.font = green_bold_font
        c7.number_format = "₹#,##0"

        c8 = ws5.cell(row=r_idx, column=8, value=r[7])
        c8.font = green_bold_font
        c8.number_format = "₹#,##0"

        for c in range(1, 9):
            ws5.cell(row=r_idx, column=c).border = cell_border
            if r_idx % 2 == 0:
                ws5.cell(row=r_idx, column=c).fill = zebra_fill
        ws5.row_dimensions[r_idx].height = 22

    col_widths_5 = [18, 22, 18, 16, 16, 16, 16, 16]
    for idx, w in enumerate(col_widths_5, start=1):
        ws5.column_dimensions[get_column_letter(idx)].width = w

    # Save workbook
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT_FILE)
    print(f"✅ Master Excel created successfully at: {OUTPUT_FILE}")

if __name__ == "__main__":
    create_excel()
