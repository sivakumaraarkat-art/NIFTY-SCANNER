"""
options_alert_sender.py
Options Alert Formatter & Telegram Sender for Intraday and BTST options scans.
Optimized for mobile view: compact headers, 22-char dividers, no horizontal text overflow.
"""

import html
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

DIVIDER = "──────────────────────"


def _get_credentials():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if bot_token and chat_id:
        return bot_token, chat_id

    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent / ".credentials.json",
        script_dir.parent / ".env",
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


TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID = _get_credentials()


def _send_tg(text: str) -> bool:
    token, chat = _get_credentials()
    if not token or not chat:
        print("⚠️ Telegram keys not found, skipping alerts.")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=12)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"[TELEGRAM] Error delivering alert: {e}")
        return False


def send_options_telegram_alerts(candidates, strategy_name="INTRADAY OPTIONS"):
    """
    Sends clean, mobile-optimized HTML formatted Telegram alerts for Options Scanners.
    """
    if not candidates:
        return

    is_btst = "BTST" in strategy_name.upper()
    title = "🌙 <b>BTST OVERNIGHT SCAN</b>" if is_btst else "⚡ <b>INTRADAY OPTIONS SCAN</b>"
    scan_time = datetime.now().strftime("%I:%M %p")

    # Header message
    header = (
        f"{title}\n"
        f"{DIVIDER}\n"
        f"🔍 <b>Setups:</b> <code>{len(candidates)} Top Ranked</code>\n"
        f"🛡️ <b>Shield:</b> <code>4-Layer Dyn SL</code>\n"
        f"🕒 <b>Time:</b>   <code>{scan_time} IST</code>\n"
        f"{DIVIDER}\n"
        "<i>Top algorithmic setups by momentum & liquidity:</i>"
    )
    _send_tg(header)
    time.sleep(0.3)

    # Send up to top 3 to avoid spam
    for i, c in enumerate(candidates[:3], 1):
        opt_type = str(c.get("option_type", c.get("type", "CE"))).upper()
        is_call = opt_type == "CE"
        header_icon = "🟢" if is_call else "🔴"
        action_verb = "BUY"
        symbol_esc = html.escape(str(c.get("symbol", "N/A")))
        contract_symbol = html.escape(str(c.get("option_symbol", f"{symbol_esc} {c.get('strike', 0):.0f} {opt_type}")))
        strike = c.get("strike", 0.0)
        spot_price = float(c.get("spot_price", 0.0))
        ltp = float(c.get("ltp", 0.0))
        sl = float(c.get("powerful_sl", c.get("sl", 0.0)))
        t1 = float(c.get("t1", 0.0))
        t2 = float(c.get("t2", 0.0))
        score = c.get("score", 0)
        momentum = c.get("momentum_score", "N/A")
        lots = c.get("recommended_qty", 1)
        lot_size = c.get("lot_size", 0)
        capital = float(c.get("capital_needed", 0.0))
        delta = c.get("delta", "N/A")
        iv = c.get("iv", "N/A")

        sl_pts = abs(ltp - sl) if ltp and sl else 0.0
        t1_pts = abs(t1 - ltp) if ltp and t1 else 0.0
        t2_pts = abs(t2 - ltp) if ltp and t2 else 0.0

        card_lines = [
            f"{header_icon} <b>#{i} {action_verb} {contract_symbol}</b>",
            f"{DIVIDER}",
            f"⭐ <b>Score:</b> <b>{score}/100</b> • ⚡ <b>Delta:</b> <code>{delta}</code> • <b>IV:</b> <code>{iv}%</code>",
            "",
            "💰 <b>TRADE LEVELS</b>",
        ]
        if spot_price > 0:
            card_lines.append(f"├─ 📊 <b>Spot:</b>    <code>₹{spot_price:,.2f}</code> (ATM {strike:.0f})")
        card_lines.extend([
            f"├─ 🟢 <b>Entry:</b>   <code>₹{ltp:,.2f}</code>",
            f"├─ 🛑 <b>SL:</b>      <code>₹{sl:,.2f}</code> (<b>-{sl_pts:.2f} pts</b>)",
            f"├─ 🥇 <b>T1:</b>      <code>₹{t1:,.2f}</code> (<b>+{t1_pts:.2f} pts</b>)",
            f"└─ 🥈 <b>T2:</b>      <code>₹{t2:,.2f}</code> (<b>+{t2_pts:.2f} pts</b>)",
            "",
            "📦 <b>POSITION SIZING</b>",
            f"├─ 🏷️ <b>Lots:</b>    <code>{lots} lots</code> ({lot_size} / lot)",
        ])
        if capital > 0:
            card_lines.append(f"└─ 💵 <b>Capital:</b> <code>₹{capital:,.0f}</code>")
        else:
            card_lines[-1] = f"└─ 🏷️ <b>Lots:</b> <code>{lots} lots</code> ({lot_size} / lot)"

        if is_btst:
            card_lines.extend([
                f"{DIVIDER}",
                "🌅 <b>BTST PLAN:</b> <i>Exit 9:15–9:20 AM next morning via Smart Exit Guide.</i>",
            ])
        else:
            card_lines.extend([
                f"{DIVIDER}",
                "⚡ <b>INTRADAY PLAN:</b> <i>Book 50% @ T1 & trail SL to breakeven for T2.</i>",
            ])

        _send_tg("\n".join(card_lines))
        time.sleep(0.3)


def send_btst_exit_telegram_alert(exit_recommendation: dict):
    """
    Sends a dedicated 9:15 AM BTST Exit Decision alert with compact formatting.
    """
    market_cond = str(exit_recommendation.get("market_condition", "flat")).lower()
    gap_pct = float(exit_recommendation.get("gap_pct", 0.0))
    entry = float(exit_recommendation.get("entry_price", 0.0))
    current = float(exit_recommendation.get("current_price", 0.0))
    sl = float(exit_recommendation.get("powerful_sl", 0.0))
    recom = exit_recommendation.get("final_recommendation", "Review position")
    symbol = exit_recommendation.get("symbol", "NIFTY/STOCK")

    if "up" in market_cond or gap_pct > 0.5:
        gap_emoji = "GAP UP 🚀"
        icon_hdr = "🟢"
    elif "down" in market_cond or gap_pct < -0.5:
        gap_emoji = "GAP DOWN ⚠️"
        icon_hdr = "🔴"
    else:
        gap_emoji = "FLAT ⚖️"
        icon_hdr = "🟡"

    pnl_pts = current - entry
    pnl_pct = (pnl_pts / entry * 100.0) if entry else 0.0
    pnl_sign = "+" if pnl_pts >= 0 else ""
    pnl_icon = "🟢" if pnl_pts >= 0 else "🔴"

    lines = [
        f"{icon_hdr} <b>BTST SMART EXIT (09:15 AM)</b>",
        f"{DIVIDER}",
        f"🏷️ <b>Symbol:</b> <code>{html.escape(str(symbol))}</code>",
        f"📈 <b>Market:</b> <b>{gap_pct:+.1f}%</b> ({gap_emoji})",
        "",
        "💰 <b>POSITION AUDIT</b>",
        f"├─ 🟢 <b>Entry:</b>   <code>₹{entry:,.2f}</code>",
        f"├─ ⚡ <b>Open:</b>    <code>₹{current:,.2f}</code>",
        f"├─ 📈 <b>P&L:</b>     {pnl_icon} <b>{pnl_sign}{pnl_pts:.2f} ({pnl_pct:+.1f}%)</b>",
        f"└─ 🛑 <b>SL:</b>      <code>₹{sl:,.2f}</code>",
        "",
        "🎯 <b>RECOMMENDATION:</b>",
        f"<b>{html.escape(str(recom))}</b>",
    ]

    rolling = exit_recommendation.get("rolling_available")
    if rolling and rolling.get("strategy") == "ROLL":
        lines.extend([
            "",
            "🔄 <b>ROLLING RECOVERY:</b>",
            f"├─ Sell current at <code>₹{current:,.2f}</code>.",
            f"└─ Buy D+1 @ <code>₹{rolling.get('day_2_entry', 0):,.2f}</code> (Basis: <code>₹{rolling.get('cost_basis_reduced', 0):,.2f}</code>).",
        ])

    lines.extend([
        f"{DIVIDER}",
        "✅ <i>Execution ready. Manage risk per plan.</i>",
    ])

    _send_tg("\n".join(lines))
