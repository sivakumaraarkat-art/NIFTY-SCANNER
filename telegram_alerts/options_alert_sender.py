import requests
import html
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_options_telegram_alerts(candidates, strategy_name="INTRADAY OPTIONS"):
    """
    Sends beautiful HTML formatted Telegram alerts for Options Scanners.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram keys not found in .env, skipping alerts.")
        return

    if not candidates:
        return

    # Header message
    emoji = "⚡" if "INTRADAY" in strategy_name else "🌙"
    header = f"<b>{emoji} {strategy_name} SCAN COMPLETE</b>\n"
    header += f"Found <b>{len(candidates)}</b> high-conviction setups.\n"
    header += f"<i>Protected by 4-Layer Powerful SL</i>"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": header, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"Failed to send header: {e}")
        return

    # Send up to top 3 to avoid spam
    for i, c in enumerate(candidates[:3], 1):
        target_emoji = "🎯" if c['score'] > 85 else "📈"
        
        opt_type_color = "🟢 CALL" if c.get('option_type', c.get('type', 'CE')) == "CE" else "🔴 PUT"
        
        msg = f"<b>{target_emoji} {c['symbol']} {c['strike']:.0f} {opt_type_color}</b>\n\n"
        
        msg += f"<b>Entry:</b> ₹{c['ltp']:.2f}\n"
        
        if "powerful_sl" in c:
            msg += f"<b>Powerful SL:</b> ₹{c['powerful_sl']:.2f} 🛡️\n"
        else:
            msg += f"<b>Stop Loss:</b> ₹{c.get('sl', 0):.2f}\n"
            
        if "t1" in c and "t2" in c:
            msg += f"<b>T1:</b> ₹{c['t1']:.2f} | <b>T2:</b> ₹{c['t2']:.2f}\n\n"
            
        msg += f"<b>Qty Size:</b> {c.get('recommended_qty', 'N/A')} lots\n"
        msg += f"<b>Score:</b> {c['score']}/100 ⭐\n"
        
        if c.get("momentum_score"):
            msg += f"<i>Momentum: {c['momentum_score']}/100</i>\n"

        if "BTST" in strategy_name:
            msg += "\n<i>Exit tomorrow at 9:15-9:20 AM using smart-exit guide!</i>"

        try:
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        except Exception as e:
            print(f"Failed to send alert for {c['symbol']}: {e}")

def send_btst_exit_telegram_alert(exit_recommendation: dict):
    """
    Sends a dedicated 9:15 AM BTST Exit Decision alert.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    emoji = "✅" 
    if "up" in exit_recommendation['market_condition']: emoji = "🚀"
    elif exit_recommendation['market_condition'] == 'flat': emoji = "⚖️"
    elif exit_recommendation['market_condition'] == 'down': emoji = "⚠️"
    elif "crash" in exit_recommendation['market_condition']: emoji = "🚨"

    msg = f"<b>🌅 BTST SMART EXIT SIGNAL (9:15 AM)</b>\n\n"
    msg += f"<b>Market Open Gap:</b> {exit_recommendation['gap_pct']:+.1f}% {emoji}\n\n"
    
    msg += f"<b>Entry:</b> ₹{exit_recommendation['entry_price']:.2f}\n"
    msg += f"<b>Open:</b> ₹{exit_recommendation['current_price']:.2f}\n"
    msg += f"<b>Powerful SL:</b> ₹{exit_recommendation['powerful_sl']:.2f}\n\n"
    
    msg += f"<b>🎯 ALGO RECOMMENDATION:</b>\n<i>{exit_recommendation['final_recommendation']}</i>\n\n"
    
    if exit_recommendation.get('rolling_available') and exit_recommendation['rolling_available']['strategy'] == 'ROLL':
        msg += f"<b>🔄 ROLLING RECOVERY ACTIVE:</b>\n"
        msg += f"Sell at ₹{exit_recommendation['current_price']:.2f} today.\n"
        msg += f"Buy tomorrow at ₹{exit_recommendation['rolling_available']['day_2_entry']:.2f} to reduce cost to ₹{exit_recommendation['rolling_available']['cost_basis_reduced']:.2f}.\n"

    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"Failed to send exit alert: {e}")
