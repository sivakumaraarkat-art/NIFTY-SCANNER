"""4 PM intraday options summary from monitor event state and scan logs."""
from __future__ import annotations

import html
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv()
IST = ZoneInfo("Asia/Kolkata")
DIVIDER = "──────────────────────"
LOG_DIR = Path(os.getenv("INTRADAY_LOG_DIR", "logs"))
STATE_FILE = LOG_DIR / "intraday_trade_state.json"


def send_telegram_message(message: str) -> bool:
    token, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("Telegram credentials missing; report printed locally only.")
        return False
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=15,
        )
        response.raise_for_status()
        return True
    except Exception as exc:
        print(f"Telegram delivery error: {exc}")
        return False


def load_trades() -> tuple[list[dict[str, Any]], int]:
    if not STATE_FILE.exists():
        return [], 0
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read monitor state {STATE_FILE}: {exc}") from exc
    today = datetime.now(IST).strftime("%Y%m%d")
    trades = [t for t in state.get("trades", {}).values() if t.get("trade_date") == today]
    return trades, len(list(LOG_DIR.glob(f"intraday_scan_powerful_sl_{today}_*.json")))


def format_time(value: str | None) -> str:
    if not value:
        return "not observed"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=IST)
        return dt.astimezone(IST).strftime("%H:%M:%S IST")
    except ValueError:
        return value


def render_report() -> str | None:
    trades, scan_count = load_trades()
    if not trades:
        return None

    total_trades = len(trades)
    wins = [t for t in trades if t.get("close_reason") in {"T1_HIT", "T2_HIT"}]
    losses = [t for t in trades if t.get("close_reason") == "SL_HIT"]
    win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0.0
    net_pnl = sum(float(t.get("pnl", 0) or 0) for t in trades)
    total_capital = sum(float(t.get("capital", 0) or 0) for t in trades)

    lines = [
        "⚡ <b>DAILY INTRADAY OPTIONS SUMMARY (4:00 PM)</b>", DIVIDER,
        f"📅 <b>Date:</b>          <code>{datetime.now(IST).strftime('%d-%b-%Y')}</code>",
        f"🔄 <b>Scans Executed:</b> <code>{scan_count} (1-Hour Interval)</code>",
        f"🔍 <b>Unique Signals:</b> <code>{total_trades} Setups (Deduplicated)</code>",
        f"🎯 <b>Win Rate:</b>      <b>{win_rate:.1f}%</b> ({len(wins)}W / {len(losses)}L)", DIVIDER,
        "💰 <b>TRADE-BY-TRADE P&L BREAKDOWN</b>",
    ]

    for i, trade in enumerate(sorted(trades, key=lambda t: t.get("signal_time", "")), 1):
        symbol = html.escape(str(trade.get("option_symbol", "unknown")))
        entry = float(trade.get("entry_price", 0) or 0)
        reason = trade.get("close_reason", "OPEN")
        close_price = float(trade.get("close_price", 0) or 0)
        pnl = float(trade.get("pnl", 0) or 0)
        pnl_pct = float(trade.get("pnl_pct", 0) or 0)
        target_reached_time = format_time(trade.get("target_reached_time") or trade.get("close_time"))

        if reason == "T2_HIT":
            status_str = f"<b>TARGET 2 HIT 🔥</b> (at {target_reached_time})"
            display_price = f"Target (₹{trade.get('t2', 0):.2f})"
        elif reason == "T1_HIT":
            status_str = f"<b>TARGET 1 HIT 🎯</b> (at {target_reached_time})"
            display_price = f"Target (₹{trade.get('t1', 0):.2f})"
        elif reason == "SL_HIT":
            status_str = f"<b>SL HIT 🛑</b> (at {target_reached_time})"
            display_price = f"SL (₹{trade.get('stop_loss', 0):.2f})"
        else:
            status_str = f"<b>{reason}</b>"
            display_price = f"Live (₹{close_price:.2f})"

        pnl_str = f"+₹{pnl:,.2f}" if pnl >= 0 else f"-₹{abs(pnl):,.2f}"
        pct_str = f"+{pnl_pct:.1f}%" if pnl_pct >= 0 else f"{pnl_pct:.1f}%"

        lines.extend([
            f"\n🟢 <b>#{i} {symbol}</b>",
            f"├─ 📈 <b>Entry:</b> <code>₹{entry:.2f}</code> → <b>Exit:</b> <code>{display_price}</code>",
            f"├─ 🎯 <b>Status:</b> {status_str}",
            f"└─ 💵 <b>P&L:</b>    <b>{pnl_str}</b> (<b>{pct_str}</b>)",
        ])

    net_pnl_str = f"+₹{net_pnl:,.2f}" if net_pnl >= 0 else f"-₹{abs(net_pnl):,.2f}"
    net_pct = (net_pnl / total_capital * 100) if total_capital > 0 else 0.0

    lines.extend([
        DIVIDER,
        f"💼 <b>TOTAL CAPITAL:</b> <code>₹{total_capital:,.0f}</code>",
        f"💰 <b>NET P&L TODAY:</b>  <b>{net_pnl_str}</b> (<b>+{net_pct:.1f}%</b>)",
        DIVIDER,
        "<i>Summary excludes duplicate scans of the same contract. All evaluations strictly use post-signal price action.</i>"
    ])
    return "\n".join(lines)


def main() -> None:
    report = render_report()
    if not report:
        print("No intraday monitor records found for today. Ensure the monitor ran during market hours.")
        return
    print(report)
    send_telegram_message(report)


if __name__ == "__main__":
    main()
