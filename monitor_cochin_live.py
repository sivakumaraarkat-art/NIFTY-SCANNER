"""
monitor_cochin_live.py
═════════════════════════════════════════════════════════════════
Live Real-Time Position, Stop-Loss, Fast Move & High Volume Monitor for Cochin Shipyard (COCHINSHIP).
• Tracks active 375 MIS shares position, live P&L, distance to targets & SL.
• Detects High Volume Spikes (RVOL / delta volume).
• Detects Fast Price Movements (>₹3 change or rapid velocity).
• Sends Telegram alerts on High Volume, Fast Move, VWAP Cross, Target 1, Target 2, or SL breach.
"""
import sys
import os
import time
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scanners.options_data_provider import get_kite_client

TARGET_1 = 1260.0
TARGET_2 = 1275.0
STOP_LOSS = 1230.0
VWAP_LEVEL = 1248.0

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8988178854:AAGMmNfaWRa0nEPgDNwG7SJO61HDVMAOMtU")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1962486108")

STATE = {
    "prev_ltp": None,
    "prev_vol": None,
    "prev_time": None,
    "crossed_vwap": False,
    "t1_alerted": False,
    "t2_alerted": False,
    "sl_alerted": False,
}

def send_telegram_alert(msg: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            pass
    except Exception:
        pass

def check_position_once():
    kite = get_kite_client()
    if not kite:
        print("❌ Kite client initialization failed.")
        return

    now_dt = datetime.now()
    now_str = now_dt.strftime("%I:%M:%S %p")
    q = kite.quote(["NSE:COCHINSHIP"]).get("NSE:COCHINSHIP", {})
    ltp = float(q.get("last_price", 0.0))
    ohlc = q.get("ohlc", {})
    day_low = float(ohlc.get("low", 0.0))
    day_high = float(ohlc.get("high", 0.0))
    vwap = float(q.get("average_price", 0.0))
    current_vol = int(q.get("volume", 0))

    # Net Position
    positions = kite.positions().get("net", [])
    cochin_pos = [p for p in positions if p.get("tradingsymbol") == "COCHINSHIP" and p.get("product") == "MIS"]

    # Open Orders
    orders = kite.orders()
    open_orders = [o for o in orders if o.get("tradingsymbol") == "COCHINSHIP" and o.get("status") == "OPEN"]
    sl_orders = [o for o in open_orders if o.get("order_type") in ("SL", "SL-M") and o.get("transaction_type") == "SELL"]

    print("=" * 80)
    print(f"📡 COCHIN SHIPYARD LIVE POSITION & MOMENTUM MONITOR  |  ⏰ {now_str}")
    print("=" * 80)

    if not cochin_pos or cochin_pos[0].get("quantity", 0) == 0:
        print("ℹ️ Position Status: FLAT (0 Shares). Trade is closed or not filled.")
        print(f"LTP: ₹{ltp:.2f} | Day Low: ₹{day_low:.2f} | Day High: ₹{day_high:.2f} | Total Vol: {current_vol:,}")
        return

    pos = cochin_pos[0]
    qty = pos.get("quantity", 0)
    avg_price = float(pos.get("buy_price", 1239.5))
    pnl = float(pos.get("pnl", 0.0))
    pnl_pct = ((ltp - avg_price) / avg_price * 100) if avg_price else 0.0

    pnl_sign = "+" if pnl >= 0 else ""
    pnl_badge = "🟢" if pnl >= 0 else "🔴"

    print(f"💼 Open Position:      {qty} Shares (MIS)")
    print(f"🏷️ Buy Average:        ₹{avg_price:.2f}")
    print(f"⚡ Live Market Price:   ₹{ltp:.2f}")
    print(f"{pnl_badge} Real-Time P&L:       {pnl_sign}₹{pnl:,.2f} ({pnl_sign}{pnl_pct:.2f}%)")
    print(f"📊 Today's Range:       Low: ₹{day_low:.2f}  |  High: ₹{day_high:.2f}  |  VWAP: ₹{vwap:.2f}")
    print(f"📦 Total Exchange Vol:  {current_vol:,} Shares")

    # -------------------------------------------------------------
    # MOMENTUM & VOLUME SPIKE DETECTION
    # -------------------------------------------------------------
    prev_vol = STATE["prev_vol"]
    prev_ltp = STATE["prev_ltp"]
    prev_time = STATE["prev_time"]

    if prev_vol is not None and prev_ltp is not None and prev_time is not None:
        elapsed = max(1.0, (now_dt - prev_time).total_seconds())
        delta_vol = current_vol - prev_vol
        delta_price = ltp - prev_ltp

        # Check High Volume Spike: > 10,000 shares in check window or rate > 300 shs/sec
        is_vol_surge = (delta_vol >= 10000) or (delta_vol >= 5000 and elapsed <= 30)
        # Check Fast Price Move: >= ₹2.50 change
        is_fast_move = abs(delta_price) >= 2.50

        if is_vol_surge or is_fast_move:
            direction = "🚀 SURGING UP" if delta_price > 0 else ("🔻 DROPPING FAST" if delta_price < 0 else "⚡ MASSIVE ACTIVITY")
            move_msg = (
                f"\n🚨 *MOMENTUM ALERT: COCHIN SHIPYARD {direction}* 🚨\n"
                f"• LTP: *₹{ltp:.2f}* ({delta_price:+.2f} in {int(elapsed)}s)\n"
                f"• Volume Surge: *+{delta_vol:,} shares* traded!\n"
                f"• Real-Time P&L: *{pnl_sign}₹{pnl:,.2f}*\n"
                f"• Targets: T1 ₹{TARGET_1:.2f} | T2 ₹{TARGET_2:.2f}"
            )
            print("-" * 80)
            print(f"🔥 ALERT TRIGGERED: {direction} | Delta Price: {delta_price:+.2f} | Delta Vol: +{delta_vol:,} in {int(elapsed)}s")
            send_telegram_alert(move_msg)

    # Check VWAP breakout
    if ltp >= VWAP_LEVEL and not STATE["crossed_vwap"]:
        STATE["crossed_vwap"] = True
        vwap_msg = f"🚀 *COCHINSHIP VWAP BREAKOUT!*\nLTP crossed above ₹{VWAP_LEVEL:.2f} (Now: ₹{ltp:.2f}).\nMomentum building toward ₹{TARGET_1:.2f}!"
        print(f"🚀 {vwap_msg}")
        send_telegram_alert(vwap_msg)

    # Check Targets & SL Alerts
    if ltp >= TARGET_1 and not STATE["t1_alerted"]:
        STATE["t1_alerted"] = True
        t1_msg = f"🎉 *TARGET 1 REACHED on COCHINSHIP!*\nLTP: ₹{ltp:.2f}\nProfit: +₹{(ltp - avg_price)*qty:,.2f}\n👉 Action: Book 50% and trail SL to ₹1,240.00!"
        print(f"🎉 {t1_msg}")
        send_telegram_alert(t1_msg)
    elif ltp >= TARGET_2 and not STATE["t2_alerted"]:
        STATE["t2_alerted"] = True
        t2_msg = f"🏆 *TARGET 2 REACHED on COCHINSHIP!*\nLTP: ₹{ltp:.2f}\nProfit: +₹{(ltp - avg_price)*qty:,.2f}\n👉 Action: Book remaining shares and celebrate!"
        print(f"🏆 {t2_msg}")
        send_telegram_alert(t2_msg)
    elif ltp <= STOP_LOSS and not STATE["sl_alerted"]:
        STATE["sl_alerted"] = True
        sl_msg = f"🛑 *STOP-LOSS HIT on COCHINSHIP!*\nLTP: ₹{ltp:.2f}\nAction: Exit MIS position immediately."
        print(f"🛑 {sl_msg}")
        send_telegram_alert(sl_msg)

    # Protection & Targets Display
    dist_to_t1 = TARGET_1 - ltp
    dist_to_t2 = TARGET_2 - ltp
    dist_to_sl = ltp - STOP_LOSS

    print("-" * 80)
    print("🎯 TARGETS & STOP-LOSS PROGRESS:")
    print(f"   • Target 1 (₹{TARGET_1:.2f}):  ₹{dist_to_t1:+.2f} away  ➔ Expected Profit: +₹{(TARGET_1 - avg_price)*qty:,.2f}")
    print(f"   • Target 2 (₹{TARGET_2:.2f}):  ₹{dist_to_t2:+.2f} away  ➔ Expected Profit: +₹{(TARGET_2 - avg_price)*qty:,.2f}")
    print(f"   • Stop-Loss (₹{STOP_LOSS:.2f}): ₹{dist_to_sl:+.2f} buffer ➔ Max Risk:        -₹{(avg_price - STOP_LOSS)*qty:,.2f}")
    print("-" * 80)

    # Protection order status
    if sl_orders:
        sl_o = sl_orders[0]
        print(f"✅ ACTIVE STOP-LOSS ON EXCHANGE: Order ID {sl_o.get('order_id')} | Trigger ₹{sl_o.get('trigger_price')} | Qty {sl_o.get('quantity')}")
    else:
        print("⚠️  WARNING: NO ACTIVE STOP-LOSS ORDER ON KITE! PLEASE PLACE SL AT ₹1,215.00!")

    print("=" * 80)

    # Update state
    STATE["prev_ltp"] = ltp
    STATE["prev_vol"] = current_vol
    STATE["prev_time"] = now_dt

def monitor_loop(interval_sec=20):
    print(f"🔄 Starting background live monitor with Volume & Fast Move Detection (every {interval_sec}s)...")
    while True:
        try:
            check_position_once()
            time.sleep(interval_sec)
        except KeyboardInterrupt:
            print("\n🛑 Stopped monitor.")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true", help="Run continuously in a loop")
    parser.add_argument("--interval", type=int, default=20, help="Check interval in seconds")
    args = parser.parse_args()

    if args.loop:
        monitor_loop(args.interval)
    else:
        check_position_once()
