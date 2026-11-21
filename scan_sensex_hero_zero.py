"""
scan_sensex_hero_zero.py
========================
Real-Time BSE SENSEX Expiry Day Hero-Zero Scanner (Peak Gamma Window).
Scans live options expiring today (Thursday, Nov 19, 2026) to identify
ultra-cheap (₹1 - ₹15) high-gamma contracts with 3x - 10x boom potential.
"""

import sys
import datetime
from pathlib import Path

# Fix Windows console UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent

# Kite Connect
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()

from kiteconnect import KiteConnect
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

now = datetime.datetime.now()
today_date = datetime.date(2026, 11, 19)

# 1. Sensex Spot Quote
spot_q = kite.quote(["BSE:SENSEX"]).get("BSE:SENSEX", {})
spot_ltp = spot_q.get("last_price", 82550.0)
spot_ohlc = spot_q.get("ohlc", {})
spot_high = spot_ohlc.get("high", spot_ltp)
spot_low = spot_ohlc.get("low", spot_ltp)
spot_open = spot_ohlc.get("open", spot_ltp)
spot_close = spot_ohlc.get("close", spot_ltp)
net_chg_pts = spot_ltp - spot_close
net_chg_pct = (net_chg_pts / spot_close * 100) if spot_close else 0.0

atm_strike = round(spot_ltp / 100) * 100

# 2. Fetch BFO Instruments for today's expiry
insts = kite.instruments("BFO")
today_sensex = [i for i in insts if i.get("name") == "SENSEX" and i.get("expiry") == today_date]

# Focus on strikes around ATM (-1300 to +1300)
min_strike = atm_strike - 1300
max_strike = atm_strike + 1300
target_strikes = [s for s in range(min_strike, max_strike, 100)]
focus_insts = [i for i in today_sensex if int(i.get("strike", 0)) in target_strikes]

symbols = [f"BFO:{i['tradingsymbol']}" for i in focus_insts]
quotes = {}
for idx in range(0, len(symbols), 100):
    quotes.update(kite.quote(symbols[idx:idx+100]))

print("=" * 115)
print(f"🔥 SENSEX HERO-ZERO EXPIRY LIVE SCANNER | {now.strftime('%Y-%m-%d %H:%M:%S IST')}")
print("=" * 115)
print(f"• SENSEX SPOT:     {spot_ltp:,.2f} ({net_chg_pts:+.2f} pts | {net_chg_pct:+.2f}%)")
print(f"• Today's Range:   Low {spot_low:,.2f}  ───►  High {spot_high:,.2f} (Total Move: {spot_high - spot_low:,.2f} pts!)")
print(f"• ATM Strike:      {atm_strike:,}")
print("=" * 115)

print(f"{'Strike':<7} | {'CE Symbol':<22} {'CE LTP':<8} {'CE OI':<10} {'CE Vol':<10} | {'PE Symbol':<22} {'PE LTP':<8} {'PE OI':<10} {'PE Vol':<10}")
print("-" * 115)

hero_zero_candidates = []

for s in target_strikes:
    ce_inst = next((i for i in focus_insts if int(i.get("strike")) == s and i.get("instrument_type") == "CE"), None)
    pe_inst = next((i for i in focus_insts if int(i.get("strike")) == s and i.get("instrument_type") == "PE"), None)

    ce_sym = ce_inst["tradingsymbol"] if ce_inst else "-"
    pe_sym = pe_inst["tradingsymbol"] if pe_inst else "-"

    ce_data = quotes.get(f"BFO:{ce_sym}", {}) if ce_inst else {}
    pe_data = quotes.get(f"BFO:{pe_sym}", {}) if pe_inst else {}

    ce_ltp = ce_data.get("last_price", 0.0)
    ce_oi = ce_data.get("oi", 0)
    ce_vol = ce_data.get("volume", 0)

    pe_ltp = pe_data.get("last_price", 0.0)
    pe_oi = pe_data.get("oi", 0)
    pe_vol = pe_data.get("volume", 0)

    ce_str = f"Rs.{ce_ltp:<6.2f}"
    pe_str = f"Rs.{pe_ltp:<6.2f}"

    # Flag ATM with arrow
    strike_marker = f"{s} ◄" if s == atm_strike else f"{s}"

    print(f"{strike_marker:<7} | {ce_sym:<22} {ce_str:<8} {ce_oi:<10,d} {ce_vol:<10,d} | {pe_sym:<22} {pe_str:<8} {pe_oi:<10,d} {pe_vol:<10,d}")

    # Hero-Zero Bucket 1: Ultra-Cheap (₹1 to ₹6)
    # Hero-Zero Bucket 2: Momentum Gamma (₹6 to ₹25)
    if 0.80 <= ce_ltp <= 30.0:
        dist_pts = s - spot_ltp
        hero_zero_candidates.append({
            "type": "CALL (CE) 🚀",
            "strike": s,
            "sym": ce_sym,
            "ltp": ce_ltp,
            "oi": ce_oi,
            "vol": ce_vol,
            "dist_pts": round(dist_pts, 1),
            "lot_size": ce_inst.get("lot_size", 10)
        })

    if 0.80 <= pe_ltp <= 30.0:
        dist_pts = spot_ltp - s
        hero_zero_candidates.append({
            "type": "PUT (PE) 🔻",
            "strike": s,
            "sym": pe_sym,
            "ltp": pe_ltp,
            "oi": pe_oi,
            "vol": pe_vol,
            "dist_pts": round(dist_pts, 1),
            "lot_size": pe_inst.get("lot_size", 10)
        })

print("\n" + "=" * 115)
print("🎯 TOP RECOMMENDED SENSEX HERO-ZERO CONTRACTS (AFTERNOON GAMMA WINDOW)")
print("=" * 115)

# Sort candidates: First Ultra-Cheap (₹1.00 - ₹5.00), then Momentum (₹5.00 - ₹20.00)
ultra_cheap = sorted([c for c in hero_zero_candidates if c["ltp"] <= 6.0], key=lambda x: (x["dist_pts"], -x["vol"]))
momentum_gamma = sorted([c for c in hero_zero_candidates if 6.0 < c["ltp"] <= 25.0], key=lambda x: (x["dist_pts"], -x["vol"]))

print(f"{'Option Type':<15} {'Strike':<8} {'Tradingsymbol':<24} {'LTP':<8} {'Lot':<5} {'OI':<10} {'Volume':<12} {'Distance':<12} {'Target Payoff'}")
print("-" * 115)

print("[CATEGORY A: ULTRA-CHEAP HERO-ZERO — ₹1.00 to ₹5.00 (5x - 10x MULTIPLIER POTENTIAL)]")
for c in ultra_cheap[:6]:
    mult_10 = round(10.0 / c["ltp"], 1) if c["ltp"] > 0 else 0
    mult_20 = round(20.0 / c["ltp"], 1) if c["ltp"] > 0 else 0
    print(f"{c['type']:<15} {c['strike']:<8} {c['sym']:<24} Rs.{c['ltp']:<5.2f} {c['lot_size']:<5} {c['oi']:<10,d} {c['vol']:<12,d} +{c['dist_pts']:<10.1f} pts -> T1:Rs.10 ({mult_10}x) | T2:Rs.20 ({mult_20}x)")

print("\n[CATEGORY B: MOMENTUM GAMMA HERO-ZERO — ₹6.00 to ₹25.00 (HIGH WIN-RATE 2x - 4x RUNNER)]")
for c in momentum_gamma[:6]:
    t1 = round(c["ltp"] * 2.2, 1)
    t2 = round(c["ltp"] * 4.0, 1)
    print(f"{c['type']:<15} {c['strike']:<8} {c['sym']:<24} Rs.{c['ltp']:<5.2f} {c['lot_size']:<5} {c['oi']:<10,d} {c['vol']:<12,d} +{c['dist_pts']:<10.1f} pts -> T1:Rs.{t1:.1f} (2.2x) | T2:Rs.{t2:.1f} (4.0x)")

print("=" * 115)
