from kiteconnect import KiteConnect
from pathlib import Path
import datetime

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

insts = kite.instruments("MCX")

# 1. Check Futures
crude_futs = [i for i in insts if i.get("name") == "CRUDEOIL" and i.get("instrument_type") == "FUT"]
crude_futs = sorted(crude_futs, key=lambda x: x.get("expiry"))

fut_symbols = [f"MCX:{f['tradingsymbol']}" for f in crude_futs[:3]]
fut_quotes = kite.quote(fut_symbols)

print("=" * 80)
print("MCX CRUDE OIL FUTURES CONTRACTS:")
print("=" * 80)
for f in crude_futs[:3]:
    sym = f"MCX:{f['tradingsymbol']}"
    q = fut_quotes.get(sym, {})
    ltp = q.get("last_price", 0)
    ohlc = q.get("ohlc", {})
    chg = ((ltp - ohlc.get("close", 1)) / ohlc.get("close", 1)) * 100 if ohlc.get("close") else 0
    print(f"Contract: {f['tradingsymbol']:<18} | Expiry: {f['expiry']} | LTP: Rs.{ltp:,.2f} ({chg:+.2f}%) | High: Rs.{ohlc.get('high')} | Low: Rs.{ohlc.get('low')} | Vol: {q.get('volume', 0):,} | OI: {q.get('oi', 0):,}")

# 2. Check Options near ATM
# The December options expire on 2026-12-16. What is the underlying future for Dec options? CRUDEOIL26DECFUT or CRUDEOIL26NOVFUT?
# In MCX, options on goods/futures devolve into the corresponding future contract:
# December Options expire on 2026-12-16 and devolve into December Futures (CRUDEOIL26DECFUT which expires on 2026-12-18)!
dec_fut = [f for f in crude_futs if f.get("tradingsymbol") == "CRUDEOIL26DECFUT"]
dec_fut_ltp = fut_quotes.get("MCX:CRUDEOIL26DECFUT", {}).get("last_price", 0)
nov_fut_ltp = fut_quotes.get("MCX:CRUDEOIL26NOVFUT", {}).get("last_price", 0)

print(f"\nUnderlying Reference LTP: Nov Fut = Rs.{nov_fut_ltp:,.2f} | Dec Fut = Rs.{dec_fut_ltp:,.2f}")

# Look at December options near ATM (strikes around 7800 - 8100 in steps of 50 or 100)
crude_opts = [i for i in insts if i.get("name") == "CRUDEOIL" and i.get("instrument_type") in ("CE", "PE") and str(i.get("expiry")) == "2026-12-16"]

# ATM around 7900 / 8000
strikes = [7600, 7700, 7800, 7900, 7950, 8000, 8050, 8100, 8200, 8300]
target_opts = [i for i in crude_opts if int(float(i.get("strike", 0))) in strikes]

opt_syms = [f"MCX:{i['tradingsymbol']}" for i in target_opts]
quotes = kite.quote(opt_syms)

print("\n" + "=" * 80)
print(f"MCX CRUDE OIL OPTIONS CHAIN (Expiry: 2026-12-16) - NEAR ATM STRIKES")
print("=" * 80)
print(f"{'CALL (CE)':<32} | Strike | {'PUT (PE)':<32}")
print(f"{'LTP':<8} {'Chg%':<8} {'OI':<8} {'Vol':<6} | Strike | {'LTP':<8} {'Chg%':<8} {'OI':<8} {'Vol':<6}")
print("-" * 80)

for st in strikes:
    ce_inst = [i for i in target_opts if int(float(i.get("strike", 0))) == st and i.get("instrument_type") == "CE"]
    pe_inst = [i for i in target_opts if int(float(i.get("strike", 0))) == st and i.get("instrument_type") == "PE"]

    ce_q = quotes.get(f"MCX:{ce_inst[0]['tradingsymbol']}", {}) if ce_inst else {}
    pe_q = quotes.get(f"MCX:{pe_inst[0]['tradingsymbol']}", {}) if pe_inst else {}

    ce_ltp = ce_q.get("last_price", 0)
    ce_pc = ce_q.get("ohlc", {}).get("close", 1)
    ce_chg = ((ce_ltp - ce_pc) / ce_pc) * 100 if ce_pc else 0
    ce_oi = ce_q.get("oi", 0)
    ce_vol = ce_q.get("volume", 0)

    pe_ltp = pe_q.get("last_price", 0)
    pe_pc = pe_q.get("ohlc", {}).get("close", 1)
    pe_chg = ((pe_ltp - pe_pc) / pe_pc) * 100 if pe_pc else 0
    pe_oi = pe_q.get("oi", 0)
    pe_vol = pe_q.get("volume", 0)

    ce_str = f"Rs.{ce_ltp:<5.1f} {ce_chg:>+5.1f}% {ce_oi:>6} {ce_vol:>5}"
    pe_str = f"Rs.{pe_ltp:<5.1f} {pe_chg:>+5.1f}% {pe_oi:>6} {pe_vol:>5}"

    atm_mark = "<-- ATM" if (st == 7900 or st == 7950) else ""
    print(f"{ce_str:<32} | {st:^6} | {pe_str:<32} {atm_mark}")
