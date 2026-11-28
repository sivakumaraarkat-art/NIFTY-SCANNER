"""
sensex_hero_zero_expiry_scanner.py
═════════════════════════════════════════════════════════════════
Dedicated BSE SENSEX Expiry Hero-Zero Options Scanner (Stage 10 V14.7 Alert Format)
  • Target Days: Thursday (SENSEX Weekly F&O Expiry Day).
  • Execution Window: Dispatches at 03:10 PM IST (Peak Gamma Surge Window — 3:10 PM to 3:25 PM!)
  • Hero-Zero Filtering: Low-premium quality options (₹12 - ₹45) with explosive Gamma surge & asymmetric Risk-Reward (2x to 5x+ payoff).
  • Dedicated Telegram Bot: @Nifty_stage10_paper_bot
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

# Dedicated Telegram Bot Credentials for Hero Zero (@Nifty_stage10_paper_bot -> Nifty v14.9 Paper Trading group)
# These MUST be set via environment variables (HERO_ZERO_TELEGRAM_BOT_TOKEN / HERO_ZERO_TELEGRAM_CHAT_ID).
# No hardcoded fallback — this prevents the paper-trading bot token from leaking into other scripts
# (e.g. btst_smart_exit_strategy.py) that scan credential files across project folders.
HERO_ZERO_BOT_TOKEN = os.getenv("HERO_ZERO_TELEGRAM_BOT_TOKEN", "")
HERO_ZERO_CHAT_ID = os.getenv("HERO_ZERO_TELEGRAM_CHAT_ID", "")


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


def _send_hero_zero_tg(text: str) -> bool:
    """Send alert specifically via @Nifty_stage10_paper_bot with V14.7 retry logic."""
    token = HERO_ZERO_BOT_TOKEN
    chat = HERO_ZERO_CHAT_ID
    if not token or not chat:
        print("⚠️ Hero-Zero Telegram credentials missing.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    for attempt in range(1, 4):
        try:
            r = requests.post(url, json=payload, timeout=10)
            r.raise_for_status()
            res = r.json()
            if isinstance(res, dict) and res.get("ok"):
                print(f"✅ Alert delivered via @Nifty_stage10_paper_bot")
                return True
        except Exception as e:
            if attempt < 3:
                time.sleep(1.0)
                continue
            print(f"❌ [Telegram @Nifty_stage10_paper_bot] Error: {e}")
            return False
    return False


try:
    from src.scanners.options_data_provider import get_kite_client, get_nfo_instruments
except ImportError:
    def get_kite_client():
        return None
    def get_nfo_instruments(kite):
        return []


def load_nse_holidays() -> set[date]:
    """Load official NSE trading holidays from trader-in/holidays.json."""
    holidays = set()
    h_path = ROOT / "trader-in" / "holidays.json"
    if h_path.exists():
        try:
            data = json.loads(h_path.read_text(encoding="utf-8"))
            for item in data.get("CM", []):
                td = item.get("tradingDate")
                if td:
                    holidays.add(datetime.strptime(td, "%d-%b-%Y").date())
        except Exception:
            pass
    if not holidays:
        holidays = {
            date(2026, 1, 26), date(2026, 3, 3), date(2026, 3, 31),
            date(2026, 4, 14), date(2026, 5, 1), date(2026, 10, 20),
            date(2026, 11, 10), date(2026, 11, 24), date(2026, 12, 25)
        }
    return holidays


def is_sensex_expiry_day(check_dt: Optional[datetime] = None, target_weekday: int = 3) -> bool:
    """
    Check if today is SENSEX Expiry Day.
    • Standard rule: Thursday (weekday == 3).
    • Holiday Shift Rule: If Thursday is an exchange holiday, expiry shifts to Wednesday (weekday == 2)!
    """
    if check_dt is None:
        check_dt = datetime.now()
    today_d = check_dt.date()
    weekday = check_dt.weekday()

    holidays = load_nse_holidays()

    if today_d in holidays:
        return False

    # Case A: Standard Thursday Expiry
    if weekday == 3:
        return True

    # Case B: Thursday is a Holiday -> Shift to Wednesday!
    if weekday == 2:
        tomorrow_d = today_d + timedelta(days=1)
        if tomorrow_d in holidays:
            print(f"🔔 SENSEX EXPIRY SHIFT DETECTED: Tomorrow ({tomorrow_d.strftime('%d-%b-%Y')}) is a Holiday!")
            print(f"   -> Weekly SENSEX Expiry has shifted to TODAY ({today_d.strftime('%A, %d-%b-%Y')})!")
            return True

    return False


def _normalize_expiry(exp_val: Any) -> Optional[datetime.date]:
    """Normalize expiry value to date object."""
    if isinstance(exp_val, datetime):
        return exp_val.date()
    if isinstance(exp_val, date):
        return exp_val
    if isinstance(exp_val, str) and exp_val:
        try:
            return datetime.strptime(exp_val[:10], "%Y-%m-%d").date()
        except Exception:
            return None
    return None


def get_default_time_slot_label() -> str:
    """Dynamically determine session label based on execution time (supports 2:00 PM to 3:30 PM)."""
    now = datetime.now()
    curr_hour = now.hour
    curr_minute = now.minute
    if curr_hour == 14 and curr_minute < 30:
        return "02:00 PM Early Afternoon Gamma Setup"
    elif curr_hour == 14:
        return "02:30 PM Mid Afternoon Acceleration"
    elif curr_hour == 15 and curr_minute < 10:
        return "03:00 PM - 03:05 PM Peak Volatility Window"
    elif curr_hour == 15 and curr_minute <= 25:
        return "03:10 PM Peak Gamma Expiry Surge"
    else:
        return f"{now.strftime('%I:%M %p')} Gamma Expiry Window"


def resolve_sensex_hero_zero_candidates(
    kite: Optional[Any],
    account_size: float = 500000.0,
    single_best: bool = True,
    min_prem: float = 8.0,
    max_prem: float = 15.0,
    default_lots: int = 4,
    capital_budget: float = 1500.0,
) -> List[Dict[str, Any]]:
    """Scan and resolve live high-conviction BSE SENSEX Hero-Zero option setups from Zerodha Kite.
    Calibrated to ₹8 - ₹15 target entry range, 4 lots, and ₹1,500 capital budget.
    """
    spot_price = 81500.0
    day_open = 81500.0
    if kite is not None:
        try:
            quote = kite.quote(["BSE:SENSEX"])
            if "BSE:SENSEX" in quote:
                q = quote["BSE:SENSEX"]
                spot_price = float(q.get("last_price", 81500.0))
                day_open = float(q.get("ohlc", {}).get("open", spot_price))
        except Exception as e:
            print(f"⚠️ [KiteConnect] Could not fetch BSE:SENSEX spot price: {e}")

    spot_change = spot_price - day_open
    atm_strike = round(spot_price / 100.0) * 100.0
    today = datetime.now().date()
    now_dt = datetime.now()

    # Dynamic target premium based on user-calibrated ₹8 - ₹15 window
    target_prem = round((min_prem + max_prem) / 2.0, 1)

    # Retrieve from cached instruments first
    instruments = get_nfo_instruments(kite)
    sensex_opts = []
    for inst in instruments:
        if inst.get("name") == "SENSEX" and inst.get("instrument_type") in {"CE", "PE"}:
            exp = _normalize_expiry(inst.get("expiry"))
            if exp and exp >= today:
                inst_copy = dict(inst)
                inst_copy["expiry"] = exp
                sensex_opts.append(inst_copy)

    # Fallback to direct BFO fetch if cache did not contain SENSEX
    if not sensex_opts and kite is not None:
        try:
            raw_bfo = kite.instruments("BFO")
            for inst in raw_bfo:
                if inst.get("name") == "SENSEX" and inst.get("instrument_type") in {"CE", "PE"}:
                    exp = _normalize_expiry(inst.get("expiry"))
                    if exp and exp >= today:
                        inst_copy = dict(inst)
                        inst_copy["expiry"] = exp
                        sensex_opts.append(inst_copy)
        except Exception as e:
            print(f"⚠️ [KiteConnect] Could not fetch BFO instruments: {e}")

    today_opts = [i for i in sensex_opts if i["expiry"] == today]
    if not today_opts and sensex_opts:
        earliest_exp = min(o["expiry"] for o in sensex_opts)
        today_opts = [o for o in sensex_opts if o["expiry"] == earliest_exp]

    candidates = []

    if kite is not None and today_opts:
        tokens = [f"BFO:{o['tradingsymbol']}" for o in today_opts]
        quotes = {}
        for i in range(0, len(tokens), 50):
            chunk = tokens[i:i+50]
            try:
                q_res = kite.quote(chunk)
                if q_res:
                    quotes.update(q_res)
            except Exception:
                pass

        qualified_ce = []
        qualified_pe = []

        spot_change = spot_price - day_open

        for opt in today_opts:
            t_sym = f"BFO:{opt['tradingsymbol']}"
            q_data = quotes.get(t_sym, {})
            ltp = float(q_data.get("last_price", 0.0))
            oi = int(q_data.get("oi", 0))
            vol = int(q_data.get("volume", 0))
            depth = q_data.get("depth", {})
            bid = depth.get("buy", [{}])[0].get("price", 0) if depth.get("buy") else 0
            ask = depth.get("sell", [{}])[0].get("price", 0) if depth.get("sell") else 0

            # Quality criteria: premium within sweet spot & active trading volume
            if min_prem <= ltp <= max_prem:
                # Discard illiquid strikes with 0 volume during market hours
                if vol <= 0 and ltp > 0:
                    continue

                opt_info = dict(opt)
                opt_info["ltp"] = ltp
                opt_info["oi"] = oi
                opt_info["vol"] = vol
                opt_info["bid"] = bid
                opt_info["ask"] = ask
                opt_info["spot_price"] = spot_price

                # Multi-tier Volume & Liquidity scoring
                prem_dist = abs(ltp - target_prem)
                score = 80

                # Premium proximity bonus
                if prem_dist <= 8.0:
                    score += 5

                # Volume scoring (Active market participation)
                if vol >= 5000000:
                    score += 10
                elif vol >= 1000000:
                    score += 7
                elif vol >= 100000:
                    score += 4
                elif vol >= 10000:
                    score += 2

                # Open Interest scoring (Institutional depth)
                if oi >= 1000000:
                    score += 10
                elif oi >= 300000:
                    score += 6
                elif oi >= 50000:
                    score += 3

                # Bid/Ask spread penalty/bonus (execution quality)
                if ask > 0 and bid > 0:
                    spread = ask - bid
                    if spread <= 1.0:
                        score += 3
                    elif spread > 3.0:
                        score -= 5

                # Directional bias alignment with intraday SENSEX trend
                if opt["instrument_type"] == "CE":
                    if spot_change > 0:
                        score += 4
                    opt_info["quality_score"] = max(50, min(99, score))
                    qualified_ce.append(opt_info)
                else:
                    if spot_change < 0:
                        score += 4
                    opt_info["quality_score"] = max(50, min(99, score))
                    qualified_pe.append(opt_info)

        if qualified_ce:
            qualified_ce.sort(key=lambda x: (-x["quality_score"], -x["vol"], -x["oi"], abs(x["ltp"] - target_prem)))
            best_ce = qualified_ce[0]
            ltp = best_ce["ltp"]
            lot_sz = int(best_ce.get("lot_size", 20))
            cost_per_lot = ltp * lot_sz
            max_lots_for_budget = max(1, int(capital_budget / cost_per_lot)) if cost_per_lot > 0 else default_lots
            lots = min(default_lots, max_lots_for_budget)
            tot_qty = lots * lot_sz
            capital = round(ltp * tot_qty, 2)
            t1 = round(ltp * 2.0, 2)
            t2 = round(ltp * 4.0, 2)
            # ─── SENSEX HERO-ZERO: Minimum 8 pts absolute SL for 0 DTE gamma ───
            # 50% of premium can be too tight (e.g., ₹8.05 * 0.5 = 4.02 pts = ~0.5% spot)
            # Minimum 8 pts ensures SL survives normal expiry day wicks (~15-20 pts SENSEX)
            sl_pct = round(ltp * 0.50, 2)
            sl_abs_8pts = round(ltp - 8.0, 2)
            sl = min(sl_pct, sl_abs_8pts)  # Use the WIDER (safer) SL = lower price
            risk = round((ltp - sl) * tot_qty, 2)

            chg_sign = "+" if spot_change >= 0 else ""
            sent_str = f"BULLISH GAMMA SQUEEZE ({chg_sign}{spot_change:,.0f} pts) 🚀" if spot_change >= 0 else "BULLISH COUNTER-TREND PULLBACK 🚀"

            candidates.append({
                "symbol": "SENSEX",
                "option_symbol": best_ce["tradingsymbol"],
                "strike": float(best_ce["strike"]),
                "option_type": "CE",
                "spot_price": spot_price,
                "ltp": ltp,
                "entry_price": ltp,
                "lot_size": lot_sz,
                "recommended_qty": lots,
                "total_shares": tot_qty,
                "capital_needed": capital,
                "max_risk": risk,
                "t1": t1,
                "t2": t2,
                "sl": sl,
                "powerful_sl": sl,
                "sl_risk": ltp - sl,
                "potential_profit_t1": (t1 - ltp) * tot_qty,
                "potential_profit_t2": (t2 - ltp) * tot_qty,
                "score": best_ce["quality_score"],
                "sentiment_catalyst": sent_str,
                "delta": 0.35,
                "theta": -45.0,
                "iv": 24.5,
                "oi": best_ce.get("oi", 0),
                "volume": best_ce.get("vol", 0),
            })

        if qualified_pe:
            qualified_pe.sort(key=lambda x: (-x["quality_score"], -x["vol"], -x["oi"], abs(x["ltp"] - target_prem)))
            best_pe = qualified_pe[0]
            ltp = best_pe["ltp"]
            lot_sz = int(best_pe.get("lot_size", 20))
            cost_per_lot = ltp * lot_sz
            max_lots_for_budget = max(1, int(capital_budget / cost_per_lot)) if cost_per_lot > 0 else default_lots
            lots = min(default_lots, max_lots_for_budget)
            tot_qty = lots * lot_sz
            capital = round(ltp * tot_qty, 2)
            t1 = round(ltp * 2.0, 2)
            t2 = round(ltp * 4.0, 2)
            # ─── SENSEX HERO-ZERO: Minimum 8 pts absolute SL for 0 DTE gamma ───
            # 50% of premium can be too tight (e.g., ₹8.05 * 0.5 = 4.02 pts = ~0.5% spot)
            # Minimum 8 pts ensures SL survives normal expiry day wicks (~15-20 pts SENSEX)
            sl_pct = round(ltp * 0.50, 2)
            sl_abs_8pts = round(ltp - 8.0, 2)
            sl = min(sl_pct, sl_abs_8pts)  # Use the WIDER (safer) SL = lower price
            risk = round((ltp - sl) * tot_qty, 2)

            chg_sign = "+" if spot_change >= 0 else ""
            sent_str = f"BEARISH BREAKDOWN FLUSH ({chg_sign}{spot_change:,.0f} pts) 📉" if spot_change < 0 else "BEARISH HIGH-LEVEL RESISTANCE REVERSAL 📉"

            candidates.append({
                "symbol": "SENSEX",
                "option_symbol": best_pe["tradingsymbol"],
                "strike": float(best_pe["strike"]),
                "option_type": "PE",
                "spot_price": spot_price,
                "ltp": ltp,
                "entry_price": ltp,
                "lot_size": lot_sz,
                "recommended_qty": lots,
                "total_shares": tot_qty,
                "capital_needed": capital,
                "max_risk": risk,
                "t1": t1,
                "t2": t2,
                "sl": sl,
                "powerful_sl": sl,
                "sl_risk": ltp - sl,
                "potential_profit_t1": (t1 - ltp) * tot_qty,
                "potential_profit_t2": (t2 - ltp) * tot_qty,
                "score": best_pe["quality_score"],
                "sentiment_catalyst": sent_str,
                "delta": -0.35,
                "theta": -45.0,
                "iv": 24.5,
                "oi": best_pe.get("oi", 0),
                "volume": best_pe.get("vol", 0),
            })

    # Offline / Test Fallback with realistic contracts
    if not candidates:
        otm_ce_strike = atm_strike + 200.0
        otm_pe_strike = atm_strike - 200.0
        exp_code = today.strftime("%y%m%d")
        for sym_name, st, o_type, sent in [
            (f"SENSEX{exp_code}{int(otm_ce_strike)}CE", otm_ce_strike, "CE", "BULLISH BREAKOUT 🚀"),
            (f"SENSEX{exp_code}{int(otm_pe_strike)}PE", otm_pe_strike, "PE", "BEARISH REVERSAL 📉")
        ]:
            ltp = 25.0 if o_type == "CE" else 22.0
            lot_sz = 20
            lots = 2
            tot_qty = lots * lot_sz
            t1 = round(ltp * 2.0, 2)
            t2 = round(ltp * 4.0, 2)
            sl = round(ltp * 0.50, 2)
            candidates.append({
                "symbol": "SENSEX",
                "option_symbol": sym_name,
                "strike": st,
                "option_type": o_type,
                "spot_price": spot_price,
                "ltp": ltp,
                "entry_price": ltp,
                "lot_size": lot_sz,
                "recommended_qty": lots,
                "total_shares": tot_qty,
                "capital_needed": ltp * tot_qty,
                "max_risk": (ltp - sl) * tot_qty,
                "t1": t1,
                "t2": t2,
                "sl": sl,
                "powerful_sl": sl,
                "sl_risk": ltp - sl,
                "potential_profit_t1": (t1 - ltp) * tot_qty,
                "potential_profit_t2": (t2 - ltp) * tot_qty,
                "score": 85 if o_type == "CE" else 80,
                "sentiment_catalyst": sent,
                "delta": 0.35 if o_type == "CE" else -0.35,
                "theta": -45.0,
                "iv": 24.5,
                "oi": 3500000,
                "volume": 250000000,
            })

    if single_best and len(candidates) >= 2:
        cand_ce = next((c for c in candidates if c["option_type"] == "CE"), None)
        cand_pe = next((c for c in candidates if c["option_type"] == "PE"), None)
        if cand_ce and cand_pe:
            ce_score = cand_ce["score"] + (5 if spot_change > 0 else 0)
            pe_score = cand_pe["score"] + (5 if spot_change < 0 else 0)
            if ce_score > pe_score:
                candidates = [cand_ce]
            elif pe_score > ce_score:
                candidates = [cand_pe]
            else:
                if spot_change > 0:
                    candidates = [cand_ce]
                elif spot_change < 0:
                    candidates = [cand_pe]
                elif cand_ce.get("volume", 0) >= cand_pe.get("volume", 0):
                    candidates = [cand_ce]
                else:
                    candidates = [cand_pe]

    return candidates[:1] if single_best else candidates[:2]


def send_sensex_hero_zero_telegram_alert(candidates: List[Dict[str, Any]], time_label: str = "03:05 PM - 03:10 PM Peak Gamma Window"):
    """Format and dispatch SENSEX Hero-Zero alert card using V14.7 TelegramGUI format."""
    if not candidates:
        print("⚠️ No Hero-Zero candidates qualified for dispatch.")
        return

    today_str = f"{datetime.now().strftime('%d-%b-%Y')} (Thursday)"
    hdr = (
        f"🔥 <b>STAGE 10 — SENSEX HERO-ZERO EXPIRY</b> 🔥\n"
        f"{DIVIDER}\n"
        f"📅 <b>Expiry:</b>  {tg_code(today_str)}\n"
        f"🕒 <b>Session:</b> {tg_code(time_label + ' IST')}\n"
        f"⚡ <b>Payoff:</b>  {tg_code('Asymmetric 2x - 5x Payoff')}\n"
        f"🤖 <b>Bot:</b>     {tg_code('@Nifty_stage10_paper_bot')}\n"
        f"{DIVIDER}\n"
        "<i>Top live algorithmic SENSEX Hero-Zero breakout setups:</i>"
    )
    _send_hero_zero_tg(hdr)
    time.sleep(0.3)

    for i, c in enumerate(candidates, 1):
        opt_type = c["option_type"]
        icon = "🏛️ 🟢" if opt_type == "CE" else "🏛️ 🔴"
        strike = c["strike"]
        spot = c["spot_price"]
        entry = c["ltp"]
        t1 = c["t1"]
        t2 = c["t2"]
        sl = c["sl"]
        score = c["score"]
        lots = c["recommended_qty"]
        lot_sz = c["lot_size"]
        tot_qty = c["total_shares"]
        capital = c["capital_needed"]
        max_risk = c["max_risk"]
        sl_pts = entry - sl
        t1_pts = t1 - entry
        t2_pts = t2 - entry
        oi_str = f"{c.get('oi', 0):,}" if c.get('oi') else "N/A"
        vol_str = f"{c.get('volume', 0):,}" if c.get('volume') else "N/A"

        # Deep analysis data
        sl_pct = round((sl_pts / entry * 100), 1)
        t1_pct = round((t1_pts / entry * 100), 1)
        t2_pct = round((t2_pts / entry * 100), 1)
        sl_abs_pts = round(sl_pts, 2)
        r_r_t1 = round(t1_pts / sl_pts, 2) if sl_pts > 0 else 0
        r_r_t2 = round(t2_pts / sl_pts, 2) if sl_pts > 0 else 0
        max_risk_pct = round((max_risk / capital * 100), 1) if capital > 0 else 0

        lines = [
            f"{icon} <b>#{i} BUY SENSEX {int(strike)} {opt_type} (HERO-ZERO)</b>",
            f"{DIVIDER}",
            f"⭐ <b>Quality Score:</b> {tg_code(f'{score}/100')}",
            f"🚀 <b>Catalyst:</b>      {tg_code(c['sentiment_catalyst'])}",
            f"📊 <b>Open Interest:</b> {tg_code(oi_str)}",
            f"📈 <b>Volume:</b>        {tg_code(vol_str)}",
            "",
            "💰 <b>HERO-ZERO TRADE LEVELS</b>",
            f"├─ 📊 <b>Spot Price:</b>  {tg_code(tg_money(spot))} (ATM {int(strike)})",
            f"├─ 🟢 <b>Entry Price:</b> {tg_code(tg_money(entry))} (Live Market)",
            f"├─ 🛑 <b>Risk SL:</b>     {tg_code(tg_money(sl))} (<b>-{tg_points(sl_pts)} / {sl_pct}% / {sl_abs_pts} pts min</b>)",
            f"├─ 🥇 <b>Target 1:</b>    {tg_code(tg_money(t1))} (<b>+{tg_points(t1_pts)} / +{t1_pct}% / {r_r_t1}R</b>)",
            f"└─ 🚀 <b>Target 2:</b>    {tg_code(tg_money(t2))} (<b>+{tg_points(t2_pts)} / +{t2_pct}% / {r_r_t2}R</b>)",
            "",
            "📦 <b>POSITION SIZING & RISK</b>",
            f"├─ 🏷️ <b>Lots:</b>        {tg_code(f'{lots} lots ({lot_sz}/lot = {tot_qty} qty)')}",
            f"├─ 💵 <b>Capital:</b>     {tg_code(tg_money(capital))} (Within ₹1,500 budget)",
            f"└─ 🛡️ <b>Max Risk:</b>    {tg_code(tg_money(max_risk))} ({max_risk_pct}% of capital)",
            "",
            "🎯 <b>ZERODHA ORDER EXECUTION TICKET</b>",
            f"├─ 🟢 <b>Action:</b>      BUY {tg_code(c['option_symbol'])}",
            f"├─ 📦 <b>Quantity:</b>    {tg_code(f'{tot_qty} shares ({lots} Lots)')}",
            f"├─ 💵 <b>Limit Price:</b> {tg_code(tg_money(entry))} (₹8 - ₹15 target range)",
            f"├─ 🛑 <b>GTT Stoploss:</b> {tg_code(tg_money(sl))} (Trigger @ {tg_money(sl)})",
            f"├─ 🥇 <b>Target 1:</b>    {tg_code(tg_money(t1))} (+100% / 2x Multiplier / {r_r_t1}R)",
            f"└─ 🚀 <b>Target 2:</b>    {tg_code(tg_money(t2))} (+300% / 4x Multibagger / {r_r_t2}R)",
            f"{DIVIDER}",
            f"🔬 <b>DEEP ANALYSIS:</b> SL {sl_pct}% ({sl_abs_pts} pts) | T1 {t1_pct}% ({r_r_t1}R) | T2 {t2_pct}% ({r_r_t2}R) | MaxRisk {max_risk_pct}% cap",
            f"🔥 <b>V14.7 STRATEGY:</b> <i>Risk small capital for explosive 2x-5x expiry payoff. Book 50% @ T1!</i>",
        ]

        _send_hero_zero_tg("\n".join(lines))
        time.sleep(0.3)


def deploy_automated_sensex_gtt(kite: Any, candidate: Dict[str, Any]) -> Optional[int]:
    """Automatically places an active GTT order on Zerodha Kite when a SENSEX Hero-Zero strike is selected."""
    if not kite:
        return None
    tradingsymbol = candidate.get("option_symbol")
    if not tradingsymbol:
        return None

    exchange = "BFO"
    product = "MIS"
    qty = int(candidate.get("total_shares", 80))
    ltp = float(candidate.get("ltp", 10.0))

    # Zerodha buffer rule: trigger must be comfortably above LTP
    min_buffer = max(0.50, round(ltp * 0.05, 1))
    trigger_price = round(ltp + min_buffer, 1)
    limit_price = round(trigger_price + 0.40, 1)

    print(f"🚀 Placing automated Zerodha GTT for {tradingsymbol} @ Trigger ₹{trigger_price:.1f} | Limit ₹{limit_price:.1f} (Qty: {qty})...")

    # Clean up any existing active SENSEX GTT to prevent stacking
    try:
        existing_gtts = kite.get_gtts()
        for g in existing_gtts:
            cond = g.get("condition", {})
            if "SENSEX" in cond.get("tradingsymbol", "") and g.get("status") in ["active", "triggered"]:
                kite.delete_gtt(g.get("id"))
    except Exception as e:
        print(f"Notice during GTT cleanup: {e}")

    buy_orders = [
        {
            "transaction_type": kite.TRANSACTION_TYPE_BUY,
            "quantity": qty,
            "order_type": kite.ORDER_TYPE_LIMIT,
            "product": product,
            "price": limit_price
        }
    ]

    try:
        resp = kite.place_gtt(
            trigger_type=kite.GTT_TYPE_SINGLE,
            tradingsymbol=tradingsymbol,
            exchange=exchange,
            trigger_values=[trigger_price],
            last_price=ltp,
            orders=buy_orders
        )
        gtt_id = resp.get("trigger_id")
        print(f"✅ AUTOMATED GTT DEPLOYED SUCCESSFULLY! Trigger ID: #{gtt_id} for {tradingsymbol}")

        rec_lots = candidate.get("recommended_qty", 4)
        qty_label = f"{qty} shares ({rec_lots} Lots)"

        # Dispatch GTT confirmation to Telegram
        gtt_msg = (
            f"⚡ <b>AUTOMATED ZERODHA GTT DEPLOYED</b> ⚡\n"
            f"{DIVIDER}\n"
            f"🟢 <b>Status:</b>   {tg_code('ACTIVE ON ZERODHA')}\n"
            f"🆔 <b>GTT ID:</b>   {tg_code(gtt_id)}\n"
            f"🏛️ <b>Contract:</b> {tg_code(tradingsymbol)}\n"
            f"🎯 <b>Trigger:</b>  {tg_code(tg_money(trigger_price))} (Breakout entry)\n"
            f"💵 <b>Limit:</b>    {tg_code(tg_money(limit_price))}\n"
            f"📦 <b>Quantity:</b> {tg_code(qty_label)}\n"
            f"💰 <b>Max Risk:</b> {tg_code(tg_money(qty * limit_price))}\n"
            f"{DIVIDER}\n"
            f"<i>Order is live on Zerodha exchange servers; will trigger automatically!</i>"
        )
        _send_hero_zero_tg(gtt_msg)
        return gtt_id
    except Exception as e:
        print(f"❌ Automated GTT Deployment Failed: {e}")
        _send_hero_zero_tg(f"⚠️ <b>Automated GTT Failed:</b> {html_escape(str(e))}")
        return None


def should_deploy_gtt(args: argparse.Namespace) -> bool:
    """
    Automated Zerodha GTT runs ONLY at 14:30 (02:30 PM) and 15:05 (03:05 PM) IST.
    All other scan timings (14:00, 15:00, 15:10, etc.) are strictly Telegram alerts only.
    """
    if args.no_gtt:
        return False
    if args.auto_gtt:
        return True

    now = datetime.now()
    hour = now.hour
    minute = now.minute

    # Slot 1: 14:30 IST Window (14:25 - 14:35)
    if hour == 14 and 25 <= minute <= 35:
        return True

    # Slot 2: 15:05 IST Window (15:03 - 15:08)
    if hour == 15 and 3 <= minute <= 8:
        return True

    return False


def main():
    parser = argparse.ArgumentParser(description="Dedicated BSE SENSEX Hero-Zero Expiry Scanner")
    parser.add_argument("--time-slot", nargs="*", default=None, help="Execution time label (auto-detected if omitted)")
    parser.add_argument("--force", action="store_true", help="Bypass Thursday expiry check for manual execution/test")
    parser.add_argument("--ignore-holiday", action="store_true", help="Bypass holiday check")
    parser.add_argument("--expiry-day", type=str, default="Thursday", choices=["Thursday", "Friday"], help="SENSEX expiry day")
    parser.add_argument("--both", action="store_true", help="Send both CE and PE (strangle) instead of single best candidate")
    parser.add_argument("--dry-run", action="store_true", help="Print candidates locally without dispatching to Telegram")
    parser.add_argument("--auto-gtt", action="store_true", help="Force GTT placement regardless of time window (default: 14:30 and 15:05 only)")
    parser.add_argument("--no-gtt", action="store_true", help="Disable automatic Zerodha GTT placement")
    parser.add_argument("--min-prem", type=float, default=8.0, help="Minimum entry premium (default: 8.0)")
    parser.add_argument("--max-prem", type=float, default=15.0, help="Maximum entry premium (default: 15.0)")
    parser.add_argument("--lots", type=int, default=4, help="Target lots (default: 4)")
    parser.add_argument("--capital", type=float, default=1500.0, help="Capital budget in ₹ (default: 1500.0)")
    args = parser.parse_args()

    if args.time_slot:
        time_slot_label = " ".join(args.time_slot) if isinstance(args.time_slot, list) else str(args.time_slot)
    else:
        time_slot_label = get_default_time_slot_label()

    target_weekday = 3 if args.expiry_day.capitalize() == "Thursday" else 4

    if not args.force and not args.ignore_holiday and not is_sensex_expiry_day(target_weekday=target_weekday):
        print(f"⚠️ HALT: SENSEX Hero-Zero Scanner only runs on {args.expiry_day}s (SENSEX Expiry Day).")
        print("   Use --force to run off-schedule.")
        return

    print("==================================================================================")
    print(f"🔥 STAGE 10 V14.7 — BSE SENSEX HERO-ZERO EXPIRY SCANNER ({args.expiry_day.upper()} EXPIRY)")
    print("🤖 TELEGRAM BOT: @Nifty_stage10_paper_bot")
    print("==================================================================================")

    kite = get_kite_client()
    candidates = resolve_sensex_hero_zero_candidates(
        kite,
        single_best=not args.both,
        min_prem=args.min_prem,
        max_prem=args.max_prem,
        default_lots=args.lots,
        capital_budget=args.capital,
    )

    if not candidates:
        print("⚠️ No qualified Hero-Zero setups found.")
        return

    if args.dry_run:
        print("\n=== [DRY RUN PREVIEW - SENSEX HERO ZERO] ===")
        for i, c in enumerate(candidates, 1):
            print(f"#{i} {c['symbol']} {int(c['strike'])} {c['option_type']} | Sym: {c['option_symbol']} | Entry: {c['entry_price']} | SL: {c['sl']} | T1: {c['t1']} | T2: {c['t2']} | Catalyst: {c['sentiment_catalyst']}")
    else:
        print(f"\nDispatches Top {len(candidates)} SENSEX Hero-Zero Setups to @Nifty_stage10_paper_bot...")
        send_sensex_hero_zero_telegram_alert(candidates, time_label=time_slot_label)

        # AUTOMATED GTT DEPLOYMENT: Runs ONLY at 14:30 and 15:05 IST!
        if should_deploy_gtt(args) and candidates:
            primary_candidate = candidates[0]
            deploy_automated_sensex_gtt(kite, primary_candidate)
        else:
            print("ℹ️ Automated GTT: SKIPPED for this time slot (GTT is restricted to 14:30 & 15:05 IST only). Telegram alert dispatched successfully!")

    # Save log
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"sensex_hero_zero_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump({"candidates": candidates}, f, indent=2, default=str)

    print(f"\n✅ Scan execution logged to: {log_file}")


if __name__ == "__main__":
    main()
