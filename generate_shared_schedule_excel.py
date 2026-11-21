r"""
generate_shared_schedule_excel.py
═════════════════════════════════════════════════════════════════
Creates a master professional Excel workbook in the shared folder:
D:/NiftyScanner/shared/NiftyScanner_Master_Schedule_and_Trading_Matrix.xlsx

Features:
  1. Executive Styling: Deep Navy (#1B365D), Slate Indigo (#2F5597),
     Soft Mint Green (#E2EFDA), Warm Gold (#FFF2CC), Soft Red (#FCE4D6),
     and Zebra Striping.
  2. Rich OpenPyXL Native Charts:
     - BarChart: Trading Engine Intensity by Hour of the Day
     - PieChart: Automated Job Breakdown by Engine Category
     - Clustered BarChart: Price Targets vs Entry & Stop-Loss (Top Candidates)
  3. Worksheets:
     - Tab 1: Master Schedule & Daily Timeline (Complete 14 Crontab Jobs)
     - Tab 2: 7-10 Day Swing Trade Matrix (11 Live Active Positions)
     - Tab 3: 5-Bot Telegram Routing Hub (Full Routing Specifications)
     - Tab 4: 4-Pillar Safety & Exit Architecture
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

import openpyxl
from openpyxl.chart import BarChart, PieChart, Reference, Series
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent
SHARED_DIR = Path("D:/NiftyScanner/shared")
OUTPUT_FILE = SHARED_DIR / "NiftyScanner_Master_Schedule_and_Trading_Matrix.xlsx"


def create_master_excel():
    SHARED_DIR.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()

    # Common Styles & Palette
    navy_dark = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
    navy_accent = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
    navy_light = PatternFill(start_color="41719C", end_color="41719C", fill_type="solid")
    kpi_card_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    kpi_card_border_fill = PatternFill(start_color="B4C6E7", end_color="B4C6E7", fill_type="solid")
    gold_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    zebra_even = PatternFill(start_color="F2F4F8", end_color="F2F4F8", fill_type="solid")
    soft_green = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    soft_red = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
    section_fill = PatternFill(start_color="EDF2F8", end_color="EDF2F8", fill_type="solid")

    font_title = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
    font_subtitle = Font(name="Calibri", size=10, italic=True, color="D9E1F2")
    font_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    font_section = Font(name="Calibri", size=11, bold=True, color="1B365D")
    font_kpi_lbl = Font(name="Calibri", size=9, bold=True, color="1B365D")
    font_kpi_val = Font(name="Calibri", size=13, bold=True, color="1B365D")
    font_bold = Font(name="Calibri", size=10, bold=True)
    font_regular = Font(name="Calibri", size=10)
    font_green = Font(name="Calibri", size=10, bold=True, color="276A3C")
    font_red = Font(name="Calibri", size=10, bold=True, color="C00000")
    font_blue = Font(name="Calibri", size=10, bold=True, color="1B365D")

    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )
    header_border = Border(
        left=Side(style="thin", color="1B365D"),
        right=Side(style="thin", color="1B365D"),
        top=Side(style="medium", color="1B365D"),
        bottom=Side(style="medium", color="1B365D"),
    )
    card_border = Border(
        left=Side(style="thin", color="B4C6E7"),
        right=Side(style="thin", color="B4C6E7"),
        top=Side(style="thin", color="B4C6E7"),
        bottom=Side(style="thin", color="B4C6E7"),
    )

    # =========================================================================
    # TAB 1: MASTER SCHEDULE & DAILY TIMELINE
    # =========================================================================
    ws1 = wb.active
    ws1.title = "Master Crontab Schedule"
    ws1.views.sheetView[0].showGridLines = True

    # Title Banner
    ws1.merge_cells("A1:J1")
    t1 = ws1["A1"]
    t1.value = "NIFTY SCANNER & ALGO TRADING — MASTER CRONTAB AUTOMATION SCHEDULE"
    t1.font = font_title
    t1.fill = navy_dark
    t1.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 36

    ws1.merge_cells("A2:J2")
    st1 = ws1["A2"]
    st1.value = f"Oracle Cloud VM (140.245.195.112) | Indian Standard Time (IST) | Generated: {datetime.now().strftime('%d-%b-%Y %I:%M %p')}"
    st1.font = font_subtitle
    st1.fill = navy_dark
    st1.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[2].height = 20

    # Top KPI Cards (Rows 4-5)
    kpis = [
        ("A4:B4", "A5:B5", "TOTAL SCHEDULED ENGINES", "14 Automated Jobs"),
        ("C4:D4", "C5:D5", "OPERATIONAL WINDOW", "06:00 AM – 04:15 PM IST"),
        ("E4:F4", "E5:F5", "ACTIVE LIVE POSITIONS", "11 Monitored Trades"),
        ("G4:H4", "G5:H5", "TELEGRAM ROUTING", "5 Dedicated Bots"),
        ("I4:J4", "I5:J5", "CRASH SAFETY RADAR", "4-Pillar Active Guard"),
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

    for r in range(4, 6):
        for c in range(1, 11):
            ws1.cell(row=r, column=c).border = card_border

    # Schedule Table Headers (Row 7)
    headers_s1 = [
        "Job #",
        "Time (IST)",
        "Frequency",
        "Active Days",
        "Trading Engine / Task Name",
        "Target Script / Command",
        "Telegram Bot",
        "Recipient Bot Handle",
        "Operational Role & Safeguard",
        "Category",
    ]
    ws1.row_dimensions[7].height = 26
    for col_idx, h in enumerate(headers_s1, start=1):
        cell = ws1.cell(row=7, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = navy_accent
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = header_border

    # Crontab schedule items (14 jobs)
    schedule_data = [
        (
            1,
            "06:00 AM",
            "Daily",
            "Mon–Fri",
            "Daily Pre-Market System Cleanup & Memory Refresh",
            "daily_system_maintenance.sh",
            "System / Server",
            "Log File Only",
            "Cleans tmp, reboots caches, archives old logs, checks RAM",
            "Maintenance",
        ),
        (
            2,
            "07:00 AM",
            "Daily",
            "Mon–Fri",
            "Automated Zerodha Kite Session Token Generator",
            "auto_kite_auth.py",
            "System Auth",
            ".kite_access_token",
            "Generates shared Kite access token used across all 3 engines",
            "Authentication",
        ),
        (
            3,
            "08:30 AM",
            "Daily",
            "Mon–Fri",
            "Pre-Market News Catalyst Scanner (for Intraday)",
            "news_scanner_with_twitter.py --hours 48",
            "Intraday Cache",
            "news_reports/ cache",
            "Scans 48h corporate announcements & news sentiment for stock picks",
            "News Catalyst",
        ),
        (
            4,
            "09:00 AM",
            "Daily",
            "Mon–Fri",
            "NIFTY V14.9 Paper Trading Engine",
            "run_NIFTY_V14_9_CRON.sh",
            "NIFTY Scalper Bot",
            "@Jinna_Nifty_BOT",
            "Full index automated algo scalping on 1-min & 3-min intervals",
            "Index Scalper",
        ),
        (
            5,
            "09:12 AM",
            "Daily",
            "Mon–Fri",
            "BTST Smart Exit Monitor & Gap-Up Evaluator",
            "btst_smart_exit_strategy.py --cron",
            "Options Swing Bot",
            "@Swingtradeniftybot",
            "Evaluates overnight BTST positions against gap-up/target/SL rules",
            "BTST Momentum",
        ),
        (
            6,
            "09:15 AM",
            "Continuous",
            "Mon–Fri",
            "Portfolio Peak Guard Continuous Sentinel Loop",
            "run_continuous_monitor.sh",
            "Portfolio Guard Bot",
            "@Zerodhaportfoliopro_bot",
            "Monitors long-term holdings, 1-day pre-earnings blackout radar",
            "Portfolio Sentinel",
        ),
        (
            7,
            "09:30 AM",
            "Weekly Cycle",
            "Mondays",
            "🎯 7–10 Day Swing Trade Entry Scan (Full NSE Universe)",
            "run_swing_trade_system.py",
            "Portfolio Swing Bot",
            "@portfolio_bot",
            "Scans entire NSE universe, evaluates Crash Shield, issues Buy entries",
            "Swing Lifecycle",
        ),
        (
            8,
            "09:35 AM",
            "Hourly (:45)",
            "Mon–Fri",
            "Intraday News Catalyst Hourly Refresh",
            "news_scanner_with_twitter.py --hours 12",
            "Intraday Cache",
            "news_reports/ cache",
            "Refreshes breaking news stream at 09:35, 10:45, 11:45, 12:45, 13:45, 14:45",
            "News Catalyst",
        ),
        (
            9,
            "09:50 AM",
            "Hourly (:50)",
            "Mon–Fri",
            "Options Intraday Scan (Min Score 60)",
            "run_options_intraday_scan_powerful_sl.py",
            "Options Swing Bot",
            "@Swingtradeniftybot",
            "Scans CE/PE options using live Kite quotes and 4-layer stop loss",
            "Options Intraday",
        ),
        (
            10,
            "09:52 AM",
            "Every 2 min",
            "Mon–Fri",
            "Intraday Trade Monitor & Target/SL Live Tracker",
            "intraday_trade_monitor.py",
            "Options Swing Bot",
            "@Swingtradeniftybot",
            "Continuously monitors open intraday options against targets & trailing SL",
            "Options Intraday",
        ),
        (
            11,
            "10:00 AM",
            "Daily",
            "Mon–Fri",
            "🛢️ MCX Crude Oil Momentum Breakout Scan",
            "run_crude_swing_scan.py",
            "Options Swing Bot",
            "@Swingtradeniftybot",
            "Scans MCX Crude futures & option breakout levels for momentum swing",
            "Commodities",
        ),
        (
            12,
            "11:45 AM",
            "Daily",
            "Mon–Fri",
            "BTST Options Next-Day P&L Summary Report",
            "daily_11am_btst_summary.py",
            "Options Swing Bot",
            "@Swingtradeniftybot",
            "Calculates realized returns and P&L for overnight BTST options",
            "BTST Momentum",
        ),
        (
            13,
            "02:00 PM",
            "Expiry Windows",
            "Tue & Thu",
            "🔥 Hero-Zero Weekly Expiry Power Scans (2:00–3:10 PM)",
            "nifty_hero_zero_expiry_scanner.py / sensex",
            "Hero-Zero Expiry Bot",
            "@Nifty_stage10_paper_bot",
            "Tuesdays for NIFTY, Thursdays for SENSEX at 14:00, 14:30, 15:00, 15:05, 15:10",
            "Expiry Hero-Zero",
        ),
        (
            14,
            "02:30 PM",
            "Daily",
            "Mon–Fri",
            "Afternoon Fresh News Catalyst Scanner (for BTST)",
            "news_scanner_with_twitter.py --hours 8",
            "BTST Cache",
            "news_reports/ cache",
            "Pulls fresh afternoon corporate news before 03:00 PM BTST scan",
            "News Catalyst",
        ),
        (
            15,
            "03:00 PM",
            "Daily",
            "Mon–Fri",
            "BTST Options Scan (Stocks & NIFTY + SENSEX)",
            "run_btst_options_scan_powerful_sl.py",
            "Options Swing Bot",
            "@Swingtradeniftybot",
            "Identifies high-probability BTST candidates for next-morning gap-up",
            "BTST Momentum",
        ),
        (
            16,
            "03:15 PM",
            "Weekly Cycle",
            "Fridays",
            "🎯 7–10 Day Swing Trade Exit Evaluation & Audit Report",
            "run_swing_trade_system.py --close-and-audit",
            "Portfolio Swing Bot",
            "@portfolio_bot",
            "Closes completed swing trades, generates Excel audit, dispatches report",
            "Swing Lifecycle",
        ),
        (
            17,
            "03:50 PM",
            "Expiry Close",
            "Tue & Thu",
            "🏆 Hero-Zero Expiry Final Settlement & Performance Summary",
            "hero_zero_350pm_summary.py",
            "Hero-Zero Expiry Bot",
            "@Nifty_stage10_paper_bot",
            "Final settlement audit, win rate, and return calculation for weekly expiry",
            "Expiry Hero-Zero",
        ),
        (
            18,
            "04:00 PM",
            "Daily",
            "Mon–Fri",
            "Intraday Options Stock 4 PM Summary Report",
            "daily_4pm_intraday_summary.py",
            "Options Swing Bot",
            "@Swingtradeniftybot",
            "Summarizes all intraday options trades, net return %, profit/loss in INR",
            "Options Intraday",
        ),
        (
            19,
            "04:15 PM",
            "Weekly",
            "Fridays",
            "Weekly Options Trade Audit & P&L Report Generation",
            "generate_weekly_audit.py",
            "Options Swing Bot",
            "@Swingtradeniftybot",
            "Comprehensive weekly audit of all options trades delivered via Telegram",
            "Auditing & P&L",
        ),
    ]

    for row_idx, item in enumerate(schedule_data, start=8):
        ws1.row_dimensions[row_idx].height = 22
        fill = zebra_even if row_idx % 2 == 0 else PatternFill(fill_type=None)

        # Highlight Swing Lifecycle rows
        if "Swing Lifecycle" in item[9]:
            fill = soft_green
        elif "Hero-Zero" in item[9]:
            fill = gold_fill

        for col_idx, val in enumerate(item, start=1):
            cell = ws1.cell(row=row_idx, column=col_idx, value=val)
            cell.font = font_bold if col_idx in (1, 2, 5, 8) else font_regular
            if fill.fill_type:
                cell.fill = fill
            cell.border = thin_border

            # Alignment
            if col_idx in (1, 2, 3, 4):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx in (7, 8, 10):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    # -------------------------------------------------------------------------
    # Chart Data Tables on Sheet 1 (Rows 30+)
    # -------------------------------------------------------------------------
    start_chart_data = len(schedule_data) + 11

    # Table A: Hourly Intensity
    ws1.cell(row=start_chart_data, column=1, value="Trading Hour (IST)").font = font_header
    ws1.cell(row=start_chart_data, column=1).fill = navy_dark
    ws1.cell(row=start_chart_data, column=2, value="Active Automated Jobs").font = font_header
    ws1.cell(row=start_chart_data, column=2).fill = navy_dark

    hourly_data = [
        ("06:00 AM - 07:00 AM", 1),
        ("07:00 AM - 08:00 AM", 1),
        ("08:00 AM - 09:00 AM", 1),
        ("09:00 AM - 10:00 AM", 6),
        ("10:00 AM - 11:00 AM", 3),
        ("11:00 AM - 12:00 PM", 2),
        ("12:00 PM - 01:00 PM", 1),
        ("01:00 PM - 02:00 PM", 1),
        ("02:00 PM - 03:00 PM", 4),
        ("03:00 PM - 04:00 PM", 5),
        ("04:00 PM - 04:30 PM", 2),
    ]
    for idx, (hr, count) in enumerate(hourly_data, start=start_chart_data + 1):
        c1 = ws1.cell(row=idx, column=1, value=hr)
        c2 = ws1.cell(row=idx, column=2, value=count)
        c1.font = font_regular
        c2.font = font_bold
        c1.border = thin_border
        c2.border = thin_border
        c2.alignment = Alignment(horizontal="center")

    # Table B: Engine Category Breakdown
    ws1.cell(row=start_chart_data, column=4, value="Engine Category").font = font_header
    ws1.cell(row=start_chart_data, column=4).fill = navy_dark
    ws1.cell(row=start_chart_data, column=5, value="Number of Routines").font = font_header
    ws1.cell(row=start_chart_data, column=5).fill = navy_dark

    category_data = [
        ("System Maintenance & Auth", 2),
        ("News Catalyst Radars", 3),
        ("Options Intraday & Scalping", 3),
        ("BTST Overnight Momentum", 3),
        ("7–10 Day Stock Swing Engine", 2),
        ("Weekly Expiry Hero-Zero", 3),
        ("Portfolio Risk Sentinel", 1),
        ("Weekly Auditing & Excel P&L", 2),
    ]
    for idx, (cat, count) in enumerate(category_data, start=start_chart_data + 1):
        c1 = ws1.cell(row=idx, column=4, value=cat)
        c2 = ws1.cell(row=idx, column=5, value=count)
        c1.font = font_regular
        c2.font = font_bold
        c1.border = thin_border
        c2.border = thin_border
        c2.alignment = Alignment(horizontal="center")

    # Chart 1: BarChart for Hourly Intensity
    chart1 = BarChart()
    chart1.type = "col"
    chart1.style = 10
    chart1.title = "Operational Trading Engine Intensity by Hour (IST)"
    chart1.y_axis.title = "Number of Executing Automations"
    chart1.x_axis.title = "Trading Session Hour"
    chart1.width = 16
    chart1.height = 9.5

    data_ref1 = Reference(
        ws1,
        min_col=2,
        min_row=start_chart_data,
        max_row=start_chart_data + len(hourly_data),
    )
    cats_ref1 = Reference(
        ws1,
        min_col=1,
        min_row=start_chart_data + 1,
        max_row=start_chart_data + len(hourly_data),
    )
    chart1.add_data(data_ref1, titles_from_data=True)
    chart1.set_categories(cats_ref1)
    chart1.legend = None
    ws1.add_chart(chart1, "A50")

    # Chart 2: PieChart for Categories
    chart2 = PieChart()
    chart2.title = "Distribution by Trading Architecture & Engine Type"
    chart2.style = 10
    chart2.width = 14
    chart2.height = 9.5

    data_ref2 = Reference(
        ws1,
        min_col=5,
        min_row=start_chart_data,
        max_row=start_chart_data + len(category_data),
    )
    cats_ref2 = Reference(
        ws1,
        min_col=4,
        min_row=start_chart_data + 1,
        max_row=start_chart_data + len(category_data),
    )
    chart2.add_data(data_ref2, titles_from_data=True)
    chart2.set_categories(cats_ref2)
    ws1.add_chart(chart2, "E50")

    # =========================================================================
    # TAB 2: 7-TO-10 DAY SWING TRADE MATRIX
    # =========================================================================
    ws2 = wb.create_sheet(title="7-10d Swing Active Matrix")
    ws2.views.sheetView[0].showGridLines = True

    # Title Banner
    ws2.merge_cells("A1:P1")
    t2 = ws2["A1"]
    t2.value = "7-TO-10 DAY REPEATING STOCK SWING TRADING MATRIX & TIMEFRAME TARGETS"
    t2.font = font_title
    t2.fill = navy_dark
    t2.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 36

    ws2.merge_cells("A2:P2")
    st2 = ws2["A2"]
    st2.value = (
        "Strict 1-Week to 10-Day Cycle | News-Based Crash Shield Verified | "
        "Dynamic Multi-Horizon Targets (1W, 10D, 1M) | Routed to @portfolio_bot"
    )
    st2.font = font_subtitle
    st2.fill = navy_dark
    st2.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[2].height = 20

    # KPI Summary Cards (Rows 4-5)
    kpis_s2 = [
        ("A4:B4", "A5:B5", "TOTAL ACTIVE POSITIONS", "11 Verified Trades"),
        ("C4:E4", "C5:E5", "TOTAL ALLOCATED CAPITAL", "₹2,50,058.70"),
        ("F4:H4", "F5:H5", "AVERAGE 1-WEEK TARGET", "+8.29% (+₹20,730)"),
        ("I4:K4", "I5:K5", "AVERAGE 10-DAY TARGET", "+14.51% (+₹36,280)"),
        ("L4:N4", "L5:N5", "AVERAGE 1-MONTH TARGET", "+22.78% (+₹56,960)"),
        ("O4:P4", "O5:P5", "MAX RISK PER TRADE", "-4.15% (Strict SL Guard)"),
    ]
    for lbl_rng, val_rng, label, val_text in kpis_s2:
        ws2.merge_cells(lbl_rng)
        cl = ws2[lbl_rng.split(":")[0]]
        cl.value = label
        cl.font = font_kpi_lbl
        cl.fill = kpi_card_fill
        cl.alignment = Alignment(horizontal="center", vertical="center")

        ws2.merge_cells(val_rng)
        cv = ws2[val_rng.split(":")[0]]
        cv.value = val_text
        cv.font = font_kpi_val
        cv.fill = kpi_card_fill
        cv.alignment = Alignment(horizontal="center", vertical="center")

    for r in range(4, 6):
        for c in range(1, 17):
            ws2.cell(row=r, column=c).border = card_border

    # Headers for Sheet 2
    headers_s2 = [
        "#",
        "Stock Symbol",
        "Entry Date",
        "Buy Entry (₹)",
        "Stop Loss (₹)",
        "Risk / SL %",
        "1-Week Target (₹)",
        "1-Week %",
        "10-Day Target (₹)",
        "10-Day %",
        "1-Month Target (₹)",
        "1-Month %",
        "Shares Qty",
        "Capital (₹)",
        "Conviction",
        "Predictive Outlook & News Catalysts",
    ]
    ws2.row_dimensions[7].height = 26
    for col_idx, h in enumerate(headers_s2, start=1):
        cell = ws2.cell(row=7, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = navy_accent
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = header_border

    # Load active trades from JSON
    active_json_path = ROOT / "database" / "active_swing_trades.json"
    active_trades = []
    if active_json_path.exists():
        try:
            with open(active_json_path, "r", encoding="utf-8") as f:
                active_trades = json.load(f).get("active_trades", [])
        except Exception:
            pass

    for idx, t in enumerate(active_trades, start=1):
        row_idx = 7 + idx
        ws2.row_dimensions[row_idx].height = 24
        fill = zebra_even if idx % 2 == 0 else PatternFill(fill_type=None)

        catalysts = " | ".join(t.get("news_catalysts", []))
        if not catalysts:
            catalysts = t.get("predictive_outlook", "Clean Structure")

        row_vals = [
            idx,
            t.get("symbol", ""),
            t.get("entry_date", ""),
            t.get("entry_price", 0.0),
            t.get("stop_loss", 0.0),
            f"{t.get('stop_loss_pct', 0.0):.2f}%",
            t.get("target_1", 0.0),
            f"+{t.get('target_1_pct', 0.0):.2f}%",
            t.get("target_2", 0.0),
            f"+{t.get('target_2_pct', 0.0):.2f}%",
            t.get("target_3", 0.0),
            f"+{t.get('target_3', 0.0) / t.get('entry_price', 1.0) * 100 - 100:.2f}%" if t.get("entry_price") else "+20.0%",
            t.get("quantity", 0),
            t.get("capital_allocated", 0.0),
            f"{t.get('score', 80)}/100",
            catalysts,
        ]

        for col_idx, val in enumerate(row_vals, start=1):
            cell = ws2.cell(row=row_idx, column=col_idx, value=val)
            cell.font = font_regular
            cell.border = thin_border
            if fill.fill_type:
                cell.fill = fill

            # Formatting
            if col_idx in (4, 5, 7, 9, 11, 14):
                if isinstance(val, (int, float)):
                    cell.number_format = "₹#,##0.00"
            if col_idx in (1, 2, 3, 13, 15):
                cell.alignment = Alignment(horizontal="center", vertical="center")
                if col_idx == 2:
                    cell.font = font_bold
            elif col_idx in (6,):
                cell.font = font_red
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx in (8, 10, 12):
                cell.font = font_green
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx in (4, 5, 7, 9, 11, 14):
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    # Totals Row
    tot_row = 8 + len(active_trades)
    ws2.row_dimensions[tot_row].height = 24
    ws2.cell(row=tot_row, column=2, value="PORTFOLIO TOTAL / AVERAGE").font = font_bold
    ws2.cell(row=tot_row, column=14, value=f"=SUM(N8:N{tot_row-1})").font = font_bold
    ws2.cell(row=tot_row, column=14).number_format = "₹#,##0.00"
    ws2.cell(row=tot_row, column=14).alignment = Alignment(horizontal="right")
    for c in range(1, 17):
        ws2.cell(row=tot_row, column=c).border = Border(
            top=Side(style="thin", color="1B365D"),
            bottom=Side(style="double", color="1B365D"),
        )
        ws2.cell(row=tot_row, column=c).fill = section_fill

    # Sheet 2 Chart: Targets vs Buy Entry Price
    chart3 = BarChart()
    chart3.type = "col"
    chart3.style = 11
    chart3.title = "Top Swing Candidates: Buy Entry vs 1-Week & 10-Day Profit Targets"
    chart3.y_axis.title = "Stock Price (₹)"
    chart3.x_axis.title = "Stock Symbol"
    chart3.width = 18
    chart3.height = 9.5

    data_ref3 = Reference(ws2, min_col=4, min_row=7, max_col=9, max_row=min(7 + 7, tot_row - 1))
    cats_ref3 = Reference(ws2, min_col=2, min_row=8, max_row=min(7 + 7, tot_row - 1))
    chart3.add_data(data_ref3, titles_from_data=True)
    chart3.set_categories(cats_ref3)
    ws2.add_chart(chart3, f"A{tot_row + 3}")

    # =========================================================================
    # TAB 3: 5-BOT TELEGRAM ROUTING HUB
    # =========================================================================
    ws3 = wb.create_sheet(title="5-Bot Telegram Routing Hub")
    ws3.views.sheetView[0].showGridLines = True

    ws3.merge_cells("A1:H1")
    t3 = ws3["A1"]
    t3.value = "TELEGRAM 5-BOT UNIFIED AUTOMATION & ROUTING ARCHITECTURE"
    t3.font = font_title
    t3.fill = navy_dark
    t3.alignment = Alignment(horizontal="center", vertical="center")
    ws3.row_dimensions[1].height = 36

    ws3.merge_cells("A2:H2")
    st3 = ws3["A2"]
    st3.value = "Dedicated zero-spam architecture with independent channel separation for every trading strategy"
    st3.font = font_subtitle
    st3.fill = navy_dark
    st3.alignment = Alignment(horizontal="center", vertical="center")
    ws3.row_dimensions[2].height = 20

    headers_s3 = [
        "Bot #",
        "Telegram Bot Username",
        "Dedicated Trading Engine",
        "Environment Token Variable",
        "Execution Cadence",
        "Trigger Conditions & Alert Types",
        "Sample Delivered Message",
        "Priority",
    ]
    ws3.row_dimensions[4].height = 26
    for col_idx, h in enumerate(headers_s3, start=1):
        cell = ws3.cell(row=4, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = navy_accent
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = header_border

    bot_routing_data = [
        (
            "Bot 1",
            "@portfolio_bot",
            "🎯 7–10 Day Stock Swing Engine",
            "PORTFOLIO_TELEGRAM_BOT_TOKEN",
            "Mondays 09:30 AM (Entry) & Fridays 03:15 PM (Exit)",
            "Buy Entries (1W, 10D, 1M targets), Dynamic Realized Exits (±%), Weekly Excel Audit",
            "🟢 BUY TRENT (10-DAY SWING)\n• Target 1 (5d): ₹3,283.84 (+8.8%)\n• Target 2 (10d): ₹3,483.75 (+15.5%)",
            "CRITICAL (HIGH)",
        ),
        (
            "Bot 2",
            "@Zerodhaportfoliopro_bot",
            "🛡️ Portfolio Peak Guard & Earnings Radar",
            "PORTFOLIO_GUARD_BOT_TOKEN",
            "Continuous 09:15 AM – 03:30 PM (Mon–Fri)",
            "Long-term portfolio drawdowns, 1-Day Pre-Earnings Blackout Warnings, Trailing Peak Alerts",
            "⚠️ EARNINGS BLACKOUT ALERT: VEDL reports Q2 results tomorrow. Profit-booking recommended.",
            "HIGH (Portfolio)",
        ),
        (
            "Bot 3",
            "@Swingtradeniftybot",
            "📊 Bidirectional Options, BTST & Crude Oil",
            "TELEGRAM_BOT_TOKEN",
            "Hourly :50 (Intraday), 10:00 AM (Crude), 03:00 PM (BTST)",
            "CE/PE Intraday Options, 2-Min Live Target/SL tracking, 11:45 AM & 4:00 PM Summary Reports",
            "🎯 TARGET 1 HIT: TRENT 3000 CE (+35.4% ROI) @ ₹48.50. Trailing SL locked to ₹42.00.",
            "MEDIUM-HIGH",
        ),
        (
            "Bot 4",
            "@Jinna_Nifty_BOT",
            "⚡ NIFTY V14.9 Paper Trading Scalper",
            "NIFTY_PAPER_BOT_TOKEN",
            "Continuous 09:00 AM – 03:30 PM (Mon–Fri)",
            "Automated index scalping signals, tick-by-tick order fills, paper P&L updates",
            "⚡ NIFTY BUY SCALP @ 24,180 | SL: 24,150 | Target: 24,240 | Signal Score: 92/100",
            "MEDIUM",
        ),
        (
            "Bot 5",
            "@Nifty_stage10_paper_bot",
            "🔥 Hero-Zero Weekly Expiry Engine",
            "HERO_ZERO_BOT_TOKEN",
            "Tue (NIFTY) & Thu (SENSEX) 02:00–03:10 PM",
            "Quality deep out-of-the-money expiry power spikes, 03:50 PM final settlement audit",
            "🔥 HERO-ZERO ALERT: NIFTY 24200 CE @ ₹12.50. High delta gamma expansion setup. Max risk: ₹12.50.",
            "EXPIRY SPECIAL",
        ),
    ]

    for idx, b in enumerate(bot_routing_data, start=5):
        ws3.row_dimensions[idx].height = 36
        fill = soft_green if idx == 5 else (zebra_even if idx % 2 == 0 else PatternFill(fill_type=None))
        for col_idx, val in enumerate(b, start=1):
            cell = ws3.cell(row=idx, column=col_idx, value=val)
            cell.font = font_bold if col_idx in (1, 2, 8) else font_regular
            cell.border = thin_border
            if fill.fill_type:
                cell.fill = fill

            if col_idx in (1, 2, 4, 5, 8):
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

    # =========================================================================
    # TAB 4: 4-PILLAR SAFETY ARCHITECTURE
    # =========================================================================
    ws4 = wb.create_sheet(title="4-Pillar Safety Architecture")
    ws4.views.sheetView[0].showGridLines = True

    ws4.merge_cells("A1:F1")
    t4 = ws4["A1"]
    t4.value = "4-PILLAR QUANTITATIVE SAFETY & PREDICTIVE CRASH RADAR"
    t4.font = font_title
    t4.fill = navy_dark
    t4.alignment = Alignment(horizontal="center", vertical="center")
    ws4.row_dimensions[1].height = 36

    ws4.merge_cells("A2:F2")
    st4 = ws4["A2"]
    st4.value = "Engineered to eliminate catastrophic 10%–50% non-technical stock collapses prior to capital entry"
    st4.font = font_subtitle
    st4.fill = navy_dark
    st4.alignment = Alignment(horizontal="center", vertical="center")
    ws4.row_dimensions[2].height = 20

    pillars = [
        (
            "Pillar 1: Universe & Liquidity Guard",
            "Full NSE Equity Universe Filter",
            "Excludes penny stocks (< ₹10) and low-liquidity counters. Requires > ₹1 Crore average daily turnover to guarantee seamless market fills without slippage.",
            "Active on All Scans",
            "ZERO SLIPPAGE",
        ),
        (
            "Pillar 2: Predictive Crash Shield",
            "Forensic Red-Flag Keyword Scanner",
            "Scans real-time corporate news feeds. Instantly rejects stocks undergoing SEBI/CBI/ED probes, auditor resignations, CFO exits, NCLT defaults, promoter pledging, or FDA import alerts.",
            "Pre-Entry Filter",
            "CATASTROPHIC SHIELD",
        ),
        (
            "Pillar 3: Quarterly Earnings Blackout",
            "1-Day Pre-Results Blackout Window",
            "Detects quarterly earnings release dates within the 7–10 day holding window. Strictly forbids gambling through binary earnings announcements.",
            "Holding Horizon Window",
            "ZERO EARNINGS GAMBLE",
        ),
        (
            "Pillar 4: 5-Trigger Dynamic Exit Engine",
            "Automated Profit-Booking & Stop Loss",
            "Evaluates live Kite spot prices: (1) Emergency News Exit, (2) Target 2 Hit (+10%+), (3) Target 1 Hit (+5.5%+), (4) Capital Stop Loss (-3.5%), (5) 10-Day Time Horizon reached.",
            "Fridays 3:15 PM & Daily",
            "CAPITAL PRESERVATION",
        ),
    ]

    headers_s4 = [
        "Pillar",
        "Safety Architecture Component",
        "Operational Mechanism & Rules",
        "Evaluation Frequency",
        "Protection Level",
    ]
    ws4.row_dimensions[4].height = 26
    for col_idx, h in enumerate(headers_s4, start=1):
        cell = ws4.cell(row=4, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = navy_accent
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = header_border

    for idx, p in enumerate(pillars, start=5):
        ws4.row_dimensions[idx].height = 42
        fill = zebra_even if idx % 2 == 0 else PatternFill(fill_type=None)
        for col_idx, val in enumerate(p, start=1):
            cell = ws4.cell(row=idx, column=col_idx, value=val)
            cell.font = font_bold if col_idx in (1, 2, 5) else font_regular
            cell.border = thin_border
            if fill.fill_type:
                cell.fill = fill

            if col_idx in (1, 4, 5):
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                if col_idx == 5:
                    cell.font = font_green
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

    # -------------------------------------------------------------------------
    # Auto-Fit Column Widths for All Sheets
    # -------------------------------------------------------------------------
    for ws in wb.worksheets:
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.row in (1, 2):  # skip merged banners
                    continue
                val = str(cell.value or "")
                if len(val) > max_len:
                    max_len = len(val)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    # Specific fine-tuned column overrides
    ws1.column_dimensions["A"].width = 8
    ws1.column_dimensions["B"].width = 14
    ws1.column_dimensions["C"].width = 14
    ws1.column_dimensions["D"].width = 12
    ws1.column_dimensions["E"].width = 44
    ws1.column_dimensions["F"].width = 38
    ws1.column_dimensions["G"].width = 22
    ws1.column_dimensions["H"].width = 24
    ws1.column_dimensions["I"].width = 54
    ws1.column_dimensions["J"].width = 20

    ws2.column_dimensions["A"].width = 6
    ws2.column_dimensions["B"].width = 14
    ws2.column_dimensions["C"].width = 13
    ws2.column_dimensions["D"].width = 15
    ws2.column_dimensions["E"].width = 15
    ws2.column_dimensions["F"].width = 13
    ws2.column_dimensions["G"].width = 18
    ws2.column_dimensions["H"].width = 12
    ws2.column_dimensions["I"].width = 18
    ws2.column_dimensions["J"].width = 12
    ws2.column_dimensions["K"].width = 18
    ws2.column_dimensions["L"].width = 12
    ws2.column_dimensions["M"].width = 12
    ws2.column_dimensions["N"].width = 16
    ws2.column_dimensions["O"].width = 13
    ws2.column_dimensions["P"].width = 60

    ws3.column_dimensions["A"].width = 8
    ws3.column_dimensions["B"].width = 26
    ws3.column_dimensions["C"].width = 32
    ws3.column_dimensions["D"].width = 30
    ws3.column_dimensions["E"].width = 30
    ws3.column_dimensions["F"].width = 50
    ws3.column_dimensions["G"].width = 46
    ws3.column_dimensions["H"].width = 18

    ws4.column_dimensions["A"].width = 30
    ws4.column_dimensions["B"].width = 32
    ws4.column_dimensions["C"].width = 65
    ws4.column_dimensions["D"].width = 22
    ws4.column_dimensions["E"].width = 24

    # Save to Shared Folder with Lock Safety
    saved_path = OUTPUT_FILE
    try:
        wb.save(OUTPUT_FILE)
        print(f"✅ Successfully created Master Excel in shared folder: {OUTPUT_FILE}")
    except PermissionError:
        saved_path = SHARED_DIR / f"NiftyScanner_Master_Schedule_and_Trading_Matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        wb.save(saved_path)
        print(f"⚠️ Primary file '{OUTPUT_FILE.name}' is open in Excel. Saved updated version to: {saved_path}")

    # Also keep a copy in NIFTY-SCANNER repo for GitHub sync
    target_dir = Path("D:/NiftyScanner/NIFTY-SCANNER")
    if not target_dir.exists():
        target_dir = Path("D:/NIFTY-SCANNER")
    nifty_scanner_copy = target_dir / "NiftyScanner_Master_Schedule_and_Trading_Matrix.xlsx"
    try:
        if target_dir.exists():
            shutil.copy2(saved_path, nifty_scanner_copy)
            print(f"✅ Synchronized copy to: {nifty_scanner_copy}")
    except Exception as exc:
        print(f"Note: Could not copy to NIFTY-SCANNER: {exc}")


if __name__ == "__main__":
    create_master_excel()
