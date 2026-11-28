"""
gtt_fill_sentinel.py
====================
Automated Sentinel for GTT Buy Order Fills & OCO Exit Attachment.
Monitors Zerodha positions on trading mornings. When a Buy GTT fills:
1. Detects the new open position.
2. Automatically attaches a two-leg OCO Exit GTT (Target 1 + Stop Loss).
3. Dispatches a priority Telegram alert to notify the trader.

Target Profiles:
- CONCORDBIO: Target ₹603.00 (+10%), SL ₹540.40 (-1.7%)
- GALLANTT:   Target ₹592.00 (+10%), SL ₹516.90 (-4.2%)
- Generic:    Target +10%, SL -3.5% below average price

Usage:
    python src/scanners/gtt_fill_sentinel.py --test
    python src/scanners/gtt_fill_sentinel.py --cron
"""

import sys
import os
import argparse
import json
import datetime
import requests
from pathlib import Path
from dotenv import load_dotenv

# Windows console encoding fix
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

STATE_FILE = ROOT / "database" / "gtt_sentinel_state.json"

# ─── HERO ZERO INDEX OPTIONS PROFILES ───
# These use Hero Zero logic: SL = min 8pts absolute, T1 = 2x, T2 = 4x
HERO_ZERO_INDEX_OPTIONS = {
    "NIFTY",
    "BANKNIFTY",
    "SENSEX",
    "FINNIFTY",
    "MIDCPNIFTY",
}

TARGET_PROFILES = {
    "CONCORDBIO": {"target": 603.00, "sl": 540.40},
    "GALLANTT":   {"target": 592.00, "sl": 516.90},
    "VTL":        {"target": 581.20, "sl": 515.80},
}


def get_kite_client():
    from kiteconnect import KiteConnect
    token_paths = [
        ROOT / ".kite_access_token",
        ROOT.parent / ".kite_access_token",
        Path("/home/ubuntu/NiftyScanner/.kite_access_token"),
        Path("D:/NiftyScanner/.kite_access_token"),
    ]
    token = None
    for p in token_paths:
        if p.exists():
            t = p.read_text(encoding="utf-8").strip()
            if t:
                token = t
                break

    key_paths = [
        ROOT / ".kite_api_key",
        ROOT.parent / ".kite_api_key",
        Path("/home/ubuntu/NiftyScanner/.kite_api_key"),
        Path("D:/NiftyScanner/.kite_api_key"),
    ]
    key = None
    for p in key_paths:
        if p.exists():
            k = p.read_text(encoding="utf-8").strip()
            if k:
                key = k
                break

    if not key:
        key = os.getenv("ZERODHA_API_KEY", "")

    if not key or not token:
        raise RuntimeError("Missing Zerodha Kite API key or access token")

    kite = KiteConnect(api_key=key)
    kite.set_access_token(token)
    return kite


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"attached_ocos": {}}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def send_telegram(message):
    token = os.getenv("PORTFOLIO_TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("PORTFOLIO_TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json().get("ok", False)
    except Exception:
        return False


def check_and_attach_oco(kite, verbose=False):
    state = load_state()
    attached = state.get("attached_ocos", {})

    try:
        positions = kite.positions().get("net", [])
    except Exception as e:
        if verbose:
            print(f"❌ Error fetching positions: {e}")
        return

    try:
        gtts = kite.get_gtts()
    except Exception as e:
        if verbose:
            print(f"❌ Error fetching GTTs: {e}")
        return

    active_symbols_with_oco = set()
    for g in gtts:
        cond = g.get("condition", {})
        sym = cond.get("tradingsymbol")
        gtype = g.get("type", "").lower()
        status = g.get("status", "").lower()
        if gtype == "two-leg" and status == "active":
            active_symbols_with_oco.add(sym)

    if verbose:
        print(f"Active positions in account: {len(positions)}")
        print(f"Active OCO GTT orders on Kite: {list(active_symbols_with_oco)}")

    for pos in positions:
        sym = pos.get("tradingsymbol")
        qty = pos.get("quantity", 0)
        product = pos.get("product", "CNC")
        exchange = pos.get("exchange", "NSE")
        avg_price = pos.get("average_price", 0.0)
        ltp = pos.get("last_price", avg_price)

        # Only process long equity positions
        if qty <= 0:
            continue

        # Check if already protected
        if sym in active_symbols_with_oco or sym in attached:
            if verbose:
                print(f"✓ {sym} ({qty} sh) is already protected by OCO GTT.")
            continue

        # Check if this is a monitored target
        profile = TARGET_PROFILES.get(sym)
        if profile:
            target = profile["target"]
            sl = profile["sl"]
        else:
            # Check if Hero Zero index option
            base_sym = sym.replace("CE", "").replace("PE", "")
            # Extract base symbol (NIFTY, BANKNIFTY, SENSEX, etc.)
            for idx in HERO_ZERO_INDEX_OPTIONS:
                if idx in sym:
                    # Hero Zero logic: SL = max 50% premium OR min 8pts absolute
                    # T1 = 2x entry, T2 = 4x entry
                    sl_pct = round(avg_price * 0.50, 2)
                    sl_abs = round(avg_price - 8.0, 2)
                    sl = min(sl_pct, sl_abs)  # Wider SL (lower price)
                    target = round(avg_price * 2.0, 2)  # 2x
                    t2 = round(avg_price * 4.0, 2)    # 4x
                    print(f"   🏛️ HERO ZERO MODE: {sym} | SL: {sl:.2f} (min 8pts) | T1: {target:.2f} (2x) | T2: {t2:.2f} (4x)")
                    # Use target for OCO leg 1, we'll add T2 as second leg
                    break
            else:
                # Default fallback: 10% target, 3.5% SL
                target = round(avg_price * 1.10, 1)
                sl = round(avg_price * 0.965, 1)

        sl_limit = round(max(0.05, sl - 0.50), 2)

        # Detect Hero Zero index option
        is_hero_zero = False
        t2 = None
        for idx in HERO_ZERO_INDEX_OPTIONS:
            if idx in sym:
                is_hero_zero = True
                t2 = round(avg_price * 4.0, 2)  # T2 = 4x entry
                break

        print(f"\n🚨 NEW FILL DETECTED: {sym} (Qty: {qty} @ ₹{avg_price:.2f})")
        if is_hero_zero:
            print(f"   🏛️ HERO ZERO MODE: SL ₹{sl:.2f} (min 8pts) | T1 ₹{target:.2f} (2x) | T2 ₹{t2:.2f} (4x)")
        else:
            print(f"   • Attaching OCO Stop Loss @ ₹{sl:.2f} | Target @ ₹{target:.2f}...")

        if is_hero_zero:
            # 3-leg OCO for Hero Zero: SL, T1, T2
            trigger_values = [sl, target, t2]
            sell_orders = [
                {"transaction_type": kite.TRANSACTION_TYPE_SELL, "quantity": qty, "order_type": kite.ORDER_TYPE_LIMIT, "product": product, "price": sl_limit},
                {"transaction_type": kite.TRANSACTION_TYPE_SELL, "quantity": qty, "order_type": kite.ORDER_TYPE_LIMIT, "product": product, "price": target},
                {"transaction_type": kite.TRANSACTION_TYPE_SELL, "quantity": qty, "order_type": kite.ORDER_TYPE_LIMIT, "product": product, "price": t2},
            ]
        else:
            # Standard 2-leg OCO
            trigger_values = [sl, target]
            sell_orders = [
                {"transaction_type": kite.TRANSACTION_TYPE_SELL, "quantity": qty, "order_type": kite.ORDER_TYPE_LIMIT, "product": product, "price": sl_limit},
                {"transaction_type": kite.TRANSACTION_TYPE_SELL, "quantity": qty, "order_type": kite.ORDER_TYPE_LIMIT, "product": product, "price": target},
            ]

        try:
            resp = kite.place_gtt(
                trigger_type=kite.GTT_TYPE_OCO,
                tradingsymbol=sym,
                exchange=exchange,
                trigger_values=trigger_values,
                last_price=ltp,
                orders=sell_orders
            )
            gid = resp.get("trigger_id")
            print(f"🎉 SUCCESS! OCO GTT #{gid} attached for {sym}!")

            attached[sym] = {
                "trigger_id": gid,
                "qty": qty,
                "avg_price": avg_price,
                "target": target,
                "sl": sl,
                "t2": t2,
                "timestamp": datetime.datetime.now().isoformat()
            }
            state["attached_ocos"] = attached
            save_state(state)

            # Send Telegram Alert
            if is_hero_zero:
                msg = (
                    f"🎉 <b>HERO ZERO GTT FILLED & 3-LEG OCO ATTACHED</b>\n"
                    f"──────────────────────────\n"
                    f"📦 <b>Symbol:</b> {sym} ({exchange})\n"
                    f"• <b>Filled Qty:</b> {qty} shares @ ₹{avg_price:.2f}\n"
                    f"• <b>Product:</b> {product}\n"
                    f"──────────────────────────\n"
                    f"🛡️ <b>3-LEG OCO PROTECTION ACTIVE:</b>\n"
                    f"• 🛑 <b>Stop Loss:</b> ₹{sl:.2f} ({((sl-avg_price)/avg_price*100):+.1f}%)\n"
                    f"• 🥇 <b>Target 1 (2x):</b> ₹{target:.2f} ({((target-avg_price)/avg_price*100):+.1f}%)\n"
                    f"• 🚀 <b>Target 2 (4x):</b> ₹{t2:.2f} ({((t2-avg_price)/avg_price*100):+.1f}%)\n"
                    f"• 🆔 <b>GTT ID:</b>   #{gid}\n"
                    f"──────────────────────────\n"
                    f"✅ <i>Your position is 100% protected on Zerodha exchange servers!</i>"
                )
            else:
                msg = (
                    f"🎉 <b>GTT BUY FILLED & OCO ATTACHED</b>\n"
                    f"──────────────────────────\n"
                    f"📦 <b>Stock:</b> {sym} ({exchange})\n"
                    f"• <b>Filled Qty:</b> {qty} shares @ ₹{avg_price:.2f}\n"
                    f"• <b>Product:</b> {product} Delivery\n"
                    f"──────────────────────────\n"
                    f"🛡️ <b>OCO PROTECTION ACTIVE:</b>\n"
                    f"• 🛑 <b>Stop Loss:</b> ₹{sl:.2f} ({((sl-avg_price)/avg_price*100):+.1f}%)\n"
                    f"• 🎯 <b>Target 1:</b>  ₹{target:.2f} ({((target-avg_price)/avg_price*100):+.1f}%)\n"
                    f"• 🆔 <b>GTT ID:</b>   #{gid}\n"
                    f"──────────────────────────\n"
                    f"✅ <i>Your position is 100% protected on Zerodha exchange servers!</i>"
                )
            send_telegram(msg)
        except Exception as ex:
            print(f"❌ Failed to attach OCO GTT for {sym}: {ex}")


def main():
    parser = argparse.ArgumentParser(description="GTT Fill Sentinel")
    parser.add_argument("--test", action="store_true", help="Verbose test mode")
    parser.add_argument("--cron", action="store_true", help="Silent cron mode")
    args = parser.parse_args()

    verbose = args.test or not args.cron
    if verbose:
        print("=" * 70)
        print("🛡️ GTT FILL & OCO PROTECTION SENTINEL")
        print("=" * 70)

    try:
        kite = get_kite_client()
        if verbose:
            print("✓ Connected to Zerodha Kite API.")
    except Exception as e:
        if verbose:
            print(f"❌ Kite connection error: {e}")
        return

    check_and_attach_oco(kite, verbose=verbose)

    if verbose:
        print("=" * 70)


if __name__ == "__main__":
    main()
