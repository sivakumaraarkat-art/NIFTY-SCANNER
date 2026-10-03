import re
import os

path2 = "src/scanners/run_btst_options_scan_powerful_sl.py"
with open(path2, "r", encoding="utf-8") as f:
    text = f.read()

new_import = """import sys
import json

# Add project root to path so we can import telegram_alerts
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from telegram_alerts.options_alert_sender import send_options_telegram_alerts"""

text = text.replace("import sys\nimport json", new_import, 1)

trigger_target = """    print(f"\n✅ Execution log saved: {log_file}\n")"""
trigger_new = """    print(f"\n✅ Execution log saved: {log_file}\n")

    # Send Telegram Alerts
    print("[*] Dispatching alerts to Telegram...")
    send_options_telegram_alerts(btst_candidates, strategy_name="🌙 BTST OVERNIGHT")
    print("✅ Telegram alerts sent successfully!")"""

text = text.replace(trigger_target, trigger_new, 1)

with open(path2, "w", encoding="utf-8") as f:
    f.write(text)

print("Patched BTST scanner!")
