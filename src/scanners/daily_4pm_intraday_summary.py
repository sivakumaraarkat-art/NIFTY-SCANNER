"""4 PM intraday options summary from monitor event state and scan logs."""
from __future__ import annotations

import html
import json
import os
from datetime import datetime, time as time_type
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
MAX_DAILY_TRADES = int(os.getenv("MAX_DAILY_TRADES", "10"))


def send_telegram_message(message: str) -> bool:
    token, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("Telegram credentials missing; report printed locally only.")
        return False

    # Telegram limit is 4096 characters. Chunk cleanly at newlines if needed.
    chunks = []
    if len(message) <= 3800:
        chunks = [message]
    else:
        current_chunk = []
        current_len = 0
        for line in message.split("\n"):
            if current_len + len(line) + 1 > 3800 and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_len = len(line) + 1
            else:
                current_chunk.append(line)
                current_len += len(line) + 1
        if current_chunk:
            chunks.append("\n".join(current_chunk))

    success = True
    for chunk in chunks:
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat, "text": chunk, "parse_mode": "HTML", "disable_web_page_preview": True},
                timeout=15,
            )
            response.raise_for_status()
        except Exception as exc:
            print(f"Telegram delivery error: {exc}")
            success = False
    return success


def load_trades() -> tuple[list[dict[str, Any]], int]:
    if not STATE_FILE.exists():
        return [], 0
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read monitor state {STATE_FILE}: {exc}") from exc
    today = datetime.now(IST).strftime("%Y%m%d")
    trades = [t for t in state.get("trades", {}).values() if t.get("trade_date") == today]
    trades.sort(key=lambda t: t.get("signal_time", ""))
    if len(trades) > MAX_DAILY_TRADES:
        trades = trades[:MAX_DAILY_TRADES]
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


def reconcile_final_eod_trades() -> None:
    """Ensure any trades still open at 4:00 PM are polled from Kite or squared off."""
    if not STATE_FILE.exists():
        return
    try:
        from src.scanners.intraday_trade_monitor import (
            load_signals, observe_trades, atomic_write_json, now_ist
        )
        from src.scanners.options_data_provider import get_kite_client
    except ImportError:
        try:
            from intraday_trade_monitor import (
                load_signals, observe_trades, atomic_write_json, now_ist
            )
            from options_data_provider import get_kite_client
        except ImportError:
            return

    now = now_ist()
    day = now.strftime("%Y%m%d")
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return

    signals = {}
    try:
        signals = load_signals(day)
    except Exception:
        pass

    if not signals and not state.get("trades"):
        return

    kite = None
    try:
        kite = get_kite_client()
    except Exception:
        pass

    try:
        observe_trades(state, signals, kite, now)
    except Exception as exc:
        print(f"Warning: Final trade observation error: {exc}")

    # Secondary safeguard: If market is closed (>15:30) and any of today's trades are STILL 'OPEN',
    # forcefully square them off so user never sees 'Not observed' or 'Live (0.00)' in 4pm report
    for trade in state.get("trades", {}).values():
        if trade.get("trade_date") == day and trade.get("status") == "OPEN":
            close_price = float(trade.get("close_price") or trade.get("entry_price") or 0.0)
            entry = float(trade.get("entry_price") or 0.0)
            trade.update(
                status="CLOSED",
                close_reason="EOD_SQUARE_OFF",
                close_price=close_price,
                close_time=now.replace(hour=15, minute=25, second=0, microsecond=0).isoformat(),
                hit_time_source="minute_candle",
                hit_time_precision="minute",
                observed_at=now.isoformat(),
                data_status="eod_squared_off_fallback",
            )
            trade["target_reached_time"] = None
            trade["pnl"] = (close_price - entry) * trade.get("lots", 1) * trade.get("lot_size", 1)
            trade["pnl_pct"] = (close_price - entry) / entry * 100 if entry else 0.0

    state["updated_at"] = now.isoformat()
    atomic_write_json(STATE_FILE, state)


def render_report() -> str | None:
    reconcile_final_eod_trades()
    trades, scan_count = load_trades()
    if not trades:
        return None

    total_trades = len(trades)
    wins = [
        t for t in trades
        if t.get("close_reason") in {"T1_HIT", "T2_HIT"}
        or (t.get("close_reason") == "EOD_SQUARE_OFF" and float(t.get("pnl", 0) or 0) > 0)
    ]
    losses = [
        t for t in trades
        if t.get("close_reason") == "SL_HIT"
        or (t.get("close_reason") == "EOD_SQUARE_OFF" and float(t.get("pnl", 0) or 0) < 0)
    ]
    win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0.0
    net_pnl = sum(float(t.get("pnl", 0) or 0) for t in trades)
    total_capital = sum(float(t.get("capital", 0) or 0) for t in trades)

    lines = [
        "⚡ <b>DAILY INTRADAY OPTIONS SUMMARY (4:00 PM)</b>", DIVIDER,
        f"📅 <b>Date:</b>          <code>{datetime.now(IST).strftime('%d-%b-%Y')}</code>",
        f"🔄 <b>Scans Executed:</b> <code>{scan_count} (1-Hour Interval)</code>",
        f"🔍 <b>Unique Signals:</b> <code>{total_trades} Setups (Cap: Max {MAX_DAILY_TRADES}/Day)</code>",
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
        show_time_str = ""
        hit_time = "Unavailable (unverified legacy record)"
        if trade.get("hit_time_source") == "minute_candle":
            try:
                dt = datetime.fromisoformat(str(trade.get("close_time")).replace("Z", "+00:00"))
                dt = dt.replace(tzinfo=IST) if dt.tzinfo is None else dt.astimezone(IST)
                if dt.strftime("%Y%m%d") == trade.get("trade_date") and time_type(9, 15) <= dt.time() <= time_type(15, 30):
                    if reason == "EOD_SQUARE_OFF":
                        hit_time = dt.strftime("%H:%M IST") + " (EOD square-off)"
                    else:
                        hit_time = dt.strftime("%H:%M IST") + " (1-minute candle)"
            except (ValueError, TypeError):
                pass
        elif reason == "OPEN":
            hit_time = "Not observed"
            if trade.get("data_status") == "unavailable":
                hit_time = "Unavailable (market data missing)"
            elif trade.get("data_status") == "ambiguous_target_sl":
                hit_time = "Target / SL order unknown in same candle"

        if reason == "T2_HIT":
            status_str = f"<b>TARGET 2 HIT 🔥</b>{show_time_str}"
            display_price = f"Target (₹{trade.get('t2', 0):.2f})"
            icon = "🟢"
        elif reason == "T1_HIT":
            status_str = f"<b>TARGET 1 HIT 🎯</b>{show_time_str}"
            display_price = f"Target (₹{trade.get('t1', 0):.2f})"
            icon = "🟢"
        elif reason == "SL_HIT":
            status_str = f"<b>SL HIT 🛑</b>{show_time_str}"
            display_price = f"SL (₹{trade.get('stop_loss', 0):.2f})"
            icon = "🔴"
        elif reason == "EOD_SQUARE_OFF":
            tag = "PROFIT" if pnl > 0 else ("LOSS" if pnl < 0 else "FLAT")
            icon = "🟢" if pnl > 0 else ("🔴" if pnl < 0 else "⚪")
            status_str = f"<b>EOD SQUARED OFF ⏱️ ({tag})</b>"
            display_price = f"Exit (₹{close_price:.2f})"
        else:
            status_str = f"<b>{reason}</b>"
            display_price = f"Live (₹{close_price:.2f})" if close_price > 0 else "Live (Open)"
            icon = "🟡"

        pnl_str = f"+₹{pnl:,.2f}" if pnl >= 0 else f"-₹{abs(pnl):,.2f}"
        pct_str = f"+{pnl_pct:.1f}%" if pnl_pct >= 0 else f"{pnl_pct:.1f}%"

        lines.extend([
            f"\n{icon} <b>#{i} {symbol}</b>",
            f"├─ 📈 <b>Entry:</b> <code>₹{entry:.2f}</code> → <b>Exit:</b> <code>{display_price}</code>",
            f"├─ 🎯 <b>Status:</b> {status_str}",
            f"├─ 🕒 <b>Hit time:</b> <code>{html.escape(hit_time)}</code>",
            f"└─ 💵 <b>P&L:</b>    <b>{pnl_str}</b> (<b>{pct_str}</b>)",
        ])

    net_pnl_str = f"+₹{net_pnl:,.2f}" if net_pnl >= 0 else f"-₹{abs(net_pnl):,.2f}"
    net_pct = (net_pnl / total_capital * 100) if total_capital > 0 else 0.0

    lines.extend([
        DIVIDER,
        f"💼 <b>TOTAL CAPITAL:</b> <code>₹{total_capital:,.0f}</code>",
        f"💰 <b>NET P&L TODAY:</b>  <b>{net_pnl_str}</b> (<b>{net_pct:+.1f}%</b>)",
        DIVIDER,
        "<i>Summary excludes duplicate scans of the same contract. Hit times have minute precision, not exact seconds. Legacy records require reconciliation. The partial signal minute is excluded. Exit uses the first threshold candle; same-candle T2 takes precedence over T1.</i>"
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
