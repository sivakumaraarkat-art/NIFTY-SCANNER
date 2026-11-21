"""
check_dixon_entry_timing.py
Evaluates Entry Timing for DIXON (NSE:DIXON / DIXON.NS) using:
  1. day-trader-skill trader-entry engine (Yahoo DIXON.NS)
  2. Live Zerodha Kite intraday bars & levels
"""

import sys
import io
import subprocess
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent

def check_yahoo_entry():
    skill_script = Path("C:/Users/Siva Kumar/.claude-omniroute/plugins/cache/day-trader-skill/day-trader-skill/2.0.0/trader-entry/entry.py")
    if skill_script.exists():
        print("[*] Running day-trader-skill trader-entry engine for DIXON.NS...")
        cmd = [sys.executable, str(skill_script), "check", "DIXON.NS"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.stdout:
            print("--- trader-entry stdout ---")
            print(res.stdout.strip())
        if res.stderr:
            print("--- trader-entry stderr ---")
            print(res.stderr.strip())

def check_zerodha_live_entry():
    print("\n[*] Checking Live Zerodha Kite Intraday & Key Level Entry for NSE:DIXON...")
    try:
        from kiteconnect import KiteConnect
        token_file = ROOT / ".kite_access_token"
        key_file = ROOT / ".kite_api_key"
        if token_file.exists() and key_file.exists():
            access_token = token_file.read_text(encoding="utf-8").strip()
            api_key = key_file.read_text(encoding="utf-8").strip()
            kite = KiteConnect(api_key=api_key)
            kite.set_access_token(access_token)

            q = kite.quote(["NSE:DIXON"])
            if q and "NSE:DIXON" in q:
                data = q["NSE:DIXON"]
                ltp = data["last_price"]
                ohlc = data["ohlc"]
                open_p = ohlc.get("open")
                high_p = ohlc.get("high")
                low_p = ohlc.get("low")
                close_prev = ohlc.get("close")

                print(f"   📡 Real-Time Zerodha Kite Quote: NSE:DIXON")
                print(f"      LTP: ₹{ltp:,.2f}")
                print(f"      Day Open: ₹{open_p:,.2f} | Day High: ₹{high_p:,.2f} | Day Low: ₹{low_p:,.2f}")
                print(f"      Previous Close: ₹{close_prev:,.2f} (Day Change: {((ltp - close_prev)/close_prev)*100:+.2f}%)")
                print(f"      Total Buy Qty: {data.get('buy_quantity', 0):,} | Total Sell Qty: {data.get('sell_quantity', 0):,}")
                print(f"      Daily Turnover: ₹{data.get('volume', 0) * ltp / 1e7:,.2f} Cr")
                return
    except Exception as e:
        print(f"   ⚠️ Zerodha quote notice: {e}")

if __name__ == "__main__":
    check_yahoo_entry()
    check_zerodha_live_entry()
