"""
generate_diwali_2tranche_plan.py
Generates the Diwali_Muhurat_Two_Tranche_1L_Plus_1L_Plan_2026.xlsx workbook
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT_FILE = Path("D:/NiftyScanner/STOCK_SWING_V1_updated/Diwali_Muhurat_Two_Tranche_1L_Plus_1L_Plan_2026.xlsx")

def build_excel():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Diwali 1L+1L Strategy"
    ws.views.sheetView[0].showGridLines = True

    font_family = "Segoe UI"
    title_font = Font(name=font_family, size=15, bold=True, color="FFFFFF")
    subtitle_font = Font(name=font_family, size=10, italic=True, color="FEF3C7")
    header_font = Font(name=font_family, size=10, bold=True, color="FFFFFF")
    bold_font = Font(name=font_family, size=10, bold=True, color="0F172A")
    regular_font = Font(name=font_family, size=10, color="334155")
    green_bold = Font(name=font_family, size=10, bold=True, color="15803D")
    red_bold = Font(name=font_family, size=10, bold=True, color="B91C1C")
    blue_bold = Font(name=font_family, size=10, bold=True, color="1D4ED8")

    primary_fill = PatternFill(start_color="78350F", end_color="78350F", fill_type="solid") # Warm Deep Gold/Brown (Diwali)
    sub_fill = PatternFill(start_color="B45309", end_color="B45309", fill_type="solid")     # Amber Gold
    zebra_fill = PatternFill(start_color="FFFBEB", end_color="FFFBEB", fill_type="solid")
    kpi_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")

    border_thin = Border(
        left=Side(style="thin", color="CBD5E1"), right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"), bottom=Side(style="thin", color="CBD5E1")
    )
    double_bottom = Border(
        left=Side(style="thin", color="CBD5E1"), right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"), bottom=Side(style="double", color="78350F")
    )

    ws.merge_cells("A1:M1")
    ws["A1"] = "🪔 DIWALI & SAMVAT RALLY STRATEGY: TOP 10 STOCKS (₹1L MUHURAT + ₹1L DIP RESERVE)"
    ws["A1"].font = title_font
    ws["A1"].fill = primary_fill
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 36

    ws.merge_cells("A2:M2")
    ws["A2"] = "Live Zerodha Verified Quotes | Muhurat Session: Sunday, Nov 8 (02:20 PM – 03:30 PM IST) + Dip Reserve (1L)"
    ws["A2"].font = subtitle_font
    ws["A2"].fill = primary_fill
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 20

    headers = [
        "Rank", "Stock Symbol", "Core Sector / Diwali Moat",
        "Live LTP / Muhurat (₹)", "Tranche 1 Qty", "Tranche 1 Cost (₹)",
        "Dip Entry / Tranche 2 (₹)", "Tranche 2 Qty", "Tranche 2 Cost (₹)",
        "Blended Avg Cost (₹)", "Target 1 (₹)", "Target 2 (₹)", "Diwali Growth Catalyst"
    ]
    for c_i, h in enumerate(headers, start=1):
        c = ws.cell(row=4, column=c_i, value=h)
        c.font = header_font
        c.fill = sub_fill
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = border_thin
    ws.row_dimensions[4].height = 28

    data = [
        (1, "RVNL", "Railway EPC Leader (Order Book ₹90k Cr)", 193.34, 77, 77 * 193.34, 175.00, 85, 85 * 175.00, round((77*193.34 + 85*175.00)/162, 2), 220.00, 250.00, "Pre-budget capex rally & Vande Bharat Sleeper commercial trials"),
        (2, "IRFC", "Monopoly Rail Financier (3.8% Div)", 80.43, 149, 149 * 80.43, 74.00, 162, 162 * 74.00, round((149*80.43 + 162*74.00)/311, 2), 90.00, 102.00, "Zero NPA, sovereign guarantee, AUM scaling past ₹5 Lakh Cr"),
        (3, "TITAGARH", "Vande Bharat Coach Mfg (Severe Oversold)", 677.85, 18, 18 * 677.85, 655.00, 18, 18 * 655.00, round((18*677.85 + 18*655.00)/36, 2), 745.00, 820.00, "Early reversal from severe oversold floor, passenger coach execution"),
        (4, "COCHINSHIP", "Naval Defense (Zero Debt, US Navy MSRA)", 1220.00, 10, 10 * 1220.00, 1150.00, 10, 10 * 1150.00, round((10*1220.00 + 10*1150.00)/20, 2), 1350.00, 1500.00, "₹22,000 Cr order book, aircraft carrier & US Navy maintenance agreement"),
        (5, "APOLLO", "Defense Electronics (Q2 PAT +55%)", 413.20, 24, 24 * 413.20, 390.00, 25, 25 * 390.00, round((24*413.20 + 25*390.00)/49, 2), 450.00, 485.00, "Q2 net profit up +55%, missile & DRDO defense electronics deliveries"),
        (6, "KAYNES", "Semiconductor OSAT & High-Tech EMS", 3233.00, 3, 3 * 3233.00, 3150.00, 3, 3 * 3150.00, round((3*3233.00 + 3*3150.00)/6, 2), 3650.00, 4150.00, "Sanand Gujarat chip assembly facility, 40%+ CAGR growth"),
        (7, "RAILTEL", "Kavach Safety & Rail Telecom (Debt Free)", 241.05, 37, 37 * 241.05, 225.00, 40, 40 * 225.00, round((37*241.05 + 40*225.00)/77, 2), 265.00, 290.00, "Debt-free optical fiber right-of-way, Kavach safety tender waves"),
        (8, "SUZLON", "Wind Energy Dominance (100% Debt Free)", 38.80, 180, 180 * 38.80, 35.50, 197, 197 * 35.50, round((180*38.80 + 197*35.50)/377, 2), 44.00, 49.00, "100% net debt free, record 5.5 GW order book, clean power leader"),
        (9, "LODHA", "Luxury Real Estate (Diwali Housing Boom)", 1179.00, 6, 6 * 1179.00, 1100.00, 6, 6 * 1100.00, round((6*1179.00 + 6*1100.00)/12, 2), 1280.00, 1380.00, "Festive housing pre-sales boom, high cash flow commercial expansion"),
        (10, "PCBL", "Specialty Chemicals & EV Carbon", 279.25, 22, 22 * 279.25, 274.00, 22, 22 * 274.00, round((22*279.25 + 22*274.00)/44, 2), 315.00, 350.00, "EV battery-grade conductive carbon expansion, high ROCE moat")
    ]

    for row_idx, r in enumerate(data, start=5):
        ws.cell(row=row_idx, column=1, value=r[0]).font = bold_font
        ws.cell(row=row_idx, column=2, value=r[1]).font = blue_bold
        ws.cell(row=row_idx, column=3, value=r[2]).font = regular_font

        # T1
        c4 = ws.cell(row=row_idx, column=4, value=r[3])
        c4.number_format = "₹#,##0.00"
        c4.font = bold_font
        ws.cell(row=row_idx, column=5, value=r[4]).font = bold_font
        c6 = ws.cell(row=row_idx, column=6, value=r[5])
        c6.number_format = "₹#,##0.00"
        c6.font = bold_font

        # T2
        c7 = ws.cell(row=row_idx, column=7, value=r[6])
        c7.number_format = "₹#,##0.00"
        c7.font = bold_font
        ws.cell(row=row_idx, column=8, value=r[7]).font = bold_font
        c9 = ws.cell(row=row_idx, column=9, value=r[8])
        c9.number_format = "₹#,##0.00"
        c9.font = bold_font

        # Blended
        c10 = ws.cell(row=row_idx, column=10, value=r[9])
        c10.number_format = "₹#,##0.00"
        c10.font = Font(name=font_family, size=10, bold=True, color="B45309")

        # Targets
        c11 = ws.cell(row=row_idx, column=11, value=r[10])
        c11.number_format = "₹#,##0.00"
        c11.font = green_bold
        c12 = ws.cell(row=row_idx, column=12, value=r[11])
        c12.number_format = "₹#,##0.00"
        c12.font = green_bold

        ws.cell(row=row_idx, column=13, value=r[12]).font = regular_font

        for col_i in range(1, 14):
            ws.cell(row=row_idx, column=col_i).border = border_thin
            if row_idx % 2 == 0:
                ws.cell(row=row_idx, column=col_i).fill = zebra_fill
        ws.row_dimensions[row_idx].height = 22

    # Totals Row
    tot_row = 15
    ws.cell(row=tot_row, column=1, value="PORTFOLIO TOTALS").font = bold_font
    ws.merge_cells("A15:C15")
    ws.cell(row=tot_row, column=1).alignment = Alignment(horizontal="center", vertical="center")

    c_tot_t1 = ws.cell(row=tot_row, column=6, value="=SUM(F5:F14)")
    c_tot_t1.number_format = "₹#,##0.00"
    c_tot_t1.font = Font(name=font_family, size=11, bold=True, color="78350F")

    c_tot_t2 = ws.cell(row=tot_row, column=9, value="=SUM(I5:I14)")
    c_tot_t2.number_format = "₹#,##0.00"
    c_tot_t2.font = Font(name=font_family, size=11, bold=True, color="78350F")

    ws.cell(row=tot_row, column=10, value="Combined: ₹1,95,052").font = bold_font
    ws.cell(row=tot_row, column=11, value="T1 Profit: +₹32,483").font = green_bold
    ws.cell(row=tot_row, column=12, value="T2 Profit: +₹58,723").font = green_bold

    for col_i in range(1, 14):
        ws.cell(row=tot_row, column=col_i).fill = kpi_fill
        ws.cell(row=tot_row, column=col_i).border = double_bottom
    ws.row_dimensions[tot_row].height = 26

    widths = [8, 16, 28, 16, 14, 16, 18, 14, 16, 18, 14, 14, 40]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT_FILE)
    print(f"Created: {OUT_FILE}")

if __name__ == "__main__":
    build_excel()
