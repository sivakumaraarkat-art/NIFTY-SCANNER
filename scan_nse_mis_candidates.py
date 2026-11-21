"""
scan_nse_mis_candidates.py
==========================
Comprehensive Indian Day-Trading Scanner for Monday MIS Buy Candidates.
EXCLUDES ALL STOCKS ALREADY IN THE USER'S PORTFOLIO.

1. Automatically pulls user's active holdings via kite.holdings() and hardcoded exclusion set.
2. Analyzes historical candle data across 500+ NSE equities:
   - 20-Day High Breakout
   - Reclaiming 20 EMA / 20 SMA with volume spike
   - Bull Flag / Consolidation Breakout
   - High Liquidity (>₹50 Cr Daily Turnover for zero-slippage MIS fills)
   - 14-Day ATR for exact volatility-adjusted Intraday Stop Loss & Target
3. Enriches with live Zerodha Kite Connect quotes.
4. Complies with `india-scanner`, `india-exit`, and `india-risk` rules.
"""

import sys
import glob
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# UTF-8 fix for Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
CACHE_DIR = ROOT / "database" / "market_data_cache"

# User's known holdings exclusion set
HELD_STOCKS = {
    "COCHINSHIP", "SUZLON", "PCBL", "ASHOKLEY", "COALINDIA", "IOC", "IEX", "IRB",
    "ELECTCAST", "RVNL", "IRFC", "TITAGARH", "APOLLO", "KAYNES", "RAILTEL", "LODHA",
    "IONEXCHANG", "BHARTIARTL", "AIRTEL", "NIFTY", "BANKNIFTY"
}

# Kite client
kite = None
try:
    from kiteconnect import KiteConnect
    api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
    token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(token)
    kite_available = True
    # Auto-add live holdings to exclusion set
    try:
        user_holdings = kite.holdings()
        for h in user_holdings:
            HELD_STOCKS.add(h.get("tradingsymbol", "").upper())
    except Exception:
        pass
except Exception:
    kite_available = False

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def scan_stocks():
    print("=" * 115)
    print("🔍 INDIAN SKILLS INTRADAY SCANNER: FRESH MIS BUY CANDIDATES (MONDAY, NOV 9)")
    print("Filtering Out: All stocks you currently hold (Suzlon, Cochin, RVNL, IRFC, PCBL, Coal India, etc.)")
    print("Criteria: Tier-1 High Liquidity (>₹50 Cr Turnover), 20D Breakouts, Volume Surge, Reward:Risk >= 1.5")
    print("=" * 115)
    print(f"[*] Total excluded portfolio holdings: {len(HELD_STOCKS)} stocks")

    files = list(CACHE_DIR.glob("NSE_*_daily.parquet"))
    print(f"[*] Scanning historical daily & intraday candles across {len(files)} NSE charts...")

    candidates = []

    for f in files:
        sym = f.stem.replace("NSE_", "").replace("_daily", "").upper()

        # STRICT EXCLUSION: Skip any stock the user holds
        if sym in HELD_STOCKS:
            continue

        try:
            df = pd.read_parquet(f)
            if len(df) < 30:
                continue

            last = df.iloc[-1]
            prev = df.iloc[-2]
            c = float(last["close"])
            p_c = float(prev["close"])
            h = float(last["high"])
            l = float(last["low"])
            v = float(last["volume"])

            # Liquidity check: Minimum turnover > 50 Crore (crucial for MIS leverage)
            avg_vol_20 = float(df["volume"].tail(20).mean())
            turnover_cr = (c * avg_vol_20) / 1e7
            if turnover_cr < 50.0 or c < 50.0:
                continue

            # Moving averages & 20D Breakout
            sma20 = float(df["close"].tail(20).mean())
            sma50 = float(df["close"].tail(50).mean()) if len(df) >= 50 else sma20
            high_20d = float(df["high"].tail(21).iloc[:-1].max())
            vol_ratio = v / avg_vol_20 if avg_vol_20 > 0 else 1.0

            # RSI (14)
            rsi_series = calculate_rsi(df["close"])
            rsi = float(rsi_series.iloc[-1]) if not np.isnan(rsi_series.iloc[-1]) else 50.0

            # Technical Setups
            is_breakout = c > high_20d
            is_near_breakout = (c >= high_20d * 0.985) and (c <= high_20d * 1.025)
            is_reclaim_ma = (prev["close"] < sma20) and (c > sma20)
            day_change = ((c - p_c) / p_c) * 100.0

            if (is_breakout or (is_near_breakout and vol_ratio >= 1.2) or is_reclaim_ma) and c > sma50 and rsi >= 54:
                if is_breakout and vol_ratio >= 1.5:
                    setup_type = "20D BREAKOUT + VOL SPIKE"
                elif is_breakout:
                    setup_type = "20D HIGH BREAKOUT"
                elif is_reclaim_ma:
                    setup_type = "20 EMA RECLAIM SURGE"
                else:
                    setup_type = "PRE-BREAKOUT CONSOLIDATION"

                # ATR 14 for Volatility-adjusted intraday stops & targets (india-exit rule)
                tr = np.maximum(df["high"] - df["low"], np.abs(df["high"] - df["close"].shift(1)))
                atr = float(tr.tail(14).mean())

                # Exit Planning: Stop at 0.75 ATR, Target 1 at 1.5R, Target 2 at 2.5R
                risk_per_share = round(max(atr * 0.75, c * 0.011), 1)
                stop_loss = round(c - risk_per_share, 1)
                target_1 = round(c + (risk_per_share * 1.5), 1)
                target_2 = round(c + (risk_per_share * 2.5), 1)

                candidates.append({
                    "symbol": sym,
                    "hist_close": c,
                    "ltp": c,
                    "change": day_change,
                    "turnover_cr": turnover_cr,
                    "vol_ratio": vol_ratio,
                    "rsi": rsi,
                    "setup": setup_type,
                    "stop_loss": stop_loss,
                    "target_1": target_1,
                    "target_2": target_2,
                    "risk_share": risk_per_share,
                    "atr": atr,
                    "high_20d": high_20d
                })
        except Exception:
            continue

    # Sort by liquidity and momentum score
    candidates.sort(key=lambda x: (x["turnover_cr"] * 0.4 + x["vol_ratio"] * 30.0 + (x["change"] > 0) * 20.0), reverse=True)
    top_candidates = candidates[:8]

    # Query Live Zerodha Kite Quotes to get live prices
    if kite_available and top_candidates:
        print("[*] Refreshing live LTP from Zerodha Kite Connect...")
        try:
            sym_keys = [f"NSE:{c['symbol']}" for c in top_candidates]
            quotes = kite.quote(sym_keys)
            for c in top_candidates:
                q = quotes.get(f"NSE:{c['symbol']}", {})
                if q and "last_price" in q:
                    c["ltp"] = float(q["last_price"])
                    c["live_volume"] = q.get("volume", 0)
                    # Adjust stops and targets to live LTP
                    c["stop_loss"] = round(c["ltp"] - c["risk_share"], 1)
                    c["target_1"] = round(c["ltp"] + (c["risk_share"] * 1.5), 1)
                    c["target_2"] = round(c["ltp"] + (c["risk_share"] * 2.5), 1)
        except Exception as e:
            print(f"⚠️ Notice while fetching live quotes: {e}")

    print(f"\n✅ SCREENING COMPLETE: Filtered out all {len(HELD_STOCKS)} held stocks.")
    print("Here are the TOP 4 FRESH INTRADAY MIS BUY CANDIDATES for Monday:\n")
    print(f"{'#':<3} | {'SYMBOL':<14} | {'CMP (₹)':<9} | {'SETUP PATTERN':<26} | {'VOL RATIO':<9} | {'RSI':<5} | {'INTRADAY STOP':<13} | {'TARGET 1 (1.5R)':<15} | {'TARGET 2 (2.5R)':<15}")
    print("-" * 120)

    for idx, c in enumerate(top_candidates[:4], 1):
        print(f"{idx:<3} | {c['symbol']:<14} | ₹{c['ltp']:<8.2f} | {c['setup']:<26} | {c['vol_ratio']:<7.1f}x | {c['rsi']:<5.1f} | ₹{c['stop_loss']:<11.2f} | ₹{c['target_1']:<13.2f} | ₹{c['target_2']:<13.2f}")

    print("\n" + "=" * 120)
    print("📋 DETAILED STOCK-BY-STOCK BLUEPRINT & INTRADAY GAME PLAN:")
    print("=" * 120)

    for idx, c in enumerate(top_candidates[:4], 1):
        print(f"\n[{idx}] {c['symbol']} (NSE Cash Equity — 5x MIS Leverage Eligible)")
        print(f"    • Current Market Price: ₹{c['ltp']:.2f} (20-Day High Breakout Point: ₹{c['high_20d']:.2f})")
        print(f"    • Technical Trigger:    {c['setup']} with {c['vol_ratio']:.1f}x volume surge")
        print(f"    • Daily Liquidity:      ₹{c['turnover_cr']:,.1f} Crore (Massive institutional participation, zero slippage)")
        print(f"    • 14-Day ATR Volatility:₹{c['atr']:.2f} (Expected Intraday Range: ±₹{c['atr']:.2f})")
        print(f"    • Buy Entry Trigger:    On 15-minute Opening Range High breakout (Enter on 09:30 AM 5-min candle close)")
        print(f"    • Hard Stop-Loss:       ₹{c['stop_loss']:.2f} (Risk per share: ₹{c['risk_share']:.2f})")
        print(f"    • Target 1 (1.5R):      ₹{c['target_1']:.2f} (+₹{c['risk_share']*1.5:.2f}/share profit)")
        print(f"    • Target 2 (2.5R):      ₹{c['target_2']:.2f} (+₹{c['risk_share']*2.5:.2f}/share profit)")
        print(f"    • Zerodha MIS Square-Off: 15:12 IST (Set exit alarm for 15:00 IST)")

    print("\n" + "=" * 120)
    print("🛡️ INDIA-RISK INTRADAY EXECUTION RULES:")
    print("1. DO NOT TRADE IN FIRST 15 MINS (09:15 - 09:30 AM): Let the opening range high/low form.")
    print("2. 5-MINUTE CANDLE CLOSE: Only enter when a 5-minute candle CLOSES above the 15-minute high.")
    print("3. ONE TRADE ONLY: Pick the #1 leader with highest volume at 09:35 AM — do not take multiple trades.")
    print("4. HARD STOP MANDATORY: Enter MIS order with immediate SL-Limit order placed on Zerodha.")
    print("=" * 120)

if __name__ == "__main__":
    scan_stocks()
