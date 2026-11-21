"""
run_intraday_timemachine_tests.py
=================================
Runs india-timemachine on realistic INTRADAY (MIS) targets:
1. SUZLON Intraday Scalp: Entry 55.80, Stop 54.90, Target 56.70 (+0.90, ~1R)
2. COCHINSHIP Intraday Scalp: Entry 1298.00, Stop 1278.00, Target 1328.00 (+30.00, 1.5R)
3. RELIANCE Intraday ORB Breakout (Benchmark)
"""

import sys
import io
import os
from contextlib import redirect_stdout, redirect_stderr

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL_DIR = r"C:\Users\Siva Kumar\.claude-omniroute\skills\india-timemachine"
sys.path.insert(0, SKILL_DIR)

import timemachine

def test_scenario(title, args):
    safe_title = title.replace("\u20b9", "INR ")
    print("=" * 80)
    print(f"INTRADAY SCENARIO: {safe_title}")
    print("=" * 80)

    buf = io.StringIO()
    try:
        with redirect_stdout(buf), redirect_stderr(buf):
            timemachine.main(args)
        out = buf.getvalue().replace("\u20b9", "INR ")
        print(out)
    except Exception as e:
        print(f"Error: {e}")
        out = buf.getvalue().replace("\u20b9", "INR ")
        if out:
            print(out)
    print()

if __name__ == "__main__":
    print("INDIAN SKILLS: REALISTIC INTRADAY (MIS) SCENARIOS (SAME-DAY HIT PROBABILITY)")
    print()

    # 1. SUZLON Intraday Scalp (1R: +INR 0.90 / -INR 0.90)
    test_scenario(
        "SUZLON — Intraday MIS Scalp (+INR 0.90 Target vs -INR 0.90 Stop)",
        [
            "run",
            "--symbol", "SUZLON",
            "--date", "2026-11-06",
            "--entry", "55.80",
            "--stop", "54.90",
            "--target", "56.70",
            "--entry-time", "09:50",
            "--qty", "1000",
            "--product", "MIS",
            "--seed", "19"
        ]
    )

    # 2. COCHINSHIP Intraday Scalp (+INR 30.00 Target vs -INR 20.00 Stop)
    test_scenario(
        "COCHIN SHIPYARD — Intraday MIS Scalp (+INR 30.00 Target vs -INR 20.00 Stop)",
        [
            "run",
            "--symbol", "COCHINSHIP",
            "--date", "2026-11-06",
            "--entry", "1298.00",
            "--stop", "1278.00",
            "--target", "1328.00",
            "--entry-time", "09:50",
            "--qty", "100",
            "--product", "MIS",
            "--seed", "19"
        ]
    )
