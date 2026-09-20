import subprocess
import sys
from pathlib import Path

import pytest
from news_analysis.negative_event_detector import detect_negative_events
from news_analysis.company_news_analyzer import (
    analyze_news_sentiment,
    enrich_candidate_with_news,
    _clean_headline,
)


def test_clean_headline():
    raw = "Samvardhana Motherson rallies 6%, hits new high - Business Standard"
    cleaned = _clean_headline(raw)
    assert cleaned == "Samvardhana Motherson rallies 6%, hits new high"


def test_negative_event_detector_flags_critical_issues():
    articles = [
        {"title": "SEBI issues show cause notice and penalty to company executives"},
        {"title": "Auditor resigns citing accounting discrepancies"},
        {"title": "Normal business operations continued"},
    ]
    flags = detect_negative_events(articles)
    assert len(flags) >= 2
    assert any("Regulatory Investigation" in f or "SEBI" in f for f in flags)
    assert any("Resignation" in f or "Auditor" in f for f in flags)


def test_negative_event_detector_clean_for_normal_news():
    articles = [
        {"title": "Company reports 25% profit jump in Q1"},
        {"title": "New manufacturing plant commissioned in Gujarat"},
    ]
    flags = detect_negative_events(articles)
    assert len(flags) == 0


def test_analyze_news_sentiment_positive():
    articles = [
        {"title": "Company secures mega order win worth Rs 500 Cr"},
        {"title": "Brokerage bullish after strong quarterly results"},
    ]
    analysis = analyze_news_sentiment("TESTSYM", articles)
    assert analysis["sentiment"] == "POSITIVE"
    assert analysis["sentiment_score"] > 0
    assert len(analysis["positive_catalysts"]) >= 1
    assert "Positive" in analysis["summary_badge"]


def test_analyze_news_sentiment_caution_on_red_flags():
    articles = [
        {"title": "CBI raids company headquarters in loan fraud probe"},
    ]
    analysis = analyze_news_sentiment("TESTSYM", articles)
    assert analysis["sentiment"] == "CAUTION"
    assert analysis["sentiment_score"] < 0
    assert len(analysis["red_flags"]) >= 1
    assert "Caution" in analysis["summary_badge"]


def test_enrich_candidate_with_news():
    cand = {
        "symbol": "MOTHERSON",
        "entry": 164.45,
        "stop_loss": 162.81,
        "score": 80,
    }
    enriched = enrich_candidate_with_news(cand)
    assert "news_sentiment" in enriched
    assert "news_badge" in enriched
    assert "news_headlines" in enriched
    assert isinstance(enriched["news_headlines"], list)


def test_company_news_analyzer_runs_when_invoked_as_script():
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "news_analysis" / "company_news_analyzer.py"

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "attempted relative import with no known parent package" not in result.stderr
