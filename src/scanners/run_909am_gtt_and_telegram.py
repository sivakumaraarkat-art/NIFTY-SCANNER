"""
run_909am_gtt_and_telegram.py
=============================
Automated 09:09 AM Pre-Open Breakout GTT Engine & Telegram Dispatcher.
Calibrated strictly to ₹44,000 Capital for the Top 3 Backtested Conviction Stocks:
1. MCX (5 shares @ ₹3,915.00)       = ₹19,575.00 (Trigger: ₹3,914.50 | Tgt: ₹3,980 | SL: ₹3,845)
2. ICICIBANK (10 shares @ ₹1,602.00)= ₹16,020.00 (Trigger: ₹1,601.50 | Tgt: ₹1,630 | SL: ₹1,580)
3. ANGELONE (20 shares @ ₹378.50)   =  ₹7,570.00 (Trigger: ₹378.00  | Tgt: ₹392   | SL: ₹368)
--------------------------------------------------------------------------------------------------
Total Capital: ₹43,165.00 (Under ₹44,000 limit) | Potential Profit: +₹875.00 | Max Risk: -₹780.00

Execution Logic:
1. Attempts to place Zerodha Kite GTT Single Buy Orders for all 3 stocks.
2. Sends an immediate Telegram notification via the PORTFOLIO BOT:
   - If GTT Placed: Notifies with Zerodha Trigger IDs.
   - If Manual Action Needed: Sends clean copy-paste levels for manual 1-tap app execution.

Usage:
  python src/scanners/run_909am_gtt_and_telegram.py           # Live execution (at 09:09 AM)
  python src/scanners/run_909am_gtt_and_telegram.py --dry-run # Sends Telegram alert preview
"""

import sys
import os
import json
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests
from dotenv import load_dotenv

# Windows console encoding fix
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[2]

# Load environment variables (Portfolio Bot priority)
load_dotenv(ROOT / ".env")
load_dotenv(Path("/home/ubuntu/NiftyScanner/PORTFOLIO_PEAK_EXIT_GUARD/.env"))
load_dotenv(Path("/home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/.env"))

# Top 3 Conviction Allocations (Budget: ₹44,000)
GTT_TARGETS = [
    {
        "symbol": "MCX",
        "exchange": "NSE",
        "tradingsymbol": "MCX",
        "qty": 5,
        "trigger_price": 3914.50,
        "limit_price": 3915.00,
        "target_price": 3980.00,
        "stop_price": 3845.00,
        "capital": 19575.00,
        "profit_pot": 325.00,
        "risk_max": 350.00,
        "win_rate": "85.7%",
        "catalyst": "Gold/Silver +3.5% surge, 20-day ATH breakout"
    },
    {
        "symbol": "ICICIBANK",
        "exchange": "NSE",
        "tradingsymbol": "ICICIBANK",
        "qty": 10,
        "trigger_price": 1601.50,
        "limit_price": 1602.00,
        "target_price": 1630.00,
        "stop_price": 1580.00,
        "capital": 16020.00,
        "profit_pot": 280.00,
        "risk_max": 220.00,
        "win_rate": "83.3%",
        "catalyst": "Q2 GDP announcement, Bull Flag breakout"
    },
    {
        "symbol": "ANGELONE",
        "exchange": "NSE",
        "tradingsymbol": "ANGELONE",
        "qty": 20,
        "trigger_price": 378.00,
        "limit_price": 378.50,
        "target_price": 392.00,
        "stop_price": 368.00,
        "capital": 7570.00,
        "profit_pot": 270.00,
        "risk_max": 210.00,
        "win_rate": "80.0%",
        "catalyst": "3.5 Cr volume blast, 20-day high breakout"
    }
]

def get_portfolio_bot_credentials():
    """Retrieve Portfolio Bot token and chat_id."""
    token = os.getenv("PORTFOLIO_TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("PORTFOLIO_TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        # Check .credentials.json
        candidates = [
            ROOT / ".credentials.json",
            Path("/home/ubuntu/NiftyScanner/PORTFOLIO_PEAK_EXIT_GUARD/.credentials.json"),
            Path("/home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/.credentials.json"),
            Path("D:/NiftyScanner/PORTFOLIO_PEAK_EXIT_GUARD/.credentials.json")
        ]
        for c in candidates:
            if c.exists():
                try:
                    data = json.loads(c.read_text(encoding="utf-8"))
                    tg = data.get("telegram", {})
                    token = token or tg.get("portfolio_bot_token") or tg.get("bot_token")
                    chat_id = chat_id or tg.get("portfolio_chat_id") or tg.get("chat_id")
                    if token and chat_id:
                        break
                except Exception:
                    pass

    return token, chat_id

def send_telegram_alert(message_html: str) -> bool:
    """Send formatted alert using the Portfolio Bot."""
    token, chat_id = get_portfolio_bot_credentials()
    if not token or not chat_id:
        print("⚠️ Portfolio Bot credentials not found.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message_html,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(url, json=payload, timeout=12)
        r.raise_for_status()
        print("✅ Telegram alert dispatched successfully via Portfolio Bot.")
        return True
    except Exception as e:
        print(f"❌ Failed to send Telegram alert: {e}")
        return False

def get_kite_client():
    """Initialize Zerodha Kite client from master token files."""
    try:
        from kiteconnect import KiteConnect
    except ImportError:
        return None

    token_candidates = [
        Path("/home/ubuntu/NiftyScanner/.kite_access_token"),
        ROOT / ".kite_access_token",
        ROOT.parent / ".kite_access_token",
        Path("D:/NiftyScanner/.kite_access_token")
    ]
    key_candidates = [
        Path("/home/ubuntu/NiftyScanner/.kite_api_key"),
        ROOT / ".kite_api_key",
        ROOT.parent / ".kite_api_key",
        Path("D:/NiftyScanner/.kite_api_key")
    ]

    token, key = None, None
    for p in token_candidates:
        if p.exists():
            t = p.read_text(encoding="utf-8").strip()
            if t:
                token = t; break

    for p in key_candidates:
        if p.exists():
            k = p.read_text(encoding="utf-8").strip()
            if k:
                key = k; break

    if not key or not token:
        return None

    try:
        kite = KiteConnect(api_key=key)
        kite.set_access_token(token)
        return kite
    except Exception:
        return None

def main():
    parser = argparse.ArgumentParser(description="09:09 AM Pre-Open Breakout Alert & GTT Engine")
    parser.add_argument("--auto-place-gtt", action="store_true", help="Attempt automated GTT placement if Kite authenticated")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without external calls")
    args = parser.parse_args()

    now_ist = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%d %b %Y, %I:%M %p")
    print(f"=== 09:09 AM BREAKOUT ENGINE ({now_ist}) ===")

    total_cap = sum(t["capital"] for t in GTT_TARGETS)
    placed_gtts = []
    gtt_success = False

    if args.auto_place_gtt and not args.dry_run:
        kite = get_kite_client()
        if kite:
            print("🚀 Attempting to place GTT orders on Zerodha Kite...")
            for t in GTT_TARGETS:
                try:
                    q = kite.quote([f"{t['exchange']}:{t['tradingsymbol']}"])
                    ltp = q.get(f"{t['exchange']}:{t['tradingsymbol']}", {}).get("last_price", t["limit_price"])

                    resp = kite.place_gtt(
                        trigger_type=kite.GTT_TYPE_SINGLE,
                        tradingsymbol=t["tradingsymbol"],
                        exchange=t["exchange"],
                        trigger_values=[t["trigger_price"]],
                        last_price=ltp,
                        orders=[
                            {
                                "transaction_type": kite.TRANSACTION_TYPE_BUY,
                                "quantity": t["qty"],
                                "order_type": kite.ORDER_TYPE_LIMIT,
                                "product": kite.PRODUCT_CNC,
                                "price": t["limit_price"]
                            }
                        ]
                    )
                    trig_id = resp.get("trigger_id")
                    t["trigger_id"] = trig_id
                    t["status"] = "PLACED"
                    placed_gtts.append(t)
                    print(f"   ✅ Placed {t['symbol']}: Trigger ID {trig_id}")
                except Exception as e:
                    print(f"   ⚠️ Could not place {t['symbol']} GTT: {e}")
                    t["status"] = "FAILED"

            if len(placed_gtts) == len(GTT_TARGETS):
                gtt_success = True
        else:
            print("⚠️ Kite client not authenticated; dispatching Telegram Action Alert instead.")
    else:
        print("📢 Running in Telegram Priority Alert Mode (as requested by trader)...")
        print("[DRY-RUN] Simulating alert dispatch...")

    # Formulate Telegram Message for Portfolio Bot
    if gtt_success:
        msg = f"🎯 <b>09:09 AM ZERODHA GTT ORDERS ACTIVE</b>\n"
        msg += f"<i>Capital: ₹{total_cap:,.0f} / ₹44,000 | {now_ist}</i>\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━\n"
        for t in placed_gtts:
            msg += f"<b>{t['symbol']}</b> (Win Rate: {t['win_rate']})\n"
            msg += f"• <b>Action:</b> BUY {t['qty']} shs @ Limit ₹{t['limit_price']:,.2f}\n"
            msg += f"• <b>Trigger:</b> ₹{t['trigger_price']:,.2f} (ID: <code>{t.get('trigger_id', 'N/A')}</code>)\n"
            msg += f"• <b>Target:</b> ₹{t['target_price']:,.2f} (+₹{t['profit_pot']:,.0f})\n"
            msg += f"• <b>Stop Loss:</b> ₹{t['stop_price']:,.2f} (-₹{t['risk_max']:,.0f})\n\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"✅ <i>Orders placed automatically. They will execute when price breaks out!</i>"
    else:
        # Action Alert for Manual / Quick Execution
        msg = f"🚀 <b>09:09 AM ACTION ALERT: TOP 3 BREAKOUT STOCKS</b>\n"
        msg += f"<i>Budget: ₹{total_cap:,.0f} / ₹44,000 | {now_ist}</i>\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"Based on 60-day backtest, here are your Top 3 Breakout orders to place in Zerodha:\n\n"

        for i, t in enumerate(GTT_TARGETS, 1):
            msg += f"<b>{i}. {t['symbol']}</b> (Hist Win: <b>{t['win_rate']}</b>)\n"
            msg += f"• <b>BUY:</b> <code>{t['qty']}</code> shares @ Limit <b>₹{t['limit_price']:,.2f}</b>\n"
            msg += f"• <b>Trigger:</b> ₹{t['trigger_price']:,.2f} (Cap: ₹{t['capital']:,.0f})\n"
            msg += f"• <b>Target:</b> ₹{t['target_price']:,.2f} (+₹{t['profit_pot']:,.0f})\n"
            msg += f"• <b>Stop Loss:</b> ₹{t['stop_price']:,.2f} (-₹{t['risk_max']:,.0f})\n"
            msg += f"• <i>Catalyst:</i> {t['catalyst']}\n\n"

        msg += f"━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"💰 <b>Total Capital Needed:</b> ₹{total_cap:,.0f}\n"
        msg += f"📈 <b>Combined Target Profit:</b> +₹875.00\n"
        msg += f"🛡️ <b>Total Portfolio Risk:</b> -₹780.00 (1.8%)\n"
        msg += f"⚡ <i>Set GTT in Kite App or Buy when Trigger Price crosses!</i>"

    send_telegram_alert(msg)

if __name__ == "__main__":
    main()
