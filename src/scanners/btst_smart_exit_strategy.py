"""
SMART BTST EXIT STRATEGY - LIVE MARKET & COST-TO-COST ENGINE
═════════════════════════════════════════════════════════════════

Automated BTST Exit Manager for 09:12 AM - 09:45 AM IST:
  1. ✅ Live Kite Integration: Automatically reads overnight BTST/NRML positions
  2. ✅ Live Quote & Spot Resolution: Real-time option LTP, underlying spot, and P&L
  3. ✅ 4-Layer Dynamic Action Triggers:
       • Gap UP (+5%+ / T1 hit): Lock Profit / Trail 50%
       • Flat (±1%): Cost-to-cost exit rule
       • Gap Down / Pullback: Hold above Powerful SL or Roll
       • Breakdown (< Powerful SL): Immediate risk protection exit
  4. ✅ Uses only the saved selected batch; no full-pool or latest-file fallback
  5. ✅ Multi-path resilient credential resolution & instant Telegram alert dispatch
"""

from __future__ import annotations

import io
import html
from btst_batch import load_batch, logs_directory, contract_id, project_root
import json
import os
import sys
import time
from datetime import datetime, time as time_type, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = project_root(__file__)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Ensure UTF-8 output for console
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except Exception:
        pass

IST = timezone(timedelta(hours=5, minutes=30))
DIVIDER = "──────────────────────"

# ──────────────────────────────────────────────────────────────
# CREDENTIAL & KITE CONNECT RESOLVER
# ──────────────────────────────────────────────────────────────

def find_file(filename: str) -> Optional[Path]:
    """Find a configuration or token file across all standard repo directories."""
    candidates = [
        Path(f"D:/NiftyScanner/{filename}"),
        Path(f"D:/NiftyScanner/VM/nifty_v14_7/{filename}"),
        Path(f"D:/NiftyScanner/PORTFOLIO_PEAK_EXIT_GUARD/{filename}"),
        Path(f"/home/ubuntu/NiftyScanner/{filename}"),
        Path(f"/home/ubuntu/NiftyScanner/nifty_v14_7/{filename}"),
        Path(f"/home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/{filename}"),
        Path(__file__).resolve().parent / filename,
        Path(__file__).resolve().parents[1] / filename,
        Path(__file__).resolve().parents[2] / filename,
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c
    return None


def get_credentials() -> Dict[str, Any]:
    """Load credentials and Telegram configuration with multi-path fallback."""
    creds: Dict[str, Any] = {"zerodha": {}, "telegram": {}}

    cred_file = find_file(".credentials.json")
    if cred_file:
        try:
            with open(cred_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                creds["zerodha"] = data.get("zerodha", {})
                creds["telegram"] = data.get("telegram", {})
        except Exception:
            pass

    # Environment variable overrides
    if os.getenv("KITE_API_KEY"):
        creds["zerodha"]["api_key"] = os.getenv("KITE_API_KEY")
    if os.getenv("TELEGRAM_BOT_TOKEN"):
        creds["telegram"]["bot_token"] = os.getenv("TELEGRAM_BOT_TOKEN")
    if os.getenv("TELEGRAM_CHAT_ID"):
        creds["telegram"]["chat_id"] = os.getenv("TELEGRAM_CHAT_ID")

    return creds


def get_kite_client():
    """Initialize authenticated KiteConnect instance."""
    try:
        from kiteconnect import KiteConnect
    except ImportError:
        return None

    creds = get_credentials()
    api_key = creds.get("zerodha", {}).get("api_key")
    if not api_key:
        return None

    token_file = find_file(".kite_access_token")
    if not token_file:
        return None

    try:
        access_token = token_file.read_text(encoding="utf-8").strip()
        if not access_token:
            return None
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        return kite
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────
# BTST EXIT DECISION ENGINE
# ──────────────────────────────────────────────────────────────

class BTSTExitManager:
    """Intelligent exit manager for BTST positions."""

    def __init__(self, entry_price: float, entry_qty: int, powerful_sl: float):
        self.entry_price = entry_price
        self.entry_qty = entry_qty
        self.powerful_sl = powerful_sl
        self.entry_time = datetime.now()

    def detect_market_condition(self, current_price: float) -> str:
        """Detect market gap condition."""
        if self.entry_price <= 0:
            return "flat"
        gap_pct = ((current_price - self.entry_price) / self.entry_price) * 100

        if gap_pct >= 5:
            return "strong_up"
        elif gap_pct >= 2:
            return "up"
        elif gap_pct >= -1:
            return "flat"
        elif gap_pct >= -5:
            return "down"
        else:
            return "crash"

    def calculate_exit_price(self, current_price: float, condition: str) -> Dict[str, Any]:
        """Calculate exit strategy based on market condition."""
        gap_pct = ((current_price - self.entry_price) / self.entry_price) * 100 if self.entry_price > 0 else 0

        if condition == "strong_up":
            return {
                "condition": "strong_up",
                "description": "Gap UP +5%+: Exit all for HUGE PROFIT!",
                "action": "exit_all",
                "exit_price": current_price,
                "exit_qty": self.entry_qty,
                "profit_loss": (current_price - self.entry_price) * self.entry_qty,
                "profit_loss_pct": gap_pct,
                "recommendation": "EXIT 100% at market - LOCK PROFIT! 🎉",
            }
        elif condition == "up":
            return {
                "condition": "up",
                "description": "Gap UP +2% to +5%: Partial exit & Trail",
                "action": "partial_exit",
                "exit_price": current_price,
                "exit_qty": int(self.entry_qty * 0.5),
                "hold_qty": int(self.entry_qty * 0.5),
                "profit_loss": (current_price - self.entry_price) * int(self.entry_qty * 0.5),
                "profit_loss_pct": gap_pct,
                "recommendation": f"EXIT 50% at ₹{current_price:.2f}, TRAIL 50% to Target 2 with SL at Cost",
            }
        elif condition == "flat":
            return {
                "condition": "flat",
                "description": "Flat ±1%: Cost-to-cost exit",
                "action": "partial_exit",
                "exit_price": current_price,
                "exit_qty": int(self.entry_qty * 0.7),
                "hold_qty": int(self.entry_qty * 0.3),
                "profit_loss": (current_price - self.entry_price) * int(self.entry_qty * 0.7),
                "profit_loss_pct": gap_pct,
                "recommendation": f"EXIT 70% at ₹{current_price:.2f} for COST-TO-COST, hold 30% for bounce",
            }
        elif condition == "down":
            if current_price > self.powerful_sl:
                return {
                    "condition": "down",
                    "description": "Pullback: Above SL, Hold/Trail or Roll",
                    "action": "hold_with_sl",
                    "exit_price": current_price,
                    "exit_qty": self.entry_qty,
                    "profit_loss": (current_price - self.entry_price) * self.entry_qty,
                    "profit_loss_pct": gap_pct,
                    "recommendation": f"HOLD above Powerful SL ₹{self.powerful_sl:.2f}. If price breaks ₹{self.powerful_sl:.2f}, exit immediately.",
                }
            else:
                return {
                    "condition": "down_below_sl",
                    "description": "Below Powerful SL: Emergency exit",
                    "action": "exit_all",
                    "exit_price": self.powerful_sl,
                    "exit_qty": self.entry_qty,
                    "profit_loss": (self.powerful_sl - self.entry_price) * self.entry_qty,
                    "profit_loss_pct": ((self.powerful_sl - self.entry_price) / self.entry_price) * 100 if self.entry_price > 0 else 0,
                    "recommendation": f"🚨 EXIT IMMEDIATELY! Price below Powerful SL ₹{self.powerful_sl:.2f}. Protect capital.",
                }
        else:
            return {
                "condition": "crash",
                "description": "CRASH: Strict emergency exit",
                "action": "exit_all",
                "exit_price": current_price,
                "exit_qty": self.entry_qty,
                "profit_loss": (current_price - self.entry_price) * self.entry_qty,
                "profit_loss_pct": gap_pct,
                "recommendation": f"⚠️ EMERGENCY EXIT at ₹{current_price:.2f}! Strict stop protection.",
            }


# ──────────────────────────────────────────────────────────────
# TELEGRAM ALERT DISPATCH
# ──────────────────────────────────────────────────────────────

def send_telegram_alert(message: str) -> bool:
    """Use the scan's bot; split long reports at complete HTML lines."""
    from telegram_alerts.options_alert_sender import _send_tg
    chunks, current = [], []
    for line in message.splitlines():
        if current and len("\n".join(current + [line])) > 3500:
            chunks.append("\n".join(current))
            current = []
        current.append(line)
    if current:
        chunks.append("\n".join(current))
    outcomes = [_send_tg(chunk) for chunk in chunks]
    return bool(outcomes) and all(outcomes)


def run_automated_exit_monitor(dry_run: bool = False, log_dir=None, scan_date=None):
    """
    Main automated morning BTST exit engine.
    Reads live overnight F&O positions from Zerodha Kite,
    evaluates spot & option prices, calculates exact T1/T2/SL,
    and dispatches live morning exit guidance to Telegram.

    Args:
        dry_run: If True, suppresses Telegram dispatch and prints the message
                 to console only. Use for testing / paper-trading mode.
    """
    now_ist = datetime.now(IST)
    print(f"[{now_ist.strftime('%Y-%m-%d %H:%M:%S IST')}] Running BTST Smart Exit Monitor...")

    try:
        _, batch = load_batch(logs_directory(__file__, log_dir), scan_date, now_ist)
    except (OSError, ValueError, KeyError) as exc:
        print(f"BTST report not sent: {exc}")
        return False
    selected_by_id = {contract_id(c): c for c in batch["selected_candidates"]}
    kite = get_kite_client()
    live_positions = []

    if kite:
        try:
            pos_data = kite.positions()
            net_positions = pos_data.get("net", [])
            for p in net_positions:
                qty = p.get("quantity", 0)
                overnight_qty = p.get("overnight_quantity", 0)
                seg = p.get("segment", "")
                tsym = p.get("tradingsymbol", "")

                # Check for open F&O option positions
                key = f"{p.get('exchange', 'NFO')}:{tsym}"
                if qty > 0 and overnight_qty > 0 and key in selected_by_id:
                    buy_price = p.get("buy_price", 0.0) or p.get("average_price", 0.0)
                    live_positions.append({
                        "tradingsymbol": tsym,
                        "exchange": p.get("exchange", "NFO"),
                        "qty": abs(qty),
                        "buy_price": buy_price,
                        "pnl": p.get("pnl", 0.0),
                        "unrealised": p.get("unrealised", 0.0),
                        "value": p.get("value", 0.0),
                    })
            print(f"Found {len(live_positions)} active F&O overnight position(s) in Zerodha Kite.")
        except Exception as ex:
            print(f"Error fetching live positions from Kite: {ex}")

    # Build Alert Message
    scan_time = now_ist.strftime("%I:%M %p")
    msg = (
        f"🎯 <b>BTST SMART EXIT PLAYBOOK & LIVE STATUS</b>\n"
        f"{DIVIDER}\n"
        f"🕒 <b>Scan Time:</b> <code>{scan_time} IST</code>\n"
        f"🛡️ <b>Strategy:</b> <code>Cost-to-Cost / Profit Lock</code>\n"
        f"{DIVIDER}\n\n"
    )

    if live_positions:
        msg += f"📊 <b>Matching overnight holdings: {len(live_positions)} / {len(selected_by_id)} selected</b>\n\n"
        for pos in live_positions:
            tsym = pos["tradingsymbol"]
            qty = pos["qty"]
            buy_price = pos["buy_price"]

            # Fetch Live Quote for Option & Underlying Spot
            opt_key = f"{pos['exchange']}:{tsym}"
            underlying = "".join([c for c in tsym.split("2")[0] if c.isalpha()])
            spot_key = f"NSE:{underlying}"

            quotes = {}
            if kite:
                try:
                    quotes = kite.quote([opt_key, spot_key])
                except Exception:
                    pass

            opt_q = quotes.get(opt_key, {})
            spot_q = quotes.get(spot_key, {})

            if opt_q.get("last_price") is None:
                msg += f"<b>{html.escape(tsym)}</b>: quote unavailable; no P&amp;L estimate.\n\n"
                continue
            opt_ltp = opt_q["last_price"]
            opt_high = opt_q.get("ohlc", {}).get("high", opt_ltp)
            opt_low = opt_q.get("ohlc", {}).get("low", opt_ltp)
            spot_ltp = spot_q.get("last_price", 0.0)
            spot_high = spot_q.get("ohlc", {}).get("high", 0.0)
            spot_low = spot_q.get("ohlc", {}).get("low", 0.0)

            # Performance & Targets
            pnl_amt = (opt_ltp - buy_price) * qty
            pnl_pct = ((opt_ltp - buy_price) / buy_price * 100) if buy_price > 0 else 0

            selected = selected_by_id[opt_key]
            powerful_sl = float(selected.get("powerful_sl", selected.get("sl", buy_price * 0.78)))
            t1 = float(selected.get("t1", buy_price * 1.25))
            t2 = float(selected.get("t2", buy_price * 1.50))

            pnl_icon = "🟢" if pnl_amt >= 0 else "🔴"
            opt_type_icon = "📈" if "CE" in tsym else "📉"

            manager = BTSTExitManager(buy_price, qty, powerful_sl)
            condition = manager.detect_market_condition(opt_ltp)
            exit_plan = manager.calculate_exit_price(opt_ltp, condition)

            msg += f"{opt_type_icon} <b>{tsym}</b>\n"
            msg += f"• <b>Quantity:</b> <code>{qty} units</code>\n"
            msg += f"• <b>Buy Avg:</b> <code>₹{buy_price:.2f}</code>\n"
            msg += f"• <b>Live Option LTP:</b> <code>₹{opt_ltp:.2f}</code> ({opt_low:.2f} - {opt_high:.2f})\n"
            if spot_ltp > 0:
                msg += f"• <b>Underlying ({underlying}) Spot:</b> <code>₹{spot_ltp:.2f}</code>\n"
            msg += f"• <b>Live P&L:</b> {pnl_icon} <b>₹{pnl_amt:+,.2f}</b> (<code>{pnl_pct:+.2f}%</code>)\n\n"

            msg += f"🎯 <b>BTST EXECUTION MATRIX:</b>\n"
            msg += f"   🚀 <b>Target 1 (+25%):</b> <code>₹{t1:.2f}</code> (Book 50% & Trail)\n"
            msg += f"   🌟 <b>Target 2 (+50%):</b> <code>₹{t2:.2f}</code> (Full Target)\n"
            msg += f"   🛡️ <b>Powerful SL:</b> <code>₹{powerful_sl:.2f}</code> (Max Risk Line)\n"
            msg += f"   💡 <b>Immediate Action:</b> <i>{exit_plan['recommendation']}</i>\n\n"
            msg += f"{DIVIDER}\n\n"

    # Include every selected contract once; never substitute unrelated broker holdings.
    held = {f"{p['exchange']}:{p['tradingsymbol']}" for p in live_positions}
    remaining = [c for key, c in selected_by_id.items() if key not in held]
    msg += f"<b>Saved batch:</b> {html.escape(batch['batch_id'])} | {batch['scan_date']}\n"
    if remaining:
        msg += "\n<b>Selected signals without a confirmed open overnight holding:</b>\n"
        for c in remaining:
            opt_sym = html.escape(c["option_symbol"])
            entry = float(c.get("entry_price", c.get("ltp", 0)))
            status = batch.get("telegram_delivery", {}).get(contract_id(c), "unknown")
            msg += f"• <b>{opt_sym}</b> | Scan entry ₹{entry:.2f} | Alert: {status}\n"
        msg += "These are saved signals; no position or exit fill is assumed.\n\n"

    msg += "⚠️ <b>DISCIPLINE NOTE:</b> Do not hold stock options through afternoon theta decay if spot momentum stalls. Lock gains at T1 or trail to cost."

    # Dispatch to Telegram (suppressed in dry-run / paper-trading mode)
    if dry_run:
        print("\n[DRY-RUN] Telegram suppressed. Message that would have been sent:\n")
        plain = (msg.replace("<b>", "").replace("</b>", "")
                    .replace("<i>", "").replace("</i>", "")
                    .replace("<code>", "").replace("</code>", ""))
        print(plain)
    else:
        return send_telegram_alert(msg)
    return True


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser(description="BTST Smart Exit Monitor")
    _parser.add_argument(
        "--cron",
        action="store_true",
        help="Run in cron/scheduled mode (identical to default, kept for backwards compat)",
    )
    _parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Suppress Telegram dispatch; print message to console only (paper-trading / test mode)",
    )
    _parser.add_argument("--log-dir", help="Shared BTST log directory (or BTST_LOG_DIR)")
    _parser.add_argument("--scan-date", help="Explicit prior scan date YYYY-MM-DD")
    _args = _parser.parse_args()
    result = run_automated_exit_monitor(dry_run=_args.dry_run, log_dir=_args.log_dir, scan_date=_args.scan_date)
    if result is False:
        sys.exit(2)
