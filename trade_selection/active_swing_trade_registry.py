"""
Active Swing Trade Registry
═════════════════════════════════════════════════════════════════
Manages persistent state of active and completed 7-to-10 day swing trades:
  • Records new Buy entry signals into database/active_swing_trades.json.
  • Prevents duplicate entries on identical active symbols.
  • Tracks 10-day time horizons, entry prices, targets, and stop-loss levels.
  • Archives closed trades into database/closed_swing_trades.json with exact
    return % and realized P&L.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_DIR = PROJECT_ROOT / "database"
ACTIVE_TRADES_FILE = DB_DIR / "active_swing_trades.json"
CLOSED_TRADES_FILE = DB_DIR / "closed_swing_trades.json"


def _ensure_db_dir() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)


def load_active_trades() -> List[Dict[str, Any]]:
    """Load all currently active/open swing trades."""
    _ensure_db_dir()
    if not ACTIVE_TRADES_FILE.exists():
        return []
    try:
        with open(ACTIVE_TRADES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("active_trades", [])
    except Exception as exc:
        print(f"Warning: Failed to read active trades ({exc}). Returning empty list.")
        return []


def save_active_trades(trades: List[Dict[str, Any]]) -> None:
    """Save active trades atomically to JSON."""
    _ensure_db_dir()
    temp_file = ACTIVE_TRADES_FILE.with_suffix(".tmp")
    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_active": len(trades),
        "active_trades": trades,
    }
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    temp_file.replace(ACTIVE_TRADES_FILE)


def load_closed_trades() -> List[Dict[str, Any]]:
    """Load all completed/closed swing trades with their return %."""
    _ensure_db_dir()
    if not CLOSED_TRADES_FILE.exists():
        return []
    try:
        with open(CLOSED_TRADES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("closed_trades", [])
    except Exception as exc:
        print(f"Warning: Failed to read closed trades ({exc}). Returning empty list.")
        return []


def save_closed_trades(trades: List[Dict[str, Any]]) -> None:
    """Save closed trades atomically to JSON."""
    _ensure_db_dir()
    temp_file = CLOSED_TRADES_FILE.with_suffix(".tmp")
    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_closed": len(trades),
        "closed_trades": trades,
    }
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    temp_file.replace(CLOSED_TRADES_FILE)


def calculate_business_days_ahead(start_date: datetime, business_days: int = 10) -> datetime:
    """Calculate date N business days (Mon-Fri) ahead."""
    current = start_date
    added = 0
    while added < business_days:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Monday to Friday
            added += 1
    return current


def calculate_trading_days_elapsed(entry_date_str: str, current_date: Optional[datetime] = None) -> int:
    """Count number of trading days (Mon-Fri) between entry date and current date."""
    if current_date is None:
        current_date = datetime.now()
    try:
        entry_date = datetime.strptime(entry_date_str, "%Y-%m-%d").date()
    except Exception:
        return 0

    end_date = current_date.date()
    if end_date <= entry_date:
        return 0

    elapsed_trading_days = 0
    cur = entry_date + timedelta(days=1)
    while cur <= end_date:
        if cur.weekday() < 5:  # Exclude Saturday & Sunday
            elapsed_trading_days += 1
        cur += timedelta(days=1)
    return elapsed_trading_days


def register_swing_candidates(
    candidates: List[Dict[str, Any]],
    max_holding_days: int = 10,
) -> List[Dict[str, Any]]:
    """
    Register newly discovered swing candidates into active trades.
    Filters out any symbol that is already open in the active registry.
    """
    active_trades = load_active_trades()
    active_symbols = {t["symbol"].upper() for t in active_trades if t.get("status") == "OPEN"}

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    max_exit_dt = calculate_business_days_ahead(now, max_holding_days)
    max_exit_str = max_exit_dt.strftime("%Y-%m-%d")

    newly_registered = []

    for c in candidates:
        symbol = str(c.get("symbol", "")).strip().upper()
        if not symbol or symbol in active_symbols:
            continue

        # Skip if flagged with critical crash risk or earnings blackout
        if c.get("is_crash_risk", False) or c.get("earnings_risk", False):
            continue

        entry = float(c.get("entry", 0.0))
        sl = float(c.get("stop_loss", 0.0))
        t1 = float(c.get("target_1", entry * 1.06))
        t2 = float(c.get("target_2", entry * 1.10))
        t3 = float(c.get("target_3", entry * 1.15))

        if entry <= 0:
            continue

        trade_id = f"SWING_{symbol}_{now.strftime('%Y%m%d_%H%M%S')}"
        qty = int(c.get("quantity", 1))
        cap = float(c.get("capital_required", entry * qty))

        record = {
            "trade_id": trade_id,
            "symbol": symbol,
            "setup": c.get("setup", "SWING MOMENTUM"),
            "entry_date": date_str,
            "entry_time": time_str,
            "entry_price": round(entry, 2),
            "stop_loss": round(sl, 2),
            "target_1": round(t1, 2),
            "target_2": round(t2, 2),
            "target_3": round(t3, 2),
            "target_1_pct": round(((t1 - entry) / entry) * 100, 2),
            "target_2_pct": round(((t2 - entry) / entry) * 100, 2),
            "stop_loss_pct": round(((sl - entry) / entry) * 100, 2),
            "max_holding_days": max_holding_days,
            "max_exit_date": max_exit_str,
            "holding_days_elapsed": 0,
            "quantity": qty,
            "capital_allocated": round(cap, 2),
            "score": c.get("score", 80),
            "predictive_outlook": c.get("predictive_outlook", "🟢 BULLISH TAILWIND"),
            "news_catalysts": c.get("news_positive_catalysts", []),
            "status": "OPEN",
            "last_checked_date": date_str,
            "last_ltp": round(entry, 2),
            "peak_price": round(entry, 2),
            "trough_price": round(entry, 2),
        }

        active_trades.append(record)
        active_symbols.add(symbol)
        newly_registered.append(record)

    if newly_registered:
        save_active_trades(active_trades)
        print(f"Registered {len(newly_registered)} new swing trade(s) to active registry.")

    return newly_registered


def close_swing_trade(
    trade_id: str,
    exit_price: float,
    exit_reason: str,
    exit_date: Optional[str] = None,
    exit_time: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Close an active swing trade and record it into closed trades with return %.
    """
    active_trades = load_active_trades()
    target_trade = None
    remaining_trades = []

    for t in active_trades:
        if t.get("trade_id") == trade_id:
            target_trade = t
        else:
            remaining_trades.append(t)

    if not target_trade:
        return None

    now = datetime.now()
    exit_date_str = exit_date or now.strftime("%Y-%m-%d")
    exit_time_str = exit_time or now.strftime("%H:%M:%S")

    entry_price = float(target_trade.get("entry_price", exit_price))
    qty = int(target_trade.get("quantity", 1))
    capital = float(target_trade.get("capital_allocated", entry_price * qty))

    return_pct = round(((exit_price - entry_price) / entry_price) * 100, 2) if entry_price > 0 else 0.0
    pnl_amount = round((exit_price - entry_price) * qty, 2)
    holding_days = calculate_trading_days_elapsed(target_trade.get("entry_date", exit_date_str), now)

    closed_record = dict(target_trade)
    closed_record.update({
        "status": "CLOSED",
        "exit_price": round(exit_price, 2),
        "exit_date": exit_date_str,
        "exit_time": exit_time_str,
        "exit_reason": exit_reason,
        "holding_days": holding_days,
        "return_pct": return_pct,
        "pnl_amount": pnl_amount,
        "capital_allocated": capital,
    })

    # Save changes
    save_active_trades(remaining_trades)
    closed_trades = load_closed_trades()
    closed_trades.append(closed_record)
    save_closed_trades(closed_trades)

    return closed_record
