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
        r"\b(sebi|ed|cbi|sfio)\b.*\b(probe|raid|notice|ban|fine|penalty|inquiry|investigation)\b",
        "Regulatory Investigation / Action",
    ),
    (
        r"\b(auditor|cfo|ceo|md)\b.*\b(resigns|resigned|quit|stepped down|fired)\b",
        "Key Executive / Auditor Resignation",
    ),
    (
        r"\b(fraud|scam|forgery|money laundering|tax evasion|bribe)\b",
        "Forensic / Integrity Red Flag",
    ),
    (
        r"\b(default|insolvency|nclt|bankruptcy|debt distress)\b",
        "Debt / Solvency Distress",
    ),
    (
        r"\b(downgrade|rating cut|junk)\b.*\b(crisil|icra|care|fitch|moody)\b",
        "Credit Rating Downgrade",
    ),
    (
        r"\b(promoter)\b.*\b(pledge|forced sale|margin call)\b",
        "Promoter Share Distress",
    ),
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
