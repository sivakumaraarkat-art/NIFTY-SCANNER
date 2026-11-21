"""
check_suzlon_entry_timing.py
Evaluates Entry Timing for SUZLON (NSE:SUZLON) using:
  1. day-trader-skill trader-entry engine (Yahoo SUZLON.NS)
  2. Live Zerodha Kite intraday bars & levels
"""

import sys
import io
import subprocess
from pathlib import Path
from datetime import datetime
import pandas as pd

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent

def check_yahoo_entry():
    skill_script = Path("C:/Users/Siva Kumar/.claude-omniroute/plugins/cache/day-trader-skill/day-trader-skill/2.0.0/trader-entry/entry.py")
    if skill_script.exists():
        print("[*] Running day-trader-skill trader-entry engine for SUZLON.NS...")
        cmd = [sys.executable, str(skill_script), "check", "SUZLON.NS"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        print("--- trader-entry stdout ---")
        print(res.stdout.strip() if res.stdout else "No stdout")
        if res.stderr:
            print("--- trader-entry stderr ---")
            print(res.stderr.strip())

def check_zerodha_live_entry():
    print("\n[*] Checking Live Zerodha Kite Intraday & Key Level Entry for NSE:SUZLON...")
    try:
        from kiteconnect import KiteConnect
        token_file = ROOT / ".kite_access_token"
        key_file = ROOT / ".kite_api_key"
        if token_file.exists() and key_file.exists():
            access_token = token_file.read_text(encoding="utf-8").strip()
            api_key = key_file.read_text(encoding="utf-8").strip()
            kite = KiteConnect(api_key=api_key)
            kite.set_access_token(access_token)

            q = kite.quote(["NSE:SUZLON"])
            if q and "NSE:SUZLON" in q:
                data = q["NSE:SUZLON"]
                ltp = data["last_price"]
                ohlc = data["ohlc"]
                open_p = ohlc.get("open")
                high_p = ohlc.get("high")
                low_p = ohlc.get("low")
                close_prev = ohlc.get("close")
                depth = data.get("depth", {})

                print(f"   📡 Real-Time Zerodha Kite Quote: NSE:SUZLON")
                print(f"      LTP: ₹{ltp:,.2f}")
                print(f"      Day Open: ₹{open_p:,.2f} | Day High: ₹{high_p:,.2f} | Day Low: ₹{low_p:,.2f}")
                print(f"      Previous Close: ₹{close_prev:,.2f} (Day Change: {((ltp - close_prev)/close_prev)*100:+.2f}%)")
                print(f"      Total Buy Qty: {data.get('buy_quantity', 0):,} | Total Sell Qty: {data.get('sell_quantity', 0):,}")
                return
    except Exception as e:
        print(f"   ⚠️ Zerodha quote notice: {e}")

    # Fallback to local Parquet cache
    cache_file = ROOT / "database" / "market_data_cache" / "NSE_SUZLON_daily.parquet"
    if cache_file.exists():
        df = pd.read_parquet(cache_file)
        last_close = df["close"].iloc[-1]
        print(f"   📊 Cached Last Close: ₹{last_close:,.2f}")

if __name__ == "__main__":
    check_yahoo_entry()
    check_zerodha_live_entry()
