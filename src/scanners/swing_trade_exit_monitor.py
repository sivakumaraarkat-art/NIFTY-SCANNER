"""
swing_trade_exit_monitor.py
═════════════════════════════════════════════════════════════════
Daily 7-to-10 Day Swing Trade Exit Monitor & P&L Engine:
  1. Reads all active swing trades from database/active_swing_trades.json.
  2. Fetches real-time market prices (LTP, High, Low) via Zerodha Kite API.
  3. Checks 5 Dynamic Exit Triggers:
       • Emergency Crash Shield: Exit immediately if sudden critical red flag appears.
       • Target 2 Reached (+10%+): Full profit booking.
       • Target 1 Reached (+5.5%+): Milestone profit booking.
       • Stop Loss Hit (-3.5%): Capital preservation stop.
       • 10-Day Time Horizon Reached: Closes position at CMP to rotate capital.
  4. Calculates exact return percentage and realized P&L.
  5. Dispatches instant Telegram Sell/Exit Alerts.
  6. Archives closed trades to database/closed_swing_trades.json.
"""

from __future__ import annotations

import io
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure UTF-8 output for console safely
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from configuration.swing_trade_settings import load_settings
from zerodha_market_data.zerodha_connection import create_zerodha_client
from trade_selection.active_swing_trade_registry import (
    load_active_trades,
    save_active_trades,
    close_swing_trade,
    partial_close_swing_trade,
    calculate_trading_days_elapsed,
)
from news_analysis.company_news_analyzer import fetch_company_news
from news_analysis.negative_event_detector import has_critical_crash_risk
from telegram_alerts.swing_trade_alert_sender import (
    send_swing_exit_alert,
    send_swing_partial_exit_alert,
)

DIVIDER = "──────────────────────────────────────────────"


def get_live_quotes(kite, symbols: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Fetch live LTP, High, and Low for a list of NSE symbols.
    Returns: {symbol: {'ltp': float, 'high': float, 'low': float, 'close': float}}
    """
    results: Dict[str, Dict[str, float]] = {}
    if not kite or not symbols:
        return results

    formatted_keys = [f"NSE:{s.strip().upper()}" for s in symbols if s.strip()]
    try:
        quotes = kite.quote(formatted_keys)
        for key, q in quotes.items():
            sym = key.replace("NSE:", "").strip().upper()
            ohlc = q.get("ohlc", {})
            ltp = float(q.get("last_price", 0.0))
            high = float(ohlc.get("high", ltp))
            low = float(ohlc.get("low", ltp))
            close = float(ohlc.get("close", ltp))
            results[sym] = {
                "ltp": ltp,
                "high": max(high, ltp),
                "low": min(low, ltp) if low > 0 else ltp,
                "close": close,
            }
    except Exception as exc:
        print(f"Warning: Failed to fetch live quotes from Kite: {exc}")

    return results


def evaluate_swing_exit(
    trade: Dict[str, Any],
    quote_data: Dict[str, float],
    check_emergency_news: bool = True,
) -> Tuple[bool, float, str]:
    """
    Evaluate if an active swing trade meets any exit condition.

    Returns:
        (should_exit: bool, exit_price: float, exit_reason: str)
    """
    symbol = trade.get("symbol", "").upper()
    entry = float(trade.get("entry_price", 0.0))
    sl = float(trade.get("stop_loss", 0.0))
    t1 = float(trade.get("target_1", entry * 1.06))
    t2 = float(trade.get("target_2", entry * 1.10))
    max_days = int(trade.get("max_holding_days", 10))

    ltp = quote_data.get("ltp", entry)
    high = quote_data.get("high", ltp)
    low = quote_data.get("low", ltp)

    entry_date = trade.get("entry_date", "")
    elapsed_trading_days = calculate_trading_days_elapsed(entry_date)

    # 1. Emergency Crash Shield Check
    if check_emergency_news:
        try:
            articles = fetch_company_news(symbol, max_articles=2)
            is_risk, reason = has_critical_crash_risk(articles)
            if is_risk:
                return True, ltp, f"EMERGENCY EXIT: {reason}"
        except Exception:
            pass

    # 2. Target 2 Hit (High Momentum Runner: +10%+)
    # On entry day (Day 0), compare against current LTP. On subsequent holding days, check session high.
    if ltp >= t2 or (elapsed_trading_days > 0 and high >= t2):
        return True, t2, "TARGET 2 HIT (+10%+) 🎯"

    # 3. Target 1 Hit (Core Target: +5.5%+)
    # Only evaluates if Target 1 has not already been partially booked
    t1_already_booked = trade.get("t1_booked", False)
    if not t1_already_booked:
        if ltp >= t1 or (elapsed_trading_days > 0 and high >= t1):
            return True, t1, "TARGET 1 HIT (+5.5%+) 🎯"

    # 4. Stop Loss Hit (P0: Whipsaw-Safe Capital Protection)
    # A true stop-loss requires current price (LTP) to be at or below SL.
    # An intraday wick low that recovers to ltp > sl by session check is a bear trap / rebound.
    # We trigger stop loss if current LTP <= sl, OR if low <= sl and price failed to recover above SL + 1.0%.
    if ltp <= sl:
        reason = "BREAK-EVEN STOP LOSS (+0.5%) 🛡️" if t1_already_booked else "STOP LOSS TRIGGERED 🛑"
        return True, sl, reason
    elif elapsed_trading_days > 0 and low > 0 and low <= sl and ltp <= (sl * 1.01):
        reason = "BREAK-EVEN STOP LOSS (+0.5%) 🛡️" if t1_already_booked else "STOP LOSS TRIGGERED 🛑"
        return True, sl, reason

    # 5. 10-Day Time Horizon Reached
    if elapsed_trading_days >= max_days:
        return True, ltp, f"10-DAY TIME HORIZON REACHED ⏱️ ({elapsed_trading_days}d)"

    return False, ltp, ""


def monitor_active_swing_trades(kite_client=None, send_telegram: bool = True) -> Dict[str, Any]:
    """
    Main monitoring driver for all active swing trades.
    """
    print("\n" + DIVIDER)
    print("🔍 SWING TRADE 7-10 DAY ACTIVE EXIT MONITOR")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")
    print(DIVIDER)

    settings = None
    try:
        settings = load_settings()
    except Exception:
        pass

    if kite_client is None and settings:
        try:
            kite_client = create_zerodha_client(settings)
            print("Connected to Zerodha Kite API for live spot prices.")
        except Exception as exc:
            print(f"Note: Kite client not available ({exc}). Using simulated/quote fallback.")

    active_trades = load_active_trades()
    if not active_trades:
        print("No active swing trades currently open in registry.")
        print(DIVIDER + "\n")
        return {"total_active": 0, "exited": 0, "retained": 0}

    print(f"Scanning {len(active_trades)} active swing trade position(s)...")

    symbols = [t["symbol"] for t in active_trades if t.get("symbol")]
    quotes = get_live_quotes(kite_client, symbols) if kite_client else {}

    exited_trades = []
    updated_active = []

    for trade in active_trades:
        trade_id = trade.get("trade_id")
        symbol = trade.get("symbol", "").upper()
        entry_price = float(trade.get("entry_price", 0.0))
        entry_date = trade.get("entry_date", "")

        q = quotes.get(symbol, {
            "ltp": trade.get("last_ltp", entry_price),
            "high": trade.get("peak_price", entry_price),
            "low": trade.get("trough_price", entry_price),
            "close": entry_price,
        })

        ltp = q["ltp"]
        elapsed_days = calculate_trading_days_elapsed(entry_date)
        trade["holding_days_elapsed"] = elapsed_days
        trade["last_ltp"] = round(ltp, 2)
        trade["peak_price"] = max(trade.get("peak_price", ltp), q["high"])
        trade["trough_price"] = min(trade.get("trough_price", ltp), q["low"])
        trade["last_checked_date"] = datetime.now().strftime("%Y-%m-%d")

        unrealized_pct = ((ltp - entry_price) / entry_price * 100) if entry_price > 0 else 0.0

        should_exit, exit_price, exit_reason = evaluate_swing_exit(trade, q)

        if should_exit:
            # P0: Partial Profit Booking (50% @ T1) + Trail SL to Break-Even (+0.5%)
            if "TARGET 1" in exit_reason and not trade.get("t1_booked", False):
                qty = int(trade.get("quantity", 1))
                if qty > 1:
                    closed_qty = qty // 2
                    print(f"🎯 PARTIAL EXIT (50%) TRIGGERED for {symbol}: Booking {closed_qty}/{qty} shares @ ₹{exit_price:,.2f} ({unrealized_pct:+.2f}%) & Trailing SL to Break-Even!")
                    closed_part, updated_trade = partial_close_swing_trade(
                        trade_id=trade_id,
                        exit_price=exit_price,
                        exit_reason="TARGET 1 PARTIAL HIT (50% BOOKED @ +5.5%+) 🎯",
                        closed_qty=closed_qty,
                        new_stop_loss=round(entry_price * 1.005, 2),
                    )
                    if closed_part:
                        exited_trades.append(closed_part)
                        if send_telegram:
                            send_swing_partial_exit_alert(closed_part, updated_trade, settings)
                    if updated_trade:
                        updated_active.append(updated_trade)
                    continue
                else:
                    # Single share trade: Trail SL to Break-Even and hold for Target 2!
                    print(f"🎯 TARGET 1 HIT for {symbol} (1 share): Trailing SL to Break-Even (₹{entry_price * 1.005:.2f}) & Holding for Target 2!")
                    trade["t1_booked"] = True
                    trade["status"] = "RUNNER_ACTIVE"
                    trade["stop_loss"] = round(entry_price * 1.005, 2)
                    trade["stop_loss_pct"] = +0.50
                    updated_active.append(trade)
                    continue

            print(f"🚨 EXIT TRIGGERED for {symbol}: {exit_reason} @ ₹{exit_price:,.2f} ({unrealized_pct:+.2f}%)")
            closed = close_swing_trade(
                trade_id=trade_id,
                exit_price=exit_price,
                exit_reason=exit_reason,
            )
            if closed:
                exited_trades.append(closed)
                if send_telegram:
                    send_swing_exit_alert(closed, settings)
        else:
            print(f"Holding {symbol}: CMP ₹{ltp:,.2f} ({unrealized_pct:+.2f}%) | Day {elapsed_days}/10")
            updated_active.append(trade)

    # Save state of retained active positions
    save_active_trades(updated_active)

    print(DIVIDER)
    print(f"Monitor Run Complete: {len(exited_trades)} trade(s) exited, {len(updated_active)} retained.")
    print(DIVIDER + "\n")

    return {
        "total_active": len(active_trades),
        "exited": len(exited_trades),
        "retained": len(updated_active),
        "exited_trades": exited_trades,
    }


if __name__ == "__main__":
    monitor_active_swing_trades()
