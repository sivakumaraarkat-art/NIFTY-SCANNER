"""
Negative Event Detector

Detects critical red flags and adverse events for stocks:
- Regulatory actions (SEBI inquiries, penalties, bans)
- Forensic / accounting red flags (auditor resignations, frauds, raids)
- Debt / liquidity distress (defaults, credit rating downgrades)
- Governance issues (promoter pledge distress, sudden executive exits)
"""

import re

# High-severity negative event triggers
CRITICAL_RED_FLAG_PATTERNS = [
    (
        r"\b(sebi|ed|cbi|sfio|rbi|cci)\b.*\b(probe|raid|notice|ban|fine|penalty|inquiry|investigation|search|seizure)\b",
        "Regulatory Investigation / Action",
    ),
    (
        r"\b(auditor|cfo|ceo|md)\b.*\b(resigns|resigned|quit|stepped down|fired|exit)\b",
        "Key Executive / Auditor Resignation",
    ),
    (
        r"\b(fraud|scam|forgery|money laundering|tax evasion|bribe|falsification|shell compan)\b",
        "Forensic / Integrity Red Flag",
    ),
    (
        r"\b(default|insolvency|nclt|bankruptcy|debt distress|liquidation|debt restructuring)\b",
        "Debt / Solvency Distress",
    ),
    (
        r"\b(downgrade|rating cut|junk|negative watch)\b.*\b(crisil|icra|care|fitch|moody)\b",
        "Credit Rating Downgrade",
    ),
    (
        r"\b(promoter)\b.*\b(pledge|forced sale|margin call|invoked|seized)\b",
        "Promoter Share Distress",
    ),
    (
        r"\b(usfda|fda)\b.*\b(warning letter|form 483|import alert|oai|inspection)\b",
        "Pharma US-FDA Warning / Import Alert",
    ),
    (
        r"\b(ofs|offer for sale|promoter stake sale)\b.*\b(discount|steep discount|floor price)\b",
        "OFS Discount / Promoter Offloading",
    ),
    (
        r"\b(slashes guidance|cuts guidance|profit warning|sales warning|margin collapse)\b",
        "Guidance Cut / Earnings Warning",
    ),
]

# Earnings / Results announcement pattern to prevent holding into binary shock
EARNINGS_ANNOUNCEMENT_PATTERNS = [
    r"\b(board meeting|to consider|approves)\b.*\b(financial results|q[1-4] results|quarterly results|earnings)\b",
    r"\b(q[1-4]|quarterly|annual)\b.*\b(results on|earnings on|to report on)\b",
    r"\b(results|earnings)\b.*\b(announcement|scheduled|calendar)\b",
]

# General negative sentiment keywords
GENERAL_NEGATIVE_KEYWORDS = [
    "plunges",
    "slumps",
    "crashes",
    "tumbles",
    "falls sharp",
    "profit drops",
    "loss widens",
    "misses estimate",
    "weak guidance",
    "warning",
    "lawsuit",
    "dispute",
    "penalized",
    "barred",
]


def detect_negative_events(articles: list[dict]) -> list[str]:
    """
    Scan article titles and descriptions for critical red flags.

    Args:
        articles: List of article dicts with 'title' and optional 'description'

    Returns:
        List of identified red-flag descriptions (empty if clean)
    """
    detected_flags = []

    for article in articles:
        text = (article.get("title", "") + " " + article.get("description", "")).lower()

        # Check critical patterns
        for pattern, label in CRITICAL_RED_FLAG_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                flag_msg = f"🚨 {label}: '{article.get('title', '')[:80]}'"
                if flag_msg not in detected_flags:
                    detected_flags.append(flag_msg)

        # Check general negative keywords
        for kw in GENERAL_NEGATIVE_KEYWORDS:
            if kw in text:
                flag_msg = f"⚠️ Negative Event: '{article.get('title', '')[:80]}'"
                if flag_msg not in detected_flags and len(detected_flags) < 3:
                    detected_flags.append(flag_msg)

    return detected_flags


def detect_upcoming_earnings(articles: list[dict]) -> list[str]:
    """
    Check if the stock has upcoming quarterly/annual earnings results announced.
    Holding a swing trade through results exposes capital to binary gap-down crash risks.
    """
    earnings_warnings = []
    for article in articles:
        text = (article.get("title", "") + " " + article.get("description", "")).lower()
        for pattern in EARNINGS_ANNOUNCEMENT_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                warning_msg = f"🗓️ Upcoming Results Notice: '{article.get('title', '')[:80]}'"
                if warning_msg not in earnings_warnings:
                    earnings_warnings.append(warning_msg)
                break
    return earnings_warnings


def has_critical_crash_risk(articles: list[dict]) -> tuple[bool, str]:
    """
    Determine if the stock has any high-severity crash catalyst that justifies disqualification.

    Returns:
        (is_risk, reason)
    """
    for article in articles:
        text = (article.get("title", "") + " " + article.get("description", "")).lower()
        for pattern, label in CRITICAL_RED_FLAG_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True, f"{label} ('{article.get('title', '')[:70]}')"
    return False, ""

