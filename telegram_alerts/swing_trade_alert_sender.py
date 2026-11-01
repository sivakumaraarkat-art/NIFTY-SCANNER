"""
Swing Trade Alert Sender
Formats and sends swing trade alerts via Telegram.
Optimized for mobile: compact single-line headers, 22-char dividers, clean tree formatting.
Includes MCX Crude Oil futures & options support.
"""

import html
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
import requests

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
if str(ROOT / "institutional_data") not in sys.path:
    sys.path.insert(0, str(ROOT / "institutional_data"))
if str(ROOT / "news_analysis") not in sys.path:
    sys.path.insert(0, str(ROOT / "news_analysis"))

try:
    from fii_dii_data_fetcher import (
        fetch_daily_fii_dii_summary,
        format_institutional_flow_header,
        get_institutional_indicator,
    )
except ImportError:
    def get_institutional_indicator(candidate):
        return ""

    def fetch_daily_fii_dii_summary():
        return None

    def format_institutional_flow_header(fii_dii):
        return ""


DIVIDER = "──────────────────────"

FRIENDLY_REASONS = {
    "uptrend: price > SMA20 > SMA50": "📈 Strong Uptrend (Above 20/50 SMA)",
    "healthy RSI (50-70 range)": "⚡ Healthy Momentum (RSI 50-70)",
    "volume surge (1.5x+ average)": "🔥 Volume Surge (1.5x+ avg volume)",
    "positive momentum (3%+ in 20d)": "🚀 Strong Momentum (+3% in 20d)",
    "near 20-day high breakout": "⭐ Near 1-Month High Breakout",
    "breakout: price at 20-day high": "🚀 20-Day High Breakout",
    "volume surge: 2x average": "🔥 Huge Volume Surge (2x normal)",
    "trend support: above MAs": "📈 Above Moving Averages",
    "momentum: 5%+ gain in 20 days": "💪 Price Momentum (+5% in 20d)",
    "strong uptrend: price > SMA50, SMA50 rising": "📈 50-Day Trend Rising",
    "pullback to SMA20 support": "🛒 Dip Buying @ 20 SMA Support",
    "near SMA20 support": "🛒 Near Support Level",
    "volume expansion on bounce": "🔥 Volume Rising on Bounce",
    "bullish price action": "🟢 Bullish Price Action",
    "crude oil momentum breakout": "🛢️ Crude Oil Trend Continuation",
}


def _make_friendly_reason(raw_reason: str) -> str:
    if raw_reason in FRIENDLY_REASONS:
        return FRIENDLY_REASONS[raw_reason]
    if "RSI bounce" in raw_reason or "oversold recovery" in raw_reason:
        return "🔄 Oversold Dip Recovery"
    if "consolidation" in raw_reason or "tight ATR" in raw_reason:
        return "📦 Tight Range Consolidation"
    return f"• {raw_reason}"


def _post_telegram_message(bot_token: str, chat_id: str, text: str) -> bool:
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        r.raise_for_status()
        return True
    except Exception:
        clean = (
            text.replace("<b>", "")
            .replace("</b>", "")
            .replace("<i>", "")
            .replace("</i>", "")
            .replace("<code>", "")
            .replace("</code>", "")
        )
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": clean, "disable_web_page_preview": True},
                timeout=15,
            )
            return r.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram plain text message: {e}")
            return False


def resolve_telegram_credentials(settings=None) -> tuple[str, str]:
    """
    Resolve Telegram credentials, prioritizing the dedicated Portfolio Telegram Bot.
    """
    # 1. Check Portfolio Telegram Bot environment / settings first
    port_token = os.getenv("PORTFOLIO_TELEGRAM_BOT_TOKEN", "").strip()
    port_chat = os.getenv("PORTFOLIO_TELEGRAM_CHAT_ID", "").strip()

    if settings:
        if not port_token:
            port_token = getattr(settings, "portfolio_telegram_bot_token", "").strip()
        if not port_chat:
            port_chat = getattr(settings, "portfolio_telegram_chat_id", "").strip()

    if port_token and port_chat:
        return port_token, port_chat

    # 2. Fall back to standard swing bot credentials
    std_token = getattr(settings, "telegram_bot_token", "").strip() if settings else os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    std_chat = getattr(settings, "telegram_chat_id", "").strip() if settings else os.getenv("TELEGRAM_CHAT_ID", "").strip()

    return std_token, std_chat


def send_swing_alerts(candidates: list[dict], settings) -> None:
    if not candidates:
        print("No candidates to alert.")
        return

    bot_token, chat_id = resolve_telegram_credentials(settings)

    fii_dii = fetch_daily_fii_dii_summary()
    fii_dii_text = format_institutional_flow_header(fii_dii)

    formatted_candidates = []
    for c in candidates:
        cand = dict(c)
        cand["friendly_reasons"] = [
            _make_friendly_reason(r) for r in c.get("reasons", [])
        ]
        formatted_candidates.append(cand)

    if not bot_token or not chat_id:
        print("\n" + "=" * 70)
        print("TELEGRAM ALERTS (Console Preview - No Bot Token Configured)")
        print("=" * 70)
        if fii_dii:
            print(
                f"FII/DII Flow: DII Net: ₹{fii_dii.get('dii_net',0):,.2f} Cr | FII Net: ₹{fii_dii.get('fii_net',0):,.2f} Cr"
            )
        for i, c in enumerate(formatted_candidates[:5], 1):
            print(f"\n[TRADE #{i}: {c['symbol']}]")
            print(f"Strategy: {c['setup']} | Score: {c['score']}/100")
            print(f"BUY: ₹{c['entry']:.2f} | STOP: ₹{c['stop_loss']:.2f}")
            print(f"TARGETS: T1: ₹{c['target_1']:.2f} | T2: ₹{c['target_2']:.2f} | T3: ₹{c['target_3']:.2f}")
        print("=" * 70)
        return

    if not settings.signal_only:
        raise RuntimeError("Safety stop: SIGNAL_ONLY must remain true.")

    # 1. Send Header Message
    header_lines = [
        "🎯 <b>STOCK SWING V1 & CRUDE SIGNALS</b>",
        f"{DIVIDER}",
        f"💰 <b>Capital:</b> <code>₹{settings.initial_capital:,.0f}</code> (Risk {settings.risk_per_trade * 100:.1f}%)",
        f"📅 <b>Scan:</b>    <code>{datetime.now().strftime('%d-%b-%Y %I:%M %p')}</code>",
        f"🔍 <b>Setups:</b>  <code>{len(formatted_candidates[:5])} Top Ranked</code>",
        f"{DIVIDER}",
    ]
    if fii_dii_text:
        header_lines.append(fii_dii_text.strip())
        header_lines.append(f"{DIVIDER}")

    _post_telegram_message(
        bot_token, chat_id, "\n".join(header_lines)
    )
    time.sleep(0.3)

    # 2. Send Individual Trade Cards
    for i, c in enumerate(formatted_candidates[:5], 1):
        risk_pct = ((c["entry"] - c["stop_loss"]) / c["entry"]) * 100
        t1_pct = ((c["target_1"] - c["entry"]) / c["entry"]) * 100
        t2_pct = ((c["target_2"] - c["entry"]) / c["entry"]) * 100
        t3_pct = ((c["target_3"] - c["entry"]) / c["entry"]) * 100

        sym_esc = html.escape(str(c["symbol"]))
        setup_esc = html.escape(str(c["setup"]))
        cap_seg = html.escape(str(c.get("cap_segment", "COMMODITY" if "CRUDE" in sym_esc.upper() else "UNKNOWN")))

        is_crude = "CRUDE" in sym_esc.upper()
        icon = "🛢️ 🟢" if is_crude else f"🟢"

        conviction_label = "🔥 HIGH CONVICTION" if c.get("score", 0) >= 85 else "🟢 SOLID CONVICTION"

        card_lines = [
            f"{icon} <b>#{i} BUY {sym_esc}</b>",
            f"{DIVIDER}",
            f"🏷️ <b>Setup:</b>      <code>{setup_esc}</code>",
            f"⭐ <b>Conviction:</b> <b>{conviction_label}</b> ({c['score']}/100)",
            f"🏢 <b>Segment:</b>    <code>{cap_seg}</code>",
            "",
            "💰 <b>TARGETS BY TIMEFRAME</b>",
            f"├─ 🟢 <b>Buy Entry:</b>             <code>₹{c['entry']:,.2f}</code>",
            f"├─ 🛑 <b>Stop Loss:</b>              <code>₹{c['stop_loss']:,.2f}</code> (<b>-{risk_pct:.1f}%</b>)",
            f"├─ 🥇 <b>1-Week Target (5d):</b>    <code>₹{c['target_1']:,.2f}</code> (<b>+{t1_pct:.1f}%</b>)",
            f"├─ 🥈 <b>10-Day Target (10d):</b>   <code>₹{c['target_2']:,.2f}</code> (<b>+{t2_pct:.1f}%</b>)",
            f"└─ 🥉 <b>1-Month Target (20d):</b>  <code>₹{c['target_3']:,.2f}</code> (<b>+{t3_pct:.1f}%</b>)",
            "",
            "⏱️ <b>Strategy:</b> <code>Book 50% at 1-Week Target, hold balance for 10-Day/1-Month target</code>",
        ]

        # Institutional Flow
        inst_indicator = get_institutional_indicator(c)
        if inst_indicator:
            inst_esc = html.escape(inst_indicator)
            card_lines.append(f"🏛️ <b>FII/DII:</b> {inst_esc}")

        # Predictive News & Catalyst Section
        predictive_outlook = c.get("predictive_outlook")
        if predictive_outlook:
            pred_esc = html.escape(str(predictive_outlook))
            card_lines.append(f"🔮 <b>Predictive Outlook:</b> <code>{pred_esc}</code>")

        news_badge = c.get("news_badge")
        news_headlines = c.get("news_headlines_with_dates", c.get("news_headlines", []))
        news_red_flags = c.get("news_red_flags", [])

        if news_badge:
            badge_esc = html.escape(str(news_badge))
            card_lines.append(f"📰 <b>News:</b> {badge_esc}")
            if news_red_flags:
                for rf in news_red_flags[:1]:
                    card_lines.append(f"⚠️ <i>{html.escape(str(rf))}</i>")

        if news_headlines:
            card_lines.append("")
            card_lines.append("📰 <b>NEWS CATALYSTS:</b>")
            for nh in news_headlines[:2]:
                if isinstance(nh, dict):
                    h_text = nh.get("headline", str(nh))
                    h_date = nh.get("date", "")
                    h_str = f"[{h_date}] {h_text}" if h_date else h_text
                else:
                    h_str = str(nh)
                if len(h_str) > 75:
                    h_str = h_str[:72] + "..."
                card_lines.append(f"• <i>{html.escape(h_str)}</i>")

        # Friendly Reasons
        reasons = c.get("friendly_reasons", [])
        if reasons:
            card_lines.append("")
            card_lines.append("🎯 <b>WHY THIS TRADE:</b>")
            for r in reasons[:3]:
                card_lines.append(f"  {html.escape(str(r))}")

        card_lines.append(DIVIDER)
        card_lines.append("✅ <i>Managed by Stock Swing V1 Engine.</i>")

        _post_telegram_message(
            bot_token, chat_id, "\n".join(card_lines)
        )
        time.sleep(0.3)


def send_swing_exit_alert(closed_trade: dict, settings=None) -> bool:
    """
    Format and send a structured Telegram SELL / Exit alert with exact % return.
    """
    bot_token, chat_id = resolve_telegram_credentials(settings)

    sym = html.escape(str(closed_trade.get("symbol", "")))
    setup = html.escape(str(closed_trade.get("setup", "10-DAY SWING")))
    entry = float(closed_trade.get("entry_price", 0.0))
    exit_p = float(closed_trade.get("exit_price", 0.0))
    ret_pct = float(closed_trade.get("return_pct", 0.0))
    pnl_amt = float(closed_trade.get("pnl_amount", 0.0))
    qty = int(closed_trade.get("quantity", 1))
    days = int(closed_trade.get("holding_days", 0))
    reason = html.escape(str(closed_trade.get("exit_reason", "EXIT")))
    entry_d = closed_trade.get("entry_date", "")
    exit_d = closed_trade.get("exit_date", "")

    ret_icon = "🟢" if ret_pct >= 0 else "🛑"
    pnl_sign = "+" if pnl_amt >= 0 else ""

    lines = [
        "🔔 <b>SWING TRADE EXIT / SELL ALERT</b>",
        f"{DIVIDER}",
        f"🏷️ <b>Stock:</b>    <code>{sym}</code>",
        f"📋 <b>Setup:</b>    <code>{setup}</code>",
        f"⏱️ <b>Holding:</b>  <code>{days} Days ({entry_d} ➔ {exit_d})</code>",
        "",
        "📊 <b>EXIT & RETURN BREAKDOWN</b>",
        f"├─ 🟢 <b>Buy Entry:</b>    <code>₹{entry:,.2f}</code>",
        f"├─ 🔴 <b>Sell Exit:</b>    <code>₹{exit_p:,.2f}</code>",
        f"├─ 🎯 <b>Exit Reason:</b>  <b>{reason}</b>",
        f"└─ {ret_icon} <b>Net Return:</b>   <b>{ret_pct:+.2f}% {ret_icon}</b>",
        "",
        f"💵 <b>Realized P&L:</b> <code>{pnl_sign}₹{pnl_amt:,.2f}</code> (Qty: {qty})",
        f"{DIVIDER}",
        "✅ <i>Managed by Stock Swing V1 Engine.</i>",
    ]

    message_text = "\n".join(lines)
    if not bot_token or not chat_id:
        print("\n" + "=" * 60)
        print("TELEGRAM SWING EXIT ALERT (Console Preview)")
        print("=" * 60)
        print(f"Stock: {sym} | Reason: {reason} | Exit: ₹{exit_p:,.2f} | Return: {ret_pct:+.2f}%")
        print("=" * 60)
        return False

    return _post_telegram_message(bot_token, chat_id, message_text)


def send_swing_audit_alert(summary: dict, settings=None) -> bool:
    """
    Format and send weekly swing trade audit summary to Telegram.
    """
    bot_token, chat_id = resolve_telegram_credentials(settings)

    total_closed = summary.get("total_closed", 0)
    wins = summary.get("wins", 0)
    losses = summary.get("losses", 0)
    win_rate = summary.get("win_rate", 0.0)
    net_return_pct = summary.get("net_return_pct", 0.0)
    net_pnl = summary.get("net_pnl", 0.0)
    avg_return = summary.get("avg_return", 0.0)
    avg_holding_days = summary.get("avg_holding_days", 0.0)
    period = summary.get("period", datetime.now().strftime("%d-%b-%Y"))

    sign = "+" if net_return_pct >= 0 else ""
    icon = "🚀 🟢" if net_return_pct >= 0 else "🛑"

    lines = [
        "📊 <b>SWING TRADE PERFORMANCE AUDIT</b>",
        f"{DIVIDER}",
        f"📅 <b>Audit Period:</b> <code>{period}</code>",
        f"🔍 <b>Strategy:</b>     <code>7–10 Days Swing Trading</code>",
        f"{DIVIDER}",
        "📈 <b>SUMMARY METRICS</b>",
        f"├─ 🎯 <b>Closed Trades:</b> <code>{total_closed}</code>",
        f"├─ 🥇 <b>Wins:</b>          <code>{wins}</code> (Win Rate: <b>{win_rate:.1f}%</b>)",
        f"├─ 🛑 <b>Losses:</b>        <code>{losses}</code>",
        f"├─ ⏱️ <b>Avg Hold:</b>      <code>{avg_holding_days:.1f} Trading Days</code>",
        f"├─ 📊 <b>Avg Return:</b>    <code>{avg_return:+.2f}% per trade</code>",
        f"└─ {icon} <b>Total Return:</b>  <b>{sign}{net_return_pct:.2f}%</b>",
        "",
        f"💰 <b>Total Realized P&L:</b> <code>{sign}₹{net_pnl:,.2f}</code>",
    ]

    closed_trades = summary.get("trades", [])
    if closed_trades:
        lines.append("")
        lines.append("📋 <b>RECENT CLOSED TRADES:</b>")
        for t in closed_trades[:8]:
            sym = t.get("symbol", "")
            r_pct = t.get("return_pct", 0.0)
            r_icon = "🟢" if r_pct >= 0 else "🛑"
            h_days = t.get("holding_days", 0)
            reason = t.get("exit_reason", "")
            lines.append(f"• <b>{sym}</b>: {r_icon} <b>{r_pct:+.2f}%</b> ({h_days}d - {reason})")

    lines.append(f"{DIVIDER}")
    lines.append("✅ <i>Managed by Stock Swing V1 Engine.</i>")

    message_text = "\n".join(lines)
    if not bot_token or not chat_id:
        print("\n" + "=" * 60)
        print("TELEGRAM SWING AUDIT SUMMARY (Console Preview)")
        print("=" * 60)
        print(f"Total Closed: {total_closed} | Win Rate: {win_rate:.1f}% | Total Return: {net_return_pct:+.2f}%")
        print("=" * 60)
        return False

    return _post_telegram_message(bot_token, chat_id, message_text)

