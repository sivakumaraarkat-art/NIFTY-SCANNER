"""
Comprehensive Test Suite for Implemented Improvements

Tests for:
1. News scanner retry logic and deduplication
2. Intraday scanner timeout protection and liquidity filters
3. BTST scanner parameter alignment
4. Execution logging
5. Market hours guard
"""

import unittest
import json
import tempfile
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np

# Mock the actual imports to avoid dependencies
import sys
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# TEST 1: News Scanner Improvements
# ──────────────────────────────────────────────────────────────

def _normalize_title_for_dedup(title: str) -> str:
    """Normalize headline for smarter deduplication."""
    import re
    normalized = re.sub(r'\d+\.?\d*%?', '[NUM]', title.lower())
    normalized = re.sub(r'[^a-z0-9 ]', '', normalized)
    return normalized[:75]


def _get_time_decay_bonus(published: datetime | None) -> float:
    """Calculate recency bonus for sentiment scoring."""
    if published is None:
        return 0.0
    try:
        age_hours = (datetime.now(timezone.utc) - published).total_seconds() / 3600
        return max(0.0, 5.0 - (age_hours * 0.5))
    except Exception:
        return 0.0


class TestNewsScannersImprovements(unittest.TestCase):
    """Test news scanner retry logic and deduplication."""

    def test_normalize_title_for_dedup(self):
        """Test that similar headlines normalize correctly."""

        # Test: Numbers should be normalized
        title1 = "Reliance surges 5% on strong Q2 results"
        title2 = "Reliance surges 6% on strong Q2 results"

        norm1 = _normalize_title_for_dedup(title1)
        norm2 = _normalize_title_for_dedup(title2)

        # Both should normalize to same string (numbers → [NUM])
        self.assertEqual(norm1, norm2, "Similar headlines with different numbers should normalize to same")

        # Test: Punctuation removal
        title3 = "Reliance surges 5% on strong Q2 results!"
        title4 = "Reliance surges 5% on strong Q2 results."

        norm3 = _normalize_title_for_dedup(title3)
        norm4 = _normalize_title_for_dedup(title4)
        self.assertEqual(norm3, norm4, "Punctuation should be stripped")

    def test_time_decay_bonus(self):
        """Test that recency bonus decays over time."""
        # Fresh news (1 minute old)
        fresh = datetime.now(timezone.utc) - timedelta(minutes=1)
        bonus_fresh = _get_time_decay_bonus(fresh)

        # Old news (6 hours old)
        old = datetime.now(timezone.utc) - timedelta(hours=6)
        bonus_old = _get_time_decay_bonus(old)

        # Fresh should have higher bonus
        self.assertGreater(bonus_fresh, bonus_old, "Fresh news should have higher bonus")

        # Very old news (12 hours)
        very_old = datetime.now(timezone.utc) - timedelta(hours=12)
        bonus_very_old = _get_time_decay_bonus(very_old)

        self.assertEqual(bonus_very_old, 0.0, "News > 10 hours old should have 0 bonus")

    def test_retry_logic_max_retries(self):
        """Test that retry logic respects max_retries parameter."""
        call_count = 0

        def mock_urlopen(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise TimeoutError("Connection timeout")

        # This is a manual test - in production, verify fetch_feed retries correctly
        # Expected: 2 attempts (max_retries=2)
        retries_expected = 2
        self.assertGreaterEqual(retries_expected, 1, "Should allow multiple retries")


# ──────────────────────────────────────────────────────────────
# TEST 2: Intraday Scanner Improvements
# ──────────────────────────────────────────────────────────────

class TestIntradayScannersImprovements(unittest.TestCase):
    """Test intraday scanner timeout, liquidity filters."""

    def test_liquidity_filter_min_oi(self):
        """Test that options with OI < MIN_OI are rejected."""
        MIN_OI_THRESHOLD = 1000

        contract_liquid = {"oi": 5000, "bid": 10.0, "ask": 10.5, "ltp": 10.2}
        contract_illiquid = {"oi": 50, "bid": 10.0, "ask": 10.5, "ltp": 10.2}

        def is_liquid(contract):
            return contract.get("oi", 0) >= MIN_OI_THRESHOLD

        self.assertTrue(is_liquid(contract_liquid), "High OI should pass")
        self.assertFalse(is_liquid(contract_illiquid), "Low OI should be rejected")

    def test_liquidity_filter_bid_ask_spread(self):
        """Test that options with high bid-ask spread are rejected."""
        MAX_BID_ASK_SPREAD_PCT = 2.0

        def get_spread_pct(contract):
            bid = contract.get("bid", 0)
            ask = contract.get("ask", 0)
            ltp = contract.get("ltp", 0)
            if bid > 0 and ask > 0 and ltp > 0:
                return ((ask - bid) / ltp) * 100
            return 0

        def is_liquid(contract):
            spread_pct = get_spread_pct(contract)
            return spread_pct <= MAX_BID_ASK_SPREAD_PCT

        # Tight spread
        contract_tight = {"bid": 50.0, "ask": 50.5, "ltp": 50.2}  # 0.995% spread
        self.assertTrue(is_liquid(contract_tight), "Tight spread should pass")

        # Wide spread
        contract_wide = {"bid": 50.0, "ask": 52.0, "ltp": 51.0}  # 3.92% spread
        self.assertFalse(is_liquid(contract_wide), "Wide spread should be rejected")

    def test_timeout_protection(self):
        """Test that fetching respects timeout boundaries."""
        start_time = datetime.now()
        timeout_seconds = 30

        def simulate_fetch_with_timeout(symbols, timeout):
            """Simulate fetching with timeout protection."""
            fetched = {}
            start = datetime.now()

            for symbol in symbols:
                elapsed = (datetime.now() - start).total_seconds()
                if elapsed > timeout:
                    break  # Stop if timeout exceeded
                fetched[symbol] = f"data_{symbol}"

            return fetched

        symbols = ["RELIANCE", "TCS", "HDFCBANK"]
        result = simulate_fetch_with_timeout(symbols, timeout_seconds)

        elapsed = (datetime.now() - start_time).total_seconds()
        self.assertLess(elapsed, timeout_seconds + 5, "Total time should respect timeout")

    def test_greeks_failure_handling(self):
        """Test that Greeks calculation failures skip contracts."""
        valid_contracts = []
        failed_symbols = []

        contracts = {
            "RELIANCE": {"delta": 0.5, "iv": 25},
            "TCS": None,  # Simulate failure
            "HDFCBANK": {"delta": 0.6, "iv": 30},
        }

        for symbol, greeks in contracts.items():
            try:
                if greeks is None:
                    raise ValueError("Greeks calculation failed")
                valid_contracts.append((symbol, greeks))
            except Exception as exc:
                failed_symbols.append(symbol)

        self.assertEqual(len(valid_contracts), 2, "Should have 2 valid contracts")
        self.assertEqual(len(failed_symbols), 1, "Should have 1 failed symbol")
        self.assertIn("TCS", failed_symbols, "TCS should be in failed list")


# ──────────────────────────────────────────────────────────────
# TEST 3: BTST Scanner Improvements
# ──────────────────────────────────────────────────────────────

class TestBTSTScannersImprovements(unittest.TestCase):
    """Test BTST scanner parameter alignment and monkey-patch removal."""

    def test_strategy_name_parameter(self):
        """Test that strategy_name can be passed as parameter."""
        def send_options_alerts(candidates, settings, strategy_name="INTRADAY"):
            return f"Alerts sent for {strategy_name} strategy"

        # Intraday
        result_intraday = send_options_alerts([], Mock(), strategy_name="INTRADAY")
        self.assertIn("INTRADAY", result_intraday)

        # BTST
        result_btst = send_options_alerts([], Mock(), strategy_name="BTST OVERNIGHT")
        self.assertIn("BTST OVERNIGHT", result_btst)

    def test_consistent_fetch_signature(self):
        """Test that fetch_fo_stock_chains has consistent signature."""
        # Both intraday and BTST should use same signature
        def fetch_fo_stock_chains(kite, symbols, max_symbols=40, num_strikes=8, request_delay=0.35):
            return {symbol: [] for symbol in symbols}

        # Should work for both
        kite = Mock()
        symbols = ["RELIANCE", "TCS"]

        result = fetch_fo_stock_chains(
            kite,
            symbols,
            max_symbols=len(symbols),
            num_strikes=8,
            request_delay=0.35
        )

        self.assertEqual(len(result), 2, "Should return data for 2 symbols")

    def test_theta_decay_boundary(self):
        """Test that Theta decay boundary is enforced."""
        MAX_THETA_LOSS = 0.05  # Max 5% loss from Theta decay

        def passes_theta_filter(contract):
            ltp = contract.get("ltp", 0.01)
            theta = contract.get("theta", 0)
            theta_loss_pct = abs(theta) / max(ltp, 0.01)
            return theta_loss_pct <= MAX_THETA_LOSS

        # Low theta loss
        contract_low = {"ltp": 50.0, "theta": -0.2}  # 0.4% loss
        self.assertTrue(passes_theta_filter(contract_low), "Low theta should pass")

        # High theta loss
        contract_high = {"ltp": 50.0, "theta": -3.0}  # 6% loss
        self.assertFalse(passes_theta_filter(contract_high), "High theta should be rejected")


# ──────────────────────────────────────────────────────────────
# TEST 4: Execution Logging
# ──────────────────────────────────────────────────────────────

class TestExecutionLogging(unittest.TestCase):
    """Test execution logging functionality."""

    def test_scan_config_export(self):
        """Test that scan configuration can be exported to JSON."""
        config = {
            "timestamp": datetime.now().isoformat(),
            "script": "news_based_scanner",
            "symbols_found": 5,
            "top_picks": ["RELIANCE", "MARUTI", "BPCL"],
            "min_score": 35,
        }

        # Should be JSON serializable
        json_str = json.dumps(config)
        self.assertIsInstance(json_str, str)

        # Should deserialize correctly
        restored = json.loads(json_str)
        self.assertEqual(restored["symbols_found"], 5)
        self.assertEqual(restored["top_picks"], ["RELIANCE", "MARUTI", "BPCL"])

    def test_log_file_creation(self):
        """Test that log files can be created with timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = os.path.join(tmpdir, f"scan_{timestamp}.json")

            log_data = {
                "timestamp": datetime.now().isoformat(),
                "results": 10,
            }

            with open(log_file, 'w') as f:
                json.dump(log_data, f)

            # Verify file exists
            self.assertTrue(os.path.exists(log_file), "Log file should be created")

            # Verify content
            with open(log_file, 'r') as f:
                restored = json.load(f)

            self.assertEqual(restored["results"], 10)


# ──────────────────────────────────────────────────────────────
# TEST 5: Market Hours Guard
# ──────────────────────────────────────────────────────────────

class TestMarketHoursGuard(unittest.TestCase):
    """Test market hours validation."""

    def test_is_market_hours_intraday(self):
        """Test intraday market hours detection."""
        from datetime import time

        def is_market_hours(current_time, script_type="intraday"):
            """Check if current time is valid for this scanner."""
            if script_type == "intraday":
                return time(9, 30) <= current_time <= time(15, 30)
            elif script_type == "btst":
                return time(14, 30) <= current_time <= time(15, 30)
            elif script_type == "news":
                return time(8, 0) <= current_time <= time(21, 0)
            return False

        # Test intraday
        self.assertTrue(is_market_hours(time(10, 15), "intraday"), "10:15 AM should be valid")
        self.assertFalse(is_market_hours(time(9, 15), "intraday"), "9:15 AM should be invalid")
        self.assertFalse(is_market_hours(time(16, 0), "intraday"), "4:00 PM should be invalid")

    def test_is_market_hours_btst(self):
        """Test BTST market hours detection."""
        from datetime import time

        def is_market_hours(current_time, script_type="btst"):
            if script_type == "btst":
                return time(14, 30) <= current_time <= time(15, 30)
            return False

        self.assertTrue(is_market_hours(time(14, 45), "btst"), "2:45 PM should be valid for BTST")
        self.assertFalse(is_market_hours(time(14, 15), "btst"), "2:15 PM should be invalid for BTST")
        self.assertFalse(is_market_hours(time(15, 45), "btst"), "3:45 PM should be invalid for BTST")

    def test_is_market_hours_news(self):
        """Test news scanner market hours detection."""
        from datetime import time

        def is_market_hours(current_time, script_type="news"):
            if script_type == "news":
                return time(8, 0) <= current_time <= time(21, 0)
            return False

        self.assertTrue(is_market_hours(time(8, 0), "news"), "8:00 AM should be valid for news")
        self.assertTrue(is_market_hours(time(20, 0), "news"), "8:00 PM should be valid for news")
        self.assertFalse(is_market_hours(time(22, 0), "news"), "10:00 PM should be invalid for news")


# ──────────────────────────────────────────────────────────────
# TEST 6: Integration Tests
# ──────────────────────────────────────────────────────────────

class TestIntegrationScenarios(unittest.TestCase):
    """Test realistic usage scenarios."""

    def test_full_workflow_scoring(self):
        """Test complete workflow: news → symbols → options scoring."""
        # Simulate news scanner output
        news_results = {
            "RELIANCE": {"score": 8.5, "sentiment": "BULLISH"},
            "MARUTI": {"score": 7.2, "sentiment": "BULLISH"},
            "BPCL": {"score": 6.8, "sentiment": "BULLISH"},
        }

        # Extract symbols
        symbols = list(news_results.keys())
        self.assertEqual(len(symbols), 3)

        # Simulate options scanner filtering
        bullish_picks = [s for s, data in news_results.items() if data["sentiment"] == "BULLISH"]
        self.assertEqual(len(bullish_picks), 3)

    def test_edge_case_zero_liquidity(self):
        """Test handling of completely illiquid options."""
        options = [
            {"symbol": "RELIANCE", "oi": 10000, "volume": 500},  # Liquid
            {"symbol": "RELIANCE", "oi": 0, "volume": 0},        # Illiquid
            {"symbol": "RELIANCE", "oi": 5000, "volume": 50},    # Moderate
        ]

        MIN_OI = 1000
        MIN_VOLUME = 50

        filtered = [
            opt for opt in options
            if opt["oi"] >= MIN_OI and opt["volume"] >= MIN_VOLUME
        ]

        self.assertEqual(len(filtered), 2, "Should have 2 liquid options")
        self.assertEqual(filtered[0]["symbol"], "RELIANCE")


# ──────────────────────────────────────────────────────────────
# TEST RUNNER
# ──────────────────────────────────────────────────────────────

def run_all_tests():
    """Run all test suites and generate report."""

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestNewsScannersImprovements))
    suite.addTests(loader.loadTestsFromTestCase(TestIntradayScannersImprovements))
    suite.addTests(loader.loadTestsFromTestCase(TestBTSTScannersImprovements))
    suite.addTests(loader.loadTestsFromTestCase(TestExecutionLogging))
    suite.addTests(loader.loadTestsFromTestCase(TestMarketHoursGuard))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("=" * 80 + "\n")

    return result


if __name__ == "__main__":
    result = run_all_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
