"""
crude_next_setup_scanner.py
═════════════════════════════════════════════════════════════════════════════
Real-time MCX Crude Oil Market Structure Audit & Setup Analyzer:
  1. Identifies the active near-month CRUDEOIL Future contract on MCX.
  2. Queries Kite quote API for real-time Futures LTP, Open, High, Low, Volume & OI.
  3. Calculates the dynamic ATM center strike (rounded to 50 pts).
  4. Scans and quotes near-expiry CE & PE options across ATM ± 150 points.
  5. Computes intraday range positioning, momentum bias, and concrete trade setups
     with dynamic entry triggers, exact Stop Loss, Targets, and risk-reward ratios.
═════════════════════════════════════════════════════════════════════════════
"""

import sys
import os
import io
from pathlib import Path
from datetime import date, datetime

# UTF-8 fix for Windows console
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scanners.options_data_provider import get_kite_client

def parse_expiry(exp_val):
    if not exp_val:
        return None
    if isinstance(exp_val, str):
        try:
            return datetime.strptime(exp_val, "%Y-%m-%d").date()
        except Exception:
            return None
    elif isinstance(exp_val, datetime):
        return exp_val.date()
    elif isinstance(exp_val, date):
        return exp_val
    return None

def main():
    print("=" * 85)
    print("🛢️ REAL-TIME MCX CRUDE OIL INTRADAY STRUCTURE AUDIT & ENTRY ANALYZER")
    print(f"Timestamp: {datetime.now().strftime('%d-%b-%Y %I:%M:%S %p')}")
    print("=" * 85)

    kite = get_kite_client()
    if not kite:
        print("❌ Kite client initialization failed. Check credentials/token.")
        return

    try:
        mcx_instruments = kite.instruments("MCX")
        today = date.today()

        # 1. Resolve Active Near-Month CRUDEOIL Future
        futures = []
        for i in mcx_instruments:
            name = str(i.get("name", "")).upper()
            tsym = str(i.get("tradingsymbol", "")).upper()
            itype = str(i.get("instrument_type", "")).upper()
            exp = parse_expiry(i.get("expiry"))

            # Exclude mini contracts for main contract evaluation
            if ("CRUDEOIL" in name or tsym.startswith("CRUDEOIL")) and itype == "FUT" and "CRUDEOILM" not in tsym:
                if exp and exp >= today:
                    futures.append((exp, i))

        if not futures:
            print("⚠️ No future CRUDEOIL futures contracts found for today or later.")
            return

        futures.sort(key=lambda x: x[0])
        near_expiry_fut, near_fut = futures[0]
        fut_sym = f"MCX:{near_fut['tradingsymbol']}"
        fut_lot_size = int(near_fut.get("lot_size", 100))

        # 2. Fetch Near Future Quote
        fut_quote_map = kite.quote([fut_sym])
        fut_q = fut_quote_map.get(fut_sym, {})
        fut_ltp = float(fut_q.get("last_price", 0.0))
        ohlc = fut_q.get("ohlc", {})
        open_p = float(ohlc.get("open", fut_ltp))
        day_high = float(ohlc.get("high", fut_ltp))
        day_low = float(ohlc.get("low", fut_ltp))
        prev_close = float(ohlc.get("close", fut_ltp))
        vol = int(fut_q.get("volume", 0))
        oi = int(fut_q.get("oi", 0))

        chg = fut_ltp - prev_close
        pct = (chg / prev_close * 100) if prev_close else 0.0
        day_span = day_high - day_low
        dist_from_high = day_high - fut_ltp
        dist_from_low = fut_ltp - day_low

        print(f"📌 ACTIVE FUTURE CONTRACT:  {near_fut['tradingsymbol']}")
        print(f"   ► Expiry Date:           {near_expiry_fut.strftime('%d-%b-%Y')} ({(near_expiry_fut - today).days} days)")
        print(f"   ► Live Future LTP:       Rs.{fut_ltp:,.2f}  ({chg:+.2f} pts | {pct:+.2f}%)")
        print(f"   ► Day's Extreme Range:   Low: Rs.{day_low:,.2f}  <--->  High: Rs.{day_high:,.2f} (Span: {day_span:.1f} pts)")
        print(f"   ► Position in Day Range: {dist_from_low:.1f} pts off Low | {dist_from_high:.1f} pts off High")
        print(f"   ► Volume & OI:           Volume: {vol:,} contracts | OI: {oi:,} contracts")
        print(f"   ► Standard Lot Size:     {fut_lot_size} Barrels")

        # 3. ATM Center Strike
        atm_strike = int(round(fut_ltp / 50.0) * 50)
        print(f"🎯 Dynamic ATM Strike:      {atm_strike}")
        print("-" * 85)

        # 4. Filter Near Expiry Options
        crude_opts = []
        for i in mcx_instruments:
            name = str(i.get("name", "")).upper()
            tsym = str(i.get("tradingsymbol", "")).upper()
            itype = str(i.get("instrument_type", "")).upper()
            exp = parse_expiry(i.get("expiry"))

            if ("CRUDEOIL" in name or tsym.startswith("CRUDEOIL")) and itype in ("CE", "PE") and "CRUDEOILM" not in tsym:
                if exp and exp >= today:
                    crude_opts.append((exp, i))

        if not crude_opts:
            print("⚠️ No active CRUDEOIL options found.")
            return

        crude_opts.sort(key=lambda x: x[0])
        near_opt_expiry = crude_opts[0][0]
        active_expiry_opts = [i for (exp, i) in crude_opts if exp == near_opt_expiry]

        # Scan candidate strikes: ATM - 100, ATM - 50, ATM, ATM + 50, ATM + 100
        candidate_strikes = [atm_strike - 100, atm_strike - 50, atm_strike, atm_strike + 50, atm_strike + 100]
        opt_keys = {}
        for s in candidate_strikes:
            for t in ["CE", "PE"]:
                matches = [
                    i for i in active_expiry_opts
                    if i.get("instrument_type") == t and abs(float(i.get("strike", 0)) - s) < 5
                ]
                if matches:
                    k_sym = f"MCX:{matches[0]['tradingsymbol']}"
                    opt_keys[k_sym] = (s, t, matches[0])

        quotes = kite.quote(list(opt_keys.keys()))

        print(f"\n📊 LIVE OPTION CHAIN (Expiry: {near_opt_expiry.strftime('%d-%b-%Y')}):")
        print("-" * 85)
        print(f"{'Option Contract':<26} | {'Strike':<6} | {'Type':<4} | {'LTP (Rs)':<9} | {'Bid / Ask':<17} | {'Day High':<9} | {'OI':<9}")
        print("-" * 85)

        sorted_keys = sorted(opt_keys.keys(), key=lambda k: (opt_keys[k][0], 0 if opt_keys[k][1] == "CE" else 1))
        for k in sorted_keys:
            s, t, inst = opt_keys[k]
            q = quotes.get(k, {})
            ltp = float(q.get("last_price", 0.0))
            d = q.get("depth", {})
            bid = float(d.get("buy", [{}])[0].get("price", 0.0))
            ask = float(d.get("sell", [{}])[0].get("price", 0.0))
            high = float(q.get("ohlc", {}).get("high", 0.0))
            opt_oi = int(q.get("oi", 0))
            bid_ask_str = f"{bid:.1f} / {ask:.1f}"
            marker = "◄ ATM" if s == atm_strike else ""
            print(f"{inst['tradingsymbol']:<26} | {s:<6} | {t:<4} | Rs.{ltp:<6.2f} | {bid_ask_str:<17} | Rs.{high:<6.2f} | {opt_oi:<9} {marker}")

        print("=" * 85)

        # -------------------------------------------------------------
        # DYNAMIC TECHNICAL VERDICT & ENTRY BLUEPRINTS
        # -------------------------------------------------------------
        print("\n" + "=" * 85)
        print("💡 TECHNICAL VERDICT: SHOULD YOU ENTER CRUDE OIL NOW OR WAIT?")
        print("=" * 85)

        # Evaluate trend condition
        # Range location: lower 30%, upper 30%, or middle 40% chop
        pct_in_range = (dist_from_low / day_span * 100) if day_span > 0 else 50.0

        # Resolve ATM CE and PE prices
        atm_ce_sym = None
        atm_ce_ltp = 0.0
        atm_pe_sym = None
        atm_pe_ltp = 0.0

        for k, (s, t, inst) in opt_keys.items():
            if s == atm_strike:
                q = quotes.get(k, {})
                if t == "CE":
                    atm_ce_sym = inst['tradingsymbol']
                    atm_ce_ltp = float(q.get("last_price", 0.0))
                elif t == "PE":
                    atm_pe_sym = inst['tradingsymbol']
                    atm_pe_ltp = float(q.get("last_price", 0.0))

        if pct_in_range < 30.0:
            trend_bias = "BEARISH PRESSURE / SUPPORT RE-TEST"
            action = "PREFER BEARISH PUT (PE) ON BREAKDOWN OR WAIT FOR REVERSAL"
        elif pct_in_range > 70.0:
            trend_bias = "BULLISH STRENGTH / DAY HIGH TEST"
            action = "PREFER BULLISH CALL (CE) ON BREAKOUT"
        else:
            trend_bias = "MID-RANGE CONSOLIDATION / CHOP ZONE"
            action = "WAIT FOR RANGE EXPANSION (DO NOT BUY IN CHOP ZONE)"

        print(f"• Current Market Regime:  {trend_bias}")
        print(f"• Day Range Position:    {pct_in_range:.1f}% from Day's Low")
        print(f"• Immediate Pivot:       Rs.{open_p:.1f}")
        print(f"• Immediate Support Floor: Rs.{day_low:.1f} (Day Low)")
        print(f"• Immediate Resistance:  Rs.{day_high:.1f} (Day High)")
        print(f"• Core Recommendation:   {action}")
        print("-" * 85)

        print("\n🎯 ACTIONABLE ENTRY BLUEPRINTS:")
        print("-" * 85)

        # 1. Bearish Breakdown Setup
        if atm_pe_sym and atm_pe_ltp > 0:
            pe_sl = round(max(atm_pe_ltp - 35, atm_pe_ltp * 0.75), 1)
            pe_t1 = round(atm_pe_ltp + 45, 1)
            pe_t2 = round(atm_pe_ltp + 90, 1)
            pe_capital = atm_pe_ltp * fut_lot_size
            print(f"1. 🔴 BEARISH CONTINUATION / BREAKDOWN PLAN:")
            print(f"   • Recommended Strike:  {atm_pe_sym} ({atm_strike} PE)")
            print(f"   • Current Option LTP:  Rs.{atm_pe_ltp:.2f}  (1 Lot Capital: Rs.{pe_capital:,.2f})")
            print(f"   • Trigger Condition:   Enter ONLY when Crude Future breaks & sustains below Rs.{day_low:.1f}")
            print(f"   • Suggested Entry:     Around Rs.{atm_pe_ltp + 5:.2f} - Rs.{atm_pe_ltp + 12:.2f} on confirmation")
            print(f"   • Stop Loss (SL):      Rs.{pe_sl:.2f} (~35 pts risk)")
            print(f"   • Target 1 (T1):       Rs.{pe_t1:.2f} (+45 pts | R:R ~ 1:1.3)")
            print(f"   • Target 2 (T2):       Rs.{pe_t2:.2f} (+90 pts | R:R ~ 1:2.6)")

        # 2. Bullish Breakout Setup
        if atm_ce_sym and atm_ce_ltp > 0:
            ce_sl = round(max(atm_ce_ltp - 35, atm_ce_ltp * 0.75), 1)
            ce_t1 = round(atm_ce_ltp + 45, 1)
            ce_t2 = round(atm_ce_ltp + 90, 1)
            ce_capital = atm_ce_ltp * fut_lot_size
            print(f"\n2. 🟢 BULLISH BREAKOUT / PULLBACK PLAN:")
            print(f"   • Recommended Strike:  {atm_ce_sym} ({atm_strike} CE)")
            print(f"   • Current Option LTP:  Rs.{atm_ce_ltp:.2f}  (1 Lot Capital: Rs.{ce_capital:,.2f})")
            print(f"   • Trigger Condition:   Enter ONLY if Crude Future reclaims & sustains above Rs.{open_p:.1f} / Rs.{day_high:.1f}")
            print(f"   • Suggested Entry:     Around Rs.{atm_ce_ltp + 5:.2f} - Rs.{atm_ce_ltp + 12:.2f} on volume breakout")
            print(f"   • Stop Loss (SL):      Rs.{ce_sl:.2f} (~35 pts risk)")
            print(f"   • Target 1 (T1):       Rs.{ce_t1:.2f} (+45 pts)")
            print(f"   • Target 2 (T2):       Rs.{ce_t2:.2f} (+90 pts)")

        print("=" * 85 + "\n")

    except Exception as e:
        print(f"❌ Error during Crude scan: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
