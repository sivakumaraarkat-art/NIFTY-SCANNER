from kiteconnect import KiteConnect
from pathlib import Path
import datetime
import json

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

# Get current Nifty LTP
q_nifty = kite.quote(["NSE:NIFTY 50"]).get("NSE:NIFTY 50", {})
n_ltp = q_nifty.get("last_price", 25360)
atm_strike = round(n_ltp / 50) * 50

print(f"NIFTY LTP: {n_ltp:.2f} | ATM Strike: {atm_strike}")

# Find current weekly or monthly expiry instruments for Nifty
instruments = kite.instruments("NFO")
nifty_inst = [i for i in instruments if i["name"] == "NIFTY" and i["segment"] == "NFO-OPT"]

# Sort unique expiry dates
expiries = sorted(list({i["expiry"] for i in nifty_inst if i["expiry"] >= datetime.date.today()}))
nearest_expiry = expiries[0] if expiries else None
print(f"Nearest Expiry: {nearest_expiry}")

if nearest_expiry:
    # Filter strikes between ATM - 400 and ATM + 400
    expiry_opts = [i for i in nifty_inst if i["expiry"] == nearest_expiry and abs(i["strike"] - atm_strike) <= 400]

    symbols = [f"NFO:{i['tradingsymbol']}" for i in expiry_opts]
    quotes = {}
    for batch in [symbols[i:i+100] for i in range(0, len(symbols), 100)]:
        quotes.update(kite.quote(batch))

    strikes_data = {}
    for i in expiry_opts:
        sym = f"NFO:{i['tradingsymbol']}"
        q = quotes.get(sym, {})
        k = i["strike"]
        t = i["instrument_type"]
        if k not in strikes_data:
            strikes_data[k] = {"CE_OI": 0, "PE_OI": 0, "CE_LTP": 0, "PE_LTP": 0}
        if t == "CE":
            strikes_data[k]["CE_OI"] = q.get("oi", 0)
            strikes_data[k]["CE_LTP"] = q.get("last_price", 0)
        else:
            strikes_data[k]["PE_OI"] = q.get("oi", 0)
            strikes_data[k]["PE_LTP"] = q.get("last_price", 0)

    print(f"\n--- OPTION CHAIN OPEN INTEREST (Expiry: {nearest_expiry}) ---")
    print(f"{'Strike':8} | {'Call OI':10} | {'CE LTP':8} | {'PE LTP':8} | {'Put OI':10} | {'Dominance':10}")
    print("-" * 65)
    total_ce_oi = 0
    total_pe_oi = 0
    for k in sorted(strikes_data.keys()):
        d = strikes_data[k]
        ce_oi = d["CE_OI"]
        pe_oi = d["PE_OI"]
        total_ce_oi += ce_oi
        total_pe_oi += pe_oi
        dom = "PUT (Supp)" if pe_oi > ce_oi * 1.2 else ("CALL (Res)" if ce_oi > pe_oi * 1.2 else "BATTLE")
        marker = "◄◄ ATM" if k == atm_strike else ""
        print(f"{k:8.0f} | {ce_oi:10,d} | {d['CE_LTP']:8.2f} | {d['PE_LTP']:8.2f} | {pe_oi:10,d} | {dom:10} {marker}")

    pcr = total_pe_oi / total_ce_oi if total_ce_oi else 0
    print("-" * 65)
    print(f"Total Call OI: {total_ce_oi:,} | Total Put OI: {total_pe_oi:,} | Overall PCR: {pcr:.2f}")
    if pcr > 1.2:
        print("PCR Bias: Bullish (Put writers in aggressive control)")
    elif pcr < 0.8:
        print("PCR Bias: Bearish (Call writers dominating)")
    else:
        print("PCR Bias: Balanced / Moderately Bullish")
