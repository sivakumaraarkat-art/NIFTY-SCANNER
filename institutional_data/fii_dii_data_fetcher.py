"""
FII/DII Institutional Data Fetcher

Fetches Foreign Institutional Investor (FII) and Domestic Institutional Investor (DII)
buying/selling data from NSE India and analyzes stock-level institutional interest.
"""

import requests
import time

_FII_DII_CACHE = {"timestamp": 0, "data": None}
CACHE_TTL = 3600  # 1 hour


def fetch_daily_fii_dii_summary() -> dict | None:
    """
    Fetch daily overall market Net FII and DII Cash Market trading activity from NSE India.

    Returns:
        Dict with DII and FII/FPI net, buy, sell values in Crores, or None if unavailable.
        {
            'dii_net': float,
            'dii_buy': float,
            'dii_sell': float,
            'fii_net': float,
            'fii_buy': float,
            'fii_sell': float,
            'total_net': float,
            'date': str,
        }
    """
    now = time.time()
    if _FII_DII_CACHE["data"] is not None and (
        now - _FII_DII_CACHE["timestamp"] < CACHE_TTL
    ):
        return _FII_DII_CACHE["data"]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        session = requests.Session()
        session.headers.update(headers)
        session.get("https://www.nseindia.com", timeout=8)
        res = session.get("https://www.nseindia.com/api/fiidiiTradeReact", timeout=8)

        if res.status_code == 200:
            raw_data = res.json()
            summary = {
                "dii_net": 0.0,
                "dii_buy": 0.0,
                "dii_sell": 0.0,
                "fii_net": 0.0,
                "fii_buy": 0.0,
                "fii_sell": 0.0,
                "total_net": 0.0,
                "date": "",
            }

            for item in raw_data:
                cat = item.get("category", "")
                net = float(item.get("netValue", 0))
                buy = float(item.get("buyValue", 0))
                sell = float(item.get("sellValue", 0))
                date_str = item.get("date", "")

                if cat == "DII":
                    summary["dii_net"] = net
                    summary["dii_buy"] = buy
                    summary["dii_sell"] = sell
                    summary["date"] = date_str
                elif "FII" in cat or "FPI" in cat:
                    summary["fii_net"] = net
                    summary["fii_buy"] = buy
                    summary["fii_sell"] = sell
                    if not summary["date"]:
                        summary["date"] = date_str

            summary["total_net"] = round(summary["dii_net"] + summary["fii_net"], 2)
            _FII_DII_CACHE["timestamp"] = now
            _FII_DII_CACHE["data"] = summary
            return summary
    except Exception as exc:
        print(f"DEBUG: NSE FII/DII summary fetch: {exc}")

    return None


def format_institutional_flow_header(fii_dii: dict | None) -> str:
    """Format institutional summary for Telegram alerts header."""
    if not fii_dii:
        return ""

    dii_net = fii_dii.get("dii_net", 0.0)
    fii_net = fii_dii.get("fii_net", 0.0)
    tot_net = fii_dii.get("total_net", 0.0)
    date_str = fii_dii.get("date", "Latest")

    dii_icon = "🟢" if dii_net >= 0 else "🔴"
    fii_icon = "🟢" if fii_net >= 0 else "🔴"
    tot_icon = "🟢" if tot_net >= 0 else "🔴"

    return (
        f"🏛️ <b>FII / DII Market Flow ({date_str}):</b>\n"
        f"├─ {dii_icon} <b>DII Net:</b> {'+' if dii_net > 0 else ''}₹{dii_net:,.2f} Cr\n"
        f"├─ {fii_icon} <b>FII Net:</b> {'+' if fii_net > 0 else ''}₹{fii_net:,.2f} Cr\n"
        f"└─ {tot_icon} <b>Combined Net:</b> {'+' if tot_net > 0 else ''}₹{tot_net:,.2f} Cr\n"
    )


def get_institutional_indicator(candidate: dict) -> str:
    """
    Generate stock-specific institutional buying indicator for trade cards.

    Args:
        candidate: Candidate dictionary with stock data

    Returns:
        Formatted string for institutional activity or empty string
    """
    volume_ratio = candidate.get("volume_ratio20", 0)

    if volume_ratio >= 2.0:
        return f"🏦 Strong Institutional Accumulation (🔥 {volume_ratio:.1f}x Volume Surge)"
    elif volume_ratio >= 1.4:
        return f"🏦 Institutional Buying Interest Detected ({volume_ratio:.1f}x Volume)"
    else:
        return "🏦 Normal Institutional Volume Flow"
