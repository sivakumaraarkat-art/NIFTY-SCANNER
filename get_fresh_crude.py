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
    "MCX:CRUDEOIL26DECFUT",
    "MCX:CRUDEOIL26DEC7800PE",
    "MCX:CRUDEOIL26DEC7900PE",
    "MCX:CRUDEOIL26DEC7700PE",
    "MCX:CRUDEOIL26DEC7900CE",
    "MCX:CRUDEOIL26DEC8000CE"
]

quotes = kite.quote(symbols)

print(f"=== LIVE CRUDE OIL UPDATE ({now.strftime('%H:%M:%S IST')}) ===")
for s in symbols:
    q = quotes.get(s, {})
    ltp = q.get("last_price", 0)
    ohlc = q.get("ohlc", {})
    pc = ohlc.get("close", 1)
    chg = ((ltp - pc) / pc) * 100 if pc else 0
    vol = q.get("volume", 0)
    oi = q.get("oi", 0)
    depth = q.get("depth", {})
    best_bid = depth.get("buy", [{}])[0].get("price", 0)
    best_ask = depth.get("sell", [{}])[0].get("price", 0)
    print(f"{s:<26} | LTP: Rs.{ltp:<7.1f} ({chg:>+5.2f}%) | Bid: Rs.{best_bid:<6.1f} | Ask: Rs.{best_ask:<6.1f} | Vol: {vol:<6} | OI: {oi}")

insts = kite.instruments("MCX")
nov_inst = [i for i in insts if i.get("tradingsymbol") == "CRUDEOIL26NOVFUT"][0]
bars = kite.historical_data(nov_inst["instrument_token"], now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d"), "5minute")
last_bars = bars[-6:]
print("\nRecent 5m candles (Nov Future):")
print(f"{'Time':<8} | {'Open':<8} | {'High':<8} | {'Low':<8} | {'Close':<8} | {'Vol':<6}")
print("-" * 55)
for b in last_bars:
    t = str(b["date"])[11:16]
    print(f"{t:<8} | Rs.{b['open']:<5} | Rs.{b['high']:<5} | Rs.{b['low']:<5} | Rs.{b['close']:<5} | {b['volume']}")
