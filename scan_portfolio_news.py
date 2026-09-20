"""
Portfolio News & Sentiment Scanner

Fetches all active holdings from Zerodha KiteConnect, analyzes live financial news
and sentiment catalysts/red flags for every holding stock, and delivers a
formatted Telegram portfolio digest.
"""

import html
import sys
import time
import requests
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from configuration.swing_trade_settings import load_settings
from zerodha_market_data.zerodha_connection import create_zerodha_client
from news_analysis.company_news_analyzer import (
    fetch_company_news,
    analyze_news_sentiment,
)
from institutional_data.fii_dii_data_fetcher import fetch_daily_fii_dii_summary


def scan_portfolio():
    settings = load_settings()
    kite = create_zerodha_client(settings)

    print("\n" + "=" * 65)
    print("💼 SCANNING ZERODHA PORTFOLIO HOLDINGS & LIVE NEWS")
    print("=" * 65)

    try:
        profile = kite.profile()
        user_name = profile.get("user_name", "User")
        user_id = profile.get("user_id", "")
        print(f"Account: {user_name} ({user_id})")
        holdings = kite.holdings()
    except Exception as exc:
        print(f"❌ Error fetching holdings: {exc}")
        return

    if not holdings:
        print("No holdings found in portfolio.")
        return

    total_invested = 0.0
    total_current = 0.0
    total_pnl = 0.0

    scored_holdings = []

    print(f"\nAnalyzing live news and sentiment for {len(holdings)} holdings...")
    for i, h in enumerate(holdings, 1):
        sym = h.get("tradingsymbol", "")
        qty = h.get("quantity", 0)
        avg = h.get("average_price", 0.0)
        ltp = h.get("last_price", 0.0)
        pnl = h.get("pnl", 0.0)
        invested = qty * avg
        current_val = qty * ltp
        pnl_pct = ((ltp - avg) / avg * 100) if avg > 0 else 0.0

        total_invested += invested
        total_current += current_val
        total_pnl += pnl

        # Fetch & analyze news
        articles = fetch_company_news(sym, max_articles=3)
        analysis = analyze_news_sentiment(sym, articles)

        item = {
            "symbol": sym,
            "quantity": qty,
            "avg_price": avg,
            "ltp": ltp,
            "invested": invested,
            "current_val": current_val,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "sentiment": analysis["sentiment"],
            "sentiment_score": analysis["sentiment_score"],
            "badge": analysis["summary_badge"],
            "headlines": analysis["headlines"],
            "headlines_with_dates": analysis["headlines_with_dates"],
            "positive_catalysts": analysis["positive_catalysts"],
            "red_flags": analysis["red_flags"],
            "articles": articles,
        }
        scored_holdings.append(item)
        latest_date = (
            analysis["headlines_with_dates"][0].split(": ", 1)[0]
            if analysis["headlines_with_dates"]
            else "Date unavailable"
        )
        print(
            f" [{i:02d}/{len(holdings)}] {sym:<12} | P&L: ₹{pnl:>9.2f} ({pnl_pct:>+6.1f}%) | Sentiment: {analysis['sentiment']} | Latest news: {latest_date}"
        )

    overall_return_pct = (
        ((total_current - total_invested) / total_invested * 100)
        if total_invested > 0
        else 0.0
    )

    # Categorize holdings
    caution_list = [h for h in scored_holdings if h["sentiment"] == "CAUTION"]
    positive_list = [h for h in scored_holdings if h["sentiment"] == "POSITIVE"]
    neutral_list = [h for h in scored_holdings if h["sentiment"] == "NEUTRAL"]

    print("\n" + "=" * 65)
    print("📊 PORTFOLIO SUMMARY")
    print("=" * 65)
    print(f"Total Holdings: {len(holdings)} stocks")
    print(f"Total Invested: ₹{total_invested:,.2f}")
    print(f"Current Value:  ₹{total_current:,.2f}")
    print(
        f"Total P&L:      {'🔴' if total_pnl < 0 else '🟢'} ₹{total_pnl:,.2f} ({overall_return_pct:+.2f}%)"
    )
    print(
        f"Sentiment Breakdown: 🚨 {len(caution_list)} Caution | 🟢 {len(positive_list)} Positive | ⚪ {len(neutral_list)} Neutral"
    )
    print("=" * 65)

    # -------------------------------------------------------------
    # TELEGRAM NOTIFICATIONS
    # -------------------------------------------------------------
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        print("Telegram bot token not configured.")
        return

    fii_dii = fetch_daily_fii_dii_summary()

    # Message 1: Portfolio Header & Overall News Health
    pnl_sign = "+" if total_pnl >= 0 else ""
    pnl_icon = "🟢" if total_pnl >= 0 else "🔴"

    header_lines = [
        "💼 <b>PORTFOLIO NEWS & SENTIMENT REPORT</b>",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"👤 <b>Account:</b> {html.escape(user_name)} (<code>{html.escape(user_id)}</code>)",
        f"📊 <b>Total Holdings:</b> {len(holdings)} stocks",
        f"💰 <b>Invested:</b> ₹{total_invested:,.2f}",
        f"📈 <b>Current:</b> ₹{total_current:,.2f}",
        f"📉 <b>Total P&L:</b> {pnl_icon} <b>{pnl_sign}₹{total_pnl:,.2f} ({overall_return_pct:+.1f}%)</b>",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🔍 <b>News Sentiment Pulse:</b>",
        f"  🚨 <b>Caution / Red Flags:</b> {len(caution_list)} stocks",
        f"  🟢 <b>Positive Catalysts:</b> {len(positive_list)} stocks",
        f"  ⚪ <b>Neutral / Stable:</b> {len(neutral_list)} stocks",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    if fii_dii:
        dii_net = fii_dii.get("dii_net", 0.0)
        fii_net = fii_dii.get("fii_net", 0.0)
        header_lines.append(
            f"🏛️ <b>Market Flow:</b> DII: {'+' if dii_net > 0 else ''}₹{dii_net:,.0f} Cr | FII: {'+' if fii_net > 0 else ''}₹{fii_net:,.0f} Cr"
        )
        header_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    _send_telegram(
        settings.telegram_bot_token, settings.telegram_chat_id, "\n".join(header_lines)
    )
    time.sleep(0.3)

    # Message 2: Holdings with Red Flags / Caution
    if caution_list:
        caution_lines = [
            "🚨 <b>PORTFOLIO ALERTS: CAUTION & RED FLAGS</b>",
            "<i>(Holdings with recent negative news or regulatory mentions)</i>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        for item in caution_list:
            sym_esc = html.escape(item["symbol"])
            pnl_esc = f"{'+' if item['pnl'] >= 0 else ''}₹{item['pnl']:,.0f} ({item['pnl_pct']:+.1f}%)"
            caution_lines.append(
                f"⚠️ <b>{sym_esc}</b> (Qty: {item['quantity']} | P&L: {pnl_esc})"
            )
            if item["red_flags"]:
                for rf in item["red_flags"]:
                    caution_lines.append(f"  ↳ {html.escape(rf)}")
            elif item["headlines"]:
                for h in item["headlines"][:2]:
                    h_clean = h[:75] + "..." if len(h) > 75 else h
                    dated_headline = next(
                        (value for value in item["headlines_with_dates"] if h in value),
                        h,
                    )
                    caution_lines.append(
                        f'  ↳ <i>"{html.escape(dated_headline[:100])}"</i>'
                    )
            caution_lines.append("")

        caution_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        _send_telegram(
            settings.telegram_bot_token,
            settings.telegram_chat_id,
            "\n".join(caution_lines),
        )
        time.sleep(0.3)

    # Message 3: Holdings with Positive Catalysts
    if positive_list:
        pos_lines = [
            "🟢 <b>PORTFOLIO GROWTH CATALYSTS & POSITIVE NEWS</b>",
            "<i>(Holdings with order wins, earnings beats, or bullish updates)</i>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        for item in positive_list:
            sym_esc = html.escape(item["symbol"])
            pnl_esc = f"{'+' if item['pnl'] >= 0 else ''}₹{item['pnl']:,.0f} ({item['pnl_pct']:+.1f}%)"
            pos_lines.append(
                f"⭐ <b>{sym_esc}</b> (Qty: {item['quantity']} | P&L: {pnl_esc})"
            )
            for h in item["headlines_with_dates"][:2]:
                h_clean = h[:100] + "..." if len(h) > 100 else h
                pos_lines.append(f'  ↳ <i>"{html.escape(h_clean)}"</i>')
            pos_lines.append("")

        pos_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        _send_telegram(
            settings.telegram_bot_token, settings.telegram_chat_id, "\n".join(pos_lines)
        )
        time.sleep(0.3)

    print("\n✅ Portfolio news & sentiment report successfully sent to Telegram!")


def _send_telegram(bot_token: str, chat_id: str, text: str) -> bool:
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=15,
        )
        return r.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False


if __name__ == "__main__":
    scan_portfolio()
