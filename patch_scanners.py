import re
import os

# Intraday
path1 = "src/scanners/run_options_intraday_scan_powerful_sl.py"
with open(path1, "r", encoding="utf-8") as f:
    text = f.read()

import_str = """import json
from pathlib import Path"""
new_import = """import json
import sys
from pathlib import Path

# Add project root to path so we can import telegram_alerts
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from telegram_alerts.options_alert_sender import send_options_telegram_alerts"""
if "options_alert_sender" not in text:
    text = text.replace(import_str, new_import, 1)

trigger_target = """    print(f"\n✅ Execution log saved: {log_file}\n")"""
trigger_new = """    print(f"\n✅ Execution log saved: {log_file}\n")

    # Send Telegram Alerts
    print("[*] Dispatching alerts to Telegram...")
    send_options_telegram_alerts(results, strategy_name="INTRADAY OPTIONS")
    print("✅ Telegram alerts sent successfully!")"""
if "Dispatching alerts" not in text:
    text = text.replace(trigger_target, trigger_new)

with open(path1, "w", encoding="utf-8") as f:
    f.write(text)

# BTST
path2 = "src/scanners/run_btst_options_scan_powerful_sl.py"
with open(path2, "r", encoding="utf-8") as f:
    text = f.read()
    
if "options_alert_sender" not in text:
    text = text.replace(import_str, new_import, 1)

trigger_target2 = """    print(f"\n✅ Execution log saved: {log_file}\n")"""
trigger_new2 = """    print(f"\n✅ Execution log saved: {log_file}\n")

    # Send Telegram Alerts
    print("[*] Dispatching alerts to Telegram...")
    send_options_telegram_alerts(btst_candidates, strategy_name="🌙 BTST OVERNIGHT")
    print("✅ Telegram alerts sent successfully!")"""
if "Dispatching alerts" not in text:
    text = text.replace(trigger_target2, trigger_new2)

with open(path2, "w", encoding="utf-8") as f:
    f.write(text)

print("Patched both scanners!")
