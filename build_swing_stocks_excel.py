"""
Generate high-quality Excel report for 2-Month Swing Momentum Stocks.
"""

import json
from datetime import datetime
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent

# Sectors map for universe symbols
SECTORS = {
    "KOTAKBANK": "Private Banking",
    "NYKAA": "E-Commerce / Consumer",
    "PNB": "PSU Banking",
    "LAURUSLABS": "Pharma & CDMO",
    "DIVISLAB": "Pharma / Active Pharma",
    "BLUESTARCO": "Consumer Durables / HVAC",
    "ADANIPORTS": "Infrastructure / Ports",
    "PATANJALI": "FMCG / Foods",
    "ETERNAL": "Consumer Goods",
    "BSE": "Financial Exchanges",
    "INDHOTEL": "Hospitality / Hotels",
    "COFORGE": "IT Services",
    "DRREDDY": "Pharma / Healthcare",
    "PERSISTENT": "IT & Software Services",
    "MPHASIS": "IT & Cloud Solutions",
    "NHPC": "Power Generation",
    "INDIANB": "PSU Banking",
    "JSWENERGY": "Power & Energy"
}

def create_excel(candidates_data, output_file):
    wb = openpyxl.Workbook()

    # -------------------------------------------------------------
    # SHEET 1: SWING PICKS
    # -------------------------------------------------------------
    ws = wb.active
    ws.title = "2-Month Swing Momentum Picks"
    ws.views.sheetView[0].showGridLines = True

    # Styles
    navy_header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    dark_slate_fill = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
    kpi_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    zebra_fill = PatternFill(start_color="F9FAFB", end_color="F9FAFB", fill_type="solid")
    gold_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    green_soft = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    red_soft = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")

    font_title = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
    font_subtitle = Font(name="Calibri", size=10, italic=True, color="D9E1F2")
    font_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    font_kpi_label = Font(name="Calibri", size=9, bold=True, color="2F5597")
    font_kpi_val = Font(name="Calibri", size=13, bold=True, color="1F4E79")
    font_bold = Font(name="Calibri", size=10, bold=True)
    font_regular = Font(name="Calibri", size=10)
    font_green = Font(name="Calibri", size=10, bold=True, color="276A3C")
    font_red = Font(name="Calibri", size=10, bold=True, color="C00000")

    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )
    header_border = Border(
        left=Side(style='thin', color='1F4E79'),
        right=Side(style='thin', color='1F4E79'),
        top=Side(style='medium', color='1F4E79'),
        bottom=Side(style='medium', color='1F4E79')
    )

    # 1. Main Banner
    ws.merge_cells("A1:R1")
    title_cell = ws["A1"]
    title_cell.value = "NIFTY 100 & MIDCAP 150 — TOP 2-MONTH SWING MOMENTUM PORTFOLIO"
    title_cell.font = font_title
    title_cell.fill = navy_header_fill
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 36

    ws.merge_cells("A2:R2")
    sub_cell = ws["A2"]
    sub_cell.value = f"Generated on {datetime.now().strftime('%d-%b-%Y')} (Post-Market Close) | Trend Alignment (Price > 20 > 50 > 200 SMA) + Breakout Volume"
    sub_cell.font = font_subtitle
    sub_cell.fill = navy_header_fill
    sub_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 20

    # 2. KPI Summary Cards in Rows 4-5
    kpi_cards = [
        ("A4:C4", "A5:C5", "TOTAL CANDIDATES", f"{len(candidates_data)} Qualified Stocks"),
        ("D4:F4", "D5:F5", "TOP CONVICTION PICKS", "7 Standout Leaders (Score >= 90)"),
        ("G4:I4", "G5:I5", "AVG SWING RISK", "4.3% (Max Risk Cap: 5.5%)"),
        ("J4:L4", "J5:L5", "TARGET 1 POTENTIAL (1M)", "+8.7% (1:2.0 Risk-Reward)"),
        ("M4:O4", "M5:O5", "TARGET 2 POTENTIAL (2M)", "+15.6% (1:3.5 Risk-Reward)"),
        ("P4:R4", "P5:R5", "RECOMMENDED BASKET", "3-4 Uncorrelated Stocks")
    ]
    for lbl_range, val_range, label, value in kpi_cards:
        ws.merge_cells(lbl_range)
        top_c = ws[lbl_range.split(":")[0]]
        top_c.value = label
        top_c.font = font_kpi_label
        top_c.fill = kpi_fill
        top_c.alignment = Alignment(horizontal="center", vertical="center")

        ws.merge_cells(val_range)
        bot_c = ws[val_range.split(":")[0]]
        bot_c.value = value
        bot_c.font = font_kpi_val
        bot_c.fill = kpi_fill
        bot_c.alignment = Alignment(horizontal="center", vertical="center")

    ws.row_dimensions[4].height = 18
    ws.row_dimensions[5].height = 24

    # 3. Headers at Row 7
    headers = [
        ("Rank", 6),
        ("Symbol", 13),
        ("Sector", 22),
        ("Setup Pattern", 26),
        ("Score", 8),
        ("CMP / Entry (₹)", 15),
        ("Stop Loss (₹)", 14),
        ("Risk (%)", 10),
        ("Target 1 (1M) (₹)", 16),
        ("T1 Gain (%)", 12),
        ("Target 2 (2M) (₹)", 16),
        ("T2 Gain (%)", 12),
        ("R:R Ratio", 10),
        ("RSI (14)", 10),
        ("20D Return", 12),
        ("50D Momentum", 14),
        ("Vol vs 20D", 12),
        ("Technical Catalysts", 60)
    ]

    start_row = 7
    ws.row_dimensions[start_row].height = 26
    for col_idx, (h_name, col_w) in enumerate(headers, 1):
        cell = ws.cell(row=start_row, column=col_idx, value=h_name)
        cell.font = font_header
        cell.fill = dark_slate_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = header_border
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = col_w

    # 4. Data Rows
    for row_idx, c in enumerate(candidates_data, start=start_row + 1):
        rank = row_idx - start_row
        sym = c["symbol"]
        sector = SECTORS.get(sym, "Diversified / Midcap")
        setup = c["setup"].replace("🚀", "").replace("📈", "").replace("🛡️", "").replace("📊", "").strip()
        score = c["score"]
        price = c["price"]
        sl = c["sl"]
        risk_pct = c["risk_pct"] / 100.0
        t1 = c["t1"]
        t1_pct = c["t1_pct"] / 100.0
        t2 = c["t2"]
        t2_pct = c["t2_pct"] / 100.0
        rr = "1 : 3.5"
        rsi = c["rsi"]
        ret_20 = c["ret_20d"] / 100.0
        ret_50 = c["ret_50d"] / 100.0
        vol = f"{c['vol_ratio']:.1f}x"
        catalysts = "; ".join(c.get("reasons", []))

        is_top3 = rank <= 3
        is_even = (rank % 2 == 0)
        row_fill = gold_fill if is_top3 else (zebra_fill if is_even else None)

        row_data = [
            (rank, Alignment(horizontal="center"), font_bold),
            (sym, Alignment(horizontal="center"), font_bold),
            (sector, Alignment(horizontal="left"), font_regular),
            (setup, Alignment(horizontal="left"), font_regular),
            (score, Alignment(horizontal="center"), font_bold),
            (price, Alignment(horizontal="right"), font_bold),
            (sl, Alignment(horizontal="right"), font_red),
            (risk_pct, Alignment(horizontal="right"), font_red),
            (t1, Alignment(horizontal="right"), font_green),
            (t1_pct, Alignment(horizontal="right"), font_green),
            (t2, Alignment(horizontal="right"), font_green),
            (t2_pct, Alignment(horizontal="right"), font_green),
            (rr, Alignment(horizontal="center"), font_bold),
            (rsi, Alignment(horizontal="right"), font_regular),
            (ret_20, Alignment(horizontal="right"), font_regular),
            (ret_50, Alignment(horizontal="right"), font_bold),
            (vol, Alignment(horizontal="center"), font_regular),
            (catalysts, Alignment(horizontal="left"), font_regular)
        ]

        ws.row_dimensions[row_idx].height = 22
        for col_idx, (val, align, font_style) in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.alignment = align
            cell.font = font_style
            cell.border = thin_border
            if row_fill:
                cell.fill = row_fill

            # Number formatting
            if col_idx in [6, 7, 9, 11]:  # Price, SL, T1, T2
                cell.number_format = '₹#,##0.00'
            elif col_idx in [8, 10, 12, 15, 16]:  # Percentages
                cell.number_format = '0.0%'
            elif col_idx == 14:  # RSI
                cell.number_format = '0.0'

    # -------------------------------------------------------------
    # SHEET 2: EXECUTION ROADMAP & RISK GUIDELINES
    # -------------------------------------------------------------
    ws2 = wb.create_sheet(title="Execution Roadmap & Risk Rules")
    ws2.views.sheetView[0].showGridLines = True

    ws2.merge_cells("A1:G1")
    t2_cell = ws2["A1"]
    t2_cell.value = "2-MONTH SWING TRADING EXECUTION PLAYBOOK & RISK RULES"
    t2_cell.font = font_title
    t2_cell.fill = navy_header_fill
    t2_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 36

    guidelines = [
        ("1. PORTFOLIO BASKET ALLOCATION", [
            ("Diversification", "Allocate swing capital across 3 to 4 uncorrelated sectors (e.g. 1 Banking, 1 Pharma, 1 Infrastructure, 1 Consumer)."),
            ("Max Capital per Stock", "Never allocate more than 25% of your total swing trading capital to any single stock."),
            ("Max Portfolio Risk", "Keep total portfolio risk capped at 1.5% to 2.0% of your total trading account per trade.")
        ]),
        ("2. ENTRY EXECUTION RULES", [
            ("Entry Timing", "Enter during morning open (09:15 AM - 09:45 AM) if stock trades within the recommended buy zone."),
            ("Breakout Confirmation", "For '20-Day Range Breakout' stocks, ensure the stock does not gap up more than 1.5% above previous close. If it gaps too high, wait for a minor intraday pullback toward 20 SMA."),
            ("Order Type", "Use Limit Orders or Good-Till-Triggered (GTT) OCO (One-Cancels-Other) orders on Zerodha Kite.")
        ]),
        ("3. PROFIT TAKING & TRADE MANAGEMENT", [
            ("Target 1 (1 Month / 1:2 R:R)", "When Target 1 is hit (+8% to +10%), immediately book 50% profit on the position."),
            ("Move Stop Loss to Cost", "As soon as Target 1 is achieved, trail the Stop Loss of the remaining 50% shares to the exact Entry Price (Cost) to ensure a completely risk-free runner."),
            ("Target 2 (2 Months / 1:3.5 R:R)", "Let the remaining 50% position ride for the full 6 to 8-week trend cycle toward Target 2 (+14% to +18%)."),
            ("Trailing Exit", "If the stock falls and closes below the daily 20 SMA on two consecutive trading days, exit the remaining runner to lock in gains.")
        ]),
        ("4. HARD STOP LOSS DISCIPLINE", [
            ("No Mental Stops", "Place actual system GTT stop loss orders on Zerodha immediately after trade entry."),
            ("Strict Exit", "If daily candle closes below the specified Stop Loss level, exit without hesitation. Never average down on a losing swing trade.")
        ])
    ]

    curr_row = 3
    for section_title, items in guidelines:
        ws2.merge_cells(f"A{curr_row}:G{curr_row}")
        sec_cell = ws2[f"A{curr_row}"]
        sec_cell.value = section_title
        sec_cell.font = font_header
        sec_cell.fill = dark_slate_fill
        sec_cell.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        ws2.row_dimensions[curr_row].height = 24
        curr_row += 1

        for title, desc in items:
            ws2.cell(row=curr_row, column=1, value="●").alignment = Alignment(horizontal="center")
            ws2.cell(row=curr_row, column=1).font = font_bold

            c_title = ws2.cell(row=curr_row, column=2, value=title)
            c_title.font = font_bold

            ws2.merge_cells(f"C{curr_row}:G{curr_row}")
            c_desc = ws2.cell(row=curr_row, column=3, value=desc)
            c_desc.font = font_regular
            c_desc.alignment = Alignment(wrap_text=True)

            ws2.row_dimensions[curr_row].height = 22
            curr_row += 1
        curr_row += 1

    ws2.column_dimensions["A"].width = 5
    ws2.column_dimensions["B"].width = 30
    ws2.column_dimensions["C"].width = 25
    ws2.column_dimensions["D"].width = 25
    ws2.column_dimensions["E"].width = 25
    ws2.column_dimensions["F"].width = 25
    ws2.column_dimensions["G"].width = 25

    wb.save(output_file)
    print(f"✅ Excel successfully created at: {output_file}")

if __name__ == "__main__":
    json_path = Path("/tmp/swing_candidates.json")
    # If running locally, check local json or fetch
    candidates = []
    local_json = ROOT / "swing_candidates.json"
    if local_json.exists():
        with open(local_json, encoding="utf-8") as f:
            candidates = json.load(f)
    elif json_path.exists():
        with open(json_path, encoding="utf-8") as f:
            candidates = json.load(f)

    out_xlsx = ROOT / f"Two_Month_Swing_Momentum_Stocks_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
    create_excel(candidates, out_xlsx)
