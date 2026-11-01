"""
Generate high-impact, professional Excel workbook for the ₹2,00,000 capital -> ₹50,000 profit plan.
"""

from datetime import datetime
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent

def build_2l_plan_excel():
    wb = openpyxl.Workbook()

    # Common Color Palette & Fills
    navy_dark = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
    navy_accent = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
    kpi_card_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    gold_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    zebra_even = PatternFill(start_color="F2F4F8", end_color="F2F4F8", fill_type="solid")
    soft_green = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    soft_red = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
    total_fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")

    # Fonts
    font_title = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
    font_subtitle = Font(name="Calibri", size=10, italic=True, color="D9E1F2")
    font_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    font_kpi_lbl = Font(name="Calibri", size=9, bold=True, color="1B365D")
    font_kpi_val = Font(name="Calibri", size=14, bold=True, color="1B365D")
    font_bold = Font(name="Calibri", size=10, bold=True)
    font_regular = Font(name="Calibri", size=10)
    font_green = Font(name="Calibri", size=10, bold=True, color="276A3C")
    font_red = Font(name="Calibri", size=10, bold=True, color="C00000")

    # Borders
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )
    header_border = Border(
        left=Side(style='thin', color='1B365D'),
        right=Side(style='thin', color='1B365D'),
        top=Side(style='medium', color='1B365D'),
        bottom=Side(style='medium', color='1B365D')
    )
    total_border = Border(
        top=Side(style='thin', color='000000'),
        bottom=Side(style='double', color='000000')
    )

    # =========================================================================
    # SHEET 1: MASTER SUMMARY & ROADMAP
    # =========================================================================
    ws1 = wb.active
    ws1.title = "Master Blueprint (₹50k Plan)"
    ws1.views.sheetView[0].showGridLines = True

    # Title
    ws1.merge_cells("A1:K1")
    t1 = ws1["A1"]
    t1.value = "₹2,00,000 CAPITAL ACCELERATOR — ₹50,000 NET PROFIT BLUEPRINT (2 MONTHS)"
    t1.font = font_title
    t1.fill = navy_dark
    t1.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 36

    ws1.merge_cells("A2:K2")
    st1 = ws1["A2"]
    st1.value = f"Created: {datetime.now().strftime('%d-%b-%Y')} | Horizon: Nov-Dec 2026 | Strategy: 2-Cycle Compound Swing (100% Cash Delivery)"
    st1.font = font_subtitle
    st1.fill = navy_dark
    st1.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[2].height = 20

    # KPI Summary Cards (Row 4-5)
    kpis = [
        ("A4:B4", "A5:B5", "STARTING CAPITAL", "₹2,00,000"),
        ("C4:D4", "C5:D5", "TARGET NET PROFIT", "+₹50,000 (+25.0%)"),
        ("E4:F4", "E5:F5", "TOTAL FINAL CAPITAL", "₹2,52,490"),
        ("G4:H4", "G5:H5", "MAX CYCLE 1 RISK", "₹8,201 (4.1%)"),
        ("I4:K4", "I5:K5", "STRATEGY RISK-REWARD", "1 : 6.4 (Risk 8.2k for 52.5k)")
    ]
    for lbl_rng, val_rng, label, val_text in kpis:
        ws1.merge_cells(lbl_rng)
        cl = ws1[lbl_rng.split(":")[0]]
        cl.value = label
        cl.font = font_kpi_lbl
        cl.fill = kpi_card_fill
        cl.alignment = Alignment(horizontal="center", vertical="center")

        ws1.merge_cells(val_rng)
        cv = ws1[val_rng.split(":")[0]]
        cv.value = val_text
        cv.font = font_kpi_val
        cv.fill = kpi_card_fill
        cv.alignment = Alignment(horizontal="center", vertical="center")

    ws1.row_dimensions[4].height = 18
    ws1.row_dimensions[5].height = 26

    # Milestone Progression Table (Row 7)
    ws1.merge_cells("A7:K7")
    ms_title = ws1["A7"]
    ms_title.value = "2-STAGE COMPOUNDING PROGRESSION ROADMAP"
    ms_title.font = font_header
    ms_title.fill = navy_accent
    ms_title.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws1.row_dimensions[7].height = 24

    ms_headers = [
        ("Stage / Milestone", 22),
        ("Execution Window", 20),
        ("Deployed Capital", 18),
        ("Selected Stocks", 28),
        ("Expected Profit", 18),
        ("Return (%)", 14),
        ("Downside Risk", 16),
        ("Capital at End", 18),
        ("Status / Objective", 30)
    ]
    ws1.row_dimensions[8].height = 24
    for idx, (h, w) in enumerate(ms_headers, 1):
        c = ws1.cell(row=8, column=idx, value=h)
        c.font = font_header
        c.fill = navy_dark
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = header_border
        ws1.column_dimensions[get_column_letter(idx)].width = w

    milestone_rows = [
        ("Cycle 1 (November)", "01-Nov to 28-Nov 2026", 200000, "KOTAKBANK, LAURUSLABS, ADANIPORTS", 22441, 0.1122, 8201, 222441, "Deploy ₹2L across 3 leaders; lock 50% at T1, trail SL"),
        ("Cycle 2 (December)", "01-Dec to 30-Dec 2026", 222441, "NYKAA, PNB, BLUESTARCO", 30049, 0.1351, 8950, 252490, "Re-deploy ₹2.22L capital into wave 2 breakouts"),
        ("FULL 2-MONTH OUTCOME", "Total Nov-Dec Horizon", 200000, "6 Diversified Market Leaders", 52490, 0.2625, 8201, 252490, "Target Achieved! Net Gain: +₹52,490 (+26.25%)")
    ]

    for r_idx, m in enumerate(milestone_rows, start=9):
        is_total = (r_idx == 11)
        ws1.row_dimensions[r_idx].height = 24
        for c_idx in range(1, 10):
            cell = ws1.cell(row=r_idx, column=c_idx, value=m[c_idx-1])
            cell.border = thin_border if not is_total else total_border
            if is_total:
                cell.font = font_bold
                cell.fill = gold_fill
            else:
                cell.font = font_regular if c_idx not in [5, 6, 8] else font_bold
                cell.fill = zebra_even if r_idx % 2 == 0 else PatternFill(fill_type=None)

            if c_idx in [3, 5, 7, 8]:
                cell.number_format = '₹#,##0'
                cell.alignment = Alignment(horizontal="right", vertical="center")
            elif c_idx == 6:
                cell.number_format = '0.0%'
                cell.alignment = Alignment(horizontal="right", vertical="center")
            elif c_idx in [1, 2]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    # =========================================================================
    # SHEET 2: CYCLE 1 (NOVEMBER TRADES - ₹2,00,000)
    # =========================================================================
    ws2 = wb.create_sheet(title="Cycle 1 — November (₹2L)")
    ws2.views.sheetView[0].showGridLines = True

    ws2.merge_cells("A1:P1")
    ws2["A1"].value = "CYCLE 1 (NOVEMBER 2026) — THREE-STOCK BASKET DEPLOYMENT (₹2,00,000)"
    ws2["A1"].font = font_title
    ws2["A1"].fill = navy_dark
    ws2["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 36

    ws2.merge_cells("A2:P2")
    ws2["A2"].value = "Capital: ₹2,00,000 | Strategy: 3 Uncorrelated Breakout Leaders | Profit Plan: Scale 50% at Target 1, Move SL to Cost, Ride Target 2"
    ws2["A2"].font = font_subtitle
    ws2["A2"].fill = navy_dark
    ws2["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[2].height = 20

    c1_headers = [
        ("Stock", 13),
        ("Sector", 20),
        ("Qty", 8),
        ("Buy Price", 13),
        ("Capital (₹)", 14),
        ("SL (₹)", 13),
        ("Max Risk (₹)", 14),
        ("Risk %", 10),
        ("T1 Price", 13),
        ("T1 Qty", 8),
        ("T1 Profit (₹)", 14),
        ("T2 Price", 13),
        ("T2 Qty", 8),
        ("T2 Profit (₹)", 14),
        ("Total Profit (₹)", 16),
        ("Return (%)", 12)
    ]
    ws2.row_dimensions[4].height = 26
    for idx, (h, w) in enumerate(c1_headers, 1):
        c = ws2.cell(row=4, column=idx, value=h)
        c.font = font_header
        c.fill = navy_accent
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = header_border
        ws2.column_dimensions[get_column_letter(idx)].width = w

    c1_data = [
        ("KOTAKBANK", "Private Banking", 142, 458.30, 65078.60, 439.90, 2612.80, 0.0401, 495.00, 71, 2605.70, 522.50, 71, 4558.20, 7163.90, 0.1101),
        ("LAURUSLABS", "Pharma & CDMO", 30, 2236.20, 67086.00, 2140.00, 2886.00, 0.0430, 2428.00, 15, 2877.00, 2570.00, 15, 5007.00, 7884.00, 0.1175),
        ("ADANIPORTS", "Infrastructure & Ports", 36, 1863.10, 67071.60, 1788.00, 2703.60, 0.0403, 2012.00, 18, 2680.20, 2125.00, 18, 4714.20, 7394.40, 0.1102)
    ]

    for r_idx, row in enumerate(c1_data, start=5):
        ws2.row_dimensions[r_idx].height = 24
        for c_idx, val in enumerate(row, 1):
            cell = ws2.cell(row=r_idx, column=c_idx, value=val)
            cell.border = thin_border
            cell.font = font_bold if c_idx in [1, 5, 15, 16] else font_regular
            if c_idx in [7, 8]:
                cell.font = font_red
            elif c_idx in [11, 14, 15, 16]:
                cell.font = font_green

            # Formatting
            if c_idx in [4, 5, 6, 7, 9, 11, 12, 14, 15]:
                cell.number_format = '₹#,##0.00'
                cell.alignment = Alignment(horizontal="right", vertical="center")
            elif c_idx in [8, 16]:
                cell.number_format = '0.0%'
                cell.alignment = Alignment(horizontal="right", vertical="center")
            elif c_idx in [3, 10, 13]:
                cell.number_format = '#,##0'
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif c_idx == 1:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    # Total Row for Cycle 1
    ws2.row_dimensions[8].height = 26
    ws2.cell(row=8, column=1, value="TOTALS").alignment = Alignment(horizontal="center", vertical="center")
    ws2.cell(row=8, column=1).font = font_bold
    ws2.cell(row=8, column=5, value="=SUM(E5:E7)").number_format = '₹#,##0.00'
    ws2.cell(row=8, column=7, value="=SUM(G5:G7)").number_format = '₹#,##0.00'
    ws2.cell(row=8, column=8, value="=G8/E8").number_format = '0.0%'
    ws2.cell(row=8, column=11, value="=SUM(K5:K7)").number_format = '₹#,##0.00'
    ws2.cell(row=8, column=14, value="=SUM(N5:N7)").number_format = '₹#,##0.00'
    ws2.cell(row=8, column=15, value="=SUM(O5:O7)").number_format = '₹#,##0.00'
    ws2.cell(row=8, column=16, value="=O8/E8").number_format = '0.0%'

    for col in range(1, 17):
        c = ws2.cell(row=8, column=col)
        c.fill = gold_fill
        c.border = total_border
        c.font = font_bold

    # Cash buffer note
    ws2.merge_cells("A10:H10")
    ws2["A10"].value = "💡 Unallocated Cash Buffer: ₹763.80 | Total Portfolio Risk: ₹8,202.40 (Only 4.1% of ₹2L capital)"
    ws2["A10"].font = Font(name="Calibri", size=10, italic=True, bold=True, color="1B365D")

    # =========================================================================
    # SHEET 3: CYCLE 2 (DECEMBER TRADES - ₹2,22,440)
    # =========================================================================
    ws3 = wb.create_sheet(title="Cycle 2 — December (₹2.22L)")
    ws3.views.sheetView[0].showGridLines = True

    ws3.merge_cells("A1:P1")
    ws3["A1"].value = "CYCLE 2 (DECEMBER 2026) — COMPOUNDED CAPITAL DEPLOYMENT (₹2,22,440)"
    ws3["A1"].font = font_title
    ws3["A1"].fill = navy_dark
    ws3["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws3.row_dimensions[1].height = 36

    ws3.merge_cells("A2:P2")
    ws3["A2"].value = "Re-investing Initial Capital + Cycle 1 Profits | Target: +₹30,000 to push cumulative profit over ₹50,000"
    ws3["A2"].font = font_subtitle
    ws3["A2"].fill = navy_dark
    ws3["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws3.row_dimensions[2].height = 20

    ws3.row_dimensions[4].height = 26
    for idx, (h, w) in enumerate(c1_headers, 1):
        c = ws3.cell(row=4, column=idx, value=h)
        c.font = font_header
        c.fill = navy_accent
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = header_border
        ws3.column_dimensions[get_column_letter(idx)].width = w

    c2_data = [
        ("NYKAA", "E-Commerce / Consumer", 213, 352.00, 74976.00, 335.40, 3535.80, 0.0472, 385.00, 106, 3498.00, 410.00, 107, 6206.00, 9704.00, 0.1294),
        ("PNB", "PSU Banking", 606, 123.75, 74992.50, 118.75, 3030.00, 0.0404, 133.70, 303, 3014.85, 141.20, 303, 5287.35, 8302.20, 0.1107),
        ("BLUESTARCO", "Consumer Durables / HVAC", 44, 1667.00, 73348.00, 1583.65, 3667.40, 0.0500, 1833.70, 22, 3667.40, 1958.70, 22, 6417.40, 10084.80, 0.1375)
    ]

    for r_idx, row in enumerate(c2_data, start=5):
        ws3.row_dimensions[r_idx].height = 24
        for c_idx, val in enumerate(row, 1):
            cell = ws3.cell(row=r_idx, column=c_idx, value=val)
            cell.border = thin_border
            cell.font = font_bold if c_idx in [1, 5, 15, 16] else font_regular
            if c_idx in [7, 8]:
                cell.font = font_red
            elif c_idx in [11, 14, 15, 16]:
                cell.font = font_green

            if c_idx in [4, 5, 6, 7, 9, 11, 12, 14, 15]:
                cell.number_format = '₹#,##0.00'
                cell.alignment = Alignment(horizontal="right", vertical="center")
            elif c_idx in [8, 16]:
                cell.number_format = '0.0%'
                cell.alignment = Alignment(horizontal="right", vertical="center")
            elif c_idx in [3, 10, 13]:
                cell.number_format = '#,##0'
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif c_idx == 1:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    # Total Row for Cycle 2
    ws3.row_dimensions[8].height = 26
    ws3.cell(row=8, column=1, value="TOTALS").alignment = Alignment(horizontal="center", vertical="center")
    ws3.cell(row=8, column=1).font = font_bold
    ws3.cell(row=8, column=5, value="=SUM(E5:E7)").number_format = '₹#,##0.00'
    ws3.cell(row=8, column=7, value="=SUM(G5:G7)").number_format = '₹#,##0.00'
    ws3.cell(row=8, column=8, value="=G8/E8").number_format = '0.0%'
    ws3.cell(row=8, column=11, value="=SUM(K5:K7)").number_format = '₹#,##0.00'
    ws3.cell(row=8, column=14, value="=SUM(N5:N7)").number_format = '₹#,##0.00'
    ws3.cell(row=8, column=15, value="=SUM(O5:O7)").number_format = '₹#,##0.00'
    ws3.cell(row=8, column=16, value="=O8/E8").number_format = '0.0%'

    for col in range(1, 17):
        c = ws3.cell(row=8, column=col)
        c.fill = gold_fill
        c.border = total_border
        c.font = font_bold

    # =========================================================================
    # SHEET 4: ZERODHA GTT ORDERS PLAYBOOK
    # =========================================================================
    ws4 = wb.create_sheet(title="Zerodha GTT Order Inputs")
    ws4.views.sheetView[0].showGridLines = True

    ws4.merge_cells("A1:H1")
    ws4["A1"].value = "ZERODHA KITE GTT (GOOD-TILL-TRIGGERED) OCO ORDER SETUP GUIDE"
    ws4["A1"].font = font_title
    ws4["A1"].fill = navy_dark
    ws4["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws4.row_dimensions[1].height = 36

    ws4.merge_cells("A2:H2")
    ws4["A2"].value = "Exact values to input in Zerodha Kite app after purchasing CNC shares tomorrow morning"
    ws4["A2"].font = font_subtitle
    ws4["A2"].fill = navy_dark
    ws4["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws4.row_dimensions[2].height = 20

    gtt_headers = [
        ("Stock Symbol", 15),
        ("Product", 10),
        ("Order Qty", 10),
        ("Stop Loss Trigger", 18),
        ("Stop Loss Limit", 18),
        ("Target 1 Trigger", 18),
        ("Target 1 Limit", 18),
        ("Execution Action & Trailing Rule", 45)
    ]
    ws4.row_dimensions[4].height = 26
    for idx, (h, w) in enumerate(gtt_headers, 1):
        c = ws4.cell(row=4, column=idx, value=h)
        c.font = font_header
        c.fill = navy_accent
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = header_border
        ws4.column_dimensions[get_column_letter(idx)].width = w

    gtt_rows = [
        ("KOTAKBANK", "CNC", 142, 440.00, 439.50, 495.00, 495.50, "At T1, sell 71 shares. Move SL for remaining 71 to ₹458.50 (Cost)"),
        ("LAURUSLABS", "CNC", 30, 2141.00, 2139.00, 2428.00, 2430.00, "At T1, sell 15 shares. Move SL for remaining 15 to ₹2,236.00 (Cost)"),
        ("ADANIPORTS", "CNC", 36, 1789.00, 1787.50, 2012.00, 2013.00, "At T1, sell 18 shares. Move SL for remaining 18 to ₹1,863.00 (Cost)"),
        ("NYKAA (Cycle 2)", "CNC", 213, 335.50, 335.00, 385.00, 385.50, "December deployment: book 50% @ T1, trail balance to cost"),
        ("PNB (Cycle 2)", "CNC", 606, 118.80, 118.60, 133.70, 133.80, "December deployment: book 50% @ T1, trail balance to cost"),
        ("BLUESTARCO (Cycle 2)", "CNC", 44, 1584.00, 1582.00, 1833.00, 1834.00, "December deployment: book 50% @ T1, trail balance to cost")
    ]

    for r_idx, row in enumerate(gtt_rows, start=5):
        ws4.row_dimensions[r_idx].height = 24
        for c_idx, val in enumerate(row, 1):
            cell = ws4.cell(row=r_idx, column=c_idx, value=val)
            cell.border = thin_border
            cell.font = font_bold if c_idx in [1, 3] else font_regular
            if c_idx in [4, 5]:
                cell.font = font_red
                cell.number_format = '₹#,##0.00'
                cell.alignment = Alignment(horizontal="right", vertical="center")
            elif c_idx in [6, 7]:
                cell.font = font_green
                cell.number_format = '₹#,##0.00'
                cell.alignment = Alignment(horizontal="right", vertical="center")
            elif c_idx in [1, 2, 3]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    output_path = ROOT / "Two_Lakh_Capital_50K_Profit_Plan_2026-10-29.xlsx"
    wb.save(output_path)
    print(f"✅ Excel file created at: {output_path}")

if __name__ == "__main__":
    build_2l_plan_excel()
