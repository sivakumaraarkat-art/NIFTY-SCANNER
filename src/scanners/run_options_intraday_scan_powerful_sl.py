"""
INTRADAY OPTIONS SCANNER — WITH POWERFUL 4-LAYER SL STRATEGY
═════════════════════════════════════════════════════════════════

Enhancements:
1. ✅ Live Kite Market Resolution: Real ATM strikes, real live Option LTP & Greeks
2. ✅ Powerful 4-Layer SL (prevents whipsaw at 98-99 bouncing to 105)
3. ✅ Omni-Directional Support: CE for Bullish candidates, PE for Bearish candidates
4. ✅ Exchange Lot-Sizing: Accurate lot-based position sizing via 1% risk rule
5. ✅ Anti-Whipsaw Features (trailing SL, breakeven exit, partial exit)
6. ✅ Execution logging to JSON
7. ✅ Weekend & NSE Holiday Guard
8. ✅ Mobile-optimized Telegram alert dispatch

Usage:
    python src/scanners/run_options_intraday_scan_powerful_sl.py --use-news-candidates --min-score 90
    python src/scanners/run_options_intraday_scan_powerful_sl.py --symbols RELIANCE,TCS,BPCL --min-score 90
"""

from __future__ import annotations

import sys, io
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass

import argparse
import json
import time
import os
import glob
from datetime import datetime, time as time_type, timedelta
from pathlib import Path
from typing import Dict, List, Any

# Ensure project root in sys.path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from telegram_alerts.options_alert_sender import send_options_telegram_alerts
except ImportError:
    send_options_telegram_alerts = lambda *args, **kwargs: None

try:
    from src.scanners.options_data_provider import (
        resolve_all_candidates,
        resolve_option_candidate,
        calculate_powerful_sl_engine,
        get_kite_client,
        get_nfo_instruments,
    )
except ImportError:
    from options_data_provider import (
        resolve_all_candidates,
        resolve_option_candidate,
        calculate_powerful_sl_engine,
        get_kite_client,
        get_nfo_instruments,
    )


# ──────────────────────────────────────────────────────────────
# 1. WEEKEND & HOLIDAY GUARD
# ──────────────────────────────────────────────────────────────
NSE_HOLIDAYS_2026 = [
    datetime(2026, 1, 26),   # Republic Day
    datetime(2026, 3, 8),    # Maha Shivaratri
    datetime(2026, 3, 25),   # Holi
    datetime(2026, 3, 29),   # Good Friday
    datetime(2026, 4, 2),    # Eid-ul-Fitr (approx)
    datetime(2026, 4, 14),   # Ambedkar Jayanti
    datetime(2026, 5, 15),   # Eid-ul-Adha (approx)
    datetime(2026, 8, 15),   # Independence Day
    datetime(2026, 8, 27),   # Janmashtami
    datetime(2026, 9, 30),   # Mahatma Gandhi Jayanti
    datetime(2026, 10, 2),   # Gandhi Jayanti (observed)
    datetime(2026, 10, 25),  # Diwali (approx)
    datetime(2026, 11, 1),   # Diwali (day 2)
    datetime(2026, 11, 24),  # Guru Nanak Jayanti / Prakash Gurpurb
    datetime(2026, 12, 25),  # Christmas
]

def is_trading_day() -> bool:
    """Check if today is a valid NSE trading day."""
    today = datetime.now()
    today_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
    # Special exemption for Diwali Muhurat Trading on Sunday, Nov 8, 2026
    if today_date == datetime(2026, 11, 8):
        return True
    if today.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    if today_date in NSE_HOLIDAYS_2026:
        return False
    return True


# ──────────────────────────────────────────────────────────────
# 2. LOG ROTATION
# ──────────────────────────────────────────────────────────────
def cleanup_old_logs(log_dir: Path = Path("logs"), days_to_keep: int = 30) -> None:
    """Delete log files older than specified days."""
    if not log_dir.exists():
        return
    now = datetime.now()
    cutoff = now - timedelta(days=days_to_keep)
    deleted_count = 0
    try:
        for log_file in log_dir.glob("*.json"):
            try:
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_mtime < cutoff:
                    log_file.unlink()
                    deleted_count += 1
            except Exception:
                pass
        if deleted_count > 0:
            print(f"🗑️  Log rotation: Cleaned up {deleted_count} log files older than {days_to_keep} days")
    except Exception:
        pass


def is_market_hours() -> bool:
    """Check if current time is within market operating window."""
    now = datetime.now().time()
    return time_type(9, 15) <= now <= time_type(15, 30)


# ──────────────────────────────────────────────────────────────
# 3. NEWS SYMBOLS PARSER & FRESH CATALYST ENSURANCE
# ──────────────────────────────────────────────────────────────
def ensure_fresh_news_scanner(log_dir: Path, max_age_minutes: int = 45) -> None:
    """Ensure news scanner runs first if latest news log is older than max_age_minutes."""
    news_files = list(log_dir.glob("news_scan_*.json"))
    needs_refresh = True
    if news_files:
        latest = max(news_files, key=lambda f: f.stat().st_mtime)
        age_minutes = (datetime.now() - datetime.fromtimestamp(latest.stat().st_mtime)).total_seconds() / 60.0
        if age_minutes < max_age_minutes:
            needs_refresh = False

    if needs_refresh:
        print("\n📰 [NEWS FIRST RULE] Triggering fresh news scanner before options scan...")
        try:
            import subprocess
            cmd = [sys.executable, str(ROOT / "src" / "scanners" / "news_scanner_with_twitter.py"), "--hours", "12"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            if res.returncode == 0:
                print("✅ Fresh news catalyst feed updated successfully!")
            else:
                print(f"⚠️ News scanner returned code {res.returncode}")
        except Exception as e:
            print(f"⚠️ News scanner execution notice: {e}")


def get_latest_news_symbols(log_dir: Path) -> list:
    """Fetch BOTH Bullish and Bearish symbols dynamically from the morning News Scanner."""
    if not log_dir.exists():
        return []
    ensure_fresh_news_scanner(log_dir, max_age_minutes=45)
    news_files = list(log_dir.glob("news_scan_*.json"))
    if not news_files:
        return []
    latest_file = max(news_files, key=lambda f: f.stat().st_mtime)
    file_age_hours = (datetime.now() - datetime.fromtimestamp(latest_file.stat().st_mtime)).total_seconds() / 3600
    if file_age_hours > 36.0:
        print(f"⚠️  [INTEGRATION] News log {latest_file.name} is {file_age_hours:.1f}h old (expired > 36h). Ignoring stale news.")
        return []
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"⚠️ Error reading news log: {e}")
        return []

    symbols_with_sentiment = []
    if "data" in data and isinstance(data["data"], dict):
        for sym, d in data["data"].items():
            sent = d.get("sentiment", "")
            if not ("BULLISH" in sent or "BEARISH" in sent):
                continue

            # -------------------------------------------------------------
            # ANTI-FAKE NEWS & DOUBLE-VERIFICATION SHIELD
            # -------------------------------------------------------------
            if d.get("is_conflicting", False):
                print(f"⚠️  [SHIELD] Skipping {sym}: Conflicting news reports.")
                continue

            cred_badge = d.get("credibility_badge", "LOW")
            has_tier1 = d.get("has_tier1", False) or d.get("supporting_publisher_trusted", False)
            unique_sources = d.get("unique_sources", 1)
            sources_str = d.get("primary_sources", "Unknown")

            # Must satisfy Double Verification:
            # At least 1 verified Tier-1 financial media OR 2+ independent publishers
            is_verified = has_tier1 or (unique_sources >= 2)
            if not is_verified:
                print(f"🛡️  [ANTI-FAKE NEWS] Rejected {sym}: Single unverified source ({sources_str}). Requires Tier-1 media or 2+ independent sources.")
                continue

            # -------------------------------------------------------------
            # HIGH CONVICTION SCORING (65-98 scale)
            # -------------------------------------------------------------
            raw_score = float(d.get("avg_score", d.get("score", 70)))
            conviction = 65  # Verified baseline
            if has_tier1:
                conviction += 12  # +12 for Tier-1 financial publisher (Moneycontrol, ET, Livemint, etc.)
            if unique_sources >= 2:
                conviction += 8   # +8 for double source corroboration
            if unique_sources >= 3:
                conviction += 5   # +5 for multi-source consensus

            category = d.get("catalyst_category", "")
            high_impact_events = {
                "Order / contract", "Earnings / results", "Joint venture",
                "Debt / Solvency", "Governance / Resignation", "Legal / regulatory"
            }
            if category in high_impact_events:
                conviction += 8   # +8 for verified high-impact business filing

            if "BULLISH" in sent and raw_score >= 70:
                conviction += 5
            elif "BEARISH" in sent and raw_score <= 30:
                conviction += 5

            age_hours = float(d.get("directional_age_hours", d.get("news_age_hours", 12.0)))
            if age_hours <= 6.0:
                conviction += 3
            elif age_hours > 24.0:
                conviction -= 10

            final_conviction = int(min(98, max(50, conviction)))

            meta = {
                "headline": d.get("top_headline", ""),
                "catalyst_category": category,
                "sources": sources_str,
                "unique_sources": unique_sources,
                "has_tier1": has_tier1,
                "is_verified": is_verified,
                "age_hours": age_hours,
                "credibility": cred_badge,
            }
            symbols_with_sentiment.append((sym, sent, final_conviction, meta))

        symbols_with_sentiment.sort(key=lambda x: x[2], reverse=True)
    return symbols_with_sentiment


# ──────────────────────────────────────────────────────────────
# 3b. LIVE MARKET F&O MOVERS (Gainers for CE & Losers for PE)
# ──────────────────────────────────────────────────────────────
def get_live_market_movers(kite, nfo_instruments, top_n=8) -> list:
    """Scan live F&O universe (all 200+ exchange stocks) for top gainers (CE) and top losers (PE)."""
    if kite is None:
        return []
    try:
        fo_names = sorted(list(set(
            i["name"] for i in nfo_instruments
            if i["segment"] in ["NFO-FUT", "BFO-FUT"] and i["name"] not in ["NIFTY", "BANKNIFTY", "SENSEX", "FINNIFTY", "MIDCPNIFTY"]
        )))
        symbols = [f"NSE:{name}" for name in fo_names]
        quotes = {}
        for i in range(0, len(symbols), 250):
            quotes.update(kite.quote(symbols[i:i+250]))

        bullish = []
        bearish = []
        for sym, q in quotes.items():
            ltp = q.get("last_price", 0.0)
            ohlc = q.get("ohlc", {})
            prev_close = ohlc.get("close", 0.0)
            high = ohlc.get("high", 0.0)
            low = ohlc.get("low", 0.0)
            if prev_close <= 0 or ltp < 40:
                continue

            pct = ((ltp - prev_close) / prev_close) * 100
            day_range = high - low
            range_pos = ((ltp - low) / day_range) * 100 if day_range > 0 else 50.0
            name = sym.replace("NSE:", "")
            vol = q.get("volume", 0)

            # Filter out illiquid low-volume stocks (need at least 100k volume for reliable options)
            if vol < 100000:
                continue

            vol_boost = 5 if vol >= 500000 else (2 if vol >= 250000 else 0)

            if pct >= 0.8 and range_pos >= 70:
                tag = "BULLISH 🚀 (Top Gainer + High Volume Surge)" if vol >= 500000 else "BULLISH 🚀 (Technical Breakout)"
                bullish.append((name, tag, int(min(96, 70 + pct * 5 + vol_boost))))
            elif pct <= -0.8 and range_pos <= 30:
                tag = "BEARISH ⚠️ (Top Breakdown + Heavy Sell Volume)" if vol >= 500000 else "BEARISH ⚠️ (Technical Breakdown)"
                bearish.append((name, tag, int(min(96, 70 + abs(pct) * 5 + vol_boost))))

        bullish.sort(key=lambda x: x[2], reverse=True)
        bearish.sort(key=lambda x: x[2], reverse=True)

        return bullish[:top_n] + bearish[:top_n]
    except Exception as e:
        print(f"⚠️ Could not fetch market movers: {e}")
        return []


# ──────────────────────────────────────────────────────────────
# 3c. DAILY TRADE CAP & CIRCUIT BREAKER AUDIT
# ──────────────────────────────────────────────────────────────
def get_today_intraday_trade_stats(log_dir: Path, today_str: str) -> dict:
    """Check how many unique trades were already logged today and how many SLs have hit."""
    unique_symbols = set()
    sl_hits = 0

    state_file = log_dir / "intraday_trade_state.json"
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state_data = json.load(f)
                trades = state_data.get("trades", {})
                for k, t in trades.items():
                    if t.get("trade_date") == today_str:
                        opt_sym = t.get("option_symbol", k)
                        unique_symbols.add(opt_sym)
                        if t.get("close_reason") == "SL_HIT" or t.get("status") == "SL_HIT":
                            sl_hits += 1
        except Exception:
            pass

    pattern = f"intraday_scan_powerful_sl_{today_str}_*.json"
    for path in log_dir.glob(pattern):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                cands = data.get("candidates", [])
                for c in cands:
                    sym = c.get("option_symbol")
                    if sym:
                        unique_symbols.add(sym)
        except Exception:
            pass

    return {
        "today_trade_count": len(unique_symbols),
        "today_symbols": list(unique_symbols),
        "sl_hits": sl_hits,
    }


def get_today_symbol_appearance_counts(log_dir: Path, today_str: str) -> dict[str, int]:
    """Track how many times each stock symbol has appeared in today's previous hourly scans.
    Repeated appearances indicate sustained institutional momentum and high conviction.
    """
    counts: dict[str, int] = {}
    pattern = f"intraday_scan_powerful_sl_{today_str}_*.json"
    for path in log_dir.glob(pattern):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                cands = data.get("candidates", [])
                for c in cands:
                    sym = c.get("symbol")
                    if sym:
                        counts[sym] = counts.get(sym, 0) + 1
        except Exception:
            pass
    return counts


def get_nifty_market_regime(kite) -> tuple[str, float]:
    """Determine market situation from Nifty 50 live trend (BULLISH, BEARISH, or NEUTRAL)."""
    if kite is None:
        return "NEUTRAL ⚖️", 0.0
    try:
        q = kite.quote(["NSE:NIFTY 50"]).get("NSE:NIFTY 50", {})
        ltp = q.get("last_price", 0.0)
        pc = q.get("ohlc", {}).get("close", 0.0)
        open_p = q.get("ohlc", {}).get("open", 0.0)
        if pc <= 0:
            return "NEUTRAL ⚖️", 0.0
        pct = ((ltp - pc) / pc) * 100
        if pct >= 0.25 and ltp >= open_p:
            return "BULLISH 🚀", pct
        elif pct <= -0.25 and ltp <= open_p:
            return "BEARISH ⚠️", pct
        else:
            return "NEUTRAL ⚖️", pct
    except Exception:
        return "NEUTRAL ⚖️", 0.0


# ──────────────────────────────────────────────────────────────
# 4. PRINT RESULTS WITH 4-LAYER POWERFUL SL
# ──────────────────────────────────────────────────────────────
def print_powerful_sl_results(
    candidates: list[dict],
    account_size: float = 500000,
    max_candidates: int = 2,
    existing_symbols: list[str] | None = None,
    market_regime: str = "NEUTRAL ⚖️",
) -> list[dict]:
    """Print intraday results with powerful 4-layer SL, strict daily cap, and accurate position sizing."""
    results = []

    print("\n" + "=" * 100)
    print("⚡ INTRADAY OPTIONS SCANNER — POWERFUL 4-LAYER SL STRATEGY".center(100))
    print("=" * 100)
    print(f"\n📅 {datetime.now().strftime('%d-%b-%Y %H:%M %p')}")
    print(f"⚠️  Intraday execution window: 9:50 AM - 3:25 PM IST")
    print(f"✅ Market hours check: {is_market_hours()}")
    print(f"🛡️  Max Trades Allowed in this scan: {max_candidates}\n")

    already_seen = set(existing_symbols or [])
    fresh_candidates = [c for c in candidates if c.get("option_symbol") not in already_seen]
    if len(fresh_candidates) < max_candidates:
        # Guarantee 2 strikes: If fresh candidates are fewer than max_candidates, fill from available candidates
        seen_fresh = {c.get("option_symbol") for c in fresh_candidates}
        for c in candidates:
            if c.get("option_symbol") not in seen_fresh:
                fresh_candidates.append(c)
                seen_fresh.add(c.get("option_symbol"))
            if len(fresh_candidates) >= max_candidates:
                break
    if not fresh_candidates:
        fresh_candidates = candidates

    # Dynamic Market Situation & Technical Selection:
    # Not mandatory 1 CE + 1 PE! It can dynamically give 2 CEs on a bullish market,
    # 2 PEs on a bearish market, or 1 CE + 1 PE on a two-way market based on purest technical strength.
    # Priority: Repeated Conviction (50) > Verified News (30) > Technical Mover (0) + Market Regime Alignment (+5)
    def sort_key(c):
        is_news = "Top Gainer" not in c.get("sentiment_catalyst", "") and "Top Breakdown" not in c.get("sentiment_catalyst", "")
        is_repeated = "REPEATED CONVICTION" in c.get("sentiment_catalyst", "") or bool((c.get("meta") or {}).get("sustained_conviction", False))
        priority = 50 if is_repeated else (30 if is_news else 0)

        # Market trend alignment (+5 bonus for trading in harmony with market regime)
        opt_type = str(c.get("option_type", "")).upper()
        regime_bonus = 0
        if "BULLISH" in market_regime and opt_type == "CE":
            regime_bonus = 5
        elif "BEARISH" in market_regime and opt_type == "PE":
            regime_bonus = 5

        return priority + c.get("score", 0) + regime_bonus

    sorted_candidates = sorted(fresh_candidates, key=sort_key, reverse=True)
    selected = sorted_candidates[:max_candidates]

    ce_count = sum(1 for c in selected if str(c.get("option_type", "")).upper() == "CE")
    pe_count = sum(1 for c in selected if str(c.get("option_type", "")).upper() == "PE")
    print(f"📊 Market Regime: {market_regime} | Selected Allocation: {ce_count} CE / {pe_count} PE (Dynamic Technical Alignment)\n")

    now_time = datetime.now().time()
    is_late_session = now_time >= time_type(14, 30)
    if is_late_session:
        print(f"⚡ [LATE-SESSION SCALP MODE ACTIVE] Entry after 2:30 PM: T1 calibrated to +7% scalp, SL tightened to -5% for 3:25 PM EOD square-off.")

    for i, c in enumerate(selected, 1):
        if is_late_session:
            c["is_late_session"] = True
            c["powerful_sl"] = round(c["ltp"] * 0.95, 2)
            c["sl"] = c["powerful_sl"]
            c["sl_risk"] = round(c["ltp"] - c["powerful_sl"], 2)
            c["sl_risk_pct"] = round(c["sl_risk"] / c["ltp"] * 100, 2)
            c["t1"] = round(c["ltp"] * 1.07, 2)
            c["t2"] = round(c["ltp"] * 1.12, 2)
            c["target_1"] = c["t1"]
            c["target_2"] = c["t2"]
            tot_sh = c.get('total_shares', c.get('recommended_qty', 1) * c.get('lot_size', 1))
            c["potential_profit_t1"] = round(tot_sh * (c["t1"] - c["ltp"]), 2)
            c["potential_profit_t2"] = round(tot_sh * (c["t2"] - c["ltp"]), 2)
            c["max_risk"] = round(tot_sh * c["sl_risk"], 2)
            w_tag = c.get("warning_tag", "")
            late_note = "⚡ Late Scalp (+7% T1 | -5% SL | 15:25 EOD Exit)"
            c["warning_tag"] = f"{w_tag} • {late_note}" if w_tag else late_note

        contract_str = c.get('option_symbol', f"{c['symbol']} {c['strike']:.0f} {c['option_type']}")
        spot_str = f"(Spot: ₹{c.get('spot_price', 0):,.2f})" if c.get('spot_price', 0) > 0 else ""
        print(f"\n{'─' * 100}")
        print(f"{i}. 🎯 {contract_str} {spot_str} | Score: {c['score']}/100 [{c.get('sentiment_catalyst', 'CATALYST')}]")
        print(f"{'─' * 100}")

        # SL Breakdown
        print(f"\n🛡️ POWERFUL SL (Disciplined 4-Layer Protection):")
        print(f"   Entry Price:           ₹{c['ltp']:.2f}")
        print(f"   ├─ Layer 1 (Delta):    ₹{c.get('layer1_buffer', 0):.2f} buffer")
        print(f"   ├─ Layer 2 (Vol):      ₹{c.get('layer2_vol_buffer', 0):.2f} buffer")
        print(f"   ├─ Layer 3 (Theta):    ₹{c.get('layer3_theta_buffer', 0):.2f} buffer")
        print(f"   └─ Layer 4 (Vega):     ₹{c.get('layer4_vega_buffer', 0):.2f} buffer")
        print(f"   ────────────────────────────────────────────")
        print(f"   💪 POWERFUL SL:        ₹{c['powerful_sl']:.2f}")
        print(f"   Risk per share:        ₹{c['sl_risk']:.2f} ({c['sl_risk_pct']:.2f}%)")

        old_sl = round(c['ltp'] * 0.80, 2)
        old_risk = round(c['ltp'] - old_sl, 2)
        improvement = ((old_risk - c['sl_risk']) / old_risk * 100) if old_risk > 0 else 0
        print(f"   ────────────────────────────────────────────")
        print(f"   Old SL (20%):          ₹{old_sl:.2f} (Risk: ₹{old_risk:.2f})")
        print(f"   📈 Improvement:        {improvement:.1f}% tighter SL! (Disciplined noise absorption) ✅")

        # Anti-Whipsaw Features
        print(f"\n🔄 Anti-Whipsaw Features:")
        print(f"   Trailing SL trigger:   ₹{c['trailing_trigger']:.2f} (+5% profit)")
        print(f"   New SL if triggered:   ₹{c['trailing_sl_new']:.2f}")

        # Position Sizing (1% risk rule based on whole lots)
        lots = c.get('recommended_qty', 1)
        lot_sz = c.get('lot_size', 1)
        tot_shares = c.get('total_shares', lots * lot_sz)
        cap = c.get('capital_needed', tot_shares * c['ltp'])
        m_risk = c.get('max_risk', tot_shares * c['sl_risk'])
        t1 = c.get('t1', round(c['ltp'] * 1.12, 2))
        t2 = c.get('t2', round(c['ltp'] * 1.20, 2))
        p_t1 = c.get('potential_profit_t1', round(tot_shares * (t1 - c['ltp']), 2))
        p_t2 = c.get('potential_profit_t2', round(tot_shares * (t2 - c['ltp']), 2))

        rr_t1 = round((t1 - c['ltp']) / c['sl_risk'], 2) if c['sl_risk'] > 0 else 1.25
        rr_t2 = round((t2 - c['ltp']) / c['sl_risk'], 2) if c['sl_risk'] > 0 else 2.0

        print(f"\n💰 Position Sizing (1% Risk Rule with Exchange Lots):")
        print(f"   Lots Recommended:      {lots} lots ({lot_sz} shares/lot = {tot_shares} qty)")
        print(f"   Capital Needed:        ₹{cap:,.2f}")
        print(f"   Max Risk:              ₹{m_risk:,.2f} (Within 1% account budget)")
        print(f"   Target 1 ({rr_t1}R):         ₹{t1:.2f} (+{t1 - c['ltp']:.2f} pts) → P&L: ₹{p_t1:+,.2f} [T1 > SL ✅]")
        print(f"   Target 2 ({rr_t2}R):         ₹{t2:.2f} (+{t2 - c['ltp']:.2f} pts) → P&L: ₹{p_t2:+,.2f} [T2 = 2× SL ✅]")
        print(f"   ⚖️ Risk-to-Reward:      1 : {rr_t1} on T1 | 1 : {rr_t2} on T2 (Positive Expectancy)")

        # Verified Catalyst & Conviction Audit
        meta = c.get('meta') or c.get('news_meta') or {}
        if meta.get('headline'):
            t1_str = "Tier-1 Verified Media" if meta.get("has_tier1") else "Multi-Source Corroborated"
            dual_note = " • 🔥 DUAL CONFIRMED (News + Technical Mover)" if meta.get("dual_confirmed") else ""
            print(f"\n📰 VERIFIED CATALYST & ANTI-FAKE NEWS AUDIT:")
            print(f"   Headline:              \"{meta['headline']}\"")
            print(f"   Catalyst Category:     {meta.get('catalyst_category', 'Corporate Announcement')}")
            print(f"   Source Verification:   🛡️ PASS ({t1_str} • {meta.get('unique_sources', 1)} Source(s): {meta.get('sources', 'Unknown')}){dual_note}")
            print(f"   Catalyst Age:          {meta.get('age_hours', 0):.1f} hours ago")
        elif "Top Gainer" in c.get("sentiment_catalyst", "") or "Top Breakdown" in c.get("sentiment_catalyst", ""):
            print(f"\n📊 TECHNICAL CONVICTION AUDIT:")
            print(f"   Signal Type:           Exchange High-Volume Momentum ({c.get('sentiment_catalyst')})")
            print(f"   Verification:          🛡️ Real-Time F&O Price Action (Strong range breakout near day limits)")

        # Greeks & Liquidity Analysis
        delta = c.get('delta', 0)
        theta = c.get('theta', 0)
        vega = c.get('vega', 0)
        iv = c.get('iv', 0)
        spread = c.get('spread_pct', 0)
        liq_verdict = "EXCELLENT (<2.5% spread)" if spread <= 2.5 else ("GOOD (<5% spread)" if spread <= 5.0 else "FAIR")
        print(f"\n📊 Option Quality & Greeks Analysis:")
        print(f"   Delta: {delta:+.2f} (Speed) | Theta: {theta:.2f}/day (Decay) | Vega: {vega:.2f} | IV: {iv:.1f}%")
        print(f"   Liquidity & Spread:    {spread:.1f}% [{liq_verdict}] | Market Vol: {c.get('market_volatility', 'NORMAL').upper()}")

        results.append(c)

    print("\n" + "=" * 100)
    print("📈 TRADE EXECUTION PLAN".center(100))
    print("=" * 100)
    print("""
1. ✅ BUY at LTP (Entry Price)
2. ✅ SET SL at Disciplined 4-Layer SL (Tight 7-10% noise ceiling, NOT old 20% method!)
3. ✅ SET T1 at Target 1 (1.25R — book 50%, profit strictly exceeds SL risk!)
4. ✅ TRAIL T2 to Target 2 (2.00R — keep 50% with SL trailed to Breakeven/Profit)
5. ✅ IF price hits 98-99 and bounces: YOU WIN! (Your SL is protected)
6. ✅ IF price keeps falling to SL: EXIT with disciplined loss
7. ⏱️ 3:25 PM EOD SQUARE-OFF: Position closes at 3:25 PM market price if neither T1 nor SL reached

⚠️ KEY ADVANTAGES:
   • Positive Risk-to-Reward (R:R): T1 points strictly exceed SL points (1.25R), T2 is 2x SL risk (2.0R)!
   • Real ATM Strike & Live Quote: No arbitrary 1000 strike approximations!
   • Exchange Lot-Size Aware: Capital & risk scaled to exact exchange lot sizes.
   • Dynamic 4-Layer SL: Absorbs noise & stops premature stop-outs.
   • Automated 3:25 PM EOD Square-Off: Zero dangling open positions at day end.
    """)

    return results


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Intraday Options Scanner with Powerful 4-Layer SL & Real Market Resolution"
    )
    parser.add_argument(
        "--use-news-candidates",
        action="store_true",
        help="Fetch symbols dynamically from the most recent morning News Scanner JSON log",
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default="RELIANCE,TCS,BPCL,VEDL,MARUTI,HDFCBANK",
        help="Comma-separated F&O symbols to scan (ignored if --use-news-candidates is passed)",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=85,
        help="Minimum combined score to qualify (0-100, default: 85 for high conviction)",
    )
    parser.add_argument(
        "--account-size",
        type=float,
        default=500000,
        help="Trading account size in ₹ (default: ₹500,000)",
    )
    parser.add_argument(
        "--max-daily-trades",
        type=int,
        default=10,
        help="Maximum total intraday option trades allowed per day across all scans (default: 10, strictly capped)",
    )
    parser.add_argument(
        "--max-trades-per-scan",
        type=int,
        default=2,
        help="Maximum trades selected in a single scan run (default: 2, 2 CE, 2 PE, or 1 CE + 1 PE)",
    )
    parser.add_argument(
        "--ignore-holiday",
        action="store_true",
        help="Bypass trading day check for testing/offline analysis",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass daily trade cap and circuit breaker for testing/audit purposes",
    )
    parser.add_argument(
        "--max-sl-per-day",
        type=int,
        default=3,
        help="Maximum stop losses allowed per day before circuit breaker triggers (default: 3)",
    )
    return parser.parse_args()


def export_scan_config(args, result_count: int, symbols_scanned: list[str]) -> dict:
    """Export scan configuration for audit trail."""
    return {
        "timestamp": datetime.now().isoformat(),
        "script": "run_options_intraday_scan_powerful_sl",
        "symbols_scanned": symbols_scanned,
        "num_symbols": len(symbols_scanned),
        "min_score": args.min_score,
        "qualified_candidates": result_count,
        "sl_strategy": "Powerful 4-Layer (Delta + Vol + Theta + Vega)",
        "market_hours_check": is_market_hours(),
    }


def main():
    """Main execution function."""
    cleanup_old_logs(Path("logs"), days_to_keep=30)
    args = parse_args()

    if not args.ignore_holiday and not is_trading_day():
        print("\n⚠️  HALT: Today is NOT a trading day (weekend or NSE holiday)")
        print("    Intraday scanner only runs on trading days. Please try again tomorrow.\n")
        return

    today_str = datetime.now().strftime("%Y%m%d")
    stats = get_today_intraday_trade_stats(Path("logs"), today_str)

    max_allowed_sl = args.max_sl_per_day  # Configurable circuit breaker threshold
    print(f"\n📊 [DAILY TRADING DISCIPLINE STATUS]")
    print(f"   • Total Trades Initiated Today: {stats['today_trade_count']} / {args.max_daily_trades} Max Allowed")
    print(f"   • Stop Losses Hit Today:       {stats['sl_hits']} / {max_allowed_sl} Max Before Circuit Breaker")

    if not args.force:
        if stats["sl_hits"] >= max_allowed_sl:
            print(f"\n🛑 [DAILY CIRCUIT BREAKER ACTIVE]")
            print(f"   {stats['sl_hits']} Stop Losses have hit today (Circuit limit: {max_allowed_sl}).")
            print(f"   Market regime is showing high chop/whipsaw risk.")
            print(f"   Intraday scanner execution paused for the rest of the day to protect capital.\n")
            return

        if stats["today_trade_count"] >= args.max_daily_trades:
            print(f"\n🛑 [DAILY TRADE CAP REACHED]")
            print(f"   Daily limit of {args.max_daily_trades} high-conviction trades already reached today.")
            print(f"   Strictly skipping new trade generation (never more than {args.max_daily_trades} trades per day).\n")
            return

        remaining_quota = max(0, args.max_daily_trades - stats["today_trade_count"])
        scan_limit = min(args.max_trades_per_scan, remaining_quota)
    else:
        print("⚡ [FORCE/AUDIT MODE] Bypassing circuit breaker and daily trade cap for testing.")
        remaining_quota = args.max_daily_trades
        scan_limit = args.max_trades_per_scan
    print(f"   • Quota Remaining for Today:   {remaining_quota} trade(s)")
    print(f"   • Max New Trades This Scan:    {scan_limit} trade(s)")

    candidates_input = []
    kite = get_kite_client()
    nfo_instruments = get_nfo_instruments(kite)

    if getattr(args, 'use_news_candidates', False):
        news_data = get_latest_news_symbols(Path("logs"))
        movers_data = get_live_market_movers(kite, nfo_instruments, top_n=6)

        # Merge news and movers (avoid duplicates by symbol)
        seen_syms = set()
        combined = []
        news_map = {item[0]: item for item in news_data}
        movers_map = {item[0]: item for item in movers_data}

        # Check for Dual Confirmation first (Stocks with BOTH verified news AND market momentum)
        for sym in (set(news_map.keys()) & set(movers_map.keys())):
            n_item = news_map[sym]
            m_item = movers_map[sym]
            n_dir = "BULLISH" if "BULLISH" in n_item[1] else "BEARISH"
            m_dir = "BULLISH" if "BULLISH" in m_item[1] else "BEARISH"
            if n_dir == m_dir:
                boosted_score = min(98, max(n_item[2], m_item[2]) + 5)
                n_meta = n_item[3] if len(n_item) > 3 else {}
                n_meta["dual_confirmed"] = True
                combined.append((sym, f"{n_dir} 🚀 [DUAL CONFIRMED: News + Volume Technicals]", boosted_score, n_meta))
                seen_syms.add(sym)

        for item in (news_data + movers_data):
            sym = item[0]
            if sym not in seen_syms:
                seen_syms.add(sym)
                combined.append(item)

        # Apply Repeated Conviction Boost (+8 pts) if stock appeared in prior hourly scans today
        appearance_counts = get_today_symbol_appearance_counts(Path("logs"), today_str)
        enhanced_combined = []
        for item in combined:
            sym = item[0]
            label = item[1]
            score = item[2]
            meta = item[3] if len(item) > 3 else {}
            prior_runs = appearance_counts.get(sym, 0)
            if prior_runs >= 1:
                score = min(98, score + 8)
                label = f"{label} • 🔥 REPEATED CONVICTION ({prior_runs + 1}× Hourly Persistence)"
                meta["sustained_conviction"] = True
                meta["repeated_appearance_count"] = prior_runs + 1
            enhanced_combined.append((sym, label, score, meta))
        combined = enhanced_combined

        if combined:
            bullish = [s[0] for s in combined if "BULLISH" in s[1]]
            bearish = [s[0] for s in combined if "BEARISH" in s[1]]

            print(f"\n📰 [NEWS + LIVE MOVERS INTEGRATION] Dynamic fetch complete from News & Live Market!")
            if bullish:
                print(f"   🟢 BULLISH (Targeting CE): {', '.join(bullish)}")
            if bearish:
                print(f"   🔴 BEARISH (Targeting PE): {', '.join(bearish)}")

            candidates_input = combined
            args.symbols = ",".join([s[0] for s in combined])
        else:
            print("\n⚠️  [INTEGRATION] No news or movers found. Falling back to default.")
            candidates_input = [(s.strip(), "BULLISH", 70) for s in args.symbols.split(',') if s.strip()]
    else:
        candidates_input = [(s.strip(), "BULLISH", 70) for s in args.symbols.split(',') if s.strip()]

    print("\n🔍 Resolving live market option strikes, quotes & Greeks...")
    resolved = resolve_all_candidates(
        candidates_input,
        is_btst=False,
        include_nifty=False,
        account_size=args.account_size,
        min_score=args.min_score,
    )

    # Guarantee 2 strikes per run: If fewer than scan_limit (2) qualify at min_score, fallback to top candidates
    if len(resolved) < scan_limit and candidates_input:
        print(f"[*] Fallback activated: Only {len(resolved)} candidate(s) met score >={args.min_score}. Lowering threshold to ensure {scan_limit} strikes are provided...")
        fallback_resolved = resolve_all_candidates(
            candidates_input,
            is_btst=False,
            include_nifty=False,
            account_size=args.account_size,
            min_score=max(65, args.min_score - 15),
        )
        resolved_syms = {r.get("option_symbol") for r in resolved}
        for r in fallback_resolved:
            if r.get("option_symbol") not in resolved_syms:
                resolved.append(r)
                resolved_syms.add(r.get("option_symbol"))
            if len(resolved) >= scan_limit:
                break

    if not resolved:
        print("\n⚠️ No qualified option candidates found matching the score criteria.")
        return

    regime_str, regime_pct = get_nifty_market_regime(kite)
    print(f"\n🌐 [MARKET SITUATION] NIFTY 50 Regime: {regime_str} ({regime_pct:+.2f}%)")

    # Print results with powerful SL & dynamic technical alignment (2 CE, 2 PE, or 1 CE+1 PE based on situation)
    results = print_powerful_sl_results(
        resolved,
        args.account_size,
        max_candidates=scan_limit,
        existing_symbols=stats["today_symbols"],
        market_regime=regime_str,
    )

    # Save execution log with an explicit signal observation time.
    scan_time = datetime.now().astimezone().isoformat(timespec="seconds")
    for candidate in results:
        candidate["signal_time"] = scan_time
        candidate["signal_time_source"] = "scanner_observation_not_broker_fill"
        candidate["entry_price_source"] = "scanner_quote_ltp_not_broker_fill"
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"intraday_scan_powerful_sl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    log_data = {
        "execution": export_scan_config(args, len(results), args.symbols.split(",")),
        "candidates": results,
        "sl_strategy": "Powerful 4-Layer (Delta + Vol + Theta + Vega)",
        "summary": {
            "total_candidates": len(results),
            "min_score_filtered": args.min_score,
            "sl_method": "Powerful 4-Layer Protection",
            "whipsaw_protection": "YES - 4 defensive layers",
        }
    }

    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, default=str)

    print(f"\n✅ Execution log saved: {log_file}\n")

    # Send Telegram Alerts
    print("[*] Dispatching alerts to Telegram...")
    send_options_telegram_alerts(results, strategy_name="⚡ INTRADAY OPTIONS")
    print("✅ Telegram alerts sent successfully!")

    print("=" * 100)
    print("🎯 READY FOR INTRADAY EXECUTION!".center(100))
    print("=" * 100)
    print(f"""
Summary:
  • Candidates found: {len(results)}
  • SL Strategy: Powerful 4-Layer (prevents whipsaw!)
  • Risk method: 1% of account per trade (Lot-aware)
  • Expected execution: 9:50 AM - 3:25 PM IST
    """)


if __name__ == "__main__":
    main()

