#!/usr/bin/env python3
"""
Smart Hero Zero Wrapper
=======================
Runs daily via cron but ONLY executes the actual scanner on REAL expiry days.
Handles holiday shifts automatically (NIFTY: Tue→Mon, SENSEX: Thu→Wed).
"""

import sys
import subprocess
import json
from datetime import datetime, date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Load NSE holidays
def load_nse_holidays() -> set[date]:
    holidays = set()
    h_path = ROOT / "trader-in" / "holidays.json"
    if h_path.exists():
        try:
            data = json.loads(h_path.read_text(encoding="utf-8"))
            for item in data.get("CM", []):
                td = item.get("tradingDate")
                if td:
                    holidays.add(datetime.strptime(td, "%d-%b-%Y").date())
        except Exception:
            pass
    # Fallback 2026 holidays
    if not holidays:
        holidays = {
            date(2026, 1, 26), date(2026, 3, 3), date(2026, 3, 31),
            date(2026, 4, 14), date(2026, 5, 1), date(2026, 10, 20),
            date(2026, 11, 10), date(2026, 11, 24), date(2026, 12, 25)
        }
    return holidays


def is_nifty_expiry_day(check_dt: datetime = None) -> tuple[bool, str]:
    """
    Check if today is NIFTY weekly expiry day.
    Normal: Tuesday (weekday 1)
    Holiday shift: Monday (weekday 0) if Tuesday is holiday
    Returns: (should_run, reason)
    """
    if check_dt is None:
        check_dt = datetime.now()
    today = check_dt.date()
    weekday = check_dt.weekday()
    holidays = load_nse_holidays()

    # Today is holiday → market closed
    if today in holidays:
        return False, f"Today ({today}) is NSE holiday"

    # Case A: Standard Tuesday Expiry
    if weekday == 1:  # Tuesday
        return True, "Standard Tuesday expiry"

    # Case B: Monday but Tuesday is holiday → Shift to Monday
    if weekday == 0:  # Monday
        tomorrow = today + timedelta(days=1)
        if tomorrow in holidays:
            return True, f"Tuesday ({tomorrow}) is holiday → Expiry shifted to Monday"

    # Case C: Any other day
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return False, f"Today is {day_names[weekday]} — NIFTY expiry only on Tuesday (or Monday if Tue holiday)"


def is_sensex_expiry_day(check_dt: datetime = None) -> tuple[bool, str]:
    """
    Check if today is SENSEX weekly expiry day.
    Normal: Thursday (weekday 3)
    Holiday shift: Wednesday (weekday 2) if Thursday is holiday
    Returns: (should_run, reason)
    """
    if check_dt is None:
        check_dt = datetime.now()
    today = check_dt.date()
    weekday = check_dt.weekday()
    holidays = load_nse_holidays()

    # Today is holiday → market closed
    if today in holidays:
        return False, f"Today ({today}) is NSE holiday"

    # Case A: Standard Thursday Expiry
    if weekday == 3:  # Thursday
        return True, "Standard Thursday expiry"

    # Case B: Wednesday but Thursday is holiday → Shift to Wednesday
    if weekday == 2:  # Wednesday
        tomorrow = today + timedelta(days=1)
        if tomorrow in holidays:
            return True, f"Thursday ({tomorrow}) is holiday → Expiry shifted to Wednesday"

    # Case C: Any other day
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return False, f"Today is {day_names[weekday]} — SENSEX expiry only on Thursday (or Wed if Thu holiday)"


def run_scanner(script_name: str, args: list[str]) -> int:
    """Execute the actual scanner script with given arguments."""
    script_path = ROOT / "src" / "scanners" / script_name
    cmd = [sys.executable, str(script_path)] + args
    print(f"🚀 Executing: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=False, text=True, timeout=300)
        return result.returncode
    except subprocess.TimeoutExpired:
        print(f"❌ {script_name} timed out after 5 minutes")
        return 1
    except Exception as e:
        print(f"❌ Failed to execute {script_name}: {e}")
        return 1


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Smart Hero Zero Wrapper - Runs only on actual expiry days")
    parser.add_argument("--symbol", choices=["NIFTY", "SENSEX", "BOTH"], default="BOTH",
                        help="Which symbol to run (default: BOTH)")
    parser.add_argument("--dry-run", action="store_true", help="Check expiry logic without running scanner")
    parser.add_argument("--force", action="store_true", help="Force run regardless of expiry day")
    args = parser.parse_args()

    now = datetime.now()
    today_str = now.strftime("%A, %d-%b-%Y %H:%M IST")
    print("=" * 70)
    print(f"🤖 SMART HERO ZERO WRAPPER — {today_str}")
    print("=" * 70)

    if args.force:
        print("⚡ FORCE MODE: Bypassing expiry day check")
        nifty_run, nifty_reason = True, "FORCED"
        sensex_run, sensex_reason = True, "FORCED"
    else:
        # Check NIFTY
        if args.symbol in ["NIFTY", "BOTH"]:
            nifty_run, nifty_reason = is_nifty_expiry_day(now)
            status = "✅ WILL RUN" if nifty_run else "⏭️ SKIP"
            print(f"\n📊 NIFTY: {status} — {nifty_reason}")
        else:
            nifty_run, nifty_reason = False, "Not requested"

        # Check SENSEX
        if args.symbol in ["SENSEX", "BOTH"]:
            sensex_run, sensex_reason = is_sensex_expiry_day(now)
            status = "✅ WILL RUN" if sensex_run else "⏭️ SKIP"
            print(f"\n📊 SENSEX: {status} — {sensex_reason}")
        else:
            sensex_run, sensex_reason = False, "Not requested"

    if args.dry_run:
        print("\n🧪 DRY RUN: Exiting without executing scanners")
        return 0

    # Execute NIFTY scanner
    if args.symbol in ["NIFTY", "BOTH"] and nifty_run:
        print(f"\n{'='*70}")
        print("🚀 EXECUTING NIFTY HERO ZERO SCANNER")
        print(f"{'='*70}")
        nifty_args = sys.argv[1:]  # Pass through remaining args
        nifty_args = [a for a in nifty_args if a not in ["--symbol", "NIFTY", "BOTH", "--dry-run", "--force"]]
        # Default NIFTY args
        if "--force" not in nifty_args:
            nifty_args.append("--force")  # Override scanner's own expiry check
        ret = run_scanner("nifty_hero_zero_expiry_scanner.py", nifty_args)
        if ret != 0:
            print(f"❌ NIFTY scanner exited with code {ret}")

    # Execute SENSEX scanner
    if args.symbol in ["SENSEX", "BOTH"] and sensex_run:
        print(f"\n{'='*70}")
        print("🚀 EXECUTING SENSEX HERO ZERO SCANNER")
        print(f"{'='*70}")
        sensex_args = sys.argv[1:]
        sensex_args = [a for a in sensex_args if a not in ["--symbol", "NIFTY", "BOTH", "--dry-run", "--force"]]
        if "--force" not in sensex_args:
            sensex_args.append("--force")
        # Add --auto-gtt for SENSEX on expiry days (wrapper controls GTT deployment)
        if "--auto-gtt" not in sensex_args:
            sensex_args.append("--auto-gtt")
        ret = run_scanner("sensex_hero_zero_expiry_scanner.py", sensex_args)
        if ret != 0:
            print(f"❌ SENSEX scanner exited with code {ret}")

    if not nifty_run and not sensex_run:
        print("\n📭 No scanners executed today (not an expiry day)")

    print(f"\n{'='*70}")
    print("✅ SMART WRAPPER COMPLETE")
    print(f"{'='*70}")
    return 0


if __name__ == "__main__":
    sys.exit(main())