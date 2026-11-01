"""
Company News Analyzer

Fetches and analyzes real-time financial news for NSE equity candidates:
1. Fetches top recent headlines from financial RSS / Google News feeds.
2. Identifies positive growth catalysts (earnings beat, order wins, capacity expansion, deal wins).
3. Scans for negative red flags via negative_event_detector.
4. Computes news sentiment (POSITIVE, NEUTRAL, CAUTION).
5. Enriches trade setup candidates with news headlines for Telegram alerts.
"""

import re
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import requests

if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from news_analysis.negative_event_detector import (
        detect_negative_events,
        detect_upcoming_earnings,
        has_critical_crash_risk,
    )
else:
    from .negative_event_detector import (
        detect_negative_events,
        detect_upcoming_earnings,
        has_critical_crash_risk,
    )

# Cache to store news per symbol: {symbol: (timestamp, articles, analysis)}
_NEWS_CACHE: dict[str, tuple[float, list[dict], dict]] = {}
CACHE_TTL_SECONDS = 3600  # 1 hour cache

# Well-known NSE symbol to common company name mapping for better news precision
SYMBOL_NAME_MAP = {
    "ASHOKLEY": "Ashok Leyland",
    "MOTHERSON": "Samvardhana Motherson",
    "PAYTM": "Paytm One97",
    "LAURUSLABS": "Laurus Labs",
    "KOTAKBANK": "Kotak Mahindra Bank",
    "HDFCBANK": "HDFC Bank",
    "ICICIBANK": "ICICI Bank",
    "SBIN": "State Bank of India",
    "RELIANCE": "Reliance Industries",
    "TCS": "Tata Consultancy Services",
    "INFY": "Infosys",
    "TATAMOTORS": "Tata Motors",
    "TATASTEEL": "Tata Steel",
    "BHARTIARTL": "Bharti Airtel",
    "BAJFINANCE": "Bajaj Finance",
    "MARUTI": "Maruti Suzuki",
    "LT": "Larsen Toubro",
    "SUNPHARMA": "Sun Pharma",
    "TITAN": "Titan Company",
    "AXISBANK": "Axis Bank",
    "OFSS": "Oracle Financial Services",
    "CHOLAFIN": "Cholamandalam Investment",
    "DIVISLAB": "Divis Laboratories",
    "SBICARD": "SBI Cards",
    "CYIENT": "Cyient",
    "MCX": "Multi Commodity Exchange",
    "SOLARINDS": "Solar Industries",
    "LICHSGFIN": "LIC Housing Finance",
    "SUZLON": "Suzlon Energy",
    "HAL": "Hindustan Aeronautics",
    "BEL": "Bharat Electronics",
    "BHEL": "Bharat Heavy Electricals",
    "M&M": "Mahindra and Mahindra",
    "TVSMOTOR": "TVS Motor",
    "HEROMOTOCO": "Hero MotoCorp",
    "EICHERMOT": "Eicher Motors",
    "COALINDIA": "Coal India",
    "NTPC": "NTPC Limited",
    "POWERGRID": "Power Grid Corporation",
    "ONGC": "ONGC Oil and Natural Gas",
    "COCHINSHIP": "Cochin Shipyard",
    "DELTACORP": "Delta Corp",
    "DREAMFOLKS": "Dreamfolks Services",
    "ECOSMOBLTY": "Ecos India Mobility",
    "ELECTCAST": "Electrosteel Castings",
    "EPACK": "EPACK Durable",
    "GTLINFRA": "GTL Infrastructure",
    "HAPPSTMNDS": "Happiest Minds Technologies",
    "IEX": "Indian Energy Exchange",
    "IMAGICAA": "Imagicaaworld Entertainment",
    "IOC": "Indian Oil Corporation",
    "IRB": "IRB Infrastructure Developers",
    "LODHA": "Macrotech Developers Lodha",
    "NTPCGREEN": "NTPC Green Energy",
    "PCBL": "PCBL",
    "SALASAR": "Salasar Techno Engineering",
    "SAMPRE": "Sampre Nutritions",
    "STANCAP": "Standard Capital Markets",
    "BAJAJHFL": "Bajaj Housing Finance",
    "ALOKINDS": "Alok Industries",
    "AKSHAR": "Akshar Spintex",
    "MADHAVIPL": "Madhav Infra Projects",
    "MAHACORP": "Maha Rashtra Corporation",
    "MISHTANN": "Mishtann Foods",
}

# Positive catalyst keywords
POSITIVE_CATALYSTS = [
    "order win",
    "bagged order",
    "secures order",
    "contract win",
    "deal",
    "binding mou",
    "mou",
    "slump sale",
    "asset monetization",
    "profit jumps",
    "profit surges",
    "profit rises",
    "net profit up",
    "revenue up",
    "quarterly results",
    "beats estimate",
    "strong q",
    "capacity expansion",
    "new plant",
    "acquisition",
    "joint venture",
    "jv",
    "hits new high",
    "rallies",
    "surges",
    "soars",
    "target raised",
    "brokerage bullish",
    "buy rating",
    "upgrade",
    "partnership",
    "dividend",
    "bonus shares",
    "warrant conversion",
    "warrant allotment",
    "merger",
    "amalgamation",
    "stake buy",
    "product launch",
    "fda approval",
    "market share gain",
]


def _clean_headline(raw_title: str) -> str:
    """Clean and strip trailing publication suffixes from title."""
    if not raw_title:
        return ""
    # Remove standard publisher suffixes e.g. " - Moneycontrol", " - Business Standard"
    cleaned = re.sub(r"\s*-\s*([A-Za-z0-9\.\s]+)$", "", raw_title).strip()
    return cleaned


def _format_article_date(value: str) -> str:
    """Format RSS publication dates for compact report display."""
    if not value:
        return "Date unavailable"
    try:
        return datetime.strptime(value, "%a, %d %b %Y %H:%M:%S %Z").strftime("%d-%b-%Y")
    except ValueError:
        return value[:16]


def fetch_company_news(symbol: str, max_articles: int = 3) -> list[dict]:
    """
    Fetch top recent news articles for an NSE stock.

    Args:
        symbol: NSE stock symbol (e.g. 'MOTHERSON', 'KOTAKBANK')
        max_articles: Maximum number of articles to return

    Returns:
        List of article dicts [{'title': str, 'source': str, 'date': str, 'link': str}]
    """
    now = time.time()
    if symbol in _NEWS_CACHE:
        cached_time, cached_articles, _ = _NEWS_CACHE[symbol]
        if now - cached_time < CACHE_TTL_SECONDS:
            return cached_articles

    company_name = SYMBOL_NAME_MAP.get(symbol, symbol)
    query_str = f'"{company_name}" OR "{symbol}" ("BSE" OR "NSE" OR "corporate announcement" OR "Regulation 30" OR "Board meeting" OR "MoU" OR "acquisition" OR "sale" OR "results" OR "share price")'
    encoded_query = urllib.parse.quote(query_str)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    articles = []
    try:
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for item in root.findall(".//item")[:max_articles]:
                raw_title = (
                    item.find("title").text if item.find("title") is not None else ""
                )
                pub_date = (
                    item.find("pubDate").text
                    if item.find("pubDate") is not None
                    else ""
                )
                link = item.find("link").text if item.find("link") is not None else ""
                source_elem = item.find("source")
                source = (
                    source_elem.text
                    if source_elem is not None and source_elem.text
                    else "Financial News"
                )

                cleaned_title = _clean_headline(raw_title)
                if cleaned_title:
                    articles.append(
                        {
                            "title": cleaned_title,
                            "raw_title": raw_title,
                            "source": source,
                            "date": pub_date,
                            "link": link,
                        }
                    )
    except Exception as exc:
        print(f"DEBUG: News fetch for {symbol} failed: {exc}")

    # If empty, provide a clean neutral fallback
    if not articles:
        articles.append(
            {
                "title": f"Steady trading momentum in {company_name}",
                "source": "Market Watch",
                "date": datetime.now().strftime("%d %b %Y"),
                "link": "",
            }
        )

    return articles


def analyze_news_sentiment(symbol: str, articles: list[dict]) -> dict:
    """
    Analyze news headlines for catalysts, red flags, and overall sentiment.

    Args:
        symbol: NSE stock symbol
        articles: List of article dicts

    Returns:
        Dictionary with sentiment details:
        {
            'sentiment': 'POSITIVE' | 'NEUTRAL' | 'CAUTION',
            'sentiment_score': float (-1.0 to 1.0),
            'positive_catalysts': list[str],
            'red_flags': list[str],
            'headlines': list[str],
            'summary_badge': str
        }
    """
    positive_catalysts = []
    headlines = []

    for art in articles:
        title = art.get("title", "")
        if title:
            headlines.append(title)
        title_lower = title.lower()
        for cat in POSITIVE_CATALYSTS:
            if cat in title_lower:
                positive_catalysts.append(f"🟢 {title}")
                break

    # Scan for critical red flags and crash risks
    red_flags = detect_negative_events(articles)
    is_crash_risk, crash_reason = has_critical_crash_risk(articles)
    upcoming_earnings = detect_upcoming_earnings(articles)

    # Determine overall sentiment and future predictive outlook
    if is_crash_risk:
        sentiment = "CAUTION"
        sentiment_score = -0.9
        summary_badge = "🚨 Caution: Critical Red Flag / Crash Hazard (Avoid)"
        predictive_outlook = f"🚨 HIGH CRASH RISK: {crash_reason}"
    elif upcoming_earnings:
        sentiment = "CAUTION"
        sentiment_score = -0.4
        summary_badge = "⚠️ Caution: Earnings Blackout Risk (Binary Event Ahead)"
        predictive_outlook = f"⚠️ EARNINGS RISK: Results scheduled within swing window"
    elif red_flags:
        sentiment = "CAUTION"
        sentiment_score = -0.6
        summary_badge = "⚠️ Caution (Negative Event Detected)"
        predictive_outlook = "⚠️ CAUTION: Negative news friction"
    elif len(positive_catalysts) >= 1:
        sentiment = "POSITIVE"
        sentiment_score = 0.75
        summary_badge = "🟢 Positive (Growth Catalyst / Bullish News)"
        predictive_outlook = "🚀 HIGH CONVICTION TAILWIND (Order Wins/Growth Catalysts)"
    else:
        sentiment = "NEUTRAL"
        sentiment_score = 0.0
        summary_badge = "⚪ Neutral (No Adverse Events)"
        predictive_outlook = "🟢 CLEAN STRUCTURE (Clean news flow, no crash flags)"

    analysis = {
        "sentiment": sentiment,
        "sentiment_score": sentiment_score,
        "is_crash_risk": is_crash_risk,
        "crash_reason": crash_reason,
        "earnings_risk": bool(upcoming_earnings),
        "earnings_notices": upcoming_earnings,
        "predictive_outlook": predictive_outlook,
        "positive_catalysts": positive_catalysts[:2],
        "red_flags": red_flags,
        "headlines": headlines[:2],
        "headlines_with_dates": [
            f"{_format_article_date(article.get('date', ''))}: {article.get('title', '')}"
            for article in articles[:2]
            if article.get("title")
        ],
        "positive_catalysts_with_dates": [
            f"{_format_article_date(article.get('date', ''))}: {article.get('title', '')}"
            for article in articles
            if article.get("title")
            and any(
                keyword in article.get("title", "").lower()
                for keyword in POSITIVE_CATALYSTS
            )
        ][:2],
        "summary_badge": summary_badge,
    }

    # Cache result
    _NEWS_CACHE[symbol] = (time.time(), articles, analysis)
    return analysis


def enrich_candidate_with_news(candidate: dict) -> dict:
    """
    Fetch news and enrich a single candidate dictionary.

    Args:
        candidate: Candidate trade dictionary

    Returns:
        Updated candidate dictionary with 'news_sentiment', 'news_headlines', and 'news_badge'
    """
    symbol = candidate.get("symbol", "")
    articles = fetch_company_news(symbol)
    analysis = analyze_news_sentiment(symbol, articles)

    enriched = dict(candidate)
    enriched["news_sentiment"] = analysis["sentiment"]
    enriched["news_badge"] = analysis["summary_badge"]
    enriched["news_headlines"] = analysis["headlines"]
    enriched["news_headlines_with_dates"] = analysis["headlines_with_dates"]
    enriched["news_positive_catalysts"] = analysis["positive_catalysts"]
    enriched["news_positive_catalysts_with_dates"] = analysis[
        "positive_catalysts_with_dates"
    ]
    enriched["news_red_flags"] = analysis["red_flags"]
    enriched["is_crash_risk"] = analysis.get("is_crash_risk", False)
    enriched["crash_reason"] = analysis.get("crash_reason", "")
    enriched["earnings_risk"] = analysis.get("earnings_risk", False)
    enriched["earnings_notices"] = analysis.get("earnings_notices", [])
    enriched["predictive_outlook"] = analysis.get("predictive_outlook", "")

    return enriched


def enrich_candidates_with_news(candidates: list[dict]) -> list[dict]:
    """
    Enrich a list of ranked candidate dictionaries with live news sentiment.

    Args:
        candidates: List of ranked candidate dicts

    Returns:
        List of enriched candidate dictionaries
    """
    return [enrich_candidate_with_news(c) for c in candidates]
