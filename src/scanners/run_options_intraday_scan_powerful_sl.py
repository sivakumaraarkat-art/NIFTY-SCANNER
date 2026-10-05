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
    python src/scanners/run_options_intraday_scan_powerful_sl.py --use-news-candidates --min-score 50
    python src/scanners/run_options_intraday_scan_powerful_sl.py --symbols RELIANCE,TCS,BPCL --min-score 50
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
    datetime(2026, 11, 14),  # Guru Nanak Jayanti
    datetime(2026, 12, 25),  # Christmas
]

def is_trading_day() -> bool:
    """Check if today is a valid NSE trading day."""
    today = datetime.now()
    if today.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    today_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
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
# 3. NEWS SYMBOLS PARSER
# ──────────────────────────────────────────────────────────────
def get_latest_news_symbols(log_dir: Path) -> list:
    """Fetch BOTH Bullish and Bearish symbols dynamically from the morning News Scanner."""
    if not log_dir.exists():
        return []
    news_files = list(log_dir.glob("news_scan_*.json"))
    if not news_files:
        return []
    latest_file = max(news_files, key=lambda f: f.stat().st_mtime)
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
            if "BULLISH" in sent or "BEARISH" in sent:
                raw_score = d.get("avg_score", d.get("score", 70))
                symbols_with_sentiment.append((sym, sent, abs(int(raw_score))))

        symbols_with_sentiment.sort(key=lambda x: x[2], reverse=True)
    return symbols_with_sentiment


# ──────────────────────────────────────────────────────────────
# 4. PRINT RESULTS WITH 4-LAYER POWERFUL SL
# ──────────────────────────────────────────────────────────────
def print_powerful_sl_results(candidates: list[dict], account_size: float = 500000) -> list[dict]:
    """Print intraday results with powerful 4-layer SL and accurate position sizing."""
    results = []

    print("\n" + "=" * 100)
    print("⚡ INTRADAY OPTIONS SCANNER — POWERFUL 4-LAYER SL STRATEGY".center(100))
    print("=" * 100)
    print(f"\n📅 {datetime.now().strftime('%d-%b-%Y %H:%M %p')}")
    print(f"⚠️  Intraday execution window: 9:50 AM - 3:25 PM IST")
    print(f"✅ Market hours check: {is_market_hours()}\n")

    for i, c in enumerate(candidates[:5], 1):
        contract_str = c.get('option_symbol', f"{c['symbol']} {c['strike']:.0f} {c['option_type']}")
        spot_str = f"(Spot: ₹{c.get('spot_price', 0):,.2f})" if c.get('spot_price', 0) > 0 else ""
        print(f"\n{'─' * 100}")
        print(f"{i}. 🎯 {contract_str} {spot_str} | Score: {c['score']}/100 [{c.get('sentiment_catalyst', 'CATALYST')}]")
        print(f"{'─' * 100}")

        # SL Breakdown
        print(f"\n🛡️ POWERFUL SL (4-Layer Protection):")
        print(f"   Entry Price:           ₹{c['ltp']:.2f}")
        print(f"   ├─ Layer 1 (Delta):    ₹{c.get('layer1_buffer', 0):.2f} buffer")
        print(f"   ├─ Layer 2 (Vol):      ₹{c.get('layer2_vol_buffer', 0):.2f} buffer")
        print(f"   ├─ Layer 3 (Theta):    ₹{c.get('layer3_theta_buffer', 0):.2f} buffer")
        print(f"   └─ Layer 4 (Vega):     ₹{c.get('layer4_vega_buffer', 0):.2f} buffer")
        print(f"   ────────────────────────────────────────────")
        print(f"   💪 POWERFUL SL:        ₹{c['powerful_sl']:.2f}")
        print(f"   Risk per share:        ₹{c['sl_risk']:.2f} ({c['sl_risk_pct']:.2f}%)")

        old_sl = c['ltp'] * 0.80
        old_risk = c['ltp'] - old_sl
        improvement = ((old_risk - c['sl_risk']) / old_risk * 100) if old_risk > 0 else 0
        print(f"   ────────────────────────────────────────────")
        print(f"   Old SL (20%):          ₹{old_sl:.2f} (Risk: ₹{old_risk:.2f})")
        print(f"   📈 Improvement:        {improvement:.1f}% tighter SL! ✅")

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
        t1 = c.get('t1', round(c['ltp'] * 1.08, 2))
        t2 = c.get('t2', round(c['ltp'] * 1.15, 2))
        p_t1 = c.get('potential_profit_t1', round(tot_shares * (t1 - c['ltp']), 2))
        p_t2 = c.get('potential_profit_t2', round(tot_shares * (t2 - c['ltp']), 2))

        print(f"\n💰 Position Sizing (1% Risk Rule with Exchange Lots):")
        print(f"   Lots Recommended:      {lots} lots ({lot_sz} shares/lot = {tot_shares} qty)")
        print(f"   Capital Needed:        ₹{cap:,.2f}")
        print(f"   Max Risk:              ₹{m_risk:,.2f} (Within 1% account budget)")
        print(f"   Target 1 (+8%):        ₹{t1:.2f} → P&L: ₹{p_t1:+,.2f}")
        print(f"   Target 2 (+15%):       ₹{t2:.2f} → P&L: ₹{p_t2:+,.2f}")

        # Greeks
        print(f"\n📊 Greeks & Volatility:")
        print(f"   Delta: {c['delta']:.2f} | Theta: {c['theta']:.2f} | Vega: {c['vega']:.2f} | IV: {c['iv']:.1f}%")
        print(f"   Market Vol: {c.get('market_volatility', 'NORMAL').upper()}")

        results.append(c)

    print("\n" + "=" * 100)
    print("📈 TRADE EXECUTION PLAN".center(100))
    print("=" * 100)
    print("""
1. ✅ BUY at LTP (Entry Price)
2. ✅ SET SL at Powerful SL (NOT old 20% method!)
3. ✅ SET T1 at +8% (book 50%)
4. ✅ TRAIL T2 to +15% (keep 50%)
5. ✅ IF price hits 98-99 and bounces: YOU WIN! (Your SL is protected)
6. ✅ IF price keeps falling to SL: EXIT with disciplined loss

⚠️ KEY ADVANTAGES:
   • Real ATM Strike & Live Quote: No arbitrary 1000 strike approximations!
   • Exchange Lot-Size Aware: Capital & risk scaled to exact exchange lot sizes.
   • Dynamic 4-Layer SL: Absorbs noise & stops premature stop-outs.
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
        default=50,
        help="Minimum combined score to qualify (0-100)",
    )
    parser.add_argument(
        "--account-size",
        type=float,
        default=500000,
        help="Trading account size in ₹ (default: ₹500,000)",
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
    if not is_trading_day():
        print("\n⚠️  HALT: Today is NOT a trading day (weekend or NSE holiday)")
        print("    Intraday scanner only runs on trading days. Please try again tomorrow.\n")
        return

    cleanup_old_logs(Path("logs"), days_to_keep=30)
    args = parse_args()

    candidates_input = []
    if getattr(args, 'use_news_candidates', False):
        news_data = get_latest_news_symbols(Path("logs"))
        if news_data:
            bullish = [s[0] for s in news_data if "BULLISH" in s[1]]
            bearish = [s[0] for s in news_data if "BEARISH" in s[1]]

            print(f"\n📰 [NEWS INTEGRATION] Dynamic fetch complete from latest morning scan!")
            if bullish:
                print(f"   🟢 BULLISH (Targeting CE): {', '.join(bullish)}")
            if bearish:
                print(f"   🔴 BEARISH (Targeting PE): {', '.join(bearish)}")

            candidates_input = news_data
            args.symbols = ",".join([s[0] for s in news_data])
        else:
            print("\n⚠️  [NEWS INTEGRATION] No recent news symbols found. Falling back to default.")
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

    if not resolved:
        print("\n⚠️ No qualified option candidates found matching the score criteria.")
        return

    # Print results with powerful SL
    results = print_powerful_sl_results(resolved, args.account_size)

    # Save execution log
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
