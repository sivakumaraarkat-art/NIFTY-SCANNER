"""
options_data_provider.py
═════════════════════════════════════════════════════════════════
Live Market Data & Real Option Strike Resolution Provider for:
  1. Intraday Options Scanner (with 4-Layer Powerful SL)
  2. BTST Options Scanner (with 4-Layer Powerful SL)

Capabilities:
  • Connects to Zerodha Kite API safely using local/shared token credentials.
  • Resolves real ATM / liquid strikes from the live NFO, BFO & MCX instrument master.
  • Fetches live underlying Spot price & Option LTP in real time.
  • Calculates analytical Black-Scholes Greeks (Delta, Theta, Vega, IV).
  • Applies 4-Layer Powerful Stop Loss & Target calculations.
  • Accurately calculates Position Sizing based on real exchange Lot Sizes.
  • Provides realistic fallback simulation if Kite is offline/pre-market.
"""

from __future__ import annotations

import os
import time
import json
import math
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

try:
    from kiteconnect import KiteConnect
except ImportError:
    KiteConnect = None

# Known Index Spot symbol mappings on Kite
INDEX_MAP = {
    "NIFTY": "NSE:NIFTY 50",
    "NIFTY 50": "NSE:NIFTY 50",
    "BANKNIFTY": "NSE:NIFTY BANK",
    "NIFTY BANK": "NSE:NIFTY BANK",
    "FINNIFTY": "NSE:NIFTY FIN SERVICE",
    "MIDCPNIFTY": "NSE:NIFTY MID SELECT",
    "SENSEX": "BSE:SENSEX",
    "BSE SENSEX": "BSE:SENSEX",
}

# Standard fallback lot sizes for major F&O and Commodity symbols if Master is unreachable
FALLBACK_LOT_SIZES = {
    "NIFTY": 65,
    "BANKNIFTY": 30,
    "SENSEX": 20,
    "FINNIFTY": 60,
    "MIDCPNIFTY": 120,
    "RELIANCE": 500,
    "TCS": 225,
    "HDFCBANK": 650,
    "INFY": 400,
    "ICICIBANK": 700,
    "SBIN": 750,
    "BHARTIARTL": 475,
    "ITC": 1600,
    "KOTAKBANK": 400,
    "LT": 175,
    "AXISBANK": 625,
    "BAJFINANCE": 750,
    "MARUTI": 50,
    "TATAMOTORS": 700,
    "SUNPHARMA": 350,
    "TITAN": 175,
    "BPCL": 1975,
    "VEDL": 1150,
    "TATASTEEL": 5500,
    "COALINDIA": 1050,
    "HINDALCO": 700,
    "JSWSTEEL": 675,
    "NTPC": 1500,
    "POWERGRID": 1900,
    "ONGC": 1925,
    "IOC": 4875,
    "WIPRO": 1500,
    "HCLTECH": 350,
    "TECHM": 300,
    "ADANIENT": 300,
    "ADANIPORTS": 400,
    "CRUDEOIL": 100,
}

# ──────────────────────────────────────────────────────────────
# 1. KITE CONNECT CLIENT INITIALIZATION
# ──────────────────────────────────────────────────────────────

def get_kite_client() -> Optional[Any]:
    """Safely initialize and authenticate KiteConnect client."""
    if KiteConnect is None:
        return None

    token_candidates = [
        Path("/home/ubuntu/NiftyScanner/.kite_access_token"),
        Path("/home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/.kite_access_token"),
        Path("/home/ubuntu/NiftyScanner/nifty_v14_7/.kite_access_token"),
        Path("/home/ubuntu/NiftyScanner/PORTFOLIO_PEAK_EXIT_GUARD/.kite_access_token"),
        Path("D:/NiftyScanner/.kite_access_token"),
        Path.home() / ".kite_access_token",
        Path(".kite_access_token"),
        Path("../.kite_access_token"),
        Path("../../.kite_access_token"),
    ]
    key_candidates = [
        Path("/home/ubuntu/NiftyScanner/.kite_api_key"),
        Path("/home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/.kite_api_key"),
        Path("/home/ubuntu/NiftyScanner/nifty_v14_7/.kite_api_key"),
        Path("D:/NiftyScanner/.kite_api_key"),
        Path.home() / ".kite_api_key",
        Path(".kite_api_key"),
        Path("../.kite_api_key"),
        Path("../../.kite_api_key"),
    ]

    token = os.getenv("ZERODHA_ACCESS_TOKEN", "").strip()
    if not token:
        master_token = Path("/home/ubuntu/NiftyScanner/.kite_access_token")
        if master_token.exists():
            try:
                val = master_token.read_text(encoding="utf-8").strip()
                if val:
                    token = val
            except Exception:
                pass

    if not token:
        existing_tokens = [p for p in token_candidates if p and p.exists()]
        existing_tokens.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        for p in existing_tokens:
            try:
                val = p.read_text(encoding="utf-8").strip()
                if val:
                    token = val
                    break
            except Exception:
                pass

    api_key = os.getenv("ZERODHA_API_KEY", "").strip()
    if not api_key:
        master_key = Path("/home/ubuntu/NiftyScanner/.kite_api_key")
        if master_key.exists():
            try:
                val = master_key.read_text(encoding="utf-8").strip()
                if val:
                    api_key = val
            except Exception:
                pass

    if not api_key:
        for p in key_candidates:
            if p and p.exists():
                try:
                    val = p.read_text(encoding="utf-8").strip()
                    if val:
                        api_key = val
                        break
                except Exception:
                    pass

    if not token or not api_key:
        return None

    try:
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(token)
        kite.profile()
        return kite
    except Exception as e:
        print(f"⚠️ [KiteConnect] Authentication check failed: {e}")
        return None


# ──────────────────────────────────────────────────────────────
# 2. INSTRUMENT MASTER CACHE (NFO, BFO & MCX)
# ──────────────────────────────────────────────────────────────

_NFO_CACHE = None
_NFO_CACHE_DATE = None

def get_nfo_instruments(kite: Optional[Any], cache_dir: Path = Path("logs")) -> List[dict]:
    """Retrieve NFO, BFO and MCX instruments, caching daily in memory and on disk."""
    global _NFO_CACHE, _NFO_CACHE_DATE
    today = datetime.date.today()

    if _NFO_CACHE is not None and _NFO_CACHE_DATE == today:
        return _NFO_CACHE

    cache_dir.mkdir(exist_ok=True, parents=True)
    cache_file = cache_dir / f"nfo_instruments_{today.strftime('%Y%m%d')}.json"

    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    if "expiry" in item and item["expiry"]:
                        item["expiry"] = datetime.datetime.strptime(item["expiry"], "%Y-%m-%d").date()
                _NFO_CACHE = data
                _NFO_CACHE_DATE = today
                return _NFO_CACHE
        except Exception:
            pass

    if kite is not None:
        try:
            print("⏳ Downloading live NFO, BFO & MCX instrument master from Zerodha Kite...")
            raw_instruments = kite.instruments("NFO")
            for exch in ["BFO", "MCX"]:
                try:
                    ex_inst = kite.instruments(exch)
                    if ex_inst:
                        raw_instruments.extend(ex_inst)
                except Exception:
                    pass

            serialized = []
            for item in raw_instruments:
                exp_date = item.get("expiry")
                exp_str = exp_date.isoformat() if isinstance(exp_date, (datetime.date, datetime.datetime)) else str(exp_date)
                serialized.append({
                    "instrument_token": item.get("instrument_token"),
                    "tradingsymbol": item.get("tradingsymbol"),
                    "name": item.get("name"),
                    "last_price": item.get("last_price", 0.0),
                    "expiry": exp_str,
                    "strike": float(item.get("strike", 0.0)),
                    "tick_size": item.get("tick_size", 0.05),
                    "lot_size": int(item.get("lot_size", 1)),
                    "instrument_type": item.get("instrument_type"),
                    "segment": item.get("segment"),
                })
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(serialized, f)

            for item in serialized:
                if item["expiry"]:
                    try:
                        item["expiry"] = datetime.datetime.strptime(item["expiry"], "%Y-%m-%d").date()
                    except Exception:
                        item["expiry"] = today
            _NFO_CACHE = serialized
            _NFO_CACHE_DATE = today
            print(f"✅ Loaded {len(_NFO_CACHE):,} total derivative contracts (NFO+BFO+MCX).")
            return _NFO_CACHE
        except Exception as e:
            print(f"⚠️ [KiteConnect] Could not fetch instrument masters: {e}")

    return []


# ──────────────────────────────────────────────────────────────
# 3. BLACK-SCHOLES GREEKS & IV CALCULATOR
# ──────────────────────────────────────────────────────────────

def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_pdf(x: float) -> float:
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)


def bs_price(spot: float, strike: float, t_years: float, r: float, sigma: float, opt_type: str = "CE") -> float:
    if t_years <= 0 or sigma <= 0 or spot <= 0 or strike <= 0:
        return max(0.0, spot - strike) if opt_type.upper() == "CE" else max(0.0, strike - spot)
    d1 = (math.log(spot / strike) + (r + 0.5 * sigma ** 2) * t_years) / (sigma * math.sqrt(t_years))
    d2 = d1 - sigma * math.sqrt(t_years)
    if opt_type.upper() == "CE":
        return spot * norm_cdf(d1) - strike * math.exp(-r * t_years) * norm_cdf(d2)
    else:
        return strike * math.exp(-r * t_years) * norm_cdf(-d2) - spot * norm_cdf(-d1)


def implied_volatility(
    price: float,
    spot: float,
    strike: float,
    t_days: float,
    r: float = 0.07,
    opt_type: str = "CE",
    default_iv: float = 0.25
) -> float:
    t_years = max(t_days / 365.0, 1.0 / 365.0)
    intrinsic = max(0.0, spot - strike) if opt_type.upper() == "CE" else max(0.0, strike - spot)
    if price <= intrinsic or price <= 0.05:
        return default_iv

    sigma = default_iv
    for _ in range(25):
        p = bs_price(spot, strike, t_years, r, sigma, opt_type)
        diff = p - price
        if abs(diff) < 1e-3:
            return max(0.05, min(sigma, 1.5))
        d1 = (math.log(spot / strike) + (r + 0.5 * sigma ** 2) * t_years) / (sigma * math.sqrt(t_years))
        vega = spot * norm_pdf(d1) * math.sqrt(t_years)
        if vega < 1e-4:
            break
        sigma = sigma - diff / vega
        if sigma <= 0.02 or sigma > 2.0:
            return default_iv
    return max(0.05, min(sigma, 1.5))


def calculate_greeks(
    spot: float,
    strike: float,
    t_days: float,
    r: float,
    iv_pct: float,
    opt_type: str = "CE"
) -> Tuple[float, float, float]:
    T = max(t_days / 365.0, 1.0 / 365.0)
    sigma = max(iv_pct, 0.05)
    d1 = (math.log(spot / strike) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    pdf_d1 = norm_pdf(d1)

    if opt_type.upper() == "CE":
        delta = norm_cdf(d1)
        theta = (- (spot * pdf_d1 * sigma) / (2 * math.sqrt(T)) - r * strike * math.exp(-r * T) * norm_cdf(d2)) / 365.0
    else:
        delta = norm_cdf(d1) - 1.0
        theta = (- (spot * pdf_d1 * sigma) / (2 * math.sqrt(T)) + r * strike * math.exp(-r * T) * norm_cdf(-d2)) / 365.0

    vega = (spot * pdf_d1 * math.sqrt(T)) / 100.0
    return round(delta, 2), round(theta, 2), round(vega, 2)


# ──────────────────────────────────────────────────────────────
# 4. POWERFUL 4-LAYER SL ENGINE
# ──────────────────────────────────────────────────────────────

def calculate_powerful_sl_engine(
    entry_price: float,
    delta: float,
    iv: float,
    theta: float,
    vega: float,
    is_btst: bool = False,
    days_held: float = 1.0
) -> Dict[str, Any]:
    iv_pct = iv / 100 if iv > 1 else iv
    theta_abs = abs(theta)
    vega_abs = abs(vega)

    if iv_pct > 0.30:
        market_vol = "extreme"
    elif iv_pct > 0.20:
        market_vol = "volatile"
    else:
        market_vol = "normal"

    if not is_btst:
        delta_mult = 0.18 if market_vol == "normal" else (0.20 if market_vol == "volatile" else 0.22)
        theta_mult = 1.5 if market_vol == "normal" else (2.0 if market_vol == "volatile" else 2.5)
        vega_mult = 5.0 if market_vol != "extreme" else 7.5

        layer1_buffer = entry_price * (abs(delta) * delta_mult)
        layer2_vol_buffer = ((iv_pct / 0.20) * entry_price * 0.05) if iv_pct > 0.20 else 0.0
        layer3_theta_buffer = theta_abs * days_held * theta_mult
        layer4_vega_buffer = vega_abs * vega_mult

        total_buffer = layer1_buffer + layer2_vol_buffer + layer3_theta_buffer + layer4_vega_buffer
        powerful_sl = entry_price - total_buffer
        powerful_sl = max(powerful_sl, entry_price * 0.80)

        trailing_trigger = entry_price * 1.05
        trailing_sl_new = powerful_sl + (entry_price * 1.05 - entry_price) * 0.5
    else:
        layer1_buffer = entry_price * (abs(delta) * 0.15)
        layer2_vol_buffer = ((iv_pct / 0.20) * entry_price * 0.08) if iv_pct > 0.20 else 0.0
        layer3_theta_buffer = theta_abs * 1.0 * 2.5
        layer4_vega_buffer = vega_abs * 7.5

        total_buffer = layer1_buffer + layer2_vol_buffer + layer3_theta_buffer + layer4_vega_buffer
        powerful_sl = entry_price - total_buffer
        powerful_sl = max(powerful_sl, entry_price * 0.75)

        trailing_trigger = entry_price * 1.10
        trailing_sl_new = entry_price

    return {
        "entry_price": round(entry_price, 2),
        "layer1_buffer": round(layer1_buffer, 2),
        "layer2_vol_buffer": round(layer2_vol_buffer, 2),
        "layer3_theta_buffer": round(layer3_theta_buffer, 2),
        "layer4_vega_buffer": round(layer4_vega_buffer, 2),
        "total_buffer": round(total_buffer, 2),
        "powerful_sl": round(powerful_sl, 2),
        "sl_risk": round(entry_price - powerful_sl, 2),
        "sl_risk_pct": round((entry_price - powerful_sl) / entry_price * 100, 2),
        "trailing_trigger": round(trailing_trigger, 2),
        "trailing_sl_new": round(trailing_sl_new, 2),
        "market_volatility": market_vol,
    }


# ──────────────────────────────────────────────────────────────
# 5. REAL OPTION CANDIDATE RESOLVER (Supports NSE, BSE & MCX)
# ──────────────────────────────────────────────────────────────

def resolve_option_candidate(
    kite: Optional[Any],
    nfo_instruments: List[dict],
    symbol: str,
    sentiment: str = "BULLISH",
    is_btst: bool = False,
    account_size: float = 500000.0,
    sentiment_score: int = 70,
) -> Optional[Dict[str, Any]]:
    opt_type = "PE" if "BEARISH" in sentiment.upper() else "CE"
    symbol = symbol.strip().upper()
    is_index = symbol in INDEX_MAP
    is_crude = "CRUDE" in symbol

    # Resolve spot / underlying price key
    if is_crude:
        spot_key = "MCX:CRUDEOIL26OCTFUT"
    elif is_index:
        spot_key = INDEX_MAP.get(symbol, f"NSE:{symbol}")
    else:
        spot_key = f"NSE:{symbol}"

    spot_price = 0.0
    if kite is not None:
        try:
            q = kite.ltp(spot_key)
            if spot_key in q and q[spot_key]["last_price"] > 0:
                spot_price = float(q[spot_key]["last_price"])
        except Exception as e:
            print(f"⚠️ Could not fetch spot price for {symbol}: {e}")

    if spot_price <= 0:
        fallback_spots = {
            "NIFTY": 22500.0, "BANKNIFTY": 54800.0, "SENSEX": 81500.0, "RELIANCE": 1180.0,
            "TCS": 2130.0, "HDFCBANK": 715.0, "INFY": 1030.0,
            "BPCL": 305.0, "VEDL": 255.0, "MARUTI": 11400.0, "BAJFINANCE": 990.0,
            "CRUDEOIL": 8750.0,
        }
        spot_price = fallback_spots.get(symbol, 1000.0)

    today = datetime.date.today()
    contract = None
    tradingsymbol = ""
    lot_size = FALLBACK_LOT_SIZES.get(symbol, 100 if is_crude else 500)
    atm_strike = spot_price
    t_days = 20

    # Match exact option contract from Master (NFO/BFO/MCX)
    if nfo_instruments:
        sym_opts = [
            i for i in nfo_instruments
            if symbol in i.get("name", "").upper() and i.get("instrument_type") == opt_type and i.get("expiry") and i["expiry"] >= today
        ]
        if sym_opts:
            expiries = sorted(list(set(i["expiry"] for i in sym_opts)))
            nearest_exp = expiries[0]
            t_days = max(1, (nearest_exp - today).days)
            exp_opts = [i for i in sym_opts if i["expiry"] == nearest_exp]
            strikes = sorted(list(set(i["strike"] for i in exp_opts)))
            if strikes:
                atm_strike = min(strikes, key=lambda s: abs(s - spot_price))
                contract = next((i for i in exp_opts if i["strike"] == atm_strike), None)
                if contract:
                    tradingsymbol = contract["tradingsymbol"]
                    lot_size = contract["lot_size"]

    option_ltp = 0.0
    bid_price = 0.0
    ask_price = 0.0
    spread_pct = 0.0
    open_interest = 0

    if kite is not None and tradingsymbol:
        try:
            exch_prefix = "MCX" if is_crude else "NFO"
            exch_key = f"{exch_prefix}:{tradingsymbol}"
            quotes = kite.quote([exch_key])
            if exch_key in quotes:
                q_info = quotes[exch_key]
                if q_info.get("last_price", 0) > 0:
                    option_ltp = float(q_info["last_price"])
                open_interest = int(q_info.get("oi", 0))

                depth = q_info.get("depth", {})
                buy_orders = depth.get("buy", [])
                sell_orders = depth.get("sell", [])
                if buy_orders and buy_orders[0].get("price", 0) > 0:
                    bid_price = float(buy_orders[0]["price"])
                if sell_orders and sell_orders[0].get("price", 0) > 0:
                    ask_price = float(sell_orders[0]["price"])

                if bid_price > 0 and ask_price > 0 and option_ltp > 0:
                    spread_pct = round(((ask_price - bid_price) / option_ltp) * 100.0, 2)
        except Exception:
            pass

    # SAFETY: Never invent an option contract or use a
    # theoretical price as a live trading entry.
    if not tradingsymbol:
        print(
            f"❌ SKIPPED: No verified MCX {symbol} "
            f"{opt_type} contract found in Zerodha instruments."
        )
        return None
    if kite is None:
        print("❌ SKIPPED: Zerodha Kite is not authenticated.")
        return None
    if option_ltp <= 0.05:
        print(
            f"❌ SKIPPED: No valid live quote for "
            f"MCX:{tradingsymbol}. No signal sent."
        )
        return None

    iv = implied_volatility(option_ltp, spot_price, atm_strike, t_days, r=0.07, opt_type=opt_type)
    delta, theta, vega = calculate_greeks(spot_price, atm_strike, t_days, r=0.07, iv_pct=iv, opt_type=opt_type)

    sl_data = calculate_powerful_sl_engine(
        entry_price=option_ltp,
        delta=delta,
        iv=iv * 100,
        theta=theta,
        vega=vega,
        is_btst=is_btst,
        days_held=1.0 if not is_btst else 1.5,
    )

    if not is_btst:
        t1 = round(option_ltp * 1.08, 2)
        t2 = round(option_ltp * 1.15, 2)
    else:
        t1 = round(option_ltp * 1.25, 2)
        t2 = round(option_ltp * 1.50, 2)

    if is_index:
        step_sz = 50.0 if symbol in ["NIFTY", "NIFTY 50"] else 100.0
    elif is_crude:
        step_sz = 50.0
    else:
        if spot_price >= 1000.0:
            step_sz = 20.0
        elif spot_price >= 500.0:
            step_sz = 10.0
        else:
            step_sz = 5.0

    if opt_type == "CE":
        conservative_itm_strike = max(0.0, atm_strike - step_sz)
    else:
        conservative_itm_strike = atm_strike + step_sz

    warning_flags = []
    if is_btst and not is_index and t_days <= 2:
        warning_flags.append(f"⚠️ DTE {t_days}d (Overnight Theta Risk)")

    if spread_pct > 5.0:
        warning_flags.append(f"⚠️ Wide Spread ({spread_pct:.1f}%)")
        if spread_pct > 8.0:
            sentiment_score = max(0, sentiment_score - 15)

    if iv * 100 > 35.0:
        warning_flags.append(f"🔥 High IV ({iv*100:.0f}% Vega Risk)")

    risk_per_share = sl_data["sl_risk"]
    risk_per_lot = risk_per_share * lot_size
    account_risk_budget = account_size * 0.01

    if risk_per_lot > 0:
        recommended_lots = max(1, int(account_risk_budget / risk_per_lot))
    else:
        recommended_lots = 1

    if iv * 100 > 40.0 and recommended_lots > 1:
        recommended_lots = max(1, recommended_lots // 2)

    total_shares = recommended_lots * lot_size
    capital_needed = round(total_shares * option_ltp, 2)
    max_risk_actual = round(total_shares * risk_per_share, 2)

    return {
        "symbol": symbol,
        "option_symbol": tradingsymbol,
        "strike": float(atm_strike),
        "conservative_strike": float(conservative_itm_strike),
        "option_type": opt_type,
        "type": opt_type,
        "spot_price": round(spot_price, 2),
        "ltp": round(option_ltp, 2),
        "entry_price": round(option_ltp, 2),
        "bid_price": round(bid_price, 2),
        "ask_price": round(ask_price, 2),
        "spread_pct": spread_pct,
        "open_interest": open_interest,
        "dte": t_days,
        "lot_size": lot_size,
        "recommended_qty": recommended_lots,
        "total_shares": total_shares,
        "capital_needed": capital_needed,
        "max_risk": max_risk_actual,
        "t1": t1,
        "t2": t2,
        "target_1": t1,
        "target_2": t2,
        "potential_profit_t1": round(total_shares * (t1 - option_ltp), 2),
        "potential_profit_t2": round(total_shares * (t2 - option_ltp), 2),
        "powerful_sl": sl_data["powerful_sl"],
        "sl": sl_data["powerful_sl"],
        "sl_risk": sl_data["sl_risk"],
        "sl_risk_pct": sl_data["sl_risk_pct"],
        "trailing_trigger": sl_data["trailing_trigger"],
        "trailing_sl_new": sl_data["trailing_sl_new"],
        "delta": delta,
        "theta": theta,
        "vega": vega,
        "iv": round(iv * 100, 1),
        "market_volatility": sl_data["market_volatility"],
        "score": sentiment_score,
        "sentiment_catalyst": sentiment,
        "warning_flags": warning_flags,
        "warning_tag": " • ".join(warning_flags) if warning_flags else "",
        "layer1_buffer": sl_data["layer1_buffer"],
        "layer2_vol_buffer": sl_data["layer2_vol_buffer"],
        "layer3_theta_buffer": sl_data["layer3_theta_buffer"],
        "layer4_vega_buffer": sl_data["layer4_vega_buffer"],
    }


# ──────────────────────────────────────────────────────────────
# 6. BATCH RESOLUTION HELPER
# ──────────────────────────────────────────────────────────────

def resolve_all_candidates(
    candidates_list: List[Any],
    is_btst: bool = False,
    include_nifty: bool = False,
    account_size: float = 500000.0,
    min_score: int = 50,
) -> List[Dict[str, Any]]:
    kite = get_kite_client()
    nfo_instruments = get_nfo_instruments(kite)

    results = []

    if is_btst and include_nifty:
        for idx in ["NIFTY", "SENSEX"]:
            res = resolve_option_candidate(
                kite, nfo_instruments, idx, "BULLISH", is_btst=True, account_size=account_size, sentiment_score=85
            )
            if res and res["score"] >= min_score:
                results.append(res)

    for item in candidates_list:
        if isinstance(item, tuple):
            sym = item[0]
            sent = item[1]
            score = int(item[2]) if len(item) > 2 else 70
        else:
            sym = str(item).strip()
            sent = "BULLISH"
            score = 70

        if not sym:
            continue

        if kite is not None:
            time.sleep(0.35)

        cand = resolve_option_candidate(
            kite, nfo_instruments, sym, sent, is_btst=is_btst, account_size=account_size, sentiment_score=score
        )
        if cand and cand["score"] >= min_score:
            results.append(cand)

    return results
