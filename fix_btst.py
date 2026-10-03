import re

file_path = "src/scanners/btst_smart_exit_strategy.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

addition = """
# ──────────────────────────────────────────────────────────────
# AUTOMATED TELEGRAM EXIT MONITOR
# ──────────────────────────────────────────────────────────────

def run_automated_exit_monitor():
    \"\"\"Run the automated exit Monitor for BTST.\"\"\"
    import glob
    import os
    from dotenv import load_dotenv
    import requests

    load_dotenv()
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    print("Running BTST Exit Monitor...")
    
    # 1. Find the latest BTST log
    log_dir = Path("logs")
    if not log_dir.exists():
        print("No logs directory found!")
        return

    json_files = list(log_dir.glob("*btst*.json")) + list(Path("data").glob("*btst*.json"))
    if not json_files:
        print("No BTST JSON scans found to calculate exit for!")
        return

    # sort by modified time
    latest_log = max(json_files, key=lambda f: f.stat().st_mtime)
    print(f"Latest BTST scan file: {latest_log}")

    try:
        with open(latest_log, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return

    candidates = []
    if "results" in data:
        candidates = data["results"].get("stocks", []) + data["results"].get("index", [])
    elif "candidates" in data:
        candidates = data["candidates"]

    if not candidates:
        print("No candidates found in the log.")
        return

    msg = "🎯 <b>BTST SMART EXIT PLAYBOOK (MORNING ALERT)</b>\n"
    msg += "<i>Avoid market traps, follow these rules exactly!</i>\n\n"

    for c in candidates:
        if isinstance(c, dict) and "symbol" in c:
            sym = c.get("symbol", "")
            ltp = c.get("ltp", 0.0)
            sl = c.get("powerful_sl", c.get("sl", ltp * 0.85)) # Fallback SL if powerful_sl wasn't recorded
            
            msg += f"<b>🏦 {sym} ({c.get('type', 'EQ')} - STRIKE {c.get('strike', 'N/A')})</b>\n"
            msg += f"• <b>Entry (Yesterday):</b> ₹{ltp}\n"
            msg += f"• <b>Powerful SL (Danger Line):</b> ₹{sl}\n"
            msg += f"• <b>Roll (Cost-to-Cost) Trigger:</b> &lt; ₹{ltp * 0.95:.1f}\n"
            msg += f"📋 <i>Strategy today:</i>\n"
            msg += f"   ✅ Gap Up (>₹{ltp * 1.02:.1f}): Lock Profit immediately!\n"
            msg += f"   ✓ Flat (₹{ltp}): Keep 30%, Exit 70% cost-to-cost.\n"
            msg += f"   ⚠️ Gap Down (&lt;₹{ltp}): Execute ROLLING if above ₹{sl}.\n\n"

    msg += "⚠️ <b>CRUCIAL:</b> No subjective trading. If it crosses Powerful SL, you must exit.\n"
    
    if bot_token and chat_id:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "HTML"
        }
        res = requests.post(url, data=payload, timeout=10)
        if res.status_code == 200:
            print("Telegram alert sent successfully!")
        else:
            print(f"Telegram alert failed: {res.text}")
    else:
        print("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set! Printing to console instead:")
        print(msg.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "").replace("&lt;", "<"))
"""

if "# ──────────────────────────────────────────────────────────────\n# AUTOMATED TELEGRAM EXIT MONITOR" not in content:
    content = content.replace(
        "# ──────────────────────────────────────────────────────────────\n# MAIN\n# ──────────────────────────────────────────────────────────────",
        addition + "\n\n# ──────────────────────────────────────────────────────────────\n# MAIN\n# ──────────────────────────────────────────────────────────────"
    )

    # Modify the __main__ block
    old_main = """if __name__ == "__main__":
    print_btst_exit_guide()
    print_action_checklist()"""
    
    new_main = """if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--cron":
        # Being run from crontab at 9:12 AM
        run_automated_exit_monitor()
    else:
        # User running interactively
        print_btst_exit_guide()
        print_action_checklist()"""

    content = content.replace(old_main, new_main)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Successfully patched btst_smart_exit_strategy.py")
else:
    print("Already patched")
