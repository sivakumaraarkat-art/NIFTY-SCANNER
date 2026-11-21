"""
run_timemachine_cli_tests.py
============================
Calls timemachine.main directly with simulated argv for Suzlon and Cochin Shipyard
across multiple strategic scenarios. Windows console UTF-8 safe.
"""

import sys
import io
import os
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr

# Force UTF-8 on Windows terminal to prevent UnicodeEncodeError for ₹ (INR symbol)
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
    print(f"RUNNING SCENARIO: {safe_title}")
    print(f"Command arguments: {' '.join(args)}")
    print("=" * 80)

    buf = io.StringIO()
    try:
        with redirect_stdout(buf), redirect_stderr(buf):
            exit_code = timemachine.main(args)
        out = buf.getvalue()
        # Cleanly display
        safe_out = out.replace("\u20b9", "INR ")
        try:
            print(safe_out)
        except UnicodeEncodeError:
            print(safe_out.encode("ascii", errors="replace").decode("ascii"))
    except Exception as e:
        print(f"Error or Warning during run: {e}")
        out = buf.getvalue()
        if out:
            safe_out = out.replace("\u20b9", "INR ")
            try:
                print(safe_out)
            except Exception:
                print(safe_out.encode("ascii", errors="replace").decode("ascii"))
    print()

if __name__ == "__main__":
    print("================================================================================")
    print("INDIAN SKILLS TIME MACHINE: 10,000 MONTE CARLO REPLAY & 60-DAY SESSIONS AUDIT")
    print("================================================================================")
    print()

    # 1. SUZLON ENERGY — SCENARIO 1: Conservative Target T1 @ 58.50 (SL: 53.00)
    test_scenario(
        "SUZLON ENERGY — Scenario 1: Conservative Breakeven Lock Target (T1: 58.50, SL: 53.00)",
        [
            "run",
            "--symbol", "SUZLON",
            "--date", "2026-11-06",
            "--entry", "55.80",
            "--stop", "53.00",
            "--target", "58.50",
            "--entry-time", "09:50",
            "--qty", "500",
            "--product", "CNC",
            "--seed", "19"
        ]
    )

    # 2. SUZLON ENERGY — SCENARIO 2: Swing Expansion Target T2 @ 62.00 (SL: 51.50)
    test_scenario(
        "SUZLON ENERGY — Scenario 2: Full Momentum Target (T2: 62.00, SL: 51.50)",
        [
            "run",
            "--symbol", "SUZLON",
            "--date", "2026-11-06",
            "--entry", "55.80",
            "--stop", "51.50",
            "--target", "62.00",
            "--entry-time", "09:50",
            "--qty", "1000",
            "--product", "CNC",
            "--seed", "19"
        ]
    )

    # 3. COCHIN SHIPYARD — SCENARIO 1: Averaging Down to Breakeven @ 1430 (SL: 1140)
    test_scenario(
        "COCHIN SHIPYARD — Scenario 1: Tranche 1 Average-Down to Breakeven (Target: 1430, SL: 1140)",
        [
            "run",
            "--symbol", "COCHINSHIP",
            "--date", "2026-11-06",
            "--entry", "1225.00",
            "--stop", "1140.00",
            "--target", "1430.00",
            "--entry-time", "09:50",
            "--qty", "25",
            "--product", "CNC",
            "--seed", "19"
        ]
    )

    # 4. COCHIN SHIPYARD — SCENARIO 2: Multi-Month 50K Profit Rally @ 1800 (SL: 1100)
    test_scenario(
        "COCHIN SHIPYARD — Scenario 2: Pre-Budget Defense 50K Profit Target (Target: 1800, SL: 1100)",
        [
            "run",
            "--symbol", "COCHINSHIP",
            "--date", "2026-11-06",
            "--entry", "1225.00",
            "--stop", "1100.00",
            "--target", "1800.00",
            "--entry-time", "09:50",
            "--qty", "25",
            "--product", "CNC",
            "--seed", "19"
        ]
    )
