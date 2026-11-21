"""
fetch_zerodha_historical.py
Fetches historical market data from Zerodha Kite Connect API.
Supports daily, 5-minute, 15-minute, 60-minute, and 1-minute intervals.
Automatically resolves instrument tokens and can save output to trader-in/kite/
format compatible with india-day-trader-skill tools.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Fix stdout/stderr for Windows console unicode (Rupee symbol support)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent

try:
    from kiteconnect import KiteConnect
except ImportError:
    print("❌ kiteconnect not installed. Run: pip install kiteconnect", file=sys.stderr)
    sys.exit(1)


def get_kite_client() -> KiteConnect:
    """Load API key & access token, verifying or refreshing if needed."""
    key_file = ROOT / ".kite_api_key"
    token_file = ROOT / ".kite_access_token"

    if not key_file.exists() or not token_file.exists():
        print("❌ Missing .kite_api_key or .kite_access_token in project root.", file=sys.stderr)
        sys.exit(1)

    api_key = key_file.read_text(encoding="utf-8").strip()
    access_token = token_file.read_text(encoding="utf-8").strip()

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

    try:
        profile = kite.profile()
        print(f"🔑 Authenticated with Zerodha: {profile.get('user_name')} ({profile.get('user_id')})")
    except Exception as e:
        print(f"⚠️ Token validation failed ({e}). Attempting auto-refresh...", file=sys.stderr)
        gen_script = ROOT / "generate_fresh_kite_token.py"
        if gen_script.exists():
            import subprocess
            res = subprocess.run([sys.executable, str(gen_script)], capture_output=True, text=True)
            if res.returncode == 0:
                print("✓ Access token successfully renewed.")
                access_token = token_file.read_text(encoding="utf-8").strip()
                kite.set_access_token(access_token)
            else:
                print(f"❌ Auto-refresh failed:\n{res.stderr}", file=sys.stderr)
                sys.exit(1)
        else:
            print("❌ Cannot refresh token: generate_fresh_kite_token.py not found.", file=sys.stderr)
            sys.exit(1)

    return kite


# Standard instrument tokens for key indices
INDEX_TOKENS = {
    "NIFTY 50": 256265,
    "NIFTY": 256265,
    "^NSEI": 256265,
    "NIFTY BANK": 260105,
    "BANKNIFTY": 260105,
    "NIFTY FIN SERVICE": 257801,
    "FINNIFTY": 257801,
    "NIFTY MIDCAP 50": 258057,
    "NIFTY NEXT 50": 259849,
    "INDIA VIX": 264969,
}


def resolve_instrument_token(kite: KiteConnect, symbol: str, exchange: str = "NSE") -> tuple[int, str]:
    """Resolve symbol to (instrument_token, formatted_symbol)."""
    clean_sym = symbol.strip().upper()
    if clean_sym.startswith("NSE:"):
        clean_sym = clean_sym[4:]
        exchange = "NSE"
    elif clean_sym.startswith("BSE:"):
        clean_sym = clean_sym[4:]
        exchange = "BSE"

    if clean_sym in INDEX_TOKENS:
        return INDEX_TOKENS[clean_sym], clean_sym

    # First try Kite LTP lookup (very fast)
    kite_key = f"{exchange}:{clean_sym}"
    try:
        quote = kite.ltp([kite_key])
        if kite_key in quote and quote[kite_key].get("instrument_token"):
            return quote[kite_key]["instrument_token"], clean_sym
    except Exception:
        pass

    # Fallback to instruments dump search
    cache_file = ROOT / f".instruments_{exchange.lower()}.json"
    instruments = None
    if cache_file.exists():
        # Check cache age < 24h
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    instruments = json.load(f)
            except Exception:
                instruments = None

    if instruments is None:
        print(f"[*] Downloading master instrument list for {exchange} from Zerodha...")
        instruments = kite.instruments(exchange)
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(instruments, f)
        except Exception:
            pass

    for inst in instruments:
        if inst.get("tradingsymbol") == clean_sym and inst.get("segment") in (exchange, f"{exchange}-EQ"):
            return inst["instrument_token"], clean_sym

    raise ValueError(f"Could not find instrument token for symbol: {symbol} on {exchange}")


def fetch_history(
    kite: KiteConnect,
    token: int,
    from_date: datetime,
    to_date: datetime,
    interval: str = "day"
) -> list[dict]:
    """Fetch historical candles from Kite Connect API."""
    # Format dates as YYYY-MM-DD for day interval, or with time for intraday
    if interval == "day":
        from_str = from_date.strftime("%Y-%m-%d")
        to_str = to_date.strftime("%Y-%m-%d")
    else:
        from_str = from_date.strftime("%Y-%m-%d %H:%M:%S")
        to_str = to_date.strftime("%Y-%m-%d %H:%M:%S")

    records = kite.historical_data(
        instrument_token=token,
        from_date=from_str,
        to_date=to_str,
        interval=interval,
        continuous=False,
        oi=False,
    )
    return records


def print_candle_table(symbol: str, interval: str, candles: list[dict], show_last: int = 15):
    """Print a clean tabular representation of OHLCV candles."""
    if not candles:
        print(f"⚠️ No candles returned for {symbol}.")
        return

    print("=" * 85)
    print(f"📈 ZERODHA HISTORICAL DATA: {symbol} | Interval: {interval.upper()} | Total Bars: {len(candles)}")
    print("=" * 85)
    print(f"{'DATE / TIME':19} | {'OPEN':>9} | {'HIGH':>9} | {'LOW':>9} | {'CLOSE':>9} | {'CHG %':>8} | {'VOLUME':>12}")
    print("-" * 85)

    subset = candles[-show_last:] if show_last > 0 else candles
    for i, c in enumerate(subset):
        dt = c["date"]
        dt_str = dt.strftime("%Y-%m-%d %H:%M") if interval != "day" else dt.strftime("%Y-%m-%d")
        o, h, l, cl = c["open"], c["high"], c["low"], c["close"]
        v = c.get("volume", 0)
        chg_pct = ((cl - o) / o) * 100 if o else 0.0
        chg_str = f"{chg_pct:+.2f}%"
        print(f"{dt_str:19} | {o:9.2f} | {h:9.2f} | {l:9.2f} | {cl:9.2f} | {chg_str:>8} | {v:12,}")

    print("-" * 85)
    if len(candles) > len(subset):
        print(f"... and {len(candles) - len(subset)} earlier bars. Showing last {len(subset)} bars.")


def save_for_india_skill(symbol: str, interval: str, candles: list[dict], out_dir: Path | None = None) -> Path:
    """Save candles in trader-in/kite/ format compatible with india-day-trader-skill."""
    if out_dir is None:
        out_dir = ROOT / "trader-in" / "kite"
    out_dir.mkdir(parents=True, exist_ok=True)

    today_str = datetime.now().strftime("%Y-%m-%d")
    out_file = out_dir / f"{symbol}-{interval}-{today_str}.json"

    # Convert datetime to ISO strings for JSON serialization
    serialized = []
    for c in candles:
        item = dict(c)
        if isinstance(item.get("date"), datetime):
            item["date"] = item["date"].isoformat()
        serialized.append(item)

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(serialized, f, indent=2)

    return out_file


def main():
    parser = argparse.ArgumentParser(description="Fetch historical market data from Zerodha Kite API.")
    parser.add_argument("--symbols", "-s", default="RELIANCE,TCS,INFY,HDFCBANK",
                        help="Comma-separated stock symbols or index (e.g. RELIANCE,TCS,NIFTY 50)")
    parser.add_argument("--interval", "-i", default="day",
                        choices=["minute", "3minute", "5minute", "10minute", "15minute", "30minute", "60minute", "day"],
                        help="Candle timeframe interval (default: day)")
    parser.add_argument("--days", "-d", type=int, default=30,
                        help="Number of lookback days (default: 30)")
    parser.add_argument("--from-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to-date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--show", type=int, default=10, help="Number of recent bars to display (default: 10)")
    parser.add_argument("--save-skill", action="store_true", default=True,
                        help="Auto-save to trader-in/kite/ for india-day-trader-skill (default: True)")
    parser.add_argument("--save-csv", action="store_true", help="Save output to CSV file")
    parser.add_argument("--exchange", default="NSE", choices=["NSE", "BSE"], help="Exchange (default: NSE)")

    args = parser.parse_args()

    kite = get_kite_client()

    now = datetime.now()
    if args.to_date:
        to_dt = datetime.strptime(args.to_date, "%Y-%m-%d")
    else:
        to_dt = now

    if args.from_date:
        from_dt = datetime.strptime(args.from_date, "%Y-%m-%d")
    else:
        from_dt = to_dt - timedelta(days=args.days)

    symbol_list = [s.strip() for s in args.symbols.split(",") if s.strip()]

    print(f"\n📡 Requesting {args.interval} historical data from {from_dt.strftime('%Y-%m-%d')} to {to_dt.strftime('%Y-%m-%d')} for {len(symbol_list)} symbols...\n")

    for symbol in symbol_list:
        try:
            token, clean_sym = resolve_instrument_token(kite, symbol, exchange=args.exchange)
            candles = fetch_history(kite, token, from_dt, to_dt, interval=args.interval)
            print_candle_table(clean_sym, args.interval, candles, show_last=args.show)

            if args.save_skill and candles:
                saved_path = save_for_india_skill(clean_sym, args.interval, candles)
                print(f"💾 Saved for India Day Trader Skill: {saved_path.relative_to(ROOT)}")

            if args.save_csv and candles:
                import csv
                csv_path = ROOT / f"{clean_sym}_{args.interval}.csv"
                keys = ["date", "open", "high", "low", "close", "volume"]
                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
                    writer.writeheader()
                    for row in candles:
                        r = dict(row)
                        if isinstance(r.get("date"), datetime):
                            r["date"] = r["date"].isoformat()
                        writer.writerow(r)
                print(f"💾 Exported CSV: {csv_path.name}")

            print()
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}\n", file=sys.stderr)


if __name__ == "__main__":
    main()
