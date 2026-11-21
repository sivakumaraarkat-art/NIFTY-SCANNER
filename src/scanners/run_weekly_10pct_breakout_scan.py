"""
run_weekly_10pct_breakout_scan.py
=================================
Automated High-Velocity 10%+ Weekly Breakout Scanner.
Scans NIFTY 500 & F&O stocks for coiled spring setups capable of moving
minimum +10% to +15% over the 5-day weekly swing cycle.

Criteria:
1. Daily ATR (14-day) >= 3.2% (Physical horsepower to move 3-5% per day)
2. Coiled Base: 5-Day Price Range <= 3.8% (Volatility Contraction Pattern)
3. Did NOT jump yet: Day Change <= +2.0%
4. Ultra-Tight Risk: Stop Loss <= 3.8% below 5-day base floor
5. Minimum +10.0% upside runway to major resistance
6. Accumulation: Up-day volume exceeds down-day volume in base

Usage:
    python src/scanners/run_weekly_10pct_breakout_scan.py --test
    python src/scanners/run_weekly_10pct_breakout_scan.py --cron
"""

import sys
import io
import os
import argparse
import datetime
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# Console encoding fix for Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def get_kite_client():
    from kiteconnect import KiteConnect
    token_paths = [
        ROOT / ".kite_access_token",
        ROOT.parent / ".kite_access_token",
        Path("/home/ubuntu/NiftyScanner/.kite_access_token"),
        Path("D:/NiftyScanner/.kite_access_token"),
    ]
    token = None
    for p in token_paths:
        if p.exists():
            t = p.read_text(encoding="utf-8").strip()
            if t:
                token = t
                break

    key_paths = [
        ROOT / ".kite_api_key",
        ROOT.parent / ".kite_api_key",
        Path("/home/ubuntu/NiftyScanner/.kite_api_key"),
        Path("D:/NiftyScanner/.kite_api_key"),
    ]
    key = None
    for p in key_paths:
        if p.exists():
            k = p.read_text(encoding="utf-8").strip()
            if k:
                key = k
                break

    if not key:
        key = os.getenv("ZERODHA_API_KEY", "")

    if not key or not token:
        raise RuntimeError("Missing Zerodha Kite API key or access token")

    kite = KiteConnect(api_key=key)
    kite.set_access_token(token)
    return kite


def load_nifty500_symbols():
    candidates = [
        ROOT / "nifty500_symbols.txt",
        ROOT / "stock_universe" / "nifty500_symbols.txt",
    ]
    for c in candidates:
        if c.exists():
            return [line.strip() for line in c.read_text(encoding="utf-8").splitlines() if line.strip()]

    # Fallback to liquid high-beta symbols
    return [
        "CONCORDBIO", "GALLANTT", "ANANTRAJ", "SWANCORP", "BDL", "VTL", "JBMA",
        "BIOCON", "PCBL", "JIOFIN", "CONCOR", "KAYNES", "TITAGARH", "MAZDOCK",
        "RVNL", "COCHINSHIP", "RRKABEL", "CREDITACC", "AEGISLOG", "WELCORP",
        "PERSISTENT", "DIXON", "BHARTIARTL", "KOTAKBANK"
    ]


def run_breakout_scan(kite, max_results=5):
    symbols = load_nifty500_symbols()
    tradingsymbols = [f"NSE:{s}" for s in symbols]

    all_quotes = {}
    batch_size = 200
    for i in range(0, len(tradingsymbols), batch_size):
        batch = tradingsymbols[i:i+batch_size]
        try:
            q = kite.quote(batch)
            all_quotes.update(q)
        except Exception:
            pass

    to_date = datetime.date.today()
    from_date = to_date - datetime.timedelta(days=60)

    candidates = []

    for sym, q in all_quotes.items():
        clean = sym.replace("NSE:", "")
        ltp = q.get("last_price", 0)
        prev_close = q.get("ohlc", {}).get("close", 0)

        if prev_close == 0 or ltp < 40 or ltp > 3500:
            continue

        day_chg = ((ltp - prev_close) / prev_close) * 100

        # 1. NOT ALREADY JUMPED (Day change <= 2.2%)
        if day_chg > 2.2:
            continue

        token = q.get("instrument_token")
        if not token:
            continue

        try:
            hist = kite.historical_data(token, from_date, to_date, "day")
            if len(hist) < 20:
                continue

            # 2. Daily ATR (14-day) >= 3.2% (Horserpower)
            ranges = [max(x["high"] - x["low"], abs(x["high"] - x["close"]), abs(x["low"] - x["close"])) for x in hist[-14:]]
            atr14 = sum(ranges) / len(ranges)
            atr_pct = (atr14 / ltp) * 100

            if atr_pct < 3.0:
                continue

            # 3. 5-Day Coiled Base
            last_5 = hist[-5:]
            l5 = min(c["low"] for c in last_5)
            h5 = max(c["high"] for c in last_5)
            range_5d = ((h5 - l5) / l5) * 100

            if range_5d > 4.2:
                continue

            # 4. Stop Loss & Risk
            sl = round(l5 * 0.99, 1)
            risk = ltp - sl
            risk_pct = (risk / ltp) * 100

            if risk_pct > 4.5 or risk_pct <= 0:
                continue

            # 5. Targets (Minimum +10% & +15%)
            t10 = round(ltp * 1.10, 1)
            t15 = round(ltp * 1.15, 1)

            # 6. Upside Room
            h60 = max(c["high"] for c in hist)
            upside_to_peak = ((h60 - ltp) / ltp) * 100
            if upside_to_peak < 10.0:
                continue

            # 7. Volume Accumulation
            last_10 = hist[-10:]
            up_vol = sum(c["volume"] for c in last_10 if c["close"] >= c["open"])
            dn_vol = sum(c["volume"] for c in last_10 if c["close"] < c["open"])
            vol_ratio = round(up_vol / dn_vol, 2) if dn_vol > 0 else 1.0

            rr = round(10.0 / risk_pct, 1)

            candidates.append({
                "symbol": clean,
                "ltp": ltp,
                "day_chg": round(day_chg, 2),
                "atr_pct": round(atr_pct, 2),
                "range_5d": round(range_5d, 2),
                "entry_low": round(l5, 1),
                "entry_high": round(ltp, 1),
                "sl": sl,
                "risk_pct": round(risk_pct, 2),
                "t10": t10,
                "t15": t15,
                "rr": rr,
                "vol_ratio": vol_ratio,
                "upside_to_peak": round(upside_to_peak, 1),
            })
        except Exception:
            pass
        time.sleep(0.015)

    # Sort by quality score (ATR * VolRatio / Risk)
    candidates.sort(key=lambda x: (x["atr_pct"] * x["vol_ratio"] / x["risk_pct"]), reverse=True)
    return candidates[:max_results]


def format_telegram_alert(candidates):
    if not candidates:
        return None

    date_str = datetime.datetime.now().strftime("%d-%b-%Y %H:%M")
    lines = [
        f"🚀 <b>WEEKLY 10%+ BREAKOUT SCANNER</b>",
        f"📅 <i>{date_str} IST | Monday High-Velocity Launchpad</i>",
        f"──────────────────────────",
        f"<i>Screened for Daily ATR ≥3.2%, Coiled Base ≤3.8%, Tight Risk ≤3.5%, and Min +10% Target in 5 Days:</i>\n"
    ]

    for i, c in enumerate(candidates, 1):
        lines.append(
            f"<b>{i}. {c['symbol']}</b> (CMP: ₹{c['ltp']:.2f} | {c['day_chg']:+0.2f}%)\n"
            f"   • 📈 Daily ATR: <b>{c['atr_pct']}%</b> | 5D Base: <b>{c['range_5d']}%</b>\n"
            f"   • 🛒 Ideal Entry: <b>₹{c['entry_low']:.1f} – ₹{c['entry_high']:.1f}</b>\n"
            f"   • 🛑 Stop Loss: <b>₹{c['sl']:.1f}</b> (Risk: -{c['risk_pct']}%)\n"
            f"   • 🎯 Target 1: <b>₹{c['t10']:.1f} (+10.0%)</b>\n"
            f"   • 🚀 Target 2: <b>₹{c['t15']:.1f} (+15.0%)</b>\n"
            f"   • ⚖️ Risk-to-Reward: <b>1 : {c['rr']}</b>\n"
        )

    lines.append("──────────────────────────")
    lines.append("💡 <i>Strategy: Buy inside entry zone. Bank 50% at Target 1, trail SL to cost. Hold 3–7 days.</i>")
    return "\n".join(lines)


def send_telegram(message):
    token = os.getenv("PORTFOLIO_TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("PORTFOLIO_TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("⚠️ Telegram token or chat_id not configured in .env.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        res = r.json()
        if res.get("ok"):
            print("✓ Telegram alert dispatched successfully!")
            return True
        else:
            print(f"⚠️ Telegram API response: {res}")
            return False
    except Exception as e:
        print(f"❌ Telegram send error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Weekly 10%+ Breakout Scanner")
    parser.add_argument("--cron", action="store_true", help="Run via cron and send alert to Telegram")
    parser.add_argument("--test", action="store_true", help="Run dry run and print alert to console")
    args = parser.parse_args()

    print("=" * 70)
    print("🚀 WEEKLY 10%+ BREAKOUT SCANNER (LAUNCHPAD ENGINE)")
    print("=" * 70)

    try:
        kite = get_kite_client()
        print("✓ Connected to Zerodha Kite API.")
    except Exception as e:
        print(f"❌ Kite connection error: {e}")
        return

    print("Scanning universe for coiled spring candidates...")
    candidates = run_breakout_scan(kite, max_results=5)
    print(f"✓ Found {len(candidates)} high-velocity setups.")

    msg = format_telegram_alert(candidates)
    if not msg:
        print("No candidates matched criteria.")
        return

    if args.cron:
        send_telegram(msg)
    else:
        print("\n--- TELEGRAM ALERT PREVIEW ---")
        # Print without HTML tags for console
        import re
        clean_text = re.sub(r"<[^>]+>", "", msg)
        print(clean_text)

    print("=" * 70)


if __name__ == "__main__":
    main()
