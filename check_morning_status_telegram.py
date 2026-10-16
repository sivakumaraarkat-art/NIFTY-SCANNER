"""
check_morning_status_telegram.py
Audits Zerodha Morning Status and sends a beautifully formatted report to Telegram via portfolio bot.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
if str(ROOT / "telegram_alerts") not in sys.path:
    sys.path.insert(0, str(ROOT / "telegram_alerts"))

load_dotenv()

def _get_telegram_credentials():
    # Use Hero-Zero / Portfolio bot credentials if available, or fall back to main bot
    bot_token = os.getenv("HERO_ZERO_TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("HERO_ZERO_TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
    if bot_token and chat_id:
        return bot_token, chat_id

    cred_paths = [
        ROOT / ".credentials.json",
        ROOT / ".env",
        Path("/home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/.credentials.json")
    ]
    for p in cred_paths:
        if p.exists():
            try:
                if p.suffix == ".json":
                    data = json.load(open(p, "r", encoding="utf-8"))
                    tg = data.get("telegram", {})
                    if tg.get("bot_token") and tg.get("chat_id"):
                        return tg.get("bot_token"), tg.get("chat_id")
            except Exception:
                continue
    return bot_token, chat_id

def send_telegram_status():
    token, chat_id = _get_telegram_credentials()
    if not token or not chat_id:
        print("⚠️ Telegram credentials not found!")
        return False

    # Run status check logic
    try:
        from kiteconnect import KiteConnect
        api_key = os.getenv("ZERODHA_API_KEY")
        token_path = Path("/home/ubuntu/NiftyScanner/.kite_access_token")
        if not token_path.exists():
            token_path = ROOT / ".kite_access_token"

        access_token = token_path.read_text(encoding="utf-8").strip() if token_path.exists() else os.getenv("ZERODHA_ACCESS_TOKEN", "")

        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)

        gtt_orders = kite.get_gtts()
        positions = kite.positions()
        net_positions = positions.get("net", [])
        active_positions = [p for p in net_positions if p.get("quantity", 0) != 0]

    except Exception as e:
        gtt_orders = []
        active_positions = []
        err_msg = str(e)

    now_str = datetime.now().strftime("%d-%b-%Y %H:%M:%S IST")

    msg = f"""<b>🌅 MORNING PORTFOLIO & MARKET STATUS AUDIT</b>
<code>📅 {now_str}</code>
──────────────────────
🛡️ <b>Active GTT Orders:</b> <code>{len(gtt_orders)}</code>
📊 <b>Open Net Positions:</b> <code>{len(active_positions)}</code>
"""

    if active_positions:
        msg += "\n<b>Active Positions:</b>\n"
        for p in active_positions:
            msg += f"• <code>{p.get('tradingsymbol')}</code> | Qty: <code>{p.get('quantity')}</code> | P&L: <b>₹{p.get('pnl', 0):.2f}</b>\n"
    else:
        msg += "\n✅ <i>No open overnight positions. Portfolio is clean and ready for fresh scans!</i>\n"

    msg += "──────────────────────\n"
    msg += "🚀 <i>Automated Morning Audit by Portfolio Bot</i>"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "HTML"
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        res_json = resp.json()
        if res_json.get("ok"):
            print("✅ Morning status message sent to Portfolio Telegram bot successfully!")
            return True
        else:
            print(f"❌ Telegram API Error: {res_json}")
            return False
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")
        return False

if __name__ == "__main__":
    send_telegram_status()
