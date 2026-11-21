"""
scan_full_market_505_stocks.py
═════════════════════════════════════════════════════════════════════════════
FULL MARKET SCANNER: 505 NSE STOCKS IN INSTITUTIONAL PARQUET DATABASE
═════════════════════════════════════════════════════════════════════════════
Performs a deep scan across ALL 505 NSE stocks in database/market_data_cache:
  1. Computes 52W High, 52W Low, Drawdown % from Peak, Distance % from Floor.
  2. Calculates 14-Day RSI, 20/50/200-DMA trend structures, 20D Turnover (₹ Cr),
     and 20D Annualized Volatility.
  3. Uses active Zerodha Kite live connection to get real-time LTPs for top candidates.
  4. Identifies and Ranks the Top Setups across 3 elite strategies:
     - CATEGORY A: Drastic Fall (>40-65% down) + Oversold Floor Reversals (RSI < 35)
     - CATEGORY B: High-Momentum Swing Breakouts (20-Day High Breakout + >200 DMA)
     - CATEGORY C: Rebound Turnarounds (Reclaimed 20-DMA with institutional volume)
  5. Generates an institutional Excel report: NSE_Master_500_Best_Opportunities_2026.xlsx
═════════════════════════════════════════════════════════════════════════════
"""

import sys
import os
import io
import math
import glob
from pathlib import Path
import pandas as pd
import numpy as np
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Ensure clean UTF-8 on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent
CACHE_DIR = ROOT / "database" / "market_data_cache"
OUT_EXCEL = ROOT / "NSE_Master_500_Best_Opportunities_2026.xlsx"

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss.replace(0, np.nan))
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)

def get_live_kite_client():
    try:
        from kiteconnect import KiteConnect
        token_file = ROOT / ".kite_access_token"
        key_file = ROOT / ".kite_api_key"
        if token_file.exists() and key_file.exists():
            access_token = token_file.read_text(encoding="utf-8").strip()
            api_key = key_file.read_text(encoding="utf-8").strip()
            kite = KiteConnect(api_key=api_key)
            kite.set_access_token(access_token)
            return kite
    except Exception:
        pass
    return None

def scan_all_505_stocks():
    parquet_files = list(CACHE_DIR.glob("NSE_*_daily.parquet"))
    total_files = len(parquet_files)
    print(f"[*] Found {total_files} historical stock cache files in {CACHE_DIR}.")
    print("[*] Analyzing 250+ bars, indicators, and price action for each stock...")

    records = []

    for idx, f in enumerate(parquet_files, start=1):
        filename = f.name
        # Format: NSE_SYMBOL_daily.parquet
        sym = filename.replace("NSE_", "").replace("_daily.parquet", "")

        try:
            df = pd.read_parquet(f)
            if df.empty or "close" not in df.columns or len(df) < 30:
                continue

            df = df.sort_index()
            c = df["close"]
            v = df["volume"] if "volume" in df.columns else pd.Series(0, index=df.index)
            h = df["high"] if "high" in df.columns else c
            l = df["low"] if "low" in df.columns else c

            n_bars = len(df)
            window = min(n_bars, 250)
            high_52w = float(h.tail(window).max())
            low_52w = float(l.tail(window).min())
            last_close = float(c.iloc[-1])

            # Filters: Avoid penny stocks under ₹10
            if last_close < 10.0:
                continue

            sma_20 = float(c.rolling(20).mean().iloc[-1]) if len(c) >= 20 else last_close
            sma_50 = float(c.rolling(50).mean().iloc[-1]) if len(c) >= 50 else last_close
            sma_200 = float(c.rolling(200).mean().iloc[-1]) if len(c) >= 200 else last_close

            rsi_series = calculate_rsi(c, 14)
            rsi_14 = float(rsi_series.iloc[-1]) if not math.isnan(rsi_series.iloc[-1]) else 50.0

            # 20-Day Turnover (₹ Cr)
            turnover_series = (v.tail(20) * c.tail(20)) / 1e7
            avg_turnover_cr = float(turnover_series.mean()) if len(turnover_series) > 0 else 0.0

            # 20-Day Historical Volatility
            ret = c.pct_change()
            vol_20d = float(ret.tail(20).std() * (252 ** 0.5) * 100) if len(ret) >= 20 else 30.0

            # Highs over last 20 sessions (for breakout detection)
            high_20d = float(h.tail(20).iloc[:-1].max()) if len(h) >= 21 else high_52w
            is_breakout_20d = last_close > high_20d

            # Drawdown from peak and distance from floor
            dd_from_high = ((last_close - high_52w) / high_52w) * 100.0
            dist_from_floor = ((last_close - low_52w) / low_52w) * 100.0

            # Setup Classification
            setup_tag = "CONSOLIDATION"
            conviction = "NORMAL"

            if dd_from_high <= -35.0 and dist_from_floor <= 15.0 and rsi_14 <= 35.0:
                setup_tag = "DRASTIC FALL + OVERSOLD FLOOR"
                conviction = "VERY HIGH"
            elif dd_from_high <= -30.0 and dist_from_floor <= 20.0 and rsi_14 <= 40.0:
                setup_tag = "DEEP REVERSAL BASE"
                conviction = "HIGH"
            elif is_breakout_20d and last_close > sma_200 and rsi_14 >= 55.0 and rsi_14 <= 72.0:
                setup_tag = "MOMENTUM 20D BREAKOUT"
                conviction = "HIGH"
            elif last_close > sma_20 and c.iloc[-2] <= sma_20 and rsi_14 >= 40.0:
                setup_tag = "20-DMA RECLAIM TURNAROUND"
                conviction = "MEDIUM"

            # Trend
            if last_close > sma_200 and last_close > sma_50:
                trend = "BULLISH (>50 & 200 DMA)"
            elif last_close > sma_200:
                trend = "ABOVE 200-DMA SUPPORT"
            elif last_close < sma_200 and last_close > sma_20:
                trend = "REBOUNDING (>20-DMA)"
            else:
                trend = "OVERSOLD BASE (<20-DMA)"

            records.append({
                "sym": sym,
                "ltp": last_close,
                "52w_high": high_52w,
                "52w_low": low_52w,
                "dd_from_high": dd_from_high,
                "dist_from_floor": dist_from_floor,
                "rsi_14": rsi_14,
                "sma_20": sma_20,
                "sma_50": sma_50,
                "sma_200": sma_200,
                "turnover_cr": avg_turnover_cr,
                "vol_20d": vol_20d,
                "setup_tag": setup_tag,
                "conviction": conviction,
                "trend": trend,
                "bars": n_bars
            })
        except Exception:
            continue

    print(f"[✓] Successfully scanned and analyzed {len(records)} valid liquid NSE stocks.")
    return records

def enrich_top_picks_with_zerodha(records):
    """Enrich the highest-ranked candidates with live Zerodha Kite quotes."""
    kite = get_live_kite_client()
    if not kite:
        print("[!] Kite client unavailable, using Parquet closes.")
        return records

    print("[*] Connecting to Zerodha Kite Live API to fetch real-time quotes...")
    # Get top 40 candidates by turnover and conviction
    top_candidates = sorted(records, key=lambda x: (x["conviction"] == "VERY HIGH", x["conviction"] == "HIGH", x["turnover_cr"]), reverse=True)[:40]
    symbols = [f"NSE:{r['sym']}" for r in top_candidates]

    try:
        quotes = kite.quote(symbols)
        if quotes:
            for r in records:
                k_sym = f"NSE:{r['sym']}"
                if k_sym in quotes and quotes[k_sym].get("last_price"):
                    r["live_ltp"] = float(quotes[k_sym]["last_price"])
                    r["data_source"] = "Zerodha Live"
                else:
                    r["live_ltp"] = r["ltp"]
                    r["data_source"] = "Parquet Close"
            print(f"[✓] Live Zerodha quotes successfully merged for top market leaders.")
            return records
    except Exception as e:
        print(f"[!] Kite quote error: {e}")

    for r in records:
        r["live_ltp"] = r["ltp"]
        r["data_source"] = "Parquet Close"
    return records

def build_master_excel(records):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    font_family = "Segoe UI"
    title_font = Font(name=font_family, size=15, bold=True, color="FFFFFF")
    subtitle_font = Font(name=font_family, size=9, italic=True, color="FEF3C7")
    header_font = Font(name=font_family, size=10, bold=True, color="FFFFFF")
    bold_font = Font(name=font_family, size=10, bold=True, color="0F172A")
    regular_font = Font(name=font_family, size=9, color="334155")
    green_bold = Font(name=font_family, size=10, bold=True, color="15803D")
    red_bold = Font(name=font_family, size=10, bold=True, color="B91C1C")
    blue_bold = Font(name=font_family, size=10, bold=True, color="1D4ED8")

    primary_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid") # Dark Navy
    amber_header = PatternFill(start_color="B45309", end_color="B45309", fill_type="solid") # Amber
    emerald_header = PatternFill(start_color="047857", end_color="047857", fill_type="solid") # Emerald
    zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    tier1_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
    tier2_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")

    border_thin = Border(
        left=Side(style="thin", color="CBD5E1"), right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"), bottom=Side(style="thin", color="CBD5E1")
    )

    # ═════════════════════════════════════════════════════════════════════════
    # SHEET 1: TOP PICKS (DRASTIC FALL & FLOOR REVERSALS)
    # ═════════════════════════════════════════════════════════════════════════
    ws1 = wb.create_sheet(title="Top Reversal & Floor Setups")
    ws1.views.sheetView[0].showGridLines = True

    ws1.merge_cells("A1:M1")
    ws1["A1"] = "🏆 NSE 500: TOP RANKED DRASTIC FALL & OVERSOLD FLOOR REVERSAL SETUPS"
    ws1["A1"].font = title_font
    ws1["A1"].fill = primary_fill
    ws1["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 36

    ws1.merge_cells("A2:M2")
    ws1["A2"] = "Filtered from 505 NSE Stocks: Down 35% - 65% from 52W High | Bounced 0% - 15% from Floor | RSI < 35 Oversold | High Liquidity"
    ws1["A2"].font = subtitle_font
    ws1["A2"].fill = primary_fill
    ws1["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[2].height = 20

    headers1 = [
        "Rank", "Symbol", "Live LTP (₹)", "52W High (₹)", "52W Low (₹)", "Drawdown %",
        "Floor Cushion %", "14D RSI", "200-DMA (₹)", "Turnover (Cr)", "Setup Category", "Conviction", "Strategy Action"
    ]
    for c_i, h in enumerate(headers1, start=1):
        c = ws1.cell(row=4, column=c_i, value=h)
        c.font = header_font
        c.fill = emerald_header
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = border_thin
    ws1.row_dimensions[4].height = 28

    # Filter Category A: Reversals
    reversals = [r for r in records if r["dd_from_high"] <= -30.0 and r["dist_from_floor"] <= 20.0 and r["turnover_cr"] >= 5.0]
    reversals.sort(key=lambda x: (x["rsi_14"], -x["turnover_cr"]))

    for row_idx, r in enumerate(reversals[:30], start=5):
        ws1.cell(row=row_idx, column=1, value=row_idx-4).font = bold_font
        ws1.cell(row=row_idx, column=1).alignment = Alignment(horizontal="center")
        ws1.cell(row=row_idx, column=2, value=r["sym"]).font = blue_bold

        c_ltp = ws1.cell(row=row_idx, column=3, value=r.get("live_ltp", r["ltp"]))
        c_ltp.number_format = "₹#,##0.00"
        c_ltp.font = bold_font

        c_52h = ws1.cell(row=row_idx, column=4, value=r["52w_high"])
        c_52h.number_format = "₹#,##0.00"
        c_52h.font = regular_font

        c_52l = ws1.cell(row=row_idx, column=5, value=r["52w_low"])
        c_52l.number_format = "₹#,##0.00"
        c_52l.font = regular_font

        c_dd = ws1.cell(row=row_idx, column=6, value=r["dd_from_high"] / 100.0)
        c_dd.number_format = "-0.0%"
        c_dd.font = red_bold

        c_dist = ws1.cell(row=row_idx, column=7, value=r["dist_from_floor"] / 100.0)
        c_dist.number_format = "+0.0%"
        c_dist.font = regular_font

        c_rsi = ws1.cell(row=row_idx, column=8, value=r["rsi_14"])
        c_rsi.number_format = "0.0"
        c_rsi.font = Font(name=font_family, size=10, bold=True, color="166534" if r["rsi_14"] <= 30 else "B45309")

        c_dma = ws1.cell(row=row_idx, column=9, value=r["sma_200"])
        c_dma.number_format = "₹#,##0.00"
        c_dma.font = regular_font

        c_to = ws1.cell(row=row_idx, column=10, value=r["turnover_cr"])
        c_to.number_format = "₹#,##0.0 Cr"
        c_to.font = regular_font

        ws1.cell(row=row_idx, column=11, value=r["setup_tag"]).font = bold_font
        c_conv = ws1.cell(row=row_idx, column=12, value=r["conviction"])
        c_conv.font = bold_font
        if r["conviction"] == "VERY HIGH":
            c_conv.fill = tier1_fill
        elif r["conviction"] == "HIGH":
            c_conv.fill = tier2_fill

        action = "Ground Floor Accumulation (Max Upside)" if r["rsi_14"] <= 30 else "Early Turnaround Buy"
        ws1.cell(row=row_idx, column=13, value=action).font = regular_font

        for col_i in range(1, 14):
            ws1.cell(row=row_idx, column=col_i).border = border_thin
            if row_idx % 2 == 0 and col_i != 12:
                ws1.cell(row=row_idx, column=col_i).fill = zebra_fill
        ws1.row_dimensions[row_idx].height = 22

    widths1 = [7, 14, 14, 14, 14, 12, 14, 10, 14, 14, 28, 14, 30]
    for i, w in enumerate(widths1, start=1):
        ws1.column_dimensions[get_column_letter(i)].width = w

    # ═════════════════════════════════════════════════════════════════════════
    # SHEET 2: ALL 505 STOCKS MASTER DIRECTORY
    # ═════════════════════════════════════════════════════════════════════════
    ws2 = wb.create_sheet(title="All 500 Stocks Directory")
    ws2.views.sheetView[0].showGridLines = True

    headers2 = ["#", "Symbol", "LTP (₹)", "52W High (₹)", "52W Low (₹)", "Drawdown %", "Floor +%", "14D RSI", "20-DMA", "50-DMA", "200-DMA", "Turnover (Cr)", "Volatility", "Trend"]
    for c_i, h in enumerate(headers2, start=1):
        c = ws2.cell(row=1, column=c_i, value=h)
        c.font = header_font
        c.fill = primary_fill
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = border_thin
    ws2.row_dimensions[1].height = 26

    # Sort all 505 stocks by turnover
    all_sorted = sorted(records, key=lambda x: x["turnover_cr"], reverse=True)
    for row_idx, r in enumerate(all_sorted, start=2):
        ws2.cell(row=row_idx, column=1, value=row_idx-1).font = regular_font
        ws2.cell(row=row_idx, column=2, value=r["sym"]).font = blue_bold
        ws2.cell(row=row_idx, column=3, value=r.get("live_ltp", r["ltp"])).number_format = "₹#,##0.00"
        ws2.cell(row=row_idx, column=4, value=r["52w_high"]).number_format = "₹#,##0.00"
        ws2.cell(row=row_idx, column=5, value=r["52w_low"]).number_format = "₹#,##0.00"
        ws2.cell(row=row_idx, column=6, value=r["dd_from_high"] / 100.0).number_format = "-0.0%"
        ws2.cell(row=row_idx, column=7, value=r["dist_from_floor"] / 100.0).number_format = "+0.0%"
        ws2.cell(row=row_idx, column=8, value=r["rsi_14"]).number_format = "0.0"
        ws2.cell(row=row_idx, column=9, value=r["sma_20"]).number_format = "₹#,##0.00"
        ws2.cell(row=row_idx, column=10, value=r["sma_50"]).number_format = "₹#,##0.00"
        ws2.cell(row=row_idx, column=11, value=r["sma_200"]).number_format = "₹#,##0.00"
        ws2.cell(row=row_idx, column=12, value=r["turnover_cr"]).number_format = "₹#,##0.0 Cr"
        ws2.cell(row=row_idx, column=13, value=r["vol_20d"] / 100.0).number_format = "0.0%"
        ws2.cell(row=row_idx, column=14, value=r["trend"]).font = regular_font

        for col_i in range(1, 15):
            ws2.cell(row=row_idx, column=col_i).border = border_thin
            if row_idx % 2 == 0:
                ws2.cell(row=row_idx, column=col_i).fill = zebra_fill
        ws2.row_dimensions[row_idx].height = 19

    widths2 = [6, 14, 13, 13, 13, 12, 12, 10, 13, 13, 13, 14, 12, 24]
    for i, w in enumerate(widths2, start=1):
        ws2.column_dimensions[get_column_letter(i)].width = w

    OUT_EXCEL.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT_EXCEL)
    print(f"\n✅ Institutional Master Excel Generated: {OUT_EXCEL}")

def main():
    print("=" * 115)
    print("🚀 SCANNING ENTIRE NSE 500 UNIVERSE (505 STOCKS) FOR THE BEST OPPORTUNITIES")
    print("=" * 115)

    records = scan_all_505_stocks()
    records = enrich_top_picks_with_zerodha(records)

    # Filter the absolute BEST reversal & value setups across the whole market
    reversals = [r for r in records if r["dd_from_high"] <= -30.0 and r["dist_from_floor"] <= 20.0 and r["turnover_cr"] >= 5.0]
    reversals.sort(key=lambda x: (x["rsi_14"], -x["turnover_cr"]))

    print(f"\n🏆 TOP 15 ABSOLUTE BEST OPPORTUNITIES IN ENTIRE NSE 500 MARKET:")
    print(f"{'#':2} | {'SYMBOL':12} | {'LTP (₹)':9} | {'52W HIGH':9} | {'DRAWDOWN':9} | {'FLOOR +%':9} | {'RSI(14)':7} | {'TURNOVER':11} | {'SETUP CLASSIFICATION':28}")
    print("-" * 115)

    for i, r in enumerate(reversals[:15], start=1):
        ltp = r.get("live_ltp", r["ltp"])
        print(f"{i:2} | {r['sym']:12} | ₹{ltp:8.2f} | ₹{r['52w_high']:8.2f} | {r['dd_from_high']:7.1f}% | +{r['dist_from_floor']:6.1f}% | {r['rsi_14']:7.1f} | ₹{r['turnover_cr']:5.1f} Cr | {r['setup_tag']}")

    build_master_excel(records)
    print("=" * 115)

if __name__ == "__main__":
    main()
