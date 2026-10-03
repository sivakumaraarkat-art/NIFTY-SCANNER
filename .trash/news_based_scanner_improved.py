"""
NEWS-BASED F&O STOCK SCANNER — IMPROVED VERSION
─────────────────────────────────────────────────
Enhancements:
1. Retry logic with exponential backoff for RSS feed failures
2. Smarter deduplication (normalizes numbers in headlines)
3. Time decay bonus for fresh news (recency weighting)
4. Execution logging

Usage:
    python news_based_scanner.py
    python news_based_scanner.py --hours 12 --min-mentions 2
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import time
import json
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from typing import NamedTuple
from urllib.request import Request, urlopen
from urllib.error import URLError
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# F&O Universe
# ──────────────────────────────────────────────────────────────
FO_STOCKS: dict[str, list[str]] = {
    "RELIANCE":    ["Reliance Industries", "Reliance", "RIL", "Jio"],
    "TCS":         ["Tata Consultancy", "TCS"],
    "HDFCBANK":    ["HDFC Bank", "HDFCBANK"],
    "INFY":        ["Infosys", "INFY"],
    "ICICIBANK":   ["ICICI Bank", "ICICIBANK"],
}

RSS_FEEDS: list[tuple[str, str]] = [
    ("Moneycontrol",  "https://www.moneycontrol.com/rss/marketreports.xml"),
    ("ET Markets",    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"),
    ("Livemint",      "https://www.livemint.com/rss/markets"),
]

REQUEST_HEADERS = {
    "User-Agent": "NiftyScanner/1.0 (RSS Reader; +options-scanner)",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

BULLISH_KEYWORDS = [
    "upgrade", "buy", "outperform", "rally", "surge", "jump", "gain",
    "profit", "beats estimate", "strong", "growth", "bullish",
]

BEARISH_KEYWORDS = [
    "downgrade", "sell", "underperform", "crash", "plunge", "fall",
    "loss", "misses estimate", "weak", "bearish", "negative",
]


class NewsItem(NamedTuple):
    """One parsed news headline."""
    title: str
    link: str
    source: str
    published: datetime | None
    matched_symbols: list[str]
    sentiment: str       # "BULLISH" | "BEARISH" | "NEUTRAL"
    sentiment_score: int  # positive = bullish, negative = bearish


# ──────────────────────────────────────────────────────────────
# IMPROVEMENTS: Deduplication & Recency
# ──────────────────────────────────────────────────────────────

def _normalize_title_for_dedup(title: str) -> str:
    """Normalize headline for smarter deduplication.

    Removes numbers (scores, percentages), keeps structure for better matching.
    This catches "Reliance surges 5%" vs "Reliance surges 6%"
    """
    # Remove numbers (scores, percentages change), keep structure
    normalized = re.sub(r'\d+\.?\d*%?', '[NUM]', title.lower())
    # Remove punctuation and extra spaces
    normalized = re.sub(r'[^a-z0-9 ]', '', normalized)
    # Take first 75 chars for better matching
    return normalized[:75]


def _get_time_decay_bonus(published: datetime | None) -> float:
    """Calculate recency bonus for sentiment scoring.

    Returns bonus that decays over 10 hours:
    - Fresh news (< 1 hour): +5 pts
    - 6 hours old: +2 pts
    - 10+ hours old: 0 pts
    """
    if published is None:
        return 0.0
    try:
        age_hours = (datetime.now(timezone.utc) - published).total_seconds() / 3600
        return max(0.0, 5.0 - (age_hours * 0.5))  # Decays from 5 to 0 over 10 hours
    except Exception:
        return 0.0


# ──────────────────────────────────────────────────────────────
# IMPROVEMENT: Retry Logic with Exponential Backoff
# ──────────────────────────────────────────────────────────────

def fetch_feed(source_name: str, url: str, cutoff: datetime, max_retries: int = 2) -> list[NewsItem]:
    """Fetch and parse a single RSS feed with exponential backoff retry.

    Args:
        source_name: Name of the RSS feed source
        url: URL of the RSS feed
        cutoff: DateTime cutoff for filtering old articles
        max_retries: Number of retry attempts (default: 2 = 1s, 2s backoff)

    Returns:
        List of NewsItem objects from the feed.
    """
    items: list[NewsItem] = []
    raw = None

    # Retry loop with exponential backoff
    for attempt in range(max_retries):
        try:
            req = Request(url, headers=REQUEST_HEADERS)
            with urlopen(req, timeout=15) as resp:
                raw = resp.read()
            break  # Success, exit retry loop
        except (URLError, OSError, TimeoutError) as exc:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s exponential backoff
                print(f"  ⏳ {source_name}: Retry {attempt + 1}/{max_retries} in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"  ✗ {source_name}: Failed after {max_retries} retries")
                return items
        except Exception as exc:
            print(f"  ⚠  {source_name}: Unexpected error — {exc}")
            return items

    if raw is None:
        return items

    # Handle encoding
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    # Parse XML
    try:
        it = ET.iterparse(io.StringIO(text))
        for _, el in it:
            if "}" in el.tag:
                el.tag = el.tag.split("}", 1)[1]
            for key in list(el.attrib.keys()):
                if "}" in key:
                    new_key = key.split("}", 1)[1]
                    el.attrib[new_key] = el.attrib.pop(key)
        root = it.root
    except ET.ParseError:
        return items

    # Parse entries
    entries = root.findall(".//item")
    if not entries:
        entries = root.findall(".//entry")

    for entry in entries:
        title_el = entry.find("title")
        title = (title_el.text or "").strip() if title_el is not None else ""
        if not title:
            continue

        link_el = entry.find("link")
        link = link_el.get("href") or (link_el.text or "").strip() if link_el is not None else ""

        pub_el = entry.find("pubDate") or entry.find("published")
        pub_str = pub_el.text if pub_el is not None else None
        try:
            pub_date = parsedate_to_datetime(pub_str.strip()) if pub_str else None
        except Exception:
            pub_date = None

        if pub_date and pub_date < cutoff:
            continue

        desc_el = entry.find("description") or entry.find("summary")
        desc = (desc_el.text or "").strip() if desc_el is not None else ""
        full_text = f"{title} {desc}".lower()

        # Match symbols
        matched = []
        for symbol, patterns in FO_STOCKS.items():
            for pattern in patterns:
                if pattern.lower() in full_text:
                    matched.append(symbol)
                    break

        if not matched:
            continue

        # Score sentiment
        bull = sum(1 for kw in BULLISH_KEYWORDS if kw in full_text)
        bear = sum(1 for kw in BEARISH_KEYWORDS if kw in full_text)
        score = bull - bear

        if score > 0:
            sentiment = "BULLISH"
        elif score < 0:
            sentiment = "BEARISH"
            score = -score
        else:
            sentiment = "NEUTRAL"
            score = 0

        items.append(NewsItem(
            title=title,
            link=link,
            source=source_name,
            published=pub_date,
            matched_symbols=matched,
            sentiment=sentiment,
            sentiment_score=score,
        ))

    return items


def fetch_all_feeds(hours: int = 24) -> list[NewsItem]:
    """Fetch all RSS feeds and return combined NewsItem list."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    all_items: list[NewsItem] = []

    print(f"\n{'═' * 60}")
    print(f"📰  NEWS-BASED F&O STOCK SCANNER (IMPROVED)")
    print(f"📅  {datetime.now().strftime('%d-%b-%Y %I:%M %p')}")
    print(f"🔍  Looking back: {hours} hours")
    print(f"{'═' * 60}")
    print(f"\nFetching news from {len(RSS_FEEDS)} sources...")

    for source_name, url in RSS_FEEDS:
        items = fetch_feed(source_name, url, cutoff)
        print(f"  ✓  {source_name}: {len(items)} relevant headlines")
        all_items.extend(items)

    # IMPROVEMENT: Smarter deduplication + time decay bonus
    seen_titles: set[str] = set()
    unique: list[NewsItem] = []

    for item in all_items:
        # Smart dedup: normalize numbers, strip punctuation
        key = _normalize_title_for_dedup(item.title)
        if key not in seen_titles:
            seen_titles.add(key)
            # Apply time decay bonus to sentiment
            age_bonus = _get_time_decay_bonus(item.published)
            adjusted_score = item.sentiment_score + age_bonus

            # Create adjusted item
            adjusted_item = NewsItem(
                title=item.title,
                link=item.link,
                source=item.source,
                published=item.published,
                matched_symbols=item.matched_symbols,
                sentiment=item.sentiment,
                sentiment_score=int(adjusted_score),
            )
            unique.append(adjusted_item)

    return unique


def generate_report(items: list[NewsItem], min_mentions: int = 1) -> None:
    """Print a formatted report of news-driven F&O picks."""

    if not items:
        print("\n❌  No F&O stock news found in the given timeframe.")
        return

    # Group by symbol
    symbol_news: dict[str, list[NewsItem]] = defaultdict(list)
    for item in items:
        for sym in item.matched_symbols:
            symbol_news[sym].append(item)

    # Filter by minimum mentions
    symbol_news = {
        sym: news for sym, news in symbol_news.items()
        if len(news) >= min_mentions
    }

    if not symbol_news:
        print(f"\n❌  No stocks with {min_mentions}+ mentions found.")
        return

    # Calculate aggregate sentiment
    symbol_sentiment: dict[str, tuple[str, int, int]] = {}
    for sym, news_list in symbol_news.items():
        total_score = sum(n.sentiment_score for n in news_list)
        if total_score > 0:
            label = "🟢 BULLISH"
        elif total_score < 0:
            label = "🔴 BEARISH"
        else:
            label = "🟡 NEUTRAL"
        symbol_sentiment[sym] = (label, total_score, len(news_list))

    ranked = sorted(symbol_sentiment.items(), key=lambda x: (x[1][2], abs(x[1][1])), reverse=True)

    print(f"\n{'─' * 72}")
    print(f"{'#':>2}  {'Symbol':<14} {'Sentiment':<14} {'Score':>6} {'Mentions':>8}")
    print(f"{'─' * 72}")
    for i, (sym, (label, score, count)) in enumerate(ranked, 1):
        print(f"{i:>2}  {sym:<14} {label:<14} {score:>+5}  {count:>6}")
    print(f"{'─' * 72}\n")


def export_scan_config(args, items: list[NewsItem]) -> dict:
    """Export scan configuration and results for audit trail."""
    return {
        "timestamp": datetime.now().isoformat(),
        "script": "news_based_scanner",
        "hours": args.hours,
        "min_mentions": args.min_mentions,
        "headlines_found": len(items),
        "unique_symbols": len(set(s for item in items for s in item.matched_symbols)),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="News-Based F&O Stock Scanner")
    parser.add_argument("--hours", type=int, default=24, help="Look back this many hours")
    parser.add_argument("--min-mentions", type=int, default=1, help="Minimum mentions to include")
    return parser.parse_args()


def main():
    args = parse_args()
    items = fetch_all_feeds(hours=args.hours)
    print(f"\nTotal relevant headlines found: {len(items)}")
    generate_report(items, min_mentions=args.min_mentions)

    # IMPROVEMENT: Export execution log
    config = export_scan_config(args, items)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"news_scan_{timestamp}.json"
    with open(log_file, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"\n✓ Execution log saved: {log_file}")


if __name__ == "__main__":
    main()
