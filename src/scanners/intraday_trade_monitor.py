"""Poll intraday scan signals and persist first observed T1/T2/SL crossings.

Run every minute during market hours, after the intraday scanner. Hit times use completed one-minute historical candles, not broker fill times.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, time as time_type
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
            else:
                signals[opt_sym]["last_seen_scan_time"] = scan_time
                signals[opt_sym]["last_seen_scan_file"] = path.name
    return signals


def as_ist(value: Any) -> datetime:
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return dt.replace(tzinfo=IST) if dt.tzinfo is None else dt.astimezone(IST)


def observe_trades(state: dict[str, Any], signals: dict[str, dict[str, Any]], kite: Any, now: datetime) -> int:
    """Close on first threshold candle; never infer hit times from daily OHLC.

    Minute bars cannot determine seconds or the ordering of SL and target in
    the same bar. The partial signal minute is excluded to avoid pre-entry hits.
    Existing unverified closed records are preserved for explicit reconciliation.
    """
    now = as_ist(now)
    trades = state.setdefault("trades", {})
    tokens = None
    new_events = 0
    for trade_id, sig in signals.items():
        trade = trades.get(trade_id)
        if trade is None or trade.get("trade_date") != sig.get("trade_date"):
            if trade is not None:
                trades[f"{trade.get('trade_date')}:{trade_id}"] = dict(trade)
            trade = trades[trade_id] = dict(sig)
        if trade.get("status") != "OPEN":
            continue
        trade["data_status"] = "unavailable"
        if kite is None:
            continue
        try:
            start = as_ist(trade["signal_time"])
            end = min(now, start.replace(hour=15, minute=30, second=0, microsecond=0))
            if start >= end:
                continue
            if tokens is None:
                tokens = {i["tradingsymbol"]: i["instrument_token"] for i in kite.instruments("NFO")}
            token = tokens.get(trade["option_symbol"])
            if token is None:
                continue
            candles = kite.historical_data(token, start, end, "minute")
            valid = []
            for candle in candles:
                stamp = as_ist(candle["date"])
                if (start <= stamp and stamp + timedelta(minutes=1) <= end
                        and stamp.date() == start.date()
                        and time_type(9, 15) <= stamp.time() < MARKET_CLOSE):
                    valid.append((stamp, candle))
            trade["data_status"] = "minute_candles" if valid else "unavailable"
            for stamp, candle in sorted(valid, key=lambda item: item[0]):
                high, low = float(candle["high"]), float(candle["low"])
                t1, t2, sl = trade["t1"], trade["t2"], trade["stop_loss"]
                stop = bool(sl and 0 < low <= sl)
                target2 = bool(t2 and high >= t2)
                target1 = bool(t1 and high >= t1)
                if not (stop or target1 or target2):
                    continue
                if stop and (target1 or target2):
                    trade["data_status"] = "ambiguous_target_sl"
                    trade["ambiguous_time"] = stamp.isoformat()
                    break
                reason, price = ("SL_HIT", sl) if stop else (("T2_HIT", t2) if target2 else ("T1_HIT", t1))
                trade.update(status="CLOSED", close_reason=reason, close_price=price,
                             close_time=stamp.isoformat(), hit_time_source="minute_candle",
                             hit_time_precision="minute", observed_at=now.isoformat())
                trade["target_reached_time"] = stamp.isoformat() if not stop else None
                entry = trade["entry_price"]
                trade["pnl"] = (price - entry) * trade["lots"] * trade["lot_size"]
                trade["pnl_pct"] = (price - entry) / entry * 100 if entry else 0.0
                new_events += 1
                break
        except Exception as exc:
            trade["data_status"] = "unavailable"
            print(f"Historical data unavailable for {trade['option_symbol']}: {type(exc).__name__}")
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
