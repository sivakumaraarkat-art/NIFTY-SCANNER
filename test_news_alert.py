"""
Interactive Stock News & Sentiment Telegram Test Utility

Allows testing live news fetching, sentiment analysis, red-flag detection,
and HTML Telegram notification delivery for any stock symbol.

Usage:
    python test_news_alert.py RELIANCE
    python test_news_alert.py TCS
    python test_news_alert.py TATAMOTORS
    python test_news_alert.py MOTHERSON
"""

import sys
import html
import requests
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from configuration.swing_trade_settings import load_settings
from news_analysis.company_news_analyzer import (
    fetch_company_news,
    analyze_news_sentiment,
)
from institutional_data.fii_dii_data_fetcher import (
    fetch_daily_fii_dii_summary,
    format_institutional_flow_header,
)


def send_news_test_alert(symbol: str) -> None:
    settings = load_settings()
    symbol = symbol.upper().strip()

    print(f"\n🔍 Fetching real-time news & sentiment for {symbol}...")
    articles = fetch_company_news(symbol, max_articles=5)
    analysis = analyze_news_sentiment(symbol, articles)
    fii_dii = fetch_daily_fii_dii_summary()

    print(
        f"📊 Sentiment Analysis: {analysis['sentiment']} (Score: {analysis['sentiment_score']:.2f})"
    )
    print(f"🏷️ Badge: {analysis['summary_badge']}")
    print(f"📰 Headlines Found: {len(articles)}")
    for i, art in enumerate(articles, 1):
        print(f"   [{i}] {art.get('title')} ({art.get('source')})")

    # Build rich HTML Telegram Card
    sym_esc = html.escape(symbol)
    badge_esc = html.escape(analysis["summary_badge"])

    lines = [
        f"🧪 <b>[NEWS TEST ALERT] {sym_esc}</b>",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🏢 <b>Stock:</b> <code>{sym_esc}</code>",
        f"📊 <b>Sentiment:</b> {badge_esc}",
        f"📈 <b>Sentiment Score:</b> {analysis['sentiment_score']:.2f} / 1.00",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "📰 <b>Latest Live Headlines:</b>",
    ]

    if analysis["red_flags"]:
        lines.append("🚨 <b>CRITICAL RED FLAGS:</b>")
        for rf in analysis["red_flags"]:
            lines.append(f"  • {html.escape(rf)}")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    for art in articles[:3]:
        title = html.escape(art.get("title", ""))
        source = html.escape(art.get("source", "Financial News"))
        lines.append(f'• <i>"{title}"</i>\n  ↳ <code>{source}</code>')

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if fii_dii:
        dii_net = fii_dii.get("dii_net", 0.0)
        fii_net = fii_dii.get("fii_net", 0.0)
        lines.append(
            f"🏛️ <b>Market Flow:</b> DII: {'+' if dii_net > 0 else ''}₹{dii_net:,.0f} Cr | FII: {'+' if fii_net > 0 else ''}₹{fii_net:,.0f} Cr"
        )

    lines.append("⚡ <i>STOCK SWING V1 News & Sentiment Test</i>")

    msg_text = "\n".join(lines)

    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        print("\n[Preview - Telegram Bot Token not set]:")
        print(msg_text)
        return

    print("\n🚀 Dispatching HTML alert to Telegram...")
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
            json={
                "chat_id": settings.telegram_chat_id,
                "text": msg_text,
                "parse_mode": "HTML",
            },
            timeout=15,
        )
        if r.status_code == 200:
            print(f"✅ Success! Telegram news alert for {symbol} sent.")
        else:
            print(f"❌ Telegram Error {r.status_code}: {r.text}")
    except Exception as exc:
        print(f"❌ Connection Error: {exc}")


if __name__ == "__main__":
    target_symbol = sys.argv[1] if len(sys.argv) > 1 else "RELIANCE"
    send_news_test_alert(target_symbol)
