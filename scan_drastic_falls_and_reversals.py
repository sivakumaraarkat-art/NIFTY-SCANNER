"""
scan_drastic_falls_and_reversals.py
Comprehensive NSE scanner for Drastic Falls & Technical Reversals:
- Uses Zerodha Kite Connect to download historical data for missing symbols
- Analyzes 52-Week High, 52-Week Low, % Fall, Rebound %, RSI, SMAs, Volume
- Identifies Confirmed Reversals vs Oversold Accumulation floors
- Updates rebound_stock_candidates.csv
- Generates Drastic_Fall_and_Reversal_Stocks_Master_Scan_2026.xlsx
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
import os, time, csv, datetime
from pathlib import Path
import pandas as pd
import numpy as np
from kiteconnect import KiteConnect
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

ROOT = Path("D:/NiftyScanner/STOCK_SWING_V1_updated")
CACHE_DIR = ROOT / "database" / "market_data_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CSV_OUTPUT = ROOT / "rebound_stock_candidates.csv"
EXCEL_OUTPUT = ROOT / "Drastic_Fall_and_Reversal_Stocks_Master_Scan_2026.xlsx"
NSE_CAP_DIR = ROOT / "data" / "nse_cap_segments"

PRIORITY_SYMBOLS = [
    ("RVNL", "MIDCAP"), ("IRFC", "LARGECAP"), ("APOLLO", "SMALLCAP"),
    ("COCHINSHIP", "MIDCAP"), ("KAYNES", "MIDCAP"), ("KPITTECH", "LARGECAP"),
    ("SUZLON", "MIDCAP"), ("TITAGARH", "MIDCAP"), ("RAILTEL", "SMALLCAP"),
    ("IRCON", "SMALLCAP"), ("JWL", "SMALLCAP"), ("ELECTCAST", "SMALLCAP"),
    ("PCBL", "SMALLCAP"), ("LODHA", "LARGECAP"), ("ASIANPAINT", "LARGECAP"),
    ("TATAMOTORS", "LARGECAP"), ("IRCTC", "LARGECAP"), ("TEXRAIL", "SMALLCAP"),
    ("RITES", "SMALLCAP"), ("DIXON", "LARGECAP")
]

def load_universe():
    symbols_map = {}
    # Priority symbols first
    for s, seg in PRIORITY_SYMBOLS:
        symbols_map[s] = seg

    files = {
        "LARGECAP": "nifty100.csv",
        "MIDCAP": "nifty_midcap150.csv",
        "SMALLCAP": "nifty_smallcap250.csv"
    }
    for seg, fn in files.items():
        p = NSE_CAP_DIR / fn
        if p.exists():
            with p.open(encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    sym = r.get("symbol", "").strip().upper()
                    if sym and sym not in symbols_map:
                        symbols_map[sym] = seg
    return symbols_map

def init_kite():
    try:
        api_key = (ROOT / ".kite_api_key").read_text(encoding="utf-8").strip()
        access_token = (ROOT / ".kite_access_token").read_text(encoding="utf-8").strip()
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        return kite
    except Exception as e:
        print(f"Error initializing Kite: {e}")
        return None

def fetch_or_load_historical(kite, instruments_map, symbol):
    parquet_path = CACHE_DIR / f"NSE_{symbol}_daily.parquet"
    if parquet_path.exists():
        try:
            df = pd.read_parquet(parquet_path)
            if len(df) >= 100:
                # verify latest date is recent (Oct 2026)
                latest_date = pd.to_datetime(df['date']).iloc[-1]
                if latest_date >= pd.to_datetime("2026-10-01"):
                    return df
        except Exception:
            pass

    if not kite or symbol not in instruments_map:
        return None

    # Download from Kite
    token = instruments_map[symbol]["instrument_token"]
    to_date = datetime.date.today()
    from_date = to_date - datetime.timedelta(days=365)
    try:
        candles = kite.historical_data(token, from_date, to_date, "day")
        if not candles or len(candles) < 50:
            return None
        df = pd.DataFrame(candles)
        df['date'] = pd.to_datetime(df['date'])
        # Save to parquet cache
        df.to_parquet(parquet_path, index=False)
        time.sleep(0.35) # respect rate limit
        return df
    except Exception as exc:
        print(f"Warning: Failed to fetch {symbol}: {exc}")
        return None

def analyze_stock(df, symbol, segment):
    if df is None or len(df) < 50:
        return None

    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    volumes = df['volume'].values

    ltp = round(float(closes[-1]), 2)
    high_52w = round(float(np.max(highs)), 2)
    low_52w = round(float(np.min(lows)), 2)

    fall_from_high_pct = round(((high_52w - ltp) / high_52w) * 100, 1)
    rebound_from_low_pct = round(((ltp - low_52w) / low_52w) * 100, 1)

    # Moving averages
    sma_20 = round(float(np.mean(closes[-20:])), 2) if len(closes) >= 20 else ltp
    sma_50 = round(float(np.mean(closes[-50:])), 2) if len(closes) >= 50 else ltp
    sma_200 = round(float(np.mean(closes[-200:])), 2) if len(closes) >= 200 else sma_50

    # 14-day RSI
    deltas = np.diff(closes)
    seed = deltas[-14:]
    up = seed[seed >= 0].sum() / 14 if len(seed[seed >= 0]) > 0 else 0
    down = -seed[seed < 0].sum() / 14 if len(seed[seed < 0]) > 0 else 0
    rs = up / down if down != 0 else 100
    rsi_14 = round(100 - (100 / (1 + rs)), 1)

    # 5-day return
    ret_5d = round(((closes[-1] / closes[-6] - 1) * 100), 1) if len(closes) >= 6 else 0.0

    # Volume ratio
    avg_vol_20 = np.mean(volumes[-21:-1]) if len(volumes) >= 21 else np.mean(volumes)
    vol_ratio = round(float(volumes[-1] / avg_vol_20), 1) if avg_vol_20 > 0 else 1.0

    # Support & Resistance
    support_20d = round(float(np.min(lows[-20:])), 2)
    recent_high_20d = round(float(np.max(highs[-20:])), 2)
    stop_loss = round(min(support_20d * 0.96, low_52w * 0.97), 2)
    target_1 = round(max(sma_20, ltp * 1.08), 2)
    target_2 = round(max(sma_50, ltp * 1.18), 2)
    target_3 = round(max(sma_200, ltp * 1.35), 2)

    # Reversal Classification
    # Only interested in stocks that had a meaningful fall (> 20%)
    if fall_from_high_pct < 18.0:
        return None

    # Logic for classification
    if fall_from_high_pct >= 25.0 and (ret_5d > 0.5 or ltp >= sma_20 * 0.98) and 35 <= rsi_14 <= 62:
        status = "CONFIRMED REVERSAL"
        conviction = "HIGH"
    elif fall_from_high_pct >= 30.0 and rsi_14 < 36 and rebound_from_low_pct <= 6.0:
        status = "OVERSOLD FLOOR ACCUMULATION"
        conviction = "HIGH"
    elif fall_from_high_pct >= 20.0 and 4.0 <= rebound_from_low_pct <= 18.0 and ret_5d >= 0:
        status = "WEEKLY BASE REBOUND"
        conviction = "MEDIUM-HIGH"
    elif fall_from_high_pct >= 35.0 and rsi_14 < 32:
        status = "DEEP VALUE WATCH"
        conviction = "MEDIUM"
    elif fall_from_high_pct >= 20.0:
        status = "PULLBACK - BASE BUILDING"
        conviction = "MONITOR"
    else:
        return None

    return {
        "symbol": symbol,
        "cap_segment": segment,
        "status": status,
        "conviction": conviction,
        "ltp": ltp,
        "52w_high": high_52w,
        "52w_low": low_52w,
        "fall_from_high_pct": fall_from_high_pct,
        "rebound_from_low_pct": rebound_from_low_pct,
        "rsi_14": rsi_14,
        "ret_5d": ret_5d,
        "vol_ratio": vol_ratio,
        "sma_20": sma_20,
        "sma_50": sma_50,
        "sma_200": sma_200,
        "support": support_20d,
        "stop_loss": stop_loss,
        "target_1": target_1,
        "target_2": target_2,
        "target_3": target_3
    }

def main():
    print("=" * 70)
    print("🚀 STARTING COMPREHENSIVE NSE HISTORICAL SCAN FOR DRASTIC FALLS & REVERSALS")
    print("=" * 70)

    universe = load_universe()
    print(f"Target Universe: {len(universe)} symbols (LargeCap, MidCap, SmallCap + Priority)")

    kite = init_kite()
    instruments_map = {}
    if kite:
        print("Fetching NSE instruments map from Zerodha...")
        try:
            for item in kite.instruments("NSE"):
                instruments_map[item["tradingsymbol"]] = item
            print(f"Loaded {len(instruments_map)} NSE instruments.")
        except Exception as e:
            print(f"Error loading instruments: {e}")

    results = []
    processed = 0
    downloaded = 0

    for sym, seg in universe.items():
        processed += 1
        parquet_path = CACHE_DIR / f"NSE_{sym}_daily.parquet"
        is_cached = parquet_path.exists()

        df = fetch_or_load_historical(kite, instruments_map, sym)
        if not is_cached and df is not None:
            downloaded += 1

        res = analyze_stock(df, sym, seg)
        if res:
            results.append(res)

        if processed % 50 == 0 or processed == len(universe):
            print(f"Progress: [{processed}/{len(universe)}] | Downloaded: {downloaded} | Reversal/Dip Matches: {len(results)}")

    print(f"\nScan Complete! Analyzed {processed} stocks. Identified {len(results)} Drastic Fall & Reversal Candidates.")

    # Sort results: High conviction first, then by Fall %
    conviction_order = {"HIGH": 0, "MEDIUM-HIGH": 1, "MEDIUM": 2, "MONITOR": 3}
    results.sort(key=lambda x: (conviction_order.get(x["conviction"], 9), -x["fall_from_high_pct"]))

    # Save to CSV
    save_to_csv(results)

    # Save to Excel
    save_to_excel(results)

def save_to_csv(results):
    fieldnames = [
        "symbol", "cap_segment", "status", "conviction", "ltp", "52w_high", "52w_low",
        "fall_from_high_pct", "rebound_from_low_pct", "rsi_14", "ret_5d", "vol_ratio",
        "sma_20", "sma_50", "sma_200", "support", "stop_loss", "target_1", "target_2", "target_3"
    ]
    with CSV_OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"✅ Saved CSV database to: {CSV_OUTPUT}")

def save_to_excel(results):
    wb = openpyxl.Workbook()
    wb.remove(wb.active) # Remove default sheet

    font_family = "Segoe UI"
    title_font = Font(name=font_family, size=15, bold=True, color="FFFFFF")
    subtitle_font = Font(name=font_family, size=10, italic=True, color="E2E8F0")
    section_font = Font(name=font_family, size=12, bold=True, color="1E293B")
    header_font = Font(name=font_family, size=10, bold=True, color="FFFFFF")
    bold_font = Font(name=font_family, size=10, bold=True, color="0F172A")
    regular_font = Font(name=font_family, size=10, color="334155")
    green_bold_font = Font(name=font_family, size=10, bold=True, color="15803D")
    red_bold_font = Font(name=font_family, size=10, bold=True, color="B91C1C")
    blue_bold_font = Font(name=font_family, size=10, bold=True, color="1D4ED8")

    primary_header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    sub_header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
    confirmed_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid") # Light Green
    oversold_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")  # Light Yellow
    zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"), right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"), bottom=Side(style="thin", color="CBD5E1")
    )
    center_align = Alignment(horizontal="center", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")

    # =============================================================
    # SHEET 1: TOP HIGH-CONVICTION REVERSALS
    # =============================================================
    ws1 = wb.create_sheet(title="Top Reversal Picks")
    ws1.views.sheetView[0].showGridLines = True

    ws1.merge_cells("A1:K1")
    ws1["A1"] = "TOP HIGH-CONVICTION REVERSAL & REBOUND PICKS (NSE MASTER SCAN)"
    ws1["A1"].font = title_font
    ws1["A1"].fill = primary_header_fill
    ws1["A1"].alignment = center_align
    ws1.row_dimensions[1].height = 34

    ws1.merge_cells("A2:K2")
    ws1["A2"] = f"Drastically Fallen Stocks (-20% to -60%) Showing Technical Reversal & Bottom Support | Scanned: {datetime.date.today()}"
    ws1["A2"].font = subtitle_font
    ws1["A2"].fill = primary_header_fill
    ws1["A2"].alignment = center_align
    ws1.row_dimensions[2].height = 20

    headers1 = [
        "Rank", "Symbol", "Segment", "Setup Status", "Conviction", "LTP (₹)",
        "Fall from High", "14D RSI", "5D Return %", "Stop-Loss (₹)", "Target 1 (₹)", "Target 2 (₹)"
    ]
    for c_idx, h in enumerate(headers1, start=1):
        c = ws1.cell(row=4, column=c_idx, value=h)
        c.font = header_font
        c.fill = sub_header_fill
        c.alignment = center_align
        c.border = thin_border
    ws1.row_dimensions[4].height = 26

    # Filter top 25 high conviction
    top_picks = [r for r in results if r["conviction"] in ["HIGH", "MEDIUM-HIGH"]][:25]
    for idx, r in enumerate(top_picks, start=1):
        r_idx = idx + 4
        ws1.cell(row=r_idx, column=1, value=idx).font = bold_font
        ws1.cell(row=r_idx, column=2, value=r["symbol"]).font = blue_bold_font
        ws1.cell(row=r_idx, column=3, value=r["cap_segment"]).font = regular_font

        c_status = ws1.cell(row=r_idx, column=4, value=r["status"])
        c_status.font = green_bold_font if "CONFIRMED" in r["status"] else bold_font
        if "CONFIRMED" in r["status"]:
            c_status.fill = confirmed_fill
        elif "OVERSOLD" in r["status"]:
            c_status.fill = oversold_fill

        ws1.cell(row=r_idx, column=5, value=r["conviction"]).font = bold_font

        c_ltp = ws1.cell(row=r_idx, column=6, value=r["ltp"])
        c_ltp.number_format = "₹#,##0.00"
        c_ltp.font = bold_font

        c_fall = ws1.cell(row=r_idx, column=7, value=-r["fall_from_high_pct"]/100)
        c_fall.number_format = "-0.0%"
        c_fall.font = red_bold_font

        ws1.cell(row=r_idx, column=8, value=r["rsi_14"]).font = bold_font

        c_ret = ws1.cell(row=r_idx, column=9, value=r["ret_5d"]/100)
        c_ret.number_format = "+0.0%;-0.0%;0.0%"
        c_ret.font = green_bold_font if r["ret_5d"] > 0 else regular_font

        c_sl = ws1.cell(row=r_idx, column=10, value=r["stop_loss"])
        c_sl.number_format = "₹#,##0.00"
        c_sl.font = red_bold_font

        c_t1 = ws1.cell(row=r_idx, column=11, value=r["target_1"])
        c_t1.number_format = "₹#,##0.00"
        c_t1.font = green_bold_font

        c_t2 = ws1.cell(row=r_idx, column=12, value=r["target_2"])
        c_t2.number_format = "₹#,##0.00"
        c_t2.font = green_bold_font

        for c_i in range(1, 13):
            ws1.cell(row=r_idx, column=c_i).border = thin_border
            if idx % 2 == 0 and not ws1.cell(row=r_idx, column=c_i).fill.fill_type:
                ws1.cell(row=r_idx, column=c_i).fill = zebra_fill
        ws1.row_dimensions[r_idx].height = 22

    widths1 = [8, 16, 14, 26, 14, 14, 15, 12, 14, 14, 14, 14]
    for i, w in enumerate(widths1, start=1):
        ws1.column_dimensions[get_column_letter(i)].width = w

    # =============================================================
    # SHEET 2: ALL CANDIDATES (COMPLETE DATABASE)
    # =============================================================
    ws2 = wb.create_sheet(title="All Drastic Fall Candidates")
    ws2.views.sheetView[0].showGridLines = True

    ws2.merge_cells("A1:N1")
    ws2["A1"] = "ALL STOCKS SCREENED WITH DRASTIC FALLS (> 20% FROM 52W HIGH)"
    ws2["A1"].font = title_font
    ws2["A1"].fill = primary_header_fill
    ws2["A1"].alignment = center_align
    ws2.row_dimensions[1].height = 34

    headers2 = [
        "Symbol", "Cap Segment", "Status", "Conviction", "LTP (₹)", "52W High (₹)", "52W Low (₹)",
        "Fall from High", "Rebound from Low", "14D RSI", "5D Return %", "Volume Ratio", "Stop-Loss (₹)", "Target 1 (₹)"
    ]
    for c_idx, h in enumerate(headers2, start=1):
        c = ws2.cell(row=3, column=c_idx, value=h)
        c.font = header_font
        c.fill = sub_header_fill
        c.alignment = center_align
        c.border = thin_border
    ws2.row_dimensions[3].height = 26

    for idx, r in enumerate(results, start=4):
        ws2.cell(row=idx, column=1, value=r["symbol"]).font = bold_font
        ws2.cell(row=idx, column=2, value=r["cap_segment"]).font = regular_font
        ws2.cell(row=idx, column=3, value=r["status"]).font = regular_font
        ws2.cell(row=idx, column=4, value=r["conviction"]).font = bold_font

        c5 = ws2.cell(row=idx, column=5, value=r["ltp"])
        c5.number_format = "₹#,##0.00"
        c6 = ws2.cell(row=idx, column=6, value=r["52w_high"])
        c6.number_format = "₹#,##0.00"
        c7 = ws2.cell(row=idx, column=7, value=r["52w_low"])
        c7.number_format = "₹#,##0.00"

        c8 = ws2.cell(row=idx, column=8, value=-r["fall_from_high_pct"]/100)
        c8.number_format = "-0.0%"
        c8.font = red_bold_font

        c9 = ws2.cell(row=idx, column=9, value=r["rebound_from_low_pct"]/100)
        c9.number_format = "+0.0%"

        ws2.cell(row=idx, column=10, value=r["rsi_14"]).font = bold_font

        c11 = ws2.cell(row=idx, column=11, value=r["ret_5d"]/100)
        c11.number_format = "+0.0%;-0.0%;0.0%"

        ws2.cell(row=idx, column=12, value=r["vol_ratio"]).font = regular_font

        c13 = ws2.cell(row=idx, column=13, value=r["stop_loss"])
        c13.number_format = "₹#,##0.00"
        c13.font = red_bold_font

        c14 = ws2.cell(row=idx, column=14, value=r["target_1"])
        c14.number_format = "₹#,##0.00"
        c14.font = green_bold_font

        for c_i in range(1, 15):
            ws2.cell(row=idx, column=c_i).border = thin_border
            if idx % 2 == 0:
                ws2.cell(row=idx, column=c_i).fill = zebra_fill
        ws2.row_dimensions[idx].height = 20

    widths2 = [16, 14, 26, 14, 14, 14, 14, 15, 16, 12, 14, 14, 14, 14]
    for i, w in enumerate(widths2, start=1):
        ws2.column_dimensions[get_column_letter(i)].width = w

    # Save
    EXCEL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(EXCEL_OUTPUT)
    print(f"✅ Saved Comprehensive Excel Master Scan to: {EXCEL_OUTPUT}")

if __name__ == "__main__":
    main()
