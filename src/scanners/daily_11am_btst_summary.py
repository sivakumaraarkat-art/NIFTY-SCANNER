"""11 AM IST review of the exact previous BTST selection; signal MTM, not realised fills."""
import argparse
import html
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from btst_batch import IST, project_root, logs_directory, load_batch, now_ist, contract_id

ROOT = project_root(__file__)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")


def get_kite_client():
    try:
        from src.scanners.options_data_provider import get_kite_client as provider
        return provider()
    except Exception as exc:
        print(f"Quotes unavailable ({type(exc).__name__}). Reporting selected contracts with N/A prices.")
        return None


def get_telegram_credentials():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if bot_token and chat_id:
        return bot_token, chat_id

    script_dir = Path(__file__).resolve().parent
    candidates = [
        ROOT / ".credentials.json",
        ROOT / ".env",
        Path("/home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/.credentials.json"),
        Path("/home/ubuntu/NiftyScanner/.credentials.json"),
    ]
    for cred_path in candidates:
        if not cred_path.exists():
            continue
        try:
            if cred_path.suffix == ".json":
                with cred_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                tg = data.get("telegram", {})
                b = tg.get("bot_token")
                c = tg.get("chat_id")
                if b and c:
                    return b, c
        except Exception:
            continue
    return bot_token, chat_id


def send_telegram_message(text: str) -> bool:
    token, chat = get_telegram_credentials()
    if not token or not chat:
        print("⚠️ Telegram keys missing. Skipping alert dispatch.")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        r.raise_for_status()
        return r.json().get("ok") is True
    except Exception as e:
        print(f"[TELEGRAM] Delivery failed or unknown ({type(e).__name__}).")
        return False


def valid_quote_price(quote, at):
    """Only use a valid quote price from today; never invent prices or fills."""
    try:
        value = float(quote.get("last_price", 0.0))
        if not math.isfinite(value) or value <= 0:
            value = float(quote.get("ohlc", {}).get("close", 0.0))
        if not math.isfinite(value) or value <= 0:
            return None

        stamp = quote.get("timestamp")
        if stamp:
            if not isinstance(stamp, datetime):
                stamp = datetime.fromisoformat(str(stamp))
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=IST)
            if stamp.astimezone(IST).date() == at.date():
                return value
        return value
    except (TypeError, ValueError, KeyError):
        return None


def evaluate_btst_performance(log_dir=None, scan_date=None, *, offline=False, at=None, kite=None):
    at = (at or now_ist()).astimezone(IST)
    path, batch = load_batch(logs_directory(__file__, log_dir), scan_date, at)
    if kite is None and not offline:
        kite = get_kite_client()
    quotes = {}
    if kite is not None and not offline:
        try:
            quotes = kite.quote([contract_id(c) for c in batch["selected_candidates"]]) or {}
        except Exception as exc:
            print(f"Quote request failed ({type(exc).__name__}); keeping every selected contract as N/A.")
    trades = []
    for c in batch["selected_candidates"]:
        key = contract_id(c)
        entry = float(c.get("entry_price", c.get("ltp")))
        quantity = int(c["recommended_qty"]) * int(c["lot_size"])
        quote = quotes.get(key) or {}
        current = valid_quote_price(quote, at)

        # Retrieve OHLC to detect if Target 1, Target 2, or SL was reached in the morning session
        ohlc = quote.get("ohlc", {})
        high = float(ohlc.get("high", current or 0.0))
        low = float(ohlc.get("low", current or 0.0))
        t1 = float(c.get("t1", entry * 1.25))
        t2 = float(c.get("t2", entry * 1.50))
        sl = float(c.get("powerful_sl", c.get("sl", entry * 0.85)))

        pct_move = ((current - entry) / entry * 100) if (current is not None and entry > 0) else 0.0
        if current is not None and current <= sl:
            outcome = "SL HIT 🛑 (-15%)"
            outcome_price = sl
        elif high >= t2:
            outcome = "TARGET 2 HIT 🎯🎯 (+50%)"
            outcome_price = t2
        elif high >= t1:
            outcome = "TARGET 1 HIT 🎯 (+25%)"
            outcome_price = t1
        elif current is not None:
            outcome = f"OPEN / MTM ({pct_move:+.1f}%)"
            outcome_price = current
        else:
            outcome = "AWAITING QUOTE"
            outcome_price = entry

        pnl = (current - entry) * quantity if current is not None else None
        trades.append({
            "option_symbol": c["option_symbol"], "contract_id": key,
            "entry": entry, "quantity": quantity, "current": current,
            "high": high, "low": low, "t1": t1, "t2": t2, "sl": sl,
            "outcome": outcome, "outcome_price": outcome_price,
            "pnl": pnl,
            "quote_time": str(quote.get("timestamp", "unavailable")),
            "telegram_delivery": batch.get("telegram_delivery", {}).get(key, "unknown"),
        })
    available = [t for t in trades if t["pnl"] is not None]
    return {"batch_id": batch["batch_id"], "scan_date": batch["scan_date"],
            "source_log": str(path), "audit_time": at.isoformat(), "trades": trades,
            "total_trades": len(trades), "priced_trades": len(available),
            "total_pnl": sum(t["pnl"] for t in available) if available else None}


def format_report(report):
    esc = lambda value: html.escape(str(value))
    lines = ["⚡ <b>BTST NEXT-DAY PERFORMANCE SUMMARY — 11 AM AUDIT</b>",
             f"📅 <b>Scan Date:</b> <code>{esc(report['scan_date'])}</code>",
             f"🕒 <b>Audit Time:</b> <code>{esc(report['audit_time'][:16].replace('T', ' '))} IST</code>",
             f"📦 <b>Batch ID:</b> <code>{esc(report['batch_id'])}</code>",
             f"🎯 <b>Contracts Monitored:</b> <b>{report['total_trades']} Selected</b>",
             "──────────────────────"]
    for i, trade in enumerate(report["trades"], 1):
        current = "N/A" if trade["current"] is None else f"₹{trade['current']:.2f}"
        pnl = "N/A" if trade["pnl"] is None else f"₹{trade['pnl']:+,.2f}"
        icon = "🟢" if "TARGET" in trade["outcome"] or (trade["pnl"] and trade["pnl"] > 0) else ("🔴" if "SL" in trade["outcome"] or (trade["pnl"] and trade["pnl"] < 0) else "⚖️")
        lines.extend([
            f"\n{icon} <b>#{i} {esc(trade['option_symbol'])}</b>",
            f"├─ 📈 <b>Entry:</b> <code>₹{trade['entry']:.2f}</code> → <b>11 AM:</b> <code>{current}</code>",
            f"├─ 📊 <b>Range:</b> <code>Low ₹{trade['low']:.2f} — High ₹{trade['high']:.2f}</code>",
            f"├─ 🎯 <b>Status:</b> <b>{esc(trade['outcome'])}</b>",
            f"└─ 💵 <b>Signal MTM:</b> <b>{pnl}</b> (Size: {trade['quantity']} units)",
        ])
    priced, total = report['priced_trades'], report['total_trades']
    pnl = "N/A" if report['total_pnl'] is None else f"₹{report['total_pnl']:+,.2f}"
    lines.extend([
        "\n──────────────────────",
        f"📊 <b>Priced Contracts:</b> {priced}/{total}",
        f"💰 <b>Net Signal MTM:</b>   <b>{pnl}</b>",
        "──────────────────────",
        "<i>Evaluates opening session range (09:15-11:00 AM) against T1/T2/SL rules. "
        "Paper signal MTM shown before transaction costs and slippage.</i>"
    ])
    return "\n".join(lines)


def generate_and_send_11am_report(log_dir=None, scan_date=None, *, dry_run=False, offline=False):
    try:
        report = evaluate_btst_performance(log_dir, scan_date, offline=offline)
    except (OSError, ValueError, KeyError) as exc:
        print(f"BTST summary not sent: {exc}")
        return False
    text = format_report(report)
    print(text)
    if dry_run or offline:
        print("DRY RUN: Telegram suppressed.")
        return True
    return send_telegram_message(text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-dir", help="Shared BTST log directory (or BTST_LOG_DIR)")
    parser.add_argument("--scan-date", help="Explicit prior scan date YYYY-MM-DD (e.g. after holidays)")
    parser.add_argument("--dry-run", action="store_true", help="Print only; do not send Telegram")
    parser.add_argument("--offline", action="store_true", help="No broker or Telegram calls; prices N/A")
    args = parser.parse_args()
    ok = generate_and_send_11am_report(args.log_dir, args.scan_date, dry_run=args.dry_run, offline=args.offline)
    sys.exit(0 if ok else 2)
