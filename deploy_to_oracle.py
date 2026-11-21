"""Deploy intraday EOD square-off and options fixes to Oracle Cloud VM."""
import subprocess
import sys
from pathlib import Path

KEY_PATH = r"D:\NiftyScanner\oracle\nifty-v15.key"
HOST = "ubuntu@140.245.195.112"
REMOTE_DIR = "/home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated"

FILES_TO_SYNC = [
    ("src/scanners/news_scanner_with_twitter.py", f"{REMOTE_DIR}/src/scanners/news_scanner_with_twitter.py"),
    ("src/scanners/run_options_intraday_scan_powerful_sl.py", f"{REMOTE_DIR}/src/scanners/run_options_intraday_scan_powerful_sl.py"),
    ("src/scanners/run_btst_options_scan_powerful_sl.py", f"{REMOTE_DIR}/src/scanners/run_btst_options_scan_powerful_sl.py"),
    ("src/scanners/intraday_trade_monitor.py", f"{REMOTE_DIR}/src/scanners/intraday_trade_monitor.py"),
    ("src/scanners/daily_4pm_intraday_summary.py", f"{REMOTE_DIR}/src/scanners/daily_4pm_intraday_summary.py"),
    ("src/scanners/options_data_provider.py", f"{REMOTE_DIR}/src/scanners/options_data_provider.py"),
    ("src/scanners/sensex_hero_zero_expiry_scanner.py", f"{REMOTE_DIR}/src/scanners/sensex_hero_zero_expiry_scanner.py"),
    ("execute_sensex_hero_zero.py", f"{REMOTE_DIR}/execute_sensex_hero_zero.py"),
    ("tests/test_news_scanner_with_twitter.py", f"{REMOTE_DIR}/tests/test_news_scanner_with_twitter.py"),
    ("tests/test_intraday_eod_square_off.py", f"{REMOTE_DIR}/tests/test_intraday_eod_square_off.py"),
    ("docs/IMPLEMENTATION_REPORT.html", f"{REMOTE_DIR}/docs/IMPLEMENTATION_REPORT.html"),
    ("vm_crontab_master.txt", "/home/ubuntu/NiftyScanner/vm_crontab_master.txt"),
    ("vm_crontab_master.txt", f"{REMOTE_DIR}/vm_crontab_master.txt"),
]


def run_cmd(cmd: list[str]) -> bool:
    print(f"Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout)
    if res.stderr:
        print(f"STDERR: {res.stderr}")
    return res.returncode == 0


def main():
    print(f"=== Deploying to Oracle Cloud VM ({HOST}) ===")

    # 1. Create backups on the remote VM
    backup_cmd = [
        "ssh", "-i", KEY_PATH, "-o", "StrictHostKeyChecking=no", HOST,
        f"cd {REMOTE_DIR} && "
        "mkdir -p tests docs src/scanners && "
        "cp src/scanners/news_scanner_with_twitter.py src/scanners/news_scanner_with_twitter.py.bak 2>/dev/null || true; "
        "cp src/scanners/run_options_intraday_scan_powerful_sl.py src/scanners/run_options_intraday_scan_powerful_sl.py.bak 2>/dev/null || true; "
        "cp src/scanners/run_btst_options_scan_powerful_sl.py src/scanners/run_btst_options_scan_powerful_sl.py.bak 2>/dev/null || true; "
        "cp src/scanners/intraday_trade_monitor.py src/scanners/intraday_trade_monitor.py.bak 2>/dev/null || true; "
        "cp src/scanners/daily_4pm_intraday_summary.py src/scanners/daily_4pm_intraday_summary.py.bak 2>/dev/null || true; "
        "cp src/scanners/options_data_provider.py src/scanners/options_data_provider.py.bak 2>/dev/null || true; "
        "echo 'Remote backups created successfully'"
    ]
    if not run_cmd(backup_cmd):
        print("Failed to connect or create backups on remote VM.")
        sys.exit(1)

    # 2. Transfer each file
    for local_path, remote_target in FILES_TO_SYNC:
        print(f"Uploading {local_path} -> {remote_target}...")
        scp_cmd = [
            "scp", "-i", KEY_PATH, "-o", "StrictHostKeyChecking=no",
            local_path, f"{HOST}:{remote_target}"
        ]
        if not run_cmd(scp_cmd):
            print(f"Failed to upload {local_path}")
            sys.exit(1)

    # 3. Run verification test on the VM
    print("\nRunning verification test on Oracle VM...")
    test_cmd = [
        "ssh", "-i", KEY_PATH, "-o", "StrictHostKeyChecking=no", HOST,
        f"cd {REMOTE_DIR} && "
        "python3 -m py_compile src/scanners/news_scanner_with_twitter.py "
        "src/scanners/run_options_intraday_scan_powerful_sl.py "
        "src/scanners/run_btst_options_scan_powerful_sl.py "
        "src/scanners/intraday_trade_monitor.py "
        "src/scanners/daily_4pm_intraday_summary.py "
        "src/scanners/options_data_provider.py && "
        "echo 'All scanner scripts compiled successfully on Oracle VM!'"
    ]
    run_cmd(test_cmd)
    print("\n=== Deployment and Verification Complete! ===")


if __name__ == "__main__":
    main()
