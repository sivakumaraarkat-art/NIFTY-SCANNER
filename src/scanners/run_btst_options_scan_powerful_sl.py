"""
BTST OPTIONS SCANNER — WITH POWERFUL 4-LAYER SL STRATEGY
═════════════════════════════════════════════════════════════════

Enhancements:
1. ✅ Live Kite Market Resolution: Real ATM strikes, real live Option LTP & Greeks
2. ✅ Powerful 4-Layer SL (BTST-optimized, Theta-focused overnight defense)
3. ✅ Omni-Directional Support: CE for Bullish candidates, PE for Bearish candidates
4. ✅ Index Options Support: NIFTY 50 & BANKNIFTY dynamic contract resolution
5. ✅ Strict Overnight Theta Filter: Max permissible overnight decay protection
6. ✅ Exchange Lot-Sizing: Accurate lot-based position sizing via 1% risk rule
7. ✅ Execution logging to JSON
8. ✅ Weekend & NSE Holiday Guard
9. ✅ Mobile-optimized Telegram alert dispatch

Strategy for BTST:
  • Entry: 3:00 PM - 3:25 PM (before market close)
  • Hold: Overnight (T to T+1)
  • Exit: Next day 9:15 AM - 9:45 AM (via Smart Exit Guide)
  • Target: +25% (T1), +50% (T2)

Usage:
    python src/scanners/run_btst_options_scan_powerful_sl.py --use-news-candidates --include-nifty --min-score 86
    python src/scanners/run_btst_options_scan_powerful_sl.py --include-nifty --symbols RELIANCE,TCS,BPCL
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
from btst_batch import (project_root, logs_directory, select_candidates, create_batch,
                        record_delivery, batch_path, now_ist, INDEX_SYMBOLS)
ROOT = project_root(__file__)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from telegram_alerts.options_alert_sender import send_options_telegram_alerts
except ImportError:
    def send_options_telegram_alerts(*args, **kwargs):
        raise RuntimeError("Telegram sender unavailable; install telegram_alerts/options_alert_sender.py")

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
    today = now_ist()
    # Special exemption for Diwali Muhurat Trading on Sunday, Nov 8, 2026
    if today.date() == datetime(2026, 11, 8).date():
        return True
    if today.weekday() >= 5:
        return False
    if today.date() in {holiday.date() for holiday in NSE_HOLIDAYS_2026}:
        return False
    return True


# ──────────────────────────────────────────────────────────────
# 2. LOG ROTATION
# ──────────────────────────────────────────────────────────────
def is_market_hours() -> bool:
    """Check if current time is valid for BTST scanner (2:30 PM to 3:30 PM)."""
    now = now_ist().time()
    return time_type(14, 30) <= now <= time_type(15, 30)


def passes_theta_filter(theta: float, ltp: float, max_decay_pct: float = 0.15) -> bool:
    """Enforce BTST Theta decay boundary (decay should not eat over 15% of option price in 1 day)."""
    if ltp <= 0:
        return False
    return (abs(theta) / ltp) <= max_decay_pct


# ──────────────────────────────────────────────────────────────
# 3. NEWS & LIVE MOVER SYMBOLS PARSER
# ──────────────────────────────────────────────────────────────
def get_latest_news_symbols(log_dir: Path) -> list:
    """Fetch BOTH Bullish and Bearish symbols dynamically from News Scanner."""
    if not log_dir.exists():
        return []
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
                conviction += 12  # +12 for Tier-1 financial publisher
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


def get_live_market_movers(kite, nfo_instruments, top_n=8) -> list:
    """Scan live F&O universe for top gainers (CE) and top losers (PE) with quality shields."""
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
            vol = q.get("volume", 0)
            if prev_close <= 0 or ltp < 60:
                continue

            # Quality Shield: Minimum volume for reliable options
            if vol < 100000:
                continue

            # Quality Shield: Bid-ask spread check (via depth)
            depth = q.get("depth", {})
            buy_orders = depth.get("buy", [])
            sell_orders = depth.get("sell", [])
            spread_pct = 0.0
            if buy_orders and sell_orders and buy_orders[0].get("price", 0) > 0 and sell_orders[0].get("price", 0) > 0:
                bid = buy_orders[0]["price"]
                ask = sell_orders[0]["price"]
                if ltp > 0:
                    spread_pct = ((ask - bid) / ltp) * 100
            if spread_pct > 7.0:
                continue

            pct = ((ltp - prev_close) / prev_close) * 100
            day_range = high - low
            range_pos = ((ltp - low) / day_range) * 100 if day_range > 0 else 50.0
            name = sym.replace("NSE:", "")

            # Require stronger momentum for BTST (overnight risk)
            if pct >= 1.2 and range_pos >= 75:
                conviction = int(min(95, 70 + pct * 5 + (5 if vol >= 500000 else 0)))
                bullish.append((name, "BULLISH 🚀 (BTST Gainer)", conviction))
            elif pct <= -1.2 and range_pos <= 25:
                conviction = int(min(95, 70 + abs(pct) * 5 + (5 if vol >= 500000 else 0)))
                bearish.append((name, "BEARISH ⚠️ (BTST Breakdown)", conviction))

        bullish.sort(key=lambda x: x[2], reverse=True)
        bearish.sort(key=lambda x: x[2], reverse=True)

        return bullish[:top_n] + bearish[:top_n]
    except Exception as e:
        print(f"⚠️ Could not fetch market movers: {e}")
        return []


# ──────────────────────────────────────────────────────────────
# 4. PRINT BTST RESULTS WITH 4-LAYER SL
# ──────────────────────────────────────────────────────────────
def print_btst_results(stock_candidates: list[dict], index_candidates: list[dict], account_size: float = 500000) -> list[dict]:
    """Print BTST results formatted with SL protection and position sizing."""
    all_results = []

    print("\n" + "=" * 100)
    print("🌙 BTST OPTIONS SCANNER — POWERFUL 4-LAYER SL STRATEGY (CE & PE)".center(100))
    print("=" * 100)
    print(f"\n📅 {now_ist().strftime('%d-%b-%Y %H:%M %p')}")
    print(f"⚠️  BTST execution window: 3:00 PM - 3:25 PM IST (Next day exit: 9:15 AM)")
    print(f"✅ Market hours check: {is_market_hours()}\n")

    # Select ONCE. Printing, persistence and Telegram share this ordered selection.
    selected = select_candidates(stock_candidates, index_candidates)
    selected_stocks = [c for c in selected if c['symbol'] not in INDEX_SYMBOLS]
    index_candidates = [c for c in selected if c['symbol'] in INDEX_SYMBOLS]

    print("━" * 100)
    print(f"📊 TOP STOCK OPTIONS CANDIDATES ({len(selected_stocks)})")
    print("━" * 100)

    for i, c in enumerate(selected_stocks, 1):
        opt_type = c.get('option_type', 'CE')
        icon = "🟢" if opt_type == "CE" else "🔴"
        contract_str = c.get('option_symbol', f"{c['symbol']} {c['strike']:.0f} {opt_type}")
        spot_str = f"(Spot: ₹{c.get('spot_price', 0):,.2f})" if c.get('spot_price', 0) > 0 else ""
        print(f"\n{i}. {icon} 🎯 {contract_str} {spot_str} | Score: {c['score']}/100 [{c.get('sentiment_catalyst', 'BTST')}]")

        # Verified Catalyst & Conviction Audit
        meta = c.get('meta') or c.get('news_meta') or {}
        if meta.get('headline'):
            t1_str = "Tier-1 Verified Media" if meta.get("has_tier1") else "Multi-Source Corroborated"
            dual_note = " • 🔥 DUAL CONFIRMED (News + Technical Mover)" if meta.get("dual_confirmed") else ""
            print(f"   📰 Catalyst: \"{meta['headline']}\"")
            print(f"   🛡️ Verification: PASS ({t1_str} • {meta.get('unique_sources', 1)} Source(s): {meta.get('sources', 'Unknown')}){dual_note}")

        print(f"   Entry: ₹{c['ltp']:.2f} | Powerful SL: ₹{c['powerful_sl']:.2f} (-{c['sl_risk_pct']:.1f}%)")
        print(f"   Targets: T1: ₹{c['t1']:.2f} (+25%) | T2: ₹{c['t2']:.2f} (+50%)")
        print(f"   Sizing: {c.get('recommended_qty', 1)} lots ({c.get('lot_size', 1)}/lot) | Capital: ₹{c.get('capital_needed', 0):,.2f} | Max Risk: ₹{c.get('max_risk', 0):,.2f}")
        spread = c.get('spread_pct', 0)
        liq_verdict = "EXCELLENT (<2.5%)" if spread <= 2.5 else ("GOOD (<5%)" if spread <= 5.0 else "FAIR")
        print(f"   Greeks: Delta: {c['delta']:+.2f} | Theta: {c['theta']:.2f}/day | IV: {c['iv']:.1f}% | Spread: {spread:.1f}% [{liq_verdict}]")
        all_results.append(c)

    # Section 2: Index Options
    if index_candidates:
        print("\n" + "━" * 100)
        print(f"📈 TOP INDEX OPTIONS CANDIDATES ({len(index_candidates)})")
        print("━" * 100)

        for i, c in enumerate(index_candidates, 1):
            opt_type = c.get('option_type', 'CE')
            icon = "🟢" if opt_type == "CE" else "🔴"
            contract_str = c.get('option_symbol', f"{c['symbol']} {c['strike']:.0f} {opt_type}")
            spot_str = f"(Spot: ₹{c.get('spot_price', 0):,.2f})" if c.get('spot_price', 0) > 0 else ""
            print(f"\n{i}. {icon} 🏛️ {contract_str} {spot_str} | Score: {c['score']}/100")
            print(f"   Entry: ₹{c['ltp']:.2f} | Powerful SL: ₹{c['powerful_sl']:.2f} (-{c['sl_risk_pct']:.1f}%)")
            print(f"   Targets: T1: ₹{c['t1']:.2f} (+25%) | T2: ₹{c['t2']:.2f} (+50%)")
            print(f"   Sizing: {c.get('recommended_qty', 1)} lots ({c.get('lot_size', 1)}/lot) | Capital: ₹{c.get('capital_needed', 0):,.2f} | Max Risk: ₹{c.get('max_risk', 0):,.2f}")
            print(f"   Greeks: Delta: {c['delta']:.2f} | Theta: {c['theta']:.2f}/day | IV: {c['iv']:.1f}%")
            all_results.append(c)

    print("\n" + "=" * 100)
    print("🌙 BTST EXECUTION & OVERNIGHT MANAGEMENT PLAN".center(100))
    print("=" * 100)
    print("""
1. ✅ BUY at 3:15 PM - 3:25 PM IST (Lock in closing momentum)
2. ✅ HOLD overnight (T to T+1)
3. ✅ AT 09:15 AM NEXT MORNING: Check market condition via BTST Smart Exit Guide:
   • Strong Gap UP (+5%+): Exit 100% at market to lock peak profit!
   • Gap UP (+2% to +5%): Exit 50% at T1, trail 50% for T2!
   • Gap FLAT (±1%): Exit at cost (breakeven) or roll!
   • Gap DOWN: Dynamic Rolling Recovery or Powerful SL protection!

⚠️ KEY ADVANTAGES:
   • Live ATM Contract Precision: Real market prices and live strikes.
   • Overnight Theta Buffer: 4-Layer SL shields against time decay.
   • Position Sizing by Risk: Never risk more than 1% of account capital.
    """)

    return all_results


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="BTST Options Scanner with Powerful 4-Layer SL & Real Market Resolution"
    )
    parser.add_argument(
        "--use-news-candidates",
        action="store_true",
        help="Fetch symbols dynamically from the most recent News Scanner JSON log",
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default="RELIANCE,TCS,BPCL,VEDL,MARUTI,HDFCBANK",
        help="Comma-separated F&O symbols to scan (ignored if --use-news-candidates is passed)",
    )
    parser.add_argument(
        "--include-nifty",
        action="store_true",
        help="Include NIFTY 50 and BANKNIFTY index options in the scan",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=90,
        help="Minimum combined score to qualify (0-100, default: 90 for elite conviction)",
    )
    parser.add_argument(
        "--account-size",
        type=float,
        default=500000,
        help="Trading account size in ₹ (default: ₹500,000)",
    )
    parser.add_argument(
        "--ignore-holiday",
        action="store_true",
        help="Bypass trading day check for testing/offline analysis",
    )
    parser.add_argument("--log-dir", help="Shared BTST log directory (or BTST_LOG_DIR)")
    parser.add_argument("--dry-run", action="store_true", help="Resolve and print only; no Telegram or daily batch")
    parser.add_argument("--force", action="store_true", help="Bypass batch lock and re-run scan")
    return parser.parse_args()


def export_scan_config(args, result_count: int, symbols_scanned: list[str]) -> dict:
    """Export scan configuration for audit trail."""
    return {
        "timestamp": now_ist().isoformat(),
        "script": "run_btst_options_scan_powerful_sl",
        "symbols_scanned": symbols_scanned,
        "num_symbols": len(symbols_scanned),
        "include_nifty": args.include_nifty,
        "min_score": args.min_score,
        "qualified_candidates": result_count,
        "sl_strategy": "Powerful 4-Layer (BTST-optimized, Theta-focused)",
        "market_hours_check": is_market_hours(),
    }


def main():
    """Main execution function."""
    args = parse_args()
    log_dir = logs_directory(__file__, args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    if not args.dry_run and not getattr(args, 'force', False) and batch_path(log_dir, now_ist().date()).exists():
        print("BTST batch already exists today. Skipping rerun to preserve the original alerts.")
        return

    if not args.ignore_holiday and not is_trading_day():
        print("\n⚠️  HALT: Today is NOT a trading day (weekend or NSE holiday)")
        print("    BTST scanner only runs on trading days. Please try again tomorrow.\n")
        return

    candidates_input = []
    kite = get_kite_client()
    nfo_instruments = get_nfo_instruments(kite)

    if getattr(args, 'use_news_candidates', False):
        news_data = get_latest_news_symbols(log_dir)
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
                combined.append((sym, f"{n_dir} 🚀 [DUAL CONFIRMED: News + Technical]", boosted_score, n_meta))
                seen_syms.add(sym)

        for item in (news_data + movers_data):
            sym = item[0]
            if sym not in seen_syms:
                seen_syms.add(sym)
                combined.append(item)

        if combined:
            bullish = [s[0] for s in combined if "BULLISH" in s[1]]
            bearish = [s[0] for s in combined if "BEARISH" in s[1]]

            print(f"\n📰 [NEWS + MOVERS INTEGRATION] Dynamic fetch complete from News & Live Market!")
            if bullish:
                print(f"   🟢 BULLISH (Targeting CE): {', '.join(bullish[:8])}")
            if bearish:
                print(f"   🔴 BEARISH (Targeting PE): {', '.join(bearish[:8])}")

            candidates_input = combined
            args.symbols = ",".join(seen_syms)
        else:
            print("\n⚠️  [NEWS INTEGRATION] No recent news symbols found. Falling back to default.")
            candidates_input = [(s.strip(), "BULLISH", 70) for s in args.symbols.split(',') if s.strip()]
    else:
        candidates_input = [(s.strip(), "BULLISH", 70) for s in args.symbols.split(',') if s.strip()]

    print("\n🔍 Resolving live market option strikes, quotes & Greeks for BTST...")
    resolved = resolve_all_candidates(
        candidates_input,
        is_btst=True,
        include_nifty=args.include_nifty,
        account_size=args.account_size,
        min_score=args.min_score,
    )

    # Filter candidates by theta decay limit for BTST
    stock_candidates = [
        c for c in resolved
        if c['symbol'] not in INDEX_SYMBOLS and passes_theta_filter(c['theta'], c['ltp'])
    ]
    index_candidates = [
        c for c in resolved
        if c['symbol'] in INDEX_SYMBOLS and passes_theta_filter(c['theta'], c['ltp'])
    ]

    # Guarantee 2 strikes for BTST: If fewer than 2 qualify at min_score, fallback to top candidates
    if len(stock_candidates) + len(index_candidates) < 2 and candidates_input:
        print(f"[*] Fallback activated: Only {len(stock_candidates) + len(index_candidates)} candidate(s) qualified at BTST score >={args.min_score}. Lowering threshold to ensure 2 strikes are delivered...")
        fallback_resolved = resolve_all_candidates(
            candidates_input,
            is_btst=True,
            include_nifty=args.include_nifty,
            account_size=args.account_size,
            min_score=max(75, args.min_score - 10),
        )
        existing_keys = {c.get("option_symbol") for c in stock_candidates + index_candidates}
        for c in fallback_resolved:
            if c.get("option_symbol") not in existing_keys and passes_theta_filter(c.get("theta", 0), c.get("ltp", 0)):
                if c["symbol"] not in INDEX_SYMBOLS:
                    stock_candidates.append(c)
                else:
                    index_candidates.append(c)
                existing_keys.add(c.get("option_symbol"))
            if len(stock_candidates) + len(index_candidates) >= 2:
                break

    if not stock_candidates and not index_candidates:
        print("\n⚠️ No qualified BTST candidates found matching score and theta criteria.")
        return

    # Print results with powerful SL
    all_results = print_btst_results(stock_candidates, index_candidates, args.account_size)

    # Save execution log
    log_file = log_dir / f"btst_options_scan_powerful_sl_{now_ist().strftime('%Y%m%d_%H%M%S')}.json"

    log_data = {
        "execution": export_scan_config(args, len(all_results), args.symbols.split(",")),
        "selected_candidates": all_results,
        "stocks": [c for c in all_results if c['symbol'] not in INDEX_SYMBOLS],
        "index": [c for c in all_results if c['symbol'] in INDEX_SYMBOLS],
        "all_candidates": {"stocks": stock_candidates, "index": index_candidates},
        "dry_run": args.dry_run,
        "sl_strategy": "Powerful 4-Layer (BTST-optimized, Theta-focused)",
        "summary": {
            "total_candidates": len(all_results),
            "stocks_count": sum(c["symbol"] not in INDEX_SYMBOLS for c in all_results),
            "index_count": sum(c["symbol"] in INDEX_SYMBOLS for c in all_results),
            "min_score_filtered": args.min_score,
            "sl_method": "Powerful 4-Layer Protection",
            "whipsaw_protection": "YES - 4 defensive layers",
        }
    }

    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, default=str)

    print(f"\n✅ Execution log saved: {log_file}\n")

    if args.dry_run:
        print("DRY RUN: no Telegram messages sent and no daily alert batch created.")
        return
    try:
        selection_path, batch = create_batch(log_dir, all_results, log_file.name)
    except FileExistsError:
        print("Another scanner has already saved today's batch; no duplicate alerts sent.")
        return
    print(f"Selected batch: {batch['batch_id']} ({selection_path})")
    print("[*] Dispatching the saved selection to Telegram...")
    receipt = send_options_telegram_alerts(
        all_results, strategy_name="🌙 BTST OVERNIGHT OPTIONS", exact_selection=True,
        batch_id=batch["batch_id"],
        on_delivery=lambda candidate, ok: record_delivery(selection_path, batch, candidate, ok),
    )
    if not receipt or not receipt["header_sent"] or not all(receipt["cards_sent"]):
        raise RuntimeError("Telegram delivery incomplete/unknown. Inspect saved batch; no automatic resend.")
    print(f"Telegram confirmed delivery of {len(all_results)} selected cards.")

    print("=" * 100)
    print("🎯 READY FOR BTST EXECUTION!".center(100))
    print("=" * 100)
    print(f"""
Summary:
  • Selected/alerted: {len(all_results)} (Qualified pool: {len(stock_candidates)} stocks, {len(index_candidates)} indices)
  • SL Strategy: Powerful 4-Layer (BTST Theta-optimized)
  • Risk method: 1% of account per trade (Lot-aware)
  • Expected execution: 3:00 PM - 3:25 PM IST
    """)


if __name__ == "__main__":
    main()
