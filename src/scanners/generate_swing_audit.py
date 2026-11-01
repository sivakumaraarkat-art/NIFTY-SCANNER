"""
generate_swing_audit.py
═════════════════════════════════════════════════════════════════
Weekly Swing Trade Audit & Percentage Return Reporter
  • Aggregates all closed 7-to-10 day swing trades from database/closed_swing_trades.json.
  • Calculates total returns, win rate %, average holding days, and net P&L.
  • Exports a polished Excel workbook (Weekly_Swing_Audit_YYYY-MM-DD.xlsx).
  • Dispatches the Performance Audit summary and Excel file to the Portfolio Telegram Bot.
"""

from __future__ import annotations

import io
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure UTF-8 output for console safely
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trade_selection.active_swing_trade_registry import (
    load_active_trades,
    load_closed_trades,
)
from telegram_alerts.swing_trade_alert_sender import (
    resolve_telegram_credentials,
    send_swing_audit_alert,
)


def send_telegram_document(bot_token: str, chat_id: str, file_path: str, caption: str = "") -> bool:
    """Send an Excel document file directly to Telegram."""
    if not bot_token or not chat_id or not os.path.exists(file_path):
        return False
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    try:
        with open(file_path, "rb") as f:
            r = requests.post(
                url,
                data={"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"},
                files={"document": f},
                timeout=30,
            )
            r.raise_for_status()
            return True
    except Exception as exc:
        print(f"Warning: Failed to send Telegram document ({exc})")
        return False


def generate_swing_trade_audit(days_lookback: int = 14) -> Dict[str, Any]:
    """
    Generate weekly swing trade performance audit, create Excel, and dispatch to Telegram.
    """
    print("\n" + "═" * 60)
    print("📊 GENERATING WEEKLY SWING TRADE AUDIT & RETURN REPORT")
    print("═" * 60)

    closed_trades = load_closed_trades()
    active_trades = load_active_trades()

    now = datetime.now()
    cutoff_date = (now - timedelta(days=days_lookback)).strftime("%Y-%m-%d")

    # Filter trades in current audit window
    recent_closed = [
        t for t in closed_trades
        if t.get("exit_date", t.get("entry_date", "")) >= cutoff_date
    ]

    total_closed = len(recent_closed)
    wins = sum(1 for t in recent_closed if float(t.get("return_pct", 0.0)) > 0)
    losses = total_closed - wins
    win_rate = (wins / total_closed * 100) if total_closed > 0 else 0.0

    total_return_pct = sum(float(t.get("return_pct", 0.0)) for t in recent_closed)
    total_pnl = sum(float(t.get("pnl_amount", 0.0)) for t in recent_closed)
    avg_return = (total_return_pct / total_closed) if total_closed > 0 else 0.0
    avg_holding = (sum(int(t.get("holding_days", 0)) for t in recent_closed) / total_closed) if total_closed > 0 else 0.0

    period_str = f"{(now - timedelta(days=days_lookback)).strftime('%d-%b-%Y')} to {now.strftime('%d-%b-%Y')}"

    summary = {
        "period": period_str,
        "total_closed": total_closed,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 1),
        "net_return_pct": round(total_return_pct, 2),
        "net_pnl": round(total_pnl, 2),
        "avg_return": round(avg_return, 2),
        "avg_holding_days": round(avg_holding, 1),
        "total_active": len(active_trades),
        "trades": recent_closed,
    }

    # Generate Excel Report
    excel_filename = f"Weekly_Swing_Audit_{now.strftime('%Y-%m-%d')}.xlsx"
    excel_path = ROOT / excel_filename

    try:
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            # Sheet 1: Closed Trades
            if recent_closed:
                df_closed = pd.DataFrame([
                    {
                        "Trade ID": t.get("trade_id"),
                        "Symbol": t.get("symbol"),
                        "Setup": t.get("setup"),
                        "Entry Date": t.get("entry_date"),
                        "Exit Date": t.get("exit_date"),
                        "Holding Days": t.get("holding_days"),
                        "Entry Price (₹)": t.get("entry_price"),
                        "Exit Price (₹)": t.get("exit_price"),
                        "Return %": t.get("return_pct"),
                        "Realized P&L (₹)": t.get("pnl_amount"),
                        "Quantity": t.get("quantity"),
                        "Exit Reason": t.get("exit_reason"),
                        "Outlook": t.get("predictive_outlook"),
                    }
                    for t in recent_closed
                ])
                df_closed.to_excel(writer, sheet_name="Closed Swing Trades", index=False)
            else:
                pd.DataFrame([{"Notice": "No closed swing trades in this audit period"}]).to_excel(
                    writer, sheet_name="Closed Swing Trades", index=False
                )

            # Sheet 2: Active Trades
            if active_trades:
                df_active = pd.DataFrame([
                    {
                        "Trade ID": t.get("trade_id"),
                        "Symbol": t.get("symbol"),
                        "Setup": t.get("setup"),
                        "Entry Date": t.get("entry_date"),
                        "Max Exit Date": t.get("max_exit_date"),
                        "Days Elapsed": t.get("holding_days_elapsed"),
                        "Entry Price (₹)": t.get("entry_price"),
                        "Last LTP (₹)": t.get("last_ltp"),
                        "Target 1 (₹)": t.get("target_1"),
                        "Target 2 (₹)": t.get("target_2"),
                        "Stop Loss (₹)": t.get("stop_loss"),
                        "Allocated Capital (₹)": t.get("capital_allocated"),
                        "Score": t.get("score"),
                        "Predictive Outlook": t.get("predictive_outlook"),
                    }
                    for t in active_trades
                ])
                df_active.to_excel(writer, sheet_name="Active Open Trades", index=False)
            else:
                pd.DataFrame([{"Notice": "No active open trades currently"}]).to_excel(
                    writer, sheet_name="Active Open Trades", index=False
                )

            # Sheet 3: KPI Metrics
            df_kpi = pd.DataFrame([
                {"Metric": "Audit Period", "Value": period_str},
                {"Metric": "Total Closed Trades", "Value": total_closed},
                {"Metric": "Winning Trades", "Value": wins},
                {"Metric": "Losing Trades", "Value": losses},
                {"Metric": "Win Rate %", "Value": f"{win_rate:.1f}%"},
                {"Metric": "Total Portfolio Return %", "Value": f"{total_return_pct:+.2f}%"},
                {"Metric": "Total Realized P&L (₹)", "Value": f"₹{total_pnl:,.2f}"},
                {"Metric": "Average Return Per Trade", "Value": f"{avg_return:+.2f}%"},
                {"Metric": "Average Holding Days", "Value": f"{avg_holding:.1f} days"},
                {"Metric": "Active Open Positions", "Value": len(active_trades)},
            ])
            df_kpi.to_excel(writer, sheet_name="Performance Summary", index=False)

        print(f"✅ Excel audit workbook generated: {excel_filename}")
    except Exception as exc:
        print(f"Warning: Could not create Excel file: {exc}")

    # Dispatch to Telegram
    bot_token, chat_id = resolve_telegram_credentials()
    if bot_token and chat_id:
        print("Sending audit performance report to Telegram...")
        send_swing_audit_alert(summary)
        if excel_path.exists():
            caption = f"📊 <b>Weekly Swing Trade Audit:</b> {period_str}\nTotal Return: <b>{total_return_pct:+.2f}%</b>"
            send_telegram_document(bot_token, chat_id, str(excel_path), caption)
            print("✅ Excel audit file uploaded to Telegram.")
    else:
        print("Telegram bot not configured; preview displayed above.")

    print("═" * 60 + "\n")
    return summary


if __name__ == "__main__":
    generate_swing_trade_audit()
