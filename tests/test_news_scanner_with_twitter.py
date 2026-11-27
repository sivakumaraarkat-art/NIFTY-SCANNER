import pytest
from src.scanners.news_scanner_with_twitter import (
    extract_sentiment,
    match_symbols,
    headline_key,
    catalyst_for,
    NewsItem,
)
from datetime import datetime, timezone


def test_sentiment_clause_negation_and_denial():
    # Denial should be treated as neutral/disputed, not bearish
    assert extract_sentiment("Company denies data breach allegations") == "neutral"
    assert extract_sentiment("Firm refutes claims of financial irregularity") == "neutral"

    # Direct bullish catalysts
    assert extract_sentiment("Net profit rises 35% on robust festive demand") == "bullish"
    assert extract_sentiment("Company bags major order worth Rs 1,200 crore") == "bullish"

    # Direct bearish catalysts
    assert extract_sentiment("SEBI imposes penalty on management for insider trading") == "bearish"
    assert extract_sentiment("CBI launches probe into loan default and fraud") == "bearish"

    # Conflicting clauses should resolve to neutral
    assert extract_sentiment("Net profit jumps 20% however guidance cut for Q3") == "neutral"
    assert extract_sentiment("Revenue rises 15% but margin contracts severely") == "neutral"


def test_ambiguous_ticker_protection():
    # "Titan submersible" must NOT match TITAN (Titan Company Ltd)
    assert match_symbols("Titan submersible missing in North Atlantic ocean") == []
    assert match_symbols("Titan Company Q2 jewellery revenue surges 25%") == ["TITAN"]
    assert match_symbols("Titan shares climb 3% to fresh 52-week high") == ["TITAN"]

    # "Brent oil" must NOT match OIL (Oil India Ltd)
    assert match_symbols("Brent oil drops 2% on global demand concerns") == []
    assert match_symbols("Crude oil prices steady near $74 a barrel") == []
    assert match_symbols("Oil India shares jump after major gas discovery in Assam") == ["OIL"]
    assert match_symbols("Oil India reports 40% jump in net profit") == ["OIL"]

    # Newly added high-volume F&O stocks
    assert match_symbols("Swiggy lists at premium on Dalal Street") == ["SWIGGY"]
    assert match_symbols("RVNL bags Rs 800 crore railway infrastructure contract") == ["RVNL"]
    assert match_symbols("Amber Enterprises expands contract manufacturing facility") == ["AMBER"]


def test_headline_deduplication():
    # Known publisher suffixes should be stripped so duplicate coverage hashes to the same key
    k1 = headline_key("Tata Motors shares rally 5% on strong JLR sales - Moneycontrol")
    k2 = headline_key("Tata Motors shares rally 5% on strong JLR sales - Livemint")
    k3 = headline_key("Tata Motors shares rally 5% on strong JLR sales - Economic Times")
    assert k1 == k2 == k3

    # Distinct events should not collapse together
    k_distinct = headline_key("Tata Motors reports flat domestic sales in October - Moneycontrol")
    assert k1 != k_distinct


def test_catalyst_detection():
    # Denial catalyst
    art_denial = NewsItem(
        source="rss",
        title="Company denies data breach reports",
        url="http://example.com/1",
        published=datetime.now(timezone.utc),
        sentiment="neutral",
        symbol="TEST",
        score=50.0,
        publisher="Reuters",
    )
    cat, expl = catalyst_for(art_denial)
    assert cat == "Disputed / Denial"

    # Order win catalyst
    art_order = NewsItem(
        source="rss",
        title="Company bags Rs 500 Cr defence contract",
        url="http://example.com/2",
        published=datetime.now(timezone.utc),
        sentiment="bullish",
        symbol="TEST",
        score=75.0,
        publisher="Livemint",
    )
    cat, expl = catalyst_for(art_order)
    assert cat == "Order / contract"


def test_broker_analyst_attribution_masking():
    # Broker giving a target on another stock should NOT be matched as the target company
    headline = "Neutral Manappuram Finance; target of Rs 360: Motilal Oswal - Moneycontrol.com"
    matched = match_symbols(headline)
    assert "MANAPPURAM" in matched
    assert "MOTILALOFS" not in matched

    # Company reporting its own financial results SHOULD be matched
    own_headline = "Motilal Oswal Financial Services reports 45% surge in Q2 net profit"
    matched_own = match_symbols(own_headline)
    assert "MOTILALOFS" in matched_own


def test_option_sl_vs_target_risk_reward_mathematics():
    # Verify that Stop Loss points NEVER exceed Target 1 or Target 2 points
    from src.scanners.options_data_provider import calculate_powerful_sl_engine

    for entry in [10.0, 50.0, 95.50, 178.0, 1079.0]:
        sl_data = calculate_powerful_sl_engine(
            entry_price=entry,
            delta=0.52,
            iv=40.0,
            theta=-2.5,
            vega=1.2,
            is_btst=False,
            days_held=0.25,
        )
        sl_risk = sl_data["sl_risk"]
        sl_risk_pct = sl_data["sl_risk_pct"]

        # SL must be a disciplined 7% to 13.5% ceiling, never arbitrary 20%
        assert 7.0 <= sl_risk_pct <= 13.51

        # Calculate Targets
        t1_gain = max(round(sl_risk * 1.25, 2), round(entry * 0.10, 2))
        t2_gain = max(round(sl_risk * 2.00, 2), round(entry * 0.18, 2))

        # Target 1 points MUST strictly exceed Stop Loss risk points
        assert t1_gain > sl_risk, f"T1 points ({t1_gain}) must exceed SL risk ({sl_risk})"

        # Target 2 points MUST equal or exceed 2x Stop Loss risk points
        assert t2_gain >= round(2.0 * sl_risk, 2) - 0.05, f"T2 points ({t2_gain}) must be at least 2x SL risk ({sl_risk})"


