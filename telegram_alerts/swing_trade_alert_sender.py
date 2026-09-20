"""
Swing Trade Alert Sender

Formats and sends swing trade alerts via Telegram:
- Header message with market context and FII/DII flow
- Individual beautiful HTML-formatted cards for each high-conviction trade setup
- Includes live news headlines & sentiment catalysts
- Converts technical indicators into plain, beginner-friendly English
- Displays Entry, Stop Loss, and Multi-Targets (T1, T2, T3)
- Shows FII/DII institutional volume surge indicators
- Shows recommended Position Size (Quantity) and Risk Amount
- Enforces strict SIGNAL_ONLY safety mode
"""

import html
import requests
import sys
import time
from pathlib import Path

# Add institutional_data and news_analysis to path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "institutional_data") not in sys.path:
    sys.path.insert(0, str(ROOT / "institutional_data"))
if str(ROOT / "news_analysis") not in sys.path:
    sys.path.insert(0, str(ROOT / "news_analysis"))

try:
    from fii_dii_data_fetcher import (
        get_institutional_indicator,
        fetch_daily_fii_dii_summary,
        format_institutional_flow_header,
    )
except ImportError:

    def get_institutional_indicator(candidate):
        return ""

    def fetch_daily_fii_dii_summary():
        return None

    def format_institutional_flow_header(fii_dii):
        return ""


# Plain English translations for technical reasons
FRIENDLY_REASONS = {
    "uptrend: price > SMA20 > SMA50": "📈 Strong Uptrend (Price above 20 & 50-day averages)",
    "healthy RSI (50-70 range)": "⚡ Healthy Momentum (Strong buying, not overheated)",
    "volume surge (1.5x+ average)": "🔥 Big Volume Surge (Institutional buying 1.5x+ avg)",
    "positive momentum (3%+ in 20d)": "🚀 Strong Monthly Growth (Up 3%+ in last 20 days)",
    "near 20-day high breakout": "⭐ Near 1-Month High (Potential breakout)",
    "breakout: price at 20-day high": "🚀 20-Day High Breakout (Breaking new highs)",
    "volume surge: 2x average": "🔥 Huge Volume Surge (2x normal trading activity)",
    "trend support: above MAs": "📈 Supported by Moving Averages (Bullish trend)",
    "momentum: 5%+ gain in 20 days": "💪 Strong Price Momentum (Up 5%+ in 20 days)",
    "strong uptrend: price > SMA50, SMA50 rising": "📈 Strong Uptrend (50-day average steadily rising)",
    "pullback to SMA20 support": "🛒 Dip Buying Opportunity (Pulled back to 20-day support)",
    "near SMA20 support": "🛒 Near Support Level (Good risk-reward entry)",
    "volume expansion on bounce": "🔥 Volume Rising on Bounce (Buyers stepping in)",
    "bullish price action": "🟢 Bullish Green Candle (Buyers taking control)",
}


def _make_friendly_reason(raw_reason: str) -> str:
    """Translate raw technical reason into plain English with emojis."""
    if raw_reason in FRIENDLY_REASONS:
        return FRIENDLY_REASONS[raw_reason]
    if "RSI bounce" in raw_reason or "oversold recovery" in raw_reason:
        return "🔄 Rebounding from Dip (Oversold bounce)"
    if "consolidation" in raw_reason or "tight ATR" in raw_reason:
        return "📦 Tight Range Consolidation (Coiling up for big move)"
    return f"• {raw_reason}"


def _post_telegram_message(bot_token: str, chat_id: str, text: str) -> bool:
    """Post an HTML message to Telegram with fallback to plain text."""
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=15,
        )
        r.raise_for_status()
        return True
    except Exception:
        # Fallback to plain text
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
                json={"chat_id": chat_id, "text": clean},
                timeout=15,
            )
            return r.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram plain text message: {e}")
            return False


def send_swing_alerts(candidates: list[dict], settings) -> None:
    """
    Format and send swing trade alerts to Telegram.

    Args:
        candidates: List of ranked candidate dicts (enriched with news)
        settings: Settings object
    """
    if not candidates:
        print("No candidates to alert.")
        return

    # Fetch daily FII/DII summary from NSE
    fii_dii = fetch_daily_fii_dii_summary()
    fii_dii_text = format_institutional_flow_header(fii_dii)

    # Prepare formatted plain-English candidates
    formatted_candidates = []
    for c in candidates:
        cand = dict(c)
        cand["friendly_reasons"] = [
            _make_friendly_reason(r) for r in c.get("reasons", [])
        ]
        formatted_candidates.append(cand)

    # Console preview if bot token is not configured
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        print("\n" + "=" * 70)
        print("TELEGRAM ALERTS (Console Preview - No Bot Token Configured)")
        print("=" * 70)
        if fii_dii:
            print(
                f"FII/DII Flow: DII Net: ₹{fii_dii.get('dii_net',0):,.2f} Cr | FII Net: ₹{fii_dii.get('fii_net',0):,.2f} Cr"
            )
        for i, c in enumerate(formatted_candidates[:5], 1):
            print(f"\n╭─── TRADE #{i}: {c['symbol']} ───╮")
            print(f"│ Strategy: {c['setup']} | Score: {c['score']}/100")
            print(f"│ NSE Cap Segment: {c.get('cap_segment', 'UNKNOWN')}")
            print(
                f"│ BUY: ₹{c['entry']:.2f} | STOP: ₹{c['stop_loss']:.2f} (-{((c['entry'] - c['stop_loss'])/c['entry'])*100:.1f}%)"
            )
            print(
                f"│ TARGETS: T1: ₹{c['target_1']:.2f} (50%) | T2: ₹{c['target_2']:.2f} (30%) | T3: ₹{c['target_3']:.2f} (20%)"
            )
            print(f"│ News Sentiment: {c.get('news_badge', 'Neutral')}")
            for h in c.get("news_headlines", []):
                print(f"│   📰 {h}")
            print(
                f"│ Position: {c.get('quantity', 0)} shares (₹{c.get('capital_required', 0):,.0f} cap, ₹{c.get('risk_amount', 0):,.0f} risk)"
            )
            print("│ Technical Signals:")
            for r in c["friendly_reasons"]:
                print(f"│   {r}")
            print(f"╰{'─' * 30}╯")
        print("=" * 70)
        return

    if not settings.signal_only:
        raise RuntimeError("Safety stop: SIGNAL_ONLY must remain true.")

    # 1. Send Header Message
    header_lines = [
        "🎯 <b>STOCK SWING V1 - HIGH CONVICTION SIGNALS</b>",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"💰 <b>Capital:</b> ₹{settings.initial_capital:,.0f}  |  🎲 <b>Risk:</b> {settings.risk_per_trade * 100:.1f}%/trade",
        f"📅 <b>Scan:</b> {__import__('datetime').datetime.now().strftime('%d-%b-%Y %I:%M %p')}",
        f"🔍 <b>Setups Found:</b> {len(formatted_candidates[:5])}",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    if fii_dii_text:
        header_lines.append(fii_dii_text.strip())
        header_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    _post_telegram_message(
        settings.telegram_bot_token, settings.telegram_chat_id, "\n".join(header_lines)
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

        card_lines = [
            f"┏━━ <b>#{i} {sym_esc}</b> ━━━ <code>{setup_esc}</code>",
            f"┃ ⭐ <b>Conviction Score:</b> {c['score']}/100",
            f"┃ 🏷️ <b>NSE Cap Segment:</b> {html.escape(str(c.get('cap_segment', 'UNKNOWN')))}",
            f"┃",
            f"┃ 💵 <b>Buy / Entry:</b> ₹{c['entry']:,.2f}",
            f"┃ 🛑 <b>Stop Loss:</b> ₹{c['stop_loss']:,.2f} <i>(-{risk_pct:.1f}%)</i>",
            f"┃",
            f"┃ 🎯 <b>Targets:</b>",
            f"┃   🥇 <b>T1:</b> ₹{c['target_1']:,.2f} <i>(+{t1_pct:.1f}%)</i> → <b>Book 50%</b>",
            f"┃   🥈 <b>T2:</b> ₹{c['target_2']:,.2f} <i>(+{t2_pct:.1f}%)</i> → <b>Book 30%</b>",
            f"┃   🥉 <b>T3:</b> ₹{c['target_3']:,.2f} <i>(+{t3_pct:.1f}%)</i> → <b>Trail 20%</b>",
            f"┃",
            f"┃ ⏱️ <b>Holding Period:</b> 5–15 trading days (1–3 weeks)",
            f"┃",
        ]

        # FII / Institutional Indicator
        inst_indicator = get_institutional_indicator(c)
        if inst_indicator:
            inst_esc = html.escape(inst_indicator)
            card_lines.append(f"┃ 🏛️ <b>Institutional Flow:</b> {inst_esc}")
            card_lines.append(f"┃")

        # News & Catalysts Section
        news_badge = c.get("news_badge")
        news_headlines = c.get("news_headlines_with_dates", c.get("news_headlines", []))
        news_red_flags = c.get("news_red_flags", [])

        if news_badge:
            badge_esc = html.escape(str(news_badge))
            card_lines.append(f"┃ 📰 <b>News Sentiment:</b> {badge_esc}")
            if news_red_flags:
                for rf in news_red_flags:
                    rf_esc = html.escape(str(rf))
                    card_lines.append(f"┃   {rf_esc}")
            elif news_headlines:
                for h in news_headlines[:2]:
                    h_clean = h[:75] + "..." if len(h) > 75 else h
                    h_esc = html.escape(h_clean)
                    card_lines.append(f'┃   • <i>"{h_esc}"</i>')
            card_lines.append(f"┃")

        if "quantity" in c and c["quantity"] > 0:
            card_lines.append(
                f"┃ 📦 <b>Position Sizing:</b> <b>{c['quantity']} shares</b>"
            )
            card_lines.append(
                f"┃   💰 Capital: ₹{c['capital_required']:,.0f}  |  🛡️ Max Risk: ₹{c['risk_amount']:,.0f}"
            )
            card_lines.append(f"┃")

        card_lines.append(f"┃ 💡 <b>Technical Setup:</b>")
        for r in c["friendly_reasons"]:
            r_esc = html.escape(str(r))
            card_lines.append(f"┃   {r_esc}")
        card_lines.append(f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━")

        _post_telegram_message(
            settings.telegram_bot_token,
            settings.telegram_chat_id,
            "\n".join(card_lines),
        )
        time.sleep(0.3)

    # 3. Footer Safety Note
    _post_telegram_message(
        settings.telegram_bot_token,
        settings.telegram_chat_id,
        "⚠️ <i>SIGNAL ONLY - Please review charts before taking trades</i>",
    )
    print(
        "Telegram alert delivered successfully in rich HTML format with News & FII/DII data!"
    )
