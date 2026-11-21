from kiteconnect import KiteConnect
from pathlib import Path
import datetime

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

now = datetime.datetime.now()
insts = kite.instruments("MCX")
crude_insts = [i for i in insts if i.get("name") == "CRUDEOIL" and i.get("instrument_type") == "FUT"]
crude_insts = sorted(crude_insts, key=lambda x: x.get("expiry"))

print("=" * 80)
print(f"🛢️ CRUDE OIL (MCX & INTERNATIONAL) LIVE MONITOR — {now.strftime('%H:%M:%S IST')}")
print("=" * 80)

if crude_insts:
    near = crude_insts[0]
    sym = f"MCX:{near['tradingsymbol']}"
    mini_inst = [i for i in insts if i.get("name") == "CRUDEOILM" and i.get("instrument_type") == "FUT" and i.get("expiry") == near.get("expiry")]
    mini_sym = f"MCX:{mini_inst[0]['tradingsymbol']}" if mini_inst else None

    symbols_to_quote = [sym]
    if mini_sym:
        symbols_to_quote.append(mini_sym)

    quotes = kite.quote(symbols_to_quote)
    q = quotes.get(sym, {})
    ltp = q.get("last_price", 0)
    ohlc = q.get("ohlc", {})
    pc = ohlc.get("close", 0)
    high_p = ohlc.get("high", 0)
    low_p = ohlc.get("low", 0)
    open_p = ohlc.get("open", 0)
    vol = q.get("volume", 0)
    oi = q.get("oi", 0)
    chg = ((ltp - pc) / pc) * 100 if pc else 0

    print(f"• Active Contract:     {near['tradingsymbol']} (Expiry: {near['expiry']})")
    print(f"• MCX Crude LTP:       ₹{ltp:,.2f} / barrel ({chg:+.2f}%)")
    print(f"• Intraday Range:      Low: ₹{low_p:,.2f} | High: ₹{high_p:,.2f} | Open: ₹{open_p:,.2f}")
    print(f"• Prev Close:          ₹{pc:,.2f}")
    print(f"• Traded Volume:       {vol:,} contracts")
    print(f"• Open Interest:       {oi:,} contracts")
    print(f"• Standard Lot Size:   {near.get('lot_size')} barrels (1 Lot Val: ₹{ltp * near.get('lot_size'):,.2f})")

    if mini_sym:
        mq = quotes.get(mini_sym, {})
        print(f"• Mini Contract:       {mini_inst[0]['tradingsymbol']} | LTP: ₹{mq.get('last_price', 0):,.2f} | Lot: {mini_inst[0].get('lot_size')} barrels")
    print("-" * 80)

    # Historical 15-min candles today
    today_str = now.strftime("%Y-%m-%d")
    token_c = near.get("instrument_token")
    bars = kite.historical_data(token_c, today_str, today_str, "15minute")
    print("📈 Last 6 15-Minute Candles (MCX Crude):")
    print("Time  | Open     | High     | Low      | Close    | Volume")
    print("-" * 60)
    for b in bars[-6:]:
        t = str(b["date"])[11:16]
        print(f"{t} | ₹{b['open']:<8.2f} | ₹{b['high']:<8.2f} | ₹{b['low']:<8.2f} | ₹{b['close']:<8.2f} | {b['volume']:,}")
    print("=" * 80)
else:
    print("No MCX Crude instruments found.")
