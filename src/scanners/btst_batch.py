"""One immutable daily selection shared by BTST scan, Telegram and next-day reports."""
import copy
import json
import math
import os
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))
INDEX_SYMBOLS = {"NIFTY", "SENSEX", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"}


def now_ist():
    return datetime.now(IST)


def project_root(script):
    path = Path(script).resolve()
    for parent in path.parents:
        if (parent / "src" / "scanners").is_dir():
            return parent
    return path.parent


def logs_directory(script, supplied=None):
    return Path(supplied or os.getenv("BTST_LOG_DIR") or
                project_root(script) / "logs").expanduser().resolve()


def contract_id(candidate):
    symbol = str(candidate.get("option_symbol") or "").strip().upper()
    if not symbol:
        raise ValueError("BTST candidates must contain the exact option_symbol including expiry.")
    exchange = str(candidate.get("exchange") or
                   ("BFO" if candidate.get("symbol") in {"SENSEX", "BANKEX"} else "NFO")).upper()
    return f"{exchange}:{symbol}"


def select_candidates(stocks, indices):
    """Keep scanner's 2 CE + 2 PE policy, with one index slot; at most five."""
    seen = set()
    unique = []
    for item in stocks + indices:
        key = contract_id(item)
        if key not in seen:
            unique.append(item)
            seen.add(key)
    stocks = [c for c in unique if c.get("symbol") not in INDEX_SYMBOLS]
    indices = [c for c in unique if c.get("symbol") in INDEX_SYMBOLS]
    selected = ([c for c in stocks if c.get("option_type") == "CE"][:2] +
                [c for c in stocks if c.get("option_type") == "PE"][:2])
    selected += [c for c in stocks if c not in selected][:4 - len(selected)]
    selected += indices[:1]
    selected += [c for c in stocks if c not in selected][:5 - len(selected)]
    return copy.deepcopy(selected[:5])


def batch_path(log_dir, scan_date):
    return Path(log_dir) / f"btst_alert_batch_{date.fromisoformat(str(scan_date)):%Y%m%d}.json"


def validate_batch(batch):
    if batch.get("schema_version") != 1:
        raise ValueError("Unknown BTST batch schema; cannot reconstruct alerts from all candidates.")
    date.fromisoformat(batch["scan_date"])
    items = batch.get("selected_candidates")
    if not isinstance(items, list) or not 1 <= len(items) <= 5:
        raise ValueError("BTST selection must contain between one and five contracts.")
    keys = [contract_id(c) for c in items]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate contracts in BTST batch.")
    for c in items:
        entry = float(c.get("entry_price", c.get("ltp", 0)))
        lots, lot_size = float(c.get("recommended_qty", 0)), float(c.get("lot_size", 0))
        if not all(math.isfinite(x) and x > 0 for x in (entry, lots, lot_size)):
            raise ValueError("BTST entry and sizing must be positive and finite.")
        if lots != int(lots) or lot_size != int(lot_size):
            raise ValueError("BTST lot counts and lot sizes must be integers.")
    return batch


def create_batch(log_dir, selected, source_log, at=None):
    at = (at or now_ist()).astimezone(IST)
    batch = validate_batch({
        "schema_version": 1, "batch_id": f"BTST-{at:%Y%m%d}-{uuid.uuid4().hex[:8]}",
        "scan_date": at.date().isoformat(), "created_at": at.isoformat(),
        "source_log": str(source_log), "selected_candidates": copy.deepcopy(selected),
        "telegram_delivery": {contract_id(c): "pending" for c in selected},
    })
    path = batch_path(log_dir, batch["scan_date"])
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation blocks duplicate cron/rerun alerts and preserves the first batch.
    with path.open("x", encoding="utf-8") as stream:
        json.dump(batch, stream, indent=2, default=str)
        stream.flush()
        os.fsync(stream.fileno())
    return path, batch


def record_delivery(path, batch, candidate, delivered):
    batch["telegram_delivery"][contract_id(candidate)] = "sent" if delivered else "failed_or_unknown"
    temp = Path(str(path) + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temp.open("x", encoding="utf-8") as stream:
            json.dump(batch, stream, indent=2, default=str)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def previous_weekday(today):
    day = today - timedelta(days=1)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


def load_batch(log_dir, scan_date=None, at=None):
    today = (at or now_ist()).astimezone(IST).date()
    target = date.fromisoformat(str(scan_date)) if scan_date else previous_weekday(today)
    if target >= today:
        raise ValueError("Next-day report requires a scan date before today (IST).")
    path = batch_path(log_dir, target)
    if not path.exists():
        raise FileNotFoundError(
            f"No saved selected batch for {target}: {path}. "
            "Old full-pool logs cannot prove which contracts were alerted. "
            "After a market holiday, specify --scan-date YYYY-MM-DD explicitly.")
    with path.open(encoding="utf-8") as stream:
        batch = validate_batch(json.load(stream))
    if batch["scan_date"] != target.isoformat():
        raise ValueError("BTST batch date does not match its filename.")
    return path, batch
