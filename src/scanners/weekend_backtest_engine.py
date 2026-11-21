"""
Weekend Backtest Engine
=======================
Runs on Saturday to replay Mon-Fri trading using historical 5-min data.
Validates thresholds, simulates all quality shields, generates Telegram + Google Drive report.

Usage:
    python src/scanners/weekend_backtest_engine.py --days 5
    python src/scanners/weekend_backtest_engine.py --days 10 --test-thresholds
"""

import sys
import os
import json
import argparse
from datetime import datetime, timedelta, time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scanners.options_data_provider import (
    get_kite_client, get_nfo_instruments,
    calculate_powerful_sl_engine
)
from src.scanners.run_options_intraday_scan_powerful_sl import (
    get_latest_news_symbols, get_live_market_movers
)
from src.scanners.run_btst_options_scan_powerful_sl import (
    select_candidates, passes_theta_filter, INDEX_SYMBOLS
)
from src.scanners.btst_batch import now_ist
from src.scanners.intraday_trade_monitor import observe_trades, load_signals, SQUARE_OFF_TIME
from src.scanners.daily_4pm_intraday_summary import reconcile_final_eod_trades

IST = datetime.now().astimezone().tzinfo

# ──────────────────────────────────────────────────────────────
# HISTORICAL DATA FETCHER
# ──────────────────────────────────────────────────────────────

def fetch_historical_5min(kite, instrument_token: int, from_date: datetime, to_date: datetime) -> pd.DataFrame:
    """Fetch 5-minute historical candles from Zerodha Kite."""
    try:
        data = kite.historical_data(instrument_token, from_date, to_date, "5minute")
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        # Ensure IST timezone
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
        else:
            df.index = df.index.tz_convert('Asia/Kolkata')
        # Filter market hours 09:15-15:30
        df = df.between_time('09:15', '15:30')
        return df
    except Exception as e:
        print(f"  ⚠️ Historical fetch error for token {instrument_token}: {e}")
        return pd.DataFrame()


def get_spot_historical_5min(kite, symbol: str, from_date: datetime, to_date: datetime) -> pd.DataFrame:
    """Get 5-min spot data for a symbol."""
    try:
        if symbol in ["NIFTY", "NIFTY 50"]:
            spot_key = "NSE:NIFTY 50"
        elif symbol == "BANKNIFTY":
            spot_key = "NSE:NIFTY BANK"
        elif symbol == "SENSEX":
            spot_key = "BSE:SENSEX"
        else:
            spot_key = f"NSE:{symbol}"

        quote = kite.quote([spot_key])
        if spot_key not in quote:
            return pd.DataFrame()
        token = quote[spot_key].get("instrument_token")
        if not token:
            return pd.DataFrame()
        return fetch_historical_5min(kite, token, from_date, to_date)
    except Exception as e:
        print(f"  ⚠️ Spot historical error for {symbol}: {e}")
        return pd.DataFrame()


def get_option_historical_5min(kite, tradingsymbol: str, exchange: str, from_date: datetime, to_date: datetime) -> pd.DataFrame:
    """Get 5-min option data for a specific contract."""
    try:
        key = f"{exchange}:{tradingsymbol}"
        quote = kite.quote([key])
        if key not in quote:
            return pd.DataFrame()
        token = quote[key].get("instrument_token")
        if not token:
            return pd.DataFrame()
        return fetch_historical_5min(kite, token, from_date, to_date)
    except Exception as e:
        print(f"  ⚠️ Option historical error for {tradingsymbol}: {e}")
        return pd.DataFrame()


# ──────────────────────────────────────────────────────────────
# HISTORICAL SIMULATION ENGINE
# ──────────────────────────────────────────────────────────────

def simulate_intraday_day(kite, instruments, date: datetime, news_symbols: List, movers: List,
                          min_score: int = 90, max_daily_trades: int = 10) -> List[Dict]:
    """Simulate intraday scanner for a specific historical date using historical data.
    For historical backtesting, test BOTH BULLISH and BEARISH for each symbol.
    """
    print(f"  📅 Simulating Intraday for {date.strftime('%d-%b-%Y')}...")

    trades = []
    candidates_input = []
    for sym, sent, score, meta in news_symbols:
        if score >= min_score:
            # Test both directions for historical validation
            candidates_input.append((sym, "BULLISH", score, meta))
            candidates_input.append((sym, "BEARISH", score, meta))
    for sym, sent, score in movers:
        if score >= min_score:
            if not any(c[0] == sym and c[1] == "BULLISH" for c in candidates_input):
                candidates_input.append((sym, "BULLISH", score, {"source": "mover"}))
            if not any(c[0] == sym and c[1] == "BEARISH" for c in candidates_input):
                candidates_input.append((sym, "BEARISH", score, {"source": "mover"}))

    if not candidates_input:
        return []

    date_start = datetime.combine(date.date(), time(9, 15))
    date_end = datetime.combine(date.date(), time(15, 30))

    for sym, sent, score, meta in candidates_input:
        try:
            spot_df = get_spot_historical_5min(kite, sym, date_start, date_end)
            if spot_df.empty:
                continue
            spot_open = spot_df.iloc[0]['open']

            opt_type = "CE" if "BULLISH" in sent.upper() else "PE"

            today = date.date()
            sym_opts = [
                i for i in instruments
                if sym.upper() in (i.get("name", "").upper()) and
                i.get("instrument_type") == opt_type and
                i.get("expiry") and i["expiry"] >= today
            ]
            if not sym_opts:
                continue

            expiries = sorted(set(i["expiry"] for i in sym_opts))
            nearest_exp = expiries[0]
            exp_opts = [i for i in sym_opts if i["expiry"] == nearest_exp]
            strikes = sorted(set(i["strike"] for i in sym_opts))
            if not strikes:
                continue

            atm_strike = min(strikes, key=lambda s: abs(s - spot_open))
            contract = next((i for i in exp_opts if i["strike"] == atm_strike), None)
            if not contract:
                continue

            tradingsymbol = contract["tradingsymbol"]
            lot_size = contract["lot_size"]
            exchange = "BFO" if "SENSEX" in sym else "NFO"

            date_start_dt = datetime.combine(date.date(), time(9, 15))
            date_end_dt = datetime.combine(date.date(), time(15, 30))
            opt_df = get_option_historical_5min(kite, tradingsymbol, exchange, date_start_dt, date_end_dt)

            if opt_df.empty:
                continue

            entry_price = opt_df.iloc[0]['open']

            # Calculate SL/T1/T2 using powerful SL engine
            # For historical simulation, we'll use simplified calculation
            sl_price = round(entry_price * 0.90, 2)
            t1 = round(entry_price * 1.15, 2)
            t2 = round(entry_price * 1.25, 2)
            lot_size = contract["lot_size"]

            trade = simulate_single_trade_historical(
                opt_df, entry_price, sl_price, t1, t2,
                sym, tradingsymbol, opt_type, date,
                1, lot_size, score, sent, meta
            )
            if trade:
                trades.append(trade)

        except Exception as e:
            print(f"    ⚠️ Error simulating {sym}: {e}")
            continue

    return trades[:max_daily_trades]


def simulate_btst_day(kite, instruments, date: datetime, news_symbols: List, movers: List,
                      min_score: int = 86, include_nifty: bool = True) -> List[Dict]:
    """Simulate BTST scanner for a specific historical date.
    For historical backtesting, test BOTH BULLISH and BEARISH for each symbol
    to validate both CE and PE trade generation.
    """
    print(f"  🌙 Simulating BTST for {date.strftime('%d-%b-%Y')}...")

    trades = []
    candidates_input = []
    for sym, sent, score, meta in news_symbols:
        if score >= min_score:
            # Test both directions for historical validation
            candidates_input.append((sym, "BULLISH", score, meta))
            candidates_input.append((sym, "BEARISH", score, meta))
    for sym, sent, score in movers:
        if score >= min_score:
            if not any(c[0] == sym and c[1] == "BULLISH" for c in candidates_input):
                candidates_input.append((sym, "BULLISH", score, {"source": "mover"}))
            if not any(c[0] == sym and c[1] == "BEARISH" for c in candidates_input):
                candidates_input.append((sym, "BEARISH", score, {"source": "mover"}))

    # Add NIFTY/BANKNIFTY if enabled - test both directions
    if include_nifty:
        for idx in ["NIFTY", "BANKNIFTY"]:
            idx_score = 85
            for item in news_symbols + movers:
                if isinstance(item, tuple) and len(item) >= 2:
                    if item[0].upper() == idx:
                        if len(item) >= 3:
                            idx_score = int(item[2])
                        break
            # Test both BULLISH and BEARISH for indices
            candidates_input.append((idx, "BULLISH", idx_score, {"source": "index"}))
            candidates_input.append((idx, "BEARISH", idx_score, {"source": "index"}))

    if not candidates_input:
        return []

    date_start = datetime.combine(date.date(), time(9, 15))
    date_end = datetime.combine(date.date(), time(15, 30))

    for sym, sent, score, meta in candidates_input:
        try:
            if sym in ["NIFTY", "BANKNIFTY", "SENSEX"]:
                # For indices, we'll fetch spot data using the index symbol
                if sym == "NIFTY":
                    spot_key = "NSE:NIFTY 50"
                elif sym == "BANKNIFTY":
                    spot_key = "NSE:NIFTY BANK"
                elif sym == "SENSEX":
                    spot_key = "BSE:SENSEX"

                spot_df = get_spot_historical_5min(kite, sym, date_start, date_end)
                if spot_df.empty:
                    continue
                spot_open = spot_df.iloc[0]['open']
            else:
                spot_df = get_spot_historical_5min(kite, sym, date_start, date_end)
                if spot_df.empty:
                    continue
                spot_open = spot_df.iloc[0]['open']

            opt_type = "CE" if "BULLISH" in sent.upper() else "PE"

            today = date.date()
            is_index = sym in ["NIFTY", "BANKNIFTY", "SENSEX", "FINNIFTY", "MIDCPNIFTY"]

            if is_index:
                sym_opts = [
                    i for i in instruments
                    if sym.upper().replace(" 50", "").replace(" BANK", "").replace("MID SELECT", "").replace(" ", "") in (i.get("name", "").upper())
                    and i.get("instrument_type") == opt_type
                    and i.get("expiry") and i["expiry"] >= today
                ]
            else:
                sym_opts = [
                    i for i in instruments
                    if sym.upper() in (i.get("name", "").upper()) and
                    i.get("instrument_type") == opt_type and
                    i.get("expiry") and i["expiry"] >= today
                ]

            if not sym_opts:
                continue

            expiries = sorted(set(i["expiry"] for i in sym_opts))
            nearest_exp = expiries[0]
            exp_opts = [i for i in sym_opts if i["expiry"] == nearest_exp]
            strikes = sorted(set(i["strike"] for i in exp_opts))
            if not strikes:
                continue

            atm_strike = min(strikes, key=lambda s: abs(s - spot_open))
            contract = next((i for i in exp_opts if i["strike"] == atm_strike), None)
            if not contract:
                continue

            tradingsymbol = contract["tradingsymbol"]
            lot_size = contract["lot_size"]
            exchange = "BFO" if "SENSEX" in sym else "NFO"

            date_start_dt = datetime.combine(date.date(), time(9, 15))
            date_end_dt = datetime.combine(date.date(), time(15, 30))
            opt_df = get_option_historical_5min(kite, tradingsymbol, exchange, date_start_dt, date_end_dt)

            if opt_df.empty:
                continue

            entry_price = opt_df.iloc[0]['open']

            # BTST: wider SL, larger targets
            sl_price = round(entry_price * 0.85, 2)
            t1 = round(entry_price * 1.25, 2)
            t2 = round(entry_price * 1.50, 2)
            lot_size = contract["lot_size"]

            trade = simulate_single_trade_historical(
                opt_df, entry_price, sl_price, t1, t2,
                sym, tradingsymbol, opt_type, date,
                1, lot_size, score, sent, meta
            )
            if trade:
                trades.append(trade)

        except Exception as e:
            print(f"    ⚠️ Error simulating BTST {sym}: {e}")
            continue

    return trades


def simulate_single_trade_historical(opt_df: pd.DataFrame, entry_price: float, sl_price: float,
                                     t1: float, t2: float, sym: str, tradingsymbol: str,
                                     opt_type: str, date: datetime, lots: int, lot_size: int,
                                     score: int, sent: str, meta: dict) -> Optional[Dict]:
    """Simulate a single trade from entry to exit using 5-min historical data."""

    if opt_df.empty:
        return None

    # Use actual entry from first candle open
    actual_entry = opt_df.iloc[0]['open']

    # Use provided SL/T1/T2
    sl = sl_price
    t1 = t1
    t2 = t2

    # Simulate minute-by-minute
    exit_price = actual_entry
    exit_reason = "NO_EXIT"
    exit_time = None

    for idx, row in opt_df.iterrows():
        high, low, close = row['high'], row['low'], row['close']
        candle_time = idx

        # Check SL hit (conservative: if low <= SL)
        if low <= sl:
            exit_price = sl
            exit_reason = "SL_HIT"
            exit_time = candle_time
            break

        # Check T2 hit (conservative: if high >= T2)
        if high >= t2:
            exit_price = t2
            exit_reason = "T2_HIT"
            exit_time = candle_time
            break

        # Check T1 hit (if not already hit T2)
        if high >= t1 and exit_reason != "T2_HIT":
            if exit_reason == "NO_EXIT":
                exit_reason = "T1_HIT"
                exit_price = t1
                exit_time = candle_time
                # Don't break - continue to see if T2 or SL hits later

    # EOD square-off at 15:25 if still open
    if exit_reason == "NO_EXIT":
        eod_candles = opt_df[opt_df.index.time <= time(15, 25)]
        if not eod_candles.empty:
            last_candle = eod_candles.iloc[-1]
            exit_price = last_candle['close']
            exit_time = eod_candles.index[-1]
            exit_reason = "EOD_SQUARE_OFF"
        else:
            exit_price = actual_entry
            exit_time = opt_df.index[-1]
            exit_reason = "NO_DATA_EOD"

    # Calculate P&L
    total_qty = lots * lot_size
    pnl = (exit_price - actual_entry) * total_qty
    pnl_pct = ((exit_price - actual_entry) / actual_entry * 100) if actual_entry else 0

    return {
        **{
            "symbol": sym,
            "tradingsymbol": tradingsymbol,
            "option_type": opt_type,
            "strategy": "BTST",
            "trade_date": date.strftime("%Y-%m-%d"),
            "entry_price": round(actual_entry, 2),
            "exit_price": round(exit_price, 2),
            "exit_reason": exit_reason,
            "entry_time": opt_df.index[0].strftime("%H:%M"),
            "exit_time": exit_time.strftime("%H:%M") if exit_time else None,
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "max_risk": round((actual_entry - sl) * total_qty, 2),
            "score": score,
            "sentiment_catalyst": sent,
            "capital_needed": round(actual_entry * total_qty, 2),
        }
    }


def simulate_single_trade_historical(opt_df: pd.DataFrame, entry_price: float, sl_price: float,
                                     t1: float, t2: float, sym: str, tradingsymbol: str,
                                     opt_type: str, date: datetime, lots: int, lot_size: int,
                                     score: int, sent: str, meta: dict) -> Optional[Dict]:
    """Simulate a single trade from entry to exit using 5-min historical data."""

    if opt_df.empty:
        return None

    # Use actual entry from first candle open
    actual_entry = opt_df.iloc[0]['open']

    # Use provided SL/T1/T2
    sl = sl_price
    t1 = t1
    t2 = t2

    # Simulate minute-by-minute
    exit_price = actual_entry
    exit_reason = "NO_EXIT"
    exit_time = None

    for idx, row in opt_df.iterrows():
        high, low, close = row['high'], row['low'], row['close']
        candle_time = idx

        # Check SL hit (conservative: if low <= SL)
        if low <= sl:
            exit_price = sl
            exit_reason = "SL_HIT"
            exit_time = candle_time
            break

        # Check T2 hit (conservative: if high >= T2)
        if high >= t2:
            exit_price = t2
            exit_reason = "T2_HIT"
            exit_time = candle_time
            break

        # Check T1 hit (if not already hit T2)
        if high >= t1 and exit_reason != "T2_HIT":
            if exit_reason == "NO_EXIT":
                exit_reason = "T1_HIT"
                exit_price = t1
                exit_time = candle_time
                # Don't break - continue to see if T2 or SL hits later

    # EOD square-off at 15:25 if still open
    if exit_reason == "NO_EXIT":
        eod_candles = opt_df[opt_df.index.time <= time(15, 25)]
        if not eod_candles.empty:
            last_candle = eod_candles.iloc[-1]
            exit_price = last_candle['close']
            exit_time = eod_candles.index[-1]
            exit_reason = "EOD_SQUARE_OFF"
        else:
            exit_price = actual_entry
            exit_time = opt_df.index[-1]
            exit_reason = "NO_DATA_EOD"

    # Calculate P&L
    total_qty = lots * lot_size
    pnl = (exit_price - actual_entry) * total_qty
    pnl_pct = ((exit_price - actual_entry) / actual_entry * 100) if actual_entry else 0

    return {
        **{
            "symbol": sym,
            "tradingsymbol": tradingsymbol,
            "option_type": opt_type,
            "strategy": "INTRADAY" if "INTRADAY" in str(meta) else "BTST",
            "trade_date": date.strftime("%Y-%m-%d"),
            "entry_price": round(actual_entry, 2),
            "exit_price": round(exit_price, 2),
            "exit_reason": exit_reason,
            "entry_time": opt_df.index[0].strftime("%H:%M"),
            "exit_time": exit_time.strftime("%H:%M") if exit_time else None,
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "max_risk": round((actual_entry - sl) * total_qty, 2),
            "score": score,
            "sentiment_catalyst": sent,
            "capital_needed": round(actual_entry * total_qty, 2),
        }
    }


# ──────────────────────────────────────────────────────────────
# THRESHOLD TESTING
# ──────────────────────────────────────────────────────────────

def test_thresholds(all_trades: List[Dict], thresholds: List[int]) -> Dict:
    """Test different min-score thresholds against simulated trades."""
    results = {}

    for threshold in thresholds:
        filtered = [t for t in all_trades if t.get("score", 0) >= threshold]

        if not filtered:
            results[threshold] = {"trades": 0, "wins": 0, "win_rate": 0, "net_pnl": 0, "avg_win": 0, "avg_loss": 0}
            continue

        wins = [t for t in filtered if t["pnl"] > 0]
        losses = [t for t in filtered if t["pnl"] < 0]

        results[threshold] = {
            "trades": len(filtered),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(len(wins) / len(filtered) * 100, 1),
            "net_pnl": round(sum(t["pnl"] for t in filtered), 2),
            "avg_win": round(np.mean([t["pnl"] for t in wins]), 2) if wins else 0,
            "avg_loss": round(np.mean([t["pnl"] for t in losses]), 2) if losses else 0,
            "total_capital": round(sum(t.get("capital_needed", 0) for t in filtered), 2),
            "return_pct": round(sum(t["pnl"] for t in filtered) / sum(t.get("capital_needed", 0) for t in filtered) * 100, 2) if sum(t.get("capital_needed", 0) for t in filtered) > 0 else 0,
        }

    return results


# ──────────────────────────────────────────────────────────────
# REPORT GENERATION
# ──────────────────────────────────────────────────────────────

def generate_telegram_report(period_start: datetime, period_end: datetime,
                             intraday_trades: List[Dict], btst_trades: List[Dict],
                             threshold_results: Dict) -> str:
    """Generate formatted Telegram report."""

    all_trades = intraday_trades + btst_trades
    wins = [t for t in all_trades if t["pnl"] > 0]
    losses = [t for t in all_trades if t["pnl"] < 0]
    total_pnl = sum(t["pnl"] for t in all_trades)
    total_capital = sum(t.get("capital_needed", 0) for t in all_trades)
    win_rate = (len(wins) / len(all_trades) * 100) if all_trades else 0

    DIVIDER = "──────────────────────"

    def safe_pct(wins_list, total):
        return f"{(len(wins_list)/total*100):.1f}" if total > 0 else "0.0"

    def avg_pnl(trades_list):
        return f"₹{np.mean([t['pnl'] for t in trades_list]):,.0f}" if trades_list else "N/A"

    lines = [
        f"📊 <b>WEEKEND BACKTEST REPORT</b>",
        f"{DIVIDER}",
        f"📅 <b>Period:</b> {period_start.strftime('%d-%b')} to {period_end.strftime('%d-%b-%Y')}",
        f"🔧 <b>Config:</b> Intraday≥90, BTST≥86",
        f"{DIVIDER}",
        f"📈 <b>INTRADAY (Min-Score 90)</b>",
    ]

    intraday_wins = [t for t in intraday_trades if t["pnl"] > 0]
    intraday_losses = [t for t in intraday_trades if t["pnl"] < 0]
    intraday_pnl = sum(t["pnl"] for t in intraday_trades)

    lines.extend([
        f"   Trades: {len(intraday_trades)} | Wins: {len(intraday_wins)} ({safe_pct(intraday_wins, len(intraday_trades))}% WR)",
        f"   Net P&L: {'+' if intraday_pnl>=0 else ''}₹{intraday_pnl:,.0f}",
        f"   Avg Win: {avg_pnl([t for t in intraday_trades if t['pnl'] > 0])}",
        f"   Avg Loss: {avg_pnl([t for t in intraday_trades if t['pnl'] < 0])}",
        f"{DIVIDER}",
        f"🌙 <b>BTST (Min-Score 86)</b>",
    ])

    btst_wins = [t for t in btst_trades if t["pnl"] > 0]
    btst_losses = [t for t in btst_trades if t["pnl"] < 0]
    btst_pnl = sum(t["pnl"] for t in btst_trades)

    lines.extend([
        f"   Trades: {len(btst_trades)} | Wins: {len([t for t in btst_trades if t['pnl'] > 0])} ({safe_pct([t for t in btst_trades if t['pnl'] > 0], len(btst_trades))}% WR)",
        f"   Net P&L: {'+' if sum(t['pnl'] for t in btst_trades)>=0 else ''}₹{sum(t['pnl'] for t in btst_trades):,.0f}",
        f"   Avg Win: {avg_pnl([t for t in btst_trades if t['pnl'] > 0])}",
        f"   Avg Loss: {avg_pnl([t for t in btst_trades if t['pnl'] < 0])}",
        f"{DIVIDER}",
        f"📊 <b>COMBINED</b>",
    ])

    all_trades = intraday_trades + btst_trades
    total_pnl = sum(t["pnl"] for t in all_trades)
    total_capital = sum(t.get("capital_needed", 0) for t in all_trades)

    lines.extend([
        f"   Total Trades: {len(all_trades)} | Win Rate: {win_rate:.1f}%",
        f"   Total Capital: ₹{total_capital:,.0f}",
        f"   Net P&L: <b>{'+' if total_pnl>=0 else ''}₹{total_pnl:,.0f}</b> ({total_pnl/total_capital*100:+.1f}%)" if total_capital else "   Net P&L: N/A",
        f"{DIVIDER}",
        f"🔍 <b>THRESHOLD SENSITIVITY:</b>",
    ])

    for thresh, stats in sorted(threshold_results.items()):
        tag = " ✅ CURRENT" if thresh in [86, 90] else ""
        return_pct = stats.get('return_pct', 0)
        net_pnl = stats.get('net_pnl', 0)
        win_rate = stats.get('win_rate', 0)
        trades = stats.get('trades', 0)
        lines.append(
            f"   Score≥{thresh}: {trades} trades | {win_rate}% WR | "
            f"P&L: {'+' if net_pnl>=0 else ''}₹{net_pnl:,.0f} | "
            f"Return: {return_pct:+.1f}%{tag}"
        )

    # Add flags
    lines.append(f"{DIVIDER}")
    lines.append(f"⚠️ <b>FLAGS:</b>")

    # Symbols with poor performance
    symbol_stats = {}
    for t in all_trades:
        sym = t.get("symbol", "")
        if sym not in symbol_stats:
            symbol_stats[sym] = {"trades": 0, "wins": 0, "pnl": 0}
        symbol_stats[sym]["trades"] += 1
        if t["pnl"] > 0:
            symbol_stats[sym]["wins"] += 1
        symbol_stats[sym]["pnl"] += t["pnl"]

    for sym, stats in sorted(symbol_stats.items(), key=lambda x: x[1]["pnl"]):
        if stats["trades"] >= 2:
            wr = stats["wins"] / stats["trades"] * 100
            if wr < 40 or stats["pnl"] < -5000:
                lines.append(f"   • {sym}: {stats['trades']} trades, {wr:.0f}% WR, ₹{stats['pnl']:,.0f}")

    lines.append(f"{DIVIDER}")
    lines.append(f"<i>Backtest completed {datetime.now().strftime('%d-%b %H:%M')} IST</i>")

    return "\n".join(lines)


def generate_excel_report(period_start: datetime, period_end: datetime,
                          intraday_trades: List[Dict], btst_trades: List[Dict],
                          threshold_results: Dict) -> str:
    """Generate Excel report with multiple sheets."""
    output_file = f"Weekend_Backtest_{datetime.now().strftime('%Y-%m-%d')}.xlsx"

    all_trades = intraday_trades + btst_trades

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Sheet 1: All Trades
        if all_trades:
            df_all = pd.DataFrame(all_trades)
            cols_order = [
                "trade_date", "strategy", "symbol", "option_symbol", "option_type",
                "entry_price", "exit_price", "exit_reason", "entry_time", "exit_time",
                "pnl", "pnl_pct", "score", "capital_needed", "max_risk"
            ]
            df_all = df_all[[c for c in cols_order if c in df_all.columns]]
            df_all.to_excel(writer, sheet_name='All Trades', index=False)

        # Sheet 2: Intraday Trades
        if intraday_trades:
            df_intra = pd.DataFrame(intraday_trades)
            df_intra.to_excel(writer, sheet_name='Intraday', index=False)

        # Sheet 3: BTST Trades
        if btst_trades:
            df_btst = pd.DataFrame(btst_trades)
            df_btst.to_excel(writer, sheet_name='BTST', index=False)

        # Sheet 4: Threshold Analysis
        thresh_df = pd.DataFrame.from_dict(threshold_results, orient='index')
        thresh_df.index.name = 'min_score'
        thresh_df.to_excel(writer, sheet_name='Threshold Analysis')

        # Sheet 5: Symbol Performance
        symbol_stats = {}
        for t in intraday_trades + btst_trades:
            sym = t.get("symbol", "")
            if sym not in symbol_stats:
                symbol_stats[sym] = {"trades": 0, "wins": 0, "pnl": 0, "capital": 0}
            symbol_stats[sym]["trades"] += 1
            if t["pnl"] > 0:
                symbol_stats[sym]["wins"] += 1
            symbol_stats[sym]["pnl"] += t["pnl"]
            symbol_stats[sym]["capital"] += t.get("capital_needed", 0)

        sym_df = pd.DataFrame.from_dict(symbol_stats, orient='index')
        sym_df["win_rate"] = (sym_df["wins"] / sym_df["trades"] * 100).round(1)
        sym_df["return_pct"] = (sym_df["pnl"] / sym_df["capital"] * 100).round(1)
        sym_df = sym_df.sort_values("pnl", ascending=False)
        sym_df.to_excel(writer, sheet_name='Symbol Performance')

        # Sheet 6: Summary
        summary_data = {
            "Period": [f"{period_start.strftime('%d-%b')} to {period_end.strftime('%d-%b-%Y')}"],
            "Intraday Threshold": [90],
            "BTST Threshold": [86],
            "Total Trades": [len(intraday_trades) + len(btst_trades)],
            "Intraday Trades": [len(intraday_trades)],
            "BTST Trades": [len(btst_trades)],
            "Win Rate %": [round((len([t for t in intraday_trades+btst_trades if t['pnl']>0]) / max(1, len(intraday_trades)+len(btst_trades))) * 100, 1)],
            "Total P&L": [sum(t['pnl'] for t in intraday_trades+btst_trades)],
            "Total Capital": [sum(t.get('capital_needed',0) for t in intraday_trades+btst_trades)],
            "Return %": [round(sum(t['pnl'] for t in intraday_trades+btst_trades) / max(1, sum(t.get('capital_needed',0) for t in intraday_trades+btst_trades)) * 100, 2)],
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)

    return output_file


# ──────────────────────────────────────────────────────────────
# MAIN ENGINE
# ──────────────────────────────────────────────────────────────

def run_weekend_backtest(days_back: int = 5, test_thresholds_flag: bool = False,
                         send_telegram: bool = True, upload_drive: bool = True) -> Dict:
    """Main backtest engine entry point."""

    print("=" * 80)
    print("📊 WEEKEND BACKTEST ENGINE".center(80))
    print("=" * 80)

    kite = get_kite_client()
    if not kite:
        print("❌ No Kite connection")
        return {"error": "No Kite connection"}

    print("✅ Connected to Kite")

    instruments = get_nfo_instruments(kite)
    print(f"✅ Loaded {len(instruments)} instruments")

    # Calculate date range
    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    # If today is Saturday/Sunday, use last Friday as end
    if end_date.weekday() >= 5:
        end_date = end_date - timedelta(days=end_date.weekday() - 4)  # Last Friday

    start_date = end_date - timedelta(days=days_back - 1)
    # Adjust to trading days only
    trading_days = []
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # Mon-Fri
            trading_days.append(current)
        current += timedelta(days=1)

    print(f"📅 Backtest Period: {len(trading_days)} trading days ({start_date.strftime('%d-%b')} to {end_date.strftime('%d-%b-%Y')})")
    print(f"   Trading days: {[d.strftime('%a %d-%b') for d in trading_days]}")

    all_intraday_trades = []
    all_btst_trades = []

    # Simulate each trading day
    for trade_date in trading_days:
        print(f"\n{'='*60}")
        print(f"📅 Processing {trade_date.strftime('%A, %d-%b-%Y')}")
        print(f"{'='*60}")

        # For historical simulation, we need historical news/movers
        # For now, use current day's news as proxy - in prod, fetch historical
        log_dir = Path("logs")
        news_symbols = get_latest_news_symbols(log_dir)

        # Get movers (using current logic)
        movers = get_live_market_movers(kite, instruments, top_n=8)

        # Simulate Intraday
        intraday_trades = simulate_intraday_day(kite, instruments, trade_date, news_symbols, movers, min_score=90, max_daily_trades=10)
        all_intraday_trades.extend(intraday_trades)
        print(f"   Intraday: {len(intraday_trades)} trades")

        # Simulate BTST
        btst_trades = simulate_btst_day(kite, instruments, trade_date, news_symbols, movers, min_score=86, include_nifty=True)
        all_btst_trades.extend(btst_trades)
        print(f"   BTST: {len(btst_trades)} trades")

    # Threshold sensitivity analysis
    all_trades = all_intraday_trades + all_btst_trades
    thresholds = [85, 86, 88, 90, 92]
    threshold_results = test_thresholds(all_trades, thresholds)

    # Generate reports
    print(f"\n{'='*60}")
    print("📋 GENERATING REPORTS")
    print(f"{'='*60}")

    telegram_report = generate_telegram_report(
        trading_days[0], trading_days[-1],
        all_intraday_trades, all_btst_trades,
        threshold_results
    )

    excel_file = generate_excel_report(
        trading_days[0], trading_days[-1],
        all_intraday_trades, all_btst_trades,
        threshold_results
    )

    print(f"✅ Excel report: {excel_file}")

    # Send Telegram
    if send_telegram:
        try:
            from dotenv import load_dotenv
            import requests
            load_dotenv()
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            chat_id = os.getenv("TELEGRAM_CHAT_ID")
            if bot_token and chat_id:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                requests.post(url, json={"chat_id": chat_id, "text": telegram_report, "parse_mode": "HTML"}, timeout=15)

                # Send Excel
                url_doc = f"https://api.telegram.org/bot{bot_token}/sendDocument"
                with open(excel_file, "rb") as f:
                    files = {"document": (excel_file, f)}
                    data = {"chat_id": chat_id, "caption": f"📊 Weekend Backtest {datetime.now().strftime('%Y-%m-%d')}", "parse_mode": "HTML"}
                    requests.post(url_doc, data=data, files=files, timeout=30)
                print("✅ Telegram report sent")
        except Exception as e:
            print(f"⚠️ Telegram send failed: {e}")

    # Upload to Google Drive
    if upload_drive:
        try:
            from src.scanners.generate_weekly_audit import upload_to_google_drive
            upload_to_google_drive(excel_file)
        except Exception as e:
            print(f"⚠️ Google Drive upload failed: {e}")

    print(f"\n{'='*80}")
    print("✅ WEEKEND BACKTEST COMPLETE")
    print(f"{'='*80}")

    return {
        "period": f"{trading_days[0].strftime('%d-%b')} to {trading_days[-1].strftime('%d-%b-%Y')}",
        "intraday_trades": len(all_intraday_trades),
        "btst_trades": len(all_btst_trades),
        "total_trades": len(all_trades),
        "net_pnl": sum(t["pnl"] for t in all_trades),
        "excel_file": excel_file,
        "threshold_analysis": threshold_results,
    }


def main():
    parser = argparse.ArgumentParser(description="Weekend Backtest Engine")
    parser.add_argument("--days", type=int, default=5, help="Number of trading days to backtest (default: 5)")
    parser.add_argument("--test-thresholds", action="store_true", help="Run threshold sensitivity analysis")
    parser.add_argument("--no-telegram", action="store_true", help="Skip Telegram notification")
    parser.add_argument("--no-drive", action="store_true", help="Skip Google Drive upload")
    args = parser.parse_args()

    result = run_weekend_backtest(
        days_back=args.days,
        test_thresholds_flag=args.test_thresholds,
        send_telegram=not args.no_telegram,
        upload_drive=not args.no_drive,
    )

    if "error" in result:
        print(f"❌ Backtest failed: {result['error']}")
        sys.exit(1)

    print(f"\n📊 Summary: {result['total_trades']} trades | P&L: ₹{result['net_pnl']:,.0f}")
    print(f"📁 Report: {result['excel_file']}")


if __name__ == "__main__":
    main()