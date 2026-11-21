import datetime
from pathlib import Path
from kiteconnect import KiteConnect

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

now = datetime.datetime.now()
symbols = [
    "MCX:CRUDEOIL26NOVFUT",
    "MCX:CRUDEOIL26DEC7800PE",
    "MCX:CRUDEOIL26DEC7900PE",
    "MCX:CRUDEOIL26DEC7900CE"
]
quotes = kite.quote(symbols)
fut = quotes["MCX:CRUDEOIL26NOVFUT"]["last_price"]
pe_7800 = quotes["MCX:CRUDEOIL26DEC7800PE"]["last_price"]
pe_7900 = quotes["MCX:CRUDEOIL26DEC7900PE"]["last_price"]
ce_7900 = quotes["MCX:CRUDEOIL26DEC7900CE"]["last_price"]

print(f"LIVE NOW ({now.strftime('%H:%M:%S')}):")
print(f"Nov Future: Rs.{fut:,.1f}")
print(f"7800 PE:    Rs.{pe_7800:,.1f}")
print(f"7900 PE:    Rs.{pe_7900:,.1f}")
print(f"7900 CE:    Rs.{ce_7900:,.1f}")

insts = kite.instruments("MCX")
nov_inst = [i for i in insts if i.get("tradingsymbol") == "CRUDEOIL26NOVFUT"][0]
bars = kite.historical_data(nov_inst["instrument_token"], now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d"), "minute")
print("\nLast 6 1-minute bars:")
for b in bars[-6:]:
    t = str(b["date"])[11:16]
    print(f"{t} | O: {b['open']} | H: {b['high']} | L: {b['low']} | C: {b['close']} | V: {b['volume']}")
