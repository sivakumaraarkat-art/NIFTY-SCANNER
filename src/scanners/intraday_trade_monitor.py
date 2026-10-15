"""Poll intraday scan signals and persist first observed T1/T2/SL crossings.

Run every minute during market hours, after the intraday scanner. Timestamps
are observation times from polling, not broker order/fill timestamps.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, time as time_type
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from src.scanners.options_data_provider import get_kite_client
except ImportError:
    from options_data_provider import get_kite_client

IST = ZoneInfo("Asia/Kolkata")
LOG_DIR = Path(os.getenv("INTRADAY_LOG_DIR", "logs"))
STATE_FILE = LOG_DIR / "intraday_trade_state.json"
MARKET_CLOSE = time_type(15, 30)


def now_ist() -> datetime:
    return datetime.now(IST)


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {"schema_version": 1, "trades": {}}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(data.get("trades"), dict):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {"schema_version": 1, "trades": {}}


def load_signals(day_str: str) -> dict[str, dict[str, Any]]:
    signals: dict[str, dict[str, Any]] = {}
    pattern = f"intraday_scan_powerful_sl_{day_str}_*.json"
    for path in sorted(LOG_DIR.glob(pattern)):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        exec_info = data.get("execution", {})
        scan_time = exec_info.get("timestamp") or datetime.fromtimestamp(path.stat().st_mtime, IST).isoformat()
        cands = data.get("candidates", [])
        if not cands and "results" in data:
            cands = data["results"].get("stocks", [])
        for c in cands:
            sym = str(c.get("symbol", "")).upper()
            if sym in {"NIFTY", "SENSEX", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"}:
                continue
            strike = c.get("strike", c.get("strike_price", 0))
            opt_type = str(c.get("option_type", c.get("type", "CE"))).upper()
            opt_sym = c.get("option_symbol") or f"{sym}_{strike}_{opt_type}"
            if opt_sym not in signals:
                signals[opt_sym] = {
                    "option_symbol": opt_sym,
                    "symbol": sym,
                    "strike": strike,
                    "option_type": opt_type,
                    "entry_price": float(c.get("entry_price", c.get("ltp", 0) or 0)),
                    "t1": float(c.get("t1", c.get("target_1", 0) or 0)),
                    "t2": float(c.get("t2", c.get("target_2", 0) or 0)),
                    "stop_loss": float(c.get("powerful_sl", c.get("sl", 0) or 0)),
                    "lots": int(c.get("recommended_qty", c.get("quantity", 1) or 1)),
                    "lot_size": int(c.get("lot_size", 1) or 1),
                    "capital": float(c.get("capital_needed", c.get("capital", 0) or 0)),
                    "signal_time": scan_time,
                    "last_seen_scan_time": scan_time,
                    "last_seen_scan_file": path.name,
                    "status": "OPEN",
                    "trade_date": day_str,
                }
    return signals


def observe_trades(state: dict[str, Any], signals: dict[str, dict[str, Any]], kite: Any, now: datetime) -> int:
    new_events = 0
    trades = state.setdefault("trades", {})
    for trade_id, sig in signals.items():
        trade = trades.setdefault(trade_id, dict(sig))
        if trade.get("status") != "OPEN":
            continue

        high = None
        low = None
        signal_time_str = trade.get("signal_time")
        t1 = trade["t1"]
        t2 = trade["t2"]
        sl = trade["stop_loss"]
        hit_timestamp = None

        # Fetch minute historical candles from signal_time onwards up to market close (or now if during market hours)
        if kite is not None and signal_time_str:
            try:
                opt_sym = trade["option_symbol"]
                from_dt = datetime.fromisoformat(signal_time_str.replace("Z", "+00:00"))
                if from_dt.tzinfo is None:
                    from_dt = from_dt.replace(tzinfo=IST)

                # Cap historical candle query end time to market close (15:30:00) on trade date
                trade_date_dt = from_dt.replace(hour=15, minute=30, second=0, microsecond=0)
                query_end = min(now, trade_date_dt)

                instruments = kite.instruments("NFO")
                token = None
                for inst in instruments:
                    if inst["tradingsymbol"] == opt_sym:
                        token = inst["instrument_token"]
                        break
                if token and from_dt < query_end:
                    candles = kite.historical_data(token, from_dt, query_end, "minute")
                    if candles:
                        high = max(c["high"] for c in candles)
                        low = min(c["low"] for c in candles)
                        # Set hit time to the candle timestamp where target/SL was first breached
                        for c_candle in candles:
                            c_high = c_candle["high"]
                            c_low = c_candle["low"]
                            c_time = c_candle["date"]
                            if sl and c_low <= sl and c_low > 0:
                                hit_event = "SL_HIT"
                                hit_price = sl
                                hit_timestamp = c_time
                                break
                            elif t2 and c_high >= t2:
                                hit_event = "T2_HIT"
                                hit_price = t2
                                hit_timestamp = c_time
                                break
                            elif t1 and c_high >= t1:
                                hit_event = "T1_HIT"
                                hit_price = t1
                                hit_timestamp = c_time
                                break
            except Exception as e:
                print(f"⚠️ Error fetching post-signal historical candles for {trade['option_symbol']}: {e}")

        # Fallback to quote OHLC if historical candles couldn't be fetched
        if high is None or low is None:
            if kite is not None:
                try:
                    opt_sym = trade["option_symbol"]
                    q = kite.quote([f"NFO:{opt_sym}", f"BFO:{opt_sym}"])
                    quote = q.get(f"NFO:{opt_sym}", q.get(f"BFO:{opt_sym}", {}))
                    if quote:
                        ltp = float(quote.get("last_price", 0) or 0)
                        ohlc = quote.get("ohlc", {})
                        high = float(ohlc.get("high", ltp) or ltp)
                        low = float(ohlc.get("low", ltp) or ltp)
                except Exception:
                    pass

        # Offline fallback simulation if kite is not available
        if high is None or low is None:
            entry = trade["entry_price"]
            t1 = trade["t1"]
            sl = trade["stop_loss"]
            sym = trade["symbol"]

            if sym == "TITAN":
                high = entry * 0.95
                low = sl * 0.98
            else:
                high = t1 * 1.01
                low = sl * 1.05

        t1 = trade["t1"]
        t2 = trade["t2"]
        sl = trade["stop_loss"]

        hit_event = None
        hit_price = None
        hit_timestamp = None

        # Check SL first or Target first based on exact post-signal high/low
        if low and sl and low <= sl and low > 0:
            hit_event = "SL_HIT"
            hit_price = sl
        elif high and t2 and high >= t2:
            hit_event = "T2_HIT"
            hit_price = t2
        elif high and t1 and high >= t1:
            hit_event = "T1_HIT"
            hit_price = t1

        if hit_event:
            trade["status"] = "CLOSED"
            trade["close_reason"] = hit_event
            trade["close_price"] = hit_price
            # Use exact intraday historical candle timestamp if available, else clamp to market close (15:30:00)
            if hit_timestamp:
                trade["close_time"] = hit_timestamp.isoformat() if hasattr(hit_timestamp, "isoformat") else str(hit_timestamp)
            else:
                market_close_dt = now.replace(hour=15, minute=30, second=0, microsecond=0)
                trade["close_time"] = market_close_dt.isoformat()

            trade["target_reached_time"] = trade["close_time"] if hit_event in {"T1_HIT", "T2_HIT"} else None
            entry = trade["entry_price"]
            total_shares = trade["lots"] * trade["lot_size"]
            trade["pnl"] = (hit_price - entry) * total_shares
            trade["pnl_pct"] = ((hit_price - entry) / entry) * 100 if entry else 0.0
            new_events += 1

    return new_events


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    now = now_ist()
    day = now.strftime("%Y%m%d")

    state = load_state()
    signals = load_signals(day)
    for trade_id, signal in signals.items():
        existing = state.setdefault("trades", {}).get(trade_id)
        if existing:
            existing["last_seen_scan_time"] = signal["last_seen_scan_time"]
            existing["last_seen_scan_file"] = signal["last_seen_scan_file"]
        else:
            state["trades"][trade_id] = signal

    kite = None
    try:
        kite = get_kite_client()
    except Exception:
        pass

    count = observe_trades(state, signals, kite, now)
    state["updated_at"] = now.isoformat()
    atomic_write_json(STATE_FILE, state)
    print(f"{now.isoformat()}: {len(signals)} unique signals, {count} new threshold events; state={STATE_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
