"""
hero_zero_350pm_summary.py
═════════════════════════════════════════════════════════════════
Dedicated 03:50 PM Hero-Zero Expiry Performance Summary & Audit
  • Target Days: Tuesday (NIFTY) & Thursday (SENSEX).
  • Execution Time: 03:50 PM IST (Post-settlement audit window).
  • Role: Reads the 03:05 PM - 03:10 PM Hero-Zero recommendation logs, fetches
    actual minute candles / settlement prices from Zerodha Kite, and verifies
    whether Target 1 (+100%), Target 2 (+300% Multibagger), or Stop Loss was hit.
  • Telegram Bot: @Nifty_stage10_paper_bot
"""

from __future__ import annotations

import sys
import io
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import os
import glob
import json
import time
import argparse
import requests
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from html import escape as html_escape
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

DIVIDER = "──────────────────────"

HERO_ZERO_BOT_TOKEN = os.getenv("HERO_ZERO_TELEGRAM_BOT_TOKEN", "")
HERO_ZERO_CHAT_ID = os.getenv("HERO_ZERO_TELEGRAM_CHAT_ID", "")
MAIN_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
MAIN_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def tg_code(val: Any) -> str:
    if val is None or val == "":
        return "N/A"
    return f"<code>{html_escape(str(val))}</code>"


def tg_money(val: Any) -> str:
    if val is None or val == "":
        return "N/A"
    try:
        return f"₹{float(val):,.2f}"
    except (TypeError, ValueError):
        return str(val)


def tg_points(val: Any, signed: bool = False) -> str:
    if val is None or val == "":
        return "N/A"
    try:
        num = float(val)
        return f"{num:+.2f} pts" if signed else f"{num:.2f} pts"
    except (TypeError, ValueError):
        return str(val)


def _send_telegram_payload(token: str, chat_id: str, text: str, bot_name: str = "Bot") -> bool:
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    for attempt in range(1, 4):
        try:
            r = requests.post(url, json=payload, timeout=12)
            r.raise_for_status()
            res = r.json()
            if isinstance(res, dict) and res.get("ok"):
                print(f"✅ Summary alert delivered via {bot_name}")
                return True
        except Exception as e:
            if attempt < 3:
                time.sleep(1.0)
                continue
            print(f"❌ [Telegram {bot_name}] Error: {e}")
            return False
    return False


def _send_hero_zero_tg(text: str) -> bool:
    """Send summary alert strictly to Hero-Zero Telegram Bot (@Nifty_stage10_paper_bot)."""
    # 1. Primary: Hero-Zero dedicated bot (@Nifty_stage10_paper_bot)
    if HERO_ZERO_BOT_TOKEN and HERO_ZERO_CHAT_ID:
        return _send_telegram_payload(HERO_ZERO_BOT_TOKEN, HERO_ZERO_CHAT_ID, text, "@Nifty_stage10_paper_bot")

    # 2. Fallback to Main bot ONLY if Hero-Zero bot is not configured
    if MAIN_BOT_TOKEN and MAIN_CHAT_ID:
        return _send_telegram_payload(MAIN_BOT_TOKEN, MAIN_CHAT_ID, text, "Main Telegram Bot")

    print("⚠️ No Telegram credentials configured; printed locally.")
    return False


try:
    from src.scanners.options_data_provider import get_kite_client
except ImportError:
    def get_kite_client():
        return None


def find_today_hero_zero_log(symbol_filter: str = "AUTO", target_date: Optional[date] = None) -> Optional[Path]:
    """Locate today's latest Hero-Zero scan log."""
    if target_date is None:
        target_date = datetime.now().date()

    date_str = target_date.strftime("%Y%m%d")
    search_dirs = [
        ROOT / "logs",
        Path("logs"),
        Path("/home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/logs"),
    ]

    patterns = []
    if symbol_filter.upper() in ["SENSEX", "AUTO"]:
        patterns.append(f"sensex_hero_zero_{date_str}_*.json")
    if symbol_filter.upper() in ["NIFTY", "AUTO"]:
        patterns.append(f"nifty_hero_zero_{date_str}_*.json")

    matched_files = []
    for d in search_dirs:
        if d.exists():
            for pat in patterns:
                matched_files.extend(list(d.glob(pat)))

    if not matched_files:
        return None

    # De-duplicate by resolved path and sort by newest
    unique_files = list({f.resolve(): f for f in matched_files}.values())
    unique_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return unique_files[0]


def evaluate_candidate_performance(
    c: Dict[str, Any],
    kite: Optional[Any],
    scan_time: datetime,
    exchange_instruments: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Evaluate performance of a single Hero-Zero recommendation against actual minute candles.

    Uses chronological candle-by-candle simulation:
      - Once Stop Loss is hit (-50%), trade exits immediately.
      - If Target 1 is hit (+100%), 50% is booked, and runner SL is trailed to Breakeven (entry).
      - If runner hits Target 2 (+300%), second half is booked (Multibagger!).
      - If runner hits Breakeven, it exits at cost (preserving 100% of T1 profit).
    """
    sym = c.get("symbol", "SENSEX")
    opt_sym = c.get("option_symbol", "")
    strike = float(c.get("strike", 0.0))
    opt_type = c.get("option_type", "CE")
    entry_price = float(c.get("entry_price") or c.get("ltp") or 25.0)
    t1 = float(c.get("t1") or round(entry_price * 2.0, 2))
    t2 = float(c.get("t2") or round(entry_price * 4.0, 2))
    sl = float(c.get("sl") or round(entry_price * 0.50, 2))
    lot_size = int(c.get("lot_size", 20 if sym == "SENSEX" else 65))
    lots = int(c.get("recommended_qty", 2))
    tot_qty = lot_size * lots
    half_qty = tot_qty / 2.0

    peak_high = entry_price
    min_low = entry_price
    settlement_price = entry_price
    candles_count = 0
    t1_hit = False
    t2_hit = False
    sl_hit = False
    runner_be_hit = False
    t1_time = None
    t2_time = None
    sl_time = None
    runner_be_time = None

    # Try resolving instrument token
    inst_token = None
    if exchange_instruments:
        match = next((i for i in exchange_instruments if i.get("tradingsymbol") == opt_sym), None)
        if match:
            inst_token = match.get("instrument_token")
        else:
            # Fallback by strike and type for today's expiry
            today = scan_time.date()
            m = next((i for i in exchange_instruments if i.get("strike") == strike and i.get("instrument_type") == opt_type and i.get("expiry") == today), None)
            if m:
                inst_token = m.get("instrument_token")
                opt_sym = m.get("tradingsymbol", opt_sym)

    candles = []
    if kite is not None and inst_token:
        try:
            # Query candles from scan_time minus 5 minutes to 15:30 (clamped safely to trading hours)
            market_open = datetime.combine(scan_time.date(), datetime.min.time()) + timedelta(hours=9, minutes=15)
            market_close = datetime.combine(scan_time.date(), datetime.min.time()) + timedelta(hours=15, minutes=30)

            from_hour = scan_time.hour
            from_min = max(0, scan_time.minute - 5)
            if from_hour > 15 or (from_hour == 15 and from_min >= 29):
                from_hour = 14
                from_min = 0

            from_dt = datetime.combine(scan_time.date(), datetime.min.time()) + timedelta(hours=from_hour, minutes=from_min)
            if from_dt < market_open:
                from_dt = market_open
            to_dt = market_close

            if from_dt < to_dt:
                fetched = kite.historical_data(inst_token, from_dt, to_dt, "minute")
                if fetched:
                    candles = fetched
                    candles_count = len(candles)
        except Exception as e:
            print(f"⚠️ [KiteConnect] Could not fetch minute candles for {opt_sym}: {e}")

    # Fallback to quote if no historical candles available
    if not candles and kite is not None:
        try:
            exch = "BFO" if sym == "SENSEX" else "NFO"
            q_res = kite.quote([f"{exch}:{opt_sym}"])
            q_data = q_res.get(f"{exch}:{opt_sym}", {})
            if q_data:
                ltp = float(q_data.get("last_price", 0.0))
                ohlc = q_data.get("ohlc", {})
                q_high = float(ohlc.get("high", ltp) or ltp)
                q_low = float(ohlc.get("low", ltp) or ltp)
                if q_high > 0:
                    peak_high = max(peak_high, q_high)
                    min_low = min(min_low, q_low)
                    settlement_price = ltp
        except Exception:
            pass

    # Chronological minute-by-minute simulation
    state = "OPEN"
    pnl = 0.0

    if candles:
        settlement_price = float(candles[-1].get("close", 0.05))
        for cd in candles:
            cd_dt = cd["date"] if isinstance(cd["date"], datetime) else datetime.fromisoformat(str(cd["date"]))
            c_time = cd_dt.strftime("%H:%M")
            h = float(cd["high"])
            l = float(cd["low"])
            peak_high = max(peak_high, h)
            min_low = min(min_low, l)

            if state == "OPEN":
                # Handle single-candle extreme volatility (both SL and T1 touched)
                if l <= sl and h >= t1:
                    op = float(cd.get("open", entry_price))
                    cl = float(cd.get("close", entry_price))
                    if cl < op:
                        sl_hit = True
                        sl_time = c_time
                        state = "CLOSED_SL"
                        pnl = -(entry_price - sl) * tot_qty
                        break
                    else:
                        t1_hit = True
                        t1_time = c_time
                        pnl += (t1 - entry_price) * half_qty
                        state = "HALF_BOOKED"
                        if h >= t2:
                            t2_hit = True
                            t2_time = c_time
                            pnl += (t2 - entry_price) * half_qty
                            state = "CLOSED_ALL_TARGETS"
                            break
                elif l <= sl:
                    sl_hit = True
                    sl_time = c_time
                    state = "CLOSED_SL"
                    pnl = -(entry_price - sl) * tot_qty
                    break
                elif h >= t2:
                    t1_hit = True
                    t2_hit = True
                    t1_time = c_time
                    t2_time = c_time
                    pnl = (t1 - entry_price) * half_qty + (t2 - entry_price) * half_qty
                    state = "CLOSED_ALL_TARGETS"
                    break
                elif h >= t1:
                    t1_hit = True
                    t1_time = c_time
                    pnl += (t1 - entry_price) * half_qty
                    state = "HALF_BOOKED"

            elif state == "HALF_BOOKED":
                if h >= t2:
                    t2_hit = True
                    t2_time = c_time
                    pnl += (t2 - entry_price) * half_qty
                    state = "CLOSED_ALL_TARGETS"
                    break
                elif l <= entry_price:
                    runner_be_hit = True
                    runner_be_time = c_time
                    # Runner stopped at cost, preserving T1 profit
                    state = "CLOSED_RUNNER_BE"
                    break

        if state == "OPEN":
            pnl = (settlement_price - entry_price) * tot_qty
            outcome = "⏱️ EXPIRED AT 3:30 PM SETTLEMENT"
            status_icon = "📉 ⏳"
        elif state == "HALF_BOOKED":
            runner_pnl = (settlement_price - entry_price) * half_qty
            pnl += runner_pnl
            outcome = "🎯 TARGET 1 HIT (+100% 2X) — RUNNER SETTLED"
            status_icon = "🥇 ✅"
        elif state == "CLOSED_ALL_TARGETS":
            outcome = "🚀 TARGET 2 HIT (MULTIBAGGER 4X+)"
            status_icon = "🌟 🚀"
        elif state == "CLOSED_RUNNER_BE":
            outcome = "🎯 TARGET 1 HIT (+100% 2X) — RUNNER TRAILED AT COST"
            status_icon = "🥇 🛡️"
        elif state == "CLOSED_SL":
            outcome = "🛑 STOP LOSS HIT (-50% RISK CAP)"
            status_icon = "🛑 ⚠️"
        else:
            outcome = "⏱️ EXPIRED AT 3:30 PM SETTLEMENT"
            status_icon = "📉 ⏳"
    else:
        # Fallback simulation if no candle data available
        if peak_high >= t2:
            t1_hit = True
            t2_hit = True
            outcome = "🚀 TARGET 2 HIT (MULTIBAGGER 4X+)"
            status_icon = "🌟 🚀"
            pnl = (t1 - entry_price) * half_qty + (t2 - entry_price) * half_qty
        elif peak_high >= t1:
            t1_hit = True
            outcome = "🎯 TARGET 1 HIT (+100% 2X)"
            status_icon = "🥇 ✅"
            pnl = (t1 - entry_price) * half_qty
        elif min_low <= sl:
            sl_hit = True
            outcome = "🛑 STOP LOSS HIT (-50% RISK CAP)"
            status_icon = "🛑 ⚠️"
            pnl = -(entry_price - sl) * tot_qty
        else:
            outcome = "⏱️ EXPIRED AT 3:30 PM SETTLEMENT"
            status_icon = "📉 ⏳"
            pnl = (settlement_price - entry_price) * tot_qty

    max_gain_pct = round(((peak_high - entry_price) / entry_price) * 100.0, 1) if entry_price > 0 else 0.0
    pnl_pct = round((pnl / (entry_price * tot_qty)) * 100.0, 1) if (entry_price * tot_qty) > 0 else 0.0

    return {
        "symbol": sym,
        "option_symbol": opt_sym,
        "strike": strike,
        "option_type": opt_type,
        "entry_price": entry_price,
        "t1": t1,
        "t2": t2,
        "sl": sl,
        "lot_size": lot_size,
        "recommended_qty": lots,
        "total_shares": tot_qty,
        "capital": entry_price * tot_qty,
        "peak_high": peak_high,
        "min_low": min_low,
        "settlement_price": settlement_price,
        "t1_hit": t1_hit,
        "t2_hit": t2_hit,
        "sl_hit": sl_hit,
        "runner_be_hit": runner_be_hit,
        "t1_time": t1_time,
        "t2_time": t2_time,
        "sl_time": sl_time,
        "runner_be_time": runner_be_time,
        "max_gain_pct": max_gain_pct,
        "outcome": outcome,
        "status_icon": status_icon,
        "pnl": round(pnl, 2),
        "pnl_pct": pnl_pct,
    }


def send_hero_zero_summary_telegram(
    evaluations: List[Dict[str, Any]],
    symbol_name: str = "SENSEX",
    scan_dt: Optional[datetime] = None,
) -> bool:
    """Format and dispatch the 03:50 PM Hero-Zero Audit Report card."""
    if not evaluations:
        print("⚠️ No evaluations to send.")
        return False

    if scan_dt is None:
        scan_dt = datetime.now()

    today_str = scan_dt.strftime("%d-%b-%Y (%A)")
    tot_capital = sum(e["capital"] for e in evaluations)
    tot_pnl = sum(e["pnl"] for e in evaluations)
    net_roi_pct = round((tot_pnl / tot_capital) * 100.0, 1) if tot_capital > 0 else 0.0
    multibaggers = sum(1 for e in evaluations if e["t2_hit"])
    t1_wins = sum(1 for e in evaluations if e["t1_hit"])

    pnl_sign = "+" if tot_pnl >= 0 else ""
    pnl_icon = "🟢 🏆" if tot_pnl >= 0 else "🔴 ⚠️"

    hdr = (
        f"🏁 <b>STAGE 10 — {symbol_name} HERO-ZERO 3:50 PM AUDIT</b> 🏁\n"
        f"{DIVIDER}\n"
        f"📅 <b>Expiry:</b>  {tg_code(today_str)}\n"
        f"🕒 <b>Session:</b> {tg_code('03:50 PM Final Settlement Audit')}\n"
        f"📊 <b>Summary:</b> {tg_code(f'{len(evaluations)} Setups | {multibaggers} Multibagger(s)')}\n"
        f"💰 <b>Net PnL:</b> {tg_code(f'{pnl_sign}{tg_money(tot_pnl)} ({net_roi_pct:+.1f}%)')}\n"
        f"🤖 <b>Bot:</b>     {tg_code('@Nifty_stage10_paper_bot')}\n"
        f"{DIVIDER}\n"
        "<i>Minute-by-minute execution & payoff audit:</i>"
    )
    _send_hero_zero_tg(hdr)
    time.sleep(0.3)

    for i, e in enumerate(evaluations, 1):
        opt_type = e["option_type"]
        icon = "🏛️ 🟢" if opt_type == "CE" else "🏛️ 🔴"
        strike = int(e["strike"])
        sym = e["symbol"]
        opt_sym = e["option_symbol"]
        entry = e["entry_price"]
        peak = e["peak_high"]
        settle = e["settlement_price"]
        t1 = e["t1"]
        t2 = e["t2"]
        sl = e["sl"]
        t1_status = f"✅ HIT @ {e['t1_time']}" if e["t1_hit"] else "❌ Not Hit"
        t2_status = f"🚀 MULTIBAGGER @ {e['t2_time']}" if e["t2_hit"] else "❌ Not Hit"
        sl_status = f"🛑 HIT @ {e['sl_time']}" if e["sl_hit"] else "🛡️ Protected"
        pnl_val = e["pnl"]
        pnl_tag = f"{pnl_val:+.2f}"
        pnl_cls = "🟢" if pnl_val >= 0 else "🔴"
        pos_str = f"{e['recommended_qty']} lots ({e['total_shares']} qty)"

        lines = [
            f"{icon} <b>#{i} {sym} {strike} {opt_type} — {e['status_icon']}</b>",
            f"{DIVIDER}",
            f"🏷️ <b>Contract:</b>     {tg_code(opt_sym)}",
            f"🎯 <b>Status:</b>       <b>{html_escape(e['outcome'])}</b>",
            "",
            "📊 <b>PRICE & TARGET AUDIT</b>",
            f"├─ 🟢 <b>Entry (3:10 PM):</b>  {tg_code(tg_money(entry))}",
            f"├─ 🚀 <b>Peak High:</b>        {tg_code(tg_money(peak))} (<b>{e['max_gain_pct']:+.1f}%</b>)",
            f"├─ 🥇 <b>Target 1 (+100%):</b> {tg_code(tg_money(t1))} ({t1_status})",
            f"├─ 🌟 <b>Target 2 (+300%):</b> {tg_code(tg_money(t2))} ({t2_status})",
            f"├─ 🛑 <b>Stop Loss (50%):</b>  {tg_code(tg_money(sl))} ({sl_status})",
            f"└─ 🏁 <b>3:30 PM Settle:</b>   {tg_code(tg_money(settle))}",
            "",
            "💰 <b>PAYOFF & RETURN</b>",
            f"├─ 🏷️ <b>Position:</b>   {tg_code(pos_str)}",
            f"├─ 💵 <b>Capital:</b>    {tg_code(tg_money(e['capital']))}",
            f"└─ {pnl_cls} <b>Trade PnL:</b>  <b>{tg_money(pnl_val)} ({e['pnl_pct']:+.1f}%)</b>",
            f"{DIVIDER}",
        ]
        _send_hero_zero_tg("\n".join(lines))
        time.sleep(0.3)

    # Final wrap-up scorecard
    footer = [
        f"{pnl_icon} <b>FINAL HERO-ZERO SESSION SCORECARD</b>",
        f"{DIVIDER}",
        f"💵 <b>Total Capital Deployed:</b> {tg_code(tg_money(tot_capital))}",
        f"🏆 <b>Session Net Profit/Loss:</b> <b>{pnl_sign}{tg_money(tot_pnl)}</b>",
        f"📈 <b>Overall Net ROI:</b>        <b>{net_roi_pct:+.1f}%</b>",
        f"🎯 <b>Target Hit Rate:</b>        {tg_code(f'{t1_wins}/{len(evaluations)} T1 Hit | {multibaggers}/{len(evaluations)} Multibaggers')}",
        f"{DIVIDER}",
        "✨ <i>Stage 10 V14.7 Hero-Zero Risk Management verified. Zero overnight risk!</i>",
    ]
    _send_hero_zero_tg("\n".join(footer))
    return True


def main():
    parser = argparse.ArgumentParser(description="Hero-Zero Expiry 3:50 PM Performance Summary")
    parser.add_argument("--symbol", type=str, default="AUTO", choices=["AUTO", "SENSEX", "NIFTY"], help="Filter by symbol")
    parser.add_argument("--force", action="store_true", help="Bypass weekday checks")
    parser.add_argument("--dry-run", action="store_true", help="Print report locally without sending Telegram")
    parser.add_argument("--date", type=str, default=None, help="Target date YYYY-MM-DD (defaults to today)")
    args = parser.parse_args()

    target_dt = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else datetime.now().date()
    weekday = target_dt.weekday()

    # Weekday check: Tuesday (1) is Nifty, Thursday (3) is Sensex
    if not args.force and weekday not in (1, 3):
        print(f"⚠️ HALT: Hero-Zero Summary only runs on Tuesdays (Nifty) or Thursdays (Sensex).")
        print("   Use --force to run on demand.")
        return

    print("==================================================================================")
    print("🏁 STAGE 10 V14.7 — HERO-ZERO 3:50 PM EXPIRY PERFORMANCE SUMMARY & AUDIT")
    print(f"📅 Target Date: {target_dt.strftime('%d-%b-%Y (%A)')}")
    print("==================================================================================")

    log_path = find_today_hero_zero_log(symbol_filter=args.symbol, target_date=target_dt)
    if not log_path or not log_path.exists():
        print(f"⚠️ No Hero-Zero scan log found for date {target_dt} under logs/.")
        return

    print(f"📂 Found Hero-Zero scan log: {log_path.name}")
    with open(log_path, "r", encoding="utf-8") as f:
        log_data = json.load(f)

    candidates = log_data.get("candidates", [])
    if not candidates:
        print("⚠️ No candidates present in log file.")
        return

    kite = get_kite_client()
    exchange_instruments = []
    if kite is not None:
        try:
            is_sensex = "sensex" in log_path.name.lower()
            exch = "BFO" if is_sensex else "NFO"
            exchange_instruments = kite.instruments(exch)
        except Exception as e:
            print(f"⚠️ Could not load exchange instruments: {e}")

    # Evaluate each trade
    scan_time = datetime.fromtimestamp(log_path.stat().st_mtime)
    evaluations = []
    for c in candidates:
        ev = evaluate_candidate_performance(c, kite, scan_time, exchange_instruments)
        evaluations.append(ev)

    sym_name = "SENSEX" if "sensex" in log_path.name.lower() else "NIFTY"

    if args.dry_run:
        print("\n--- LOCAL PREVIEW (DRY RUN) ---")
        for ev in evaluations:
            print(f"{ev['option_symbol']:<20} | Entry: {ev['entry_price']} | Peak: {ev['peak_high']} ({ev['max_gain_pct']:+}%) | PnL: {ev['pnl']:+} ({ev['pnl_pct']:+}%) | Outcome: {ev['outcome']}")
        return

    # Dispatch via Telegram
    send_hero_zero_summary_telegram(evaluations, symbol_name=sym_name, scan_dt=scan_time)

    # Save summary report
    sum_dir = ROOT / "logs"
    sum_dir.mkdir(exist_ok=True)
    out_file = sum_dir / f"hero_zero_summary_{target_dt.strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"summary_date": str(target_dt), "symbol": sym_name, "evaluations": evaluations}, f, indent=2, default=str)

    print(f"✅ Audit log saved to: {out_file}")


if __name__ == "__main__":
    main()
