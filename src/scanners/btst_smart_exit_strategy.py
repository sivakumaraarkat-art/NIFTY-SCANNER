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
  4. ✅ Fallback to latest BTST scan JSON candidates
  5. ✅ Multi-path resilient credential resolution & instant Telegram alert dispatch
"""

from __future__ import annotations

import io
import json
import os
import sys
import time
from datetime import datetime, time as time_type, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

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
    """Send alert to the main Stock Swing V1 Telegram bot and chat."""
    try:
        import requests
    except ImportError:
        print(message.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "").replace("<code>", "").replace("</code>", ""))
        return False

    # Force direct load from environment or project .credentials.json (Stock Swing V1 bot only)
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    targets = []
    if bot_token and chat_id:
        targets.append((bot_token, str(chat_id)))

    # Also check project specific credentials.json if env vars not fully loaded
    cred_file = find_file(".credentials.json")
    if cred_file and cred_file.exists():
        try:
            with open(cred_file, "r", encoding="utf-8") as f:
                cdata = json.load(f)
            tg = cdata.get("telegram", {})
            b_tok = tg.get("bot_token")
            c_id = tg.get("chat_id")
            if b_tok and c_id and (b_tok, str(c_id)) not in targets:
                targets.append((b_tok, str(c_id)))
        except Exception:
            pass

    if not targets:
        print("⚠️ No Telegram targets found. Outputting to console:")
        print(message.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "").replace("<code>", "").replace("</code>", ""))
        return False

    success = False
    for b_tok, cid in targets:
        try:
            url = f"https://api.telegram.org/bot{b_tok}/sendMessage"
            payload = {
                "chat_id": cid,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                print(f"✓ Telegram alert delivered successfully to {cid} (Bot: ...{b_tok[-6:]})!")
                success = True
            else:
                print(f"✗ Telegram delivery failed to {cid}: {res.text}")
        except Exception as e:
            print(f"✗ Telegram dispatch error to {cid}: {e}")

    return success


# ──────────────────────────────────────────────────────────────
# LIVE POSITIONS & BTST EXIT MONITOR
# ──────────────────────────────────────────────────────────────

def run_automated_exit_monitor(dry_run: bool = False):
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
                if qty != 0 and (seg == "FO" or "CE" in tsym or "PE" in tsym):
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
        msg += "📊 <b>LIVE OVERNIGHT BTST POSITIONS:</b>\n\n"
        for pos in live_positions:
            tsym = pos["tradingsymbol"]
            qty = pos["qty"]
            buy_price = pos["buy_price"]

            # Fetch Live Quote for Option & Underlying Spot
            opt_key = f"NFO:{tsym}"
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

            opt_ltp = opt_q.get("last_price", buy_price)
            opt_high = opt_q.get("ohlc", {}).get("high", opt_ltp)
            opt_low = opt_q.get("ohlc", {}).get("low", opt_ltp)
            spot_ltp = spot_q.get("last_price", 0.0)
            spot_high = spot_q.get("ohlc", {}).get("high", 0.0)
            spot_low = spot_q.get("ohlc", {}).get("low", 0.0)

            # Performance & Targets
            pnl_amt = (opt_ltp - buy_price) * qty
            pnl_pct = ((opt_ltp - buy_price) / buy_price * 100) if buy_price > 0 else 0

            powerful_sl = round(buy_price * 0.78, 2)
            t1 = round(buy_price * 1.25, 2)
            t2 = round(buy_price * 1.50, 2)

            pnl_icon = "🟢" if pnl_amt >= 0 else "🔴"
            opt_type_icon = "📈" if "CE" in tsym else "📉"

            manager = BTSTExitManager(buy_price, qty, powerful_sl)
            condition = manager.detect_market_condition(opt_ltp)
            exit_plan = manager.calculate_exit_price(opt_ltp, condition)

            msg += f"{opt_type_icon} <b>{tsym}</b>\n"
            msg += f"• <b>Quantity:</b> <code>{qty} ({qty // 175 if qty >= 175 else 1} Lot)</code>\n"
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

    else:
        # Fallback: Read latest BTST scan candidates from logs / data directory
        search_dirs = [
            Path("logs"),
            Path("data"),
            Path("D:/NiftyScanner/STOCK_SWING_V1_updated/logs"),
            Path("D:/NiftyScanner/STOCK_SWING_V1_updated/data"),
            Path("/home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/logs"),
            Path("/home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/data"),
        ]
        json_files = []
        for d in search_dirs:
            if d.exists():
                json_files.extend(list(d.glob("*btst*.json")))

        if json_files:
            latest_log = max(json_files, key=lambda f: f.stat().st_mtime)
            try:
                with open(latest_log, "r", encoding="utf-8") as f:
                    data = json.load(f)

                stock_list = data.get("stocks", []) or data.get("results", {}).get("stocks", []) or data.get("candidates", [])
                # Show all candidates from yesterday's scan log so matching is complete
                candidates = stock_list

                if candidates:
                    msg += "📋 <b>YESTERDAY'S BTST SCAN CANDIDATES:</b>\n\n"
                    for c in candidates:
                        sym = c.get("symbol", "")
                        opt_type = c.get("option_type", "CE")
                        icon = "🟢" if opt_type == "CE" else "🔴"
                        opt_sym = c.get("option_symbol", f"{sym} {c.get('strike', 'ATM')} {opt_type}")
                        ltp = c.get("ltp", c.get("entry_price", 0.0))
                        sl = c.get("powerful_sl", c.get("sl", round(ltp * 0.78, 2)))
                        t1 = round(ltp * 1.25, 2)

                        msg += f"{icon} <b>{opt_sym}</b>\n"
                        msg += f"• <b>Entry:</b> ₹{ltp:.2f} | <b>SL:</b> ₹{sl:.2f} | <b>T1:</b> ₹{t1:.2f}\n"
                        msg += f"• <i>Action: If gap up >₹{t1:.2f}, lock profit. If below ₹{sl:.2f}, cut loss.</i>\n\n"
            except Exception as e:
                print(f"Error reading BTST JSON log: {e}")

    msg += "⚠️ <b>DISCIPLINE NOTE:</b> Do not hold stock options through afternoon theta decay if spot momentum stalls. Lock gains at T1 or trail to cost."

    # Dispatch to Telegram (suppressed in dry-run / paper-trading mode)
    if dry_run:
        print("\n[DRY-RUN] Telegram suppressed. Message that would have been sent:\n")
        plain = (msg.replace("<b>", "").replace("</b>", "")
                    .replace("<i>", "").replace("</i>", "")
                    .replace("<code>", "").replace("</code>", ""))
        print(plain)
    else:
        send_telegram_alert(msg)


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
    _args = _parser.parse_args()
    run_automated_exit_monitor(dry_run=_args.dry_run)
