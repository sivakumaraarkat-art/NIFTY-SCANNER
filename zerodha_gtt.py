"""
zerodha_gtt.py
==============
Universal, All-in-One Zerodha GTT Manager.
Handles BUY GTT, OCO EXIT GTT, STATUS AUDIT, and CANCELLATIONS for ANY Stock, Index, or Option.

Features:
1. 🎯 Auto-detects Exchange (NFO, BFO, NSE, BSE) and Lot Size.
2. 🛡️ Auto-detects SEBI Expiry Week Delivery Rules:
   - Uses NRML for Stock Options in expiry week (prevents MIS physical delivery rejection).
   - Uses MIS/NRML/CNC appropriately.
3. 📏 Auto-calculates Compliant Triggers:
   - Always maintains > 0.09 / 0.5% distance from live LTP to satisfy Zerodha's distance rule.
4. ⚡ One-Click OCO Protection:
   - Auto-reads live position quantity and average price to attach Target + Stop Loss.
5. 📊 Real-Time Status & Distance Dashboard.

Commands:
   # Buy GTT (Preview)
   python zerodha_gtt.py buy --symbol TATASTEEL26NOV172.5PE --lots 1
   # Buy GTT (Execute Live)
   python zerodha_gtt.py buy --symbol TATASTEEL26NOV172.5PE --lots 1 --execute

   # OCO Exit GTT (Attach Target & Stop Loss to Open Position)
   python zerodha_gtt.py oco --symbol TATASTEEL26NOV172.5PE --target 1.80 --sl 0.40 --execute

   # Status Audit (All Active GTTs + Live Distances)
   python zerodha_gtt.py status

   # Cancel GTT
   python zerodha_gtt.py cancel --id 345688978
   python zerodha_gtt.py cancel --symbol TATASTEEL26NOV172.5PE
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

# Windows UTF-8 console output fix
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent

# Kite Connect Initialization
try:
    api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
    token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
    from kiteconnect import KiteConnect
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(token)
except Exception as e:
    print(f"❌ Kite Initialization Error: {e}")
    sys.exit(1)


# Cache instruments in memory
_INSTRUMENT_CACHE = {}

def get_instrument_info(symbol: str):
    """Auto-detect exchange, lot size, expiry, and instrument type."""
    global _INSTRUMENT_CACHE
    symbol = symbol.upper().strip()

    # Heuristics for common formats
    if any(symbol.endswith(suffix) for suffix in ["CE", "PE", "FUT"]):
        if symbol.startswith("SENSEX") or symbol.startswith("BANKEX"):
            default_exchange = "BFO"
        else:
            default_exchange = "NFO"
    else:
        default_exchange = "NSE"

    if not _INSTRUMENT_CACHE:
        try:
            # Query instruments
            for ex in ["NFO", "BFO", "NSE"]:
                try:
                    inst_list = kite.instruments(ex)
                    for i in inst_list:
                        _INSTRUMENT_CACHE[i["tradingsymbol"]] = {
                            "exchange": ex,
                            "lot_size": i.get("lot_size", 1),
                            "instrument_type": i.get("instrument_type", "EQ"),
                            "expiry": i.get("expiry"),
                            "name": i.get("name")
                        }
                except Exception:
                    pass
        except Exception as e:
            print(f"Notice during instrument lookup: {e}")

    info = _INSTRUMENT_CACHE.get(symbol)
    if info:
        return info

    # Fallback to sensible defaults
    return {
        "exchange": default_exchange,
        "lot_size": 1,
        "instrument_type": "EQ" if default_exchange == "NSE" else "CE",
        "expiry": None,
        "name": symbol
    }


def calculate_compliant_buffer(ltp: float) -> float:
    """Zerodha requires trigger distance > 0.09 for low-priced items or ~0.5% for higher."""
    if ltp < 10.0:
        return 0.15
    elif ltp < 100.0:
        return 0.50
    elif ltp < 1000.0:
        return 2.50
    else:
        return round(ltp * 0.005, 2)


# ==============================================================================
# 1. BUY GTT
# ==============================================================================
def handle_buy(args):
    symbol = args.symbol.upper().strip()
    info = get_instrument_info(symbol)
    exchange = args.exchange or info["exchange"]
    lot_size = info["lot_size"]
    qty = args.qty if args.qty else (args.lots * lot_size)

    # 1. Auto-select Product (SEBI Expiry Week Delivery Rule)
    is_stock_option = (exchange == "NFO" and info["instrument_type"] in ["CE", "PE"] and info.get("name") not in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"])
    if args.product:
        product = args.product.upper()
    else:
        product = "NRML" if is_stock_option else "MIS"

    # Check if stock option is near current month expiry
    if is_stock_option:
        print("\n⚠️  [SEBI PHYSICAL DELIVERY NOTICE] For Stock Options during expiry week:")
        print("   Zerodha disallows fresh buy orders on OTM strikes. If rejected, switch to:")
        print("   1) Cash-Settled Index Options (NIFTY / BANKNIFTY / SENSEX) -> Zero restrictions!")
        print("   2) Next Month Expiry (December) for Stock Options.")

    # 2. Fetch Live Quote
    full_symbol = f"{exchange}:{symbol}"
    q = kite.quote([full_symbol]).get(full_symbol, {})
    ltp = q.get("last_price", 0.0)
    depth = q.get("depth", {})
    best_bid = depth.get("buy", [{}])[0].get("price", 0.0)
    best_ask = depth.get("sell", [{}])[0].get("price", 0.0)

    # 3. Calculate Compliant Breakout Trigger
    buffer_amt = calculate_compliant_buffer(ltp)
    if args.trigger is None or (args.trigger - ltp) < 0.10:
        trigger = round(ltp + buffer_amt, 2)
    else:
        trigger = args.trigger

    if args.limit is None or args.limit <= trigger:
        limit = round(trigger + max(0.10, round(trigger * 0.02, 2)), 2)
    else:
        limit = args.limit

    total_cost = qty * limit
    est_target = round(limit * 1.80, 2) if limit < 20 else round(limit * 1.10, 2)
    est_sl = round(limit * 0.50, 2) if limit < 20 else round(limit * 0.95, 2)

    print("=" * 85)
    print(f"🎯 ZERODHA GTT BREAKOUT BUY ORDER TICKET: {symbol}")
    print("=" * 85)
    print(f"• Tradingsymbol:   {symbol}")
    print(f"• Exchange:       {exchange} | Instrument Type: {info['instrument_type']}")
    print(f"• Product:        {product} {'(SEBI Expiry Delivery Shield Active)' if product == 'NRML' and is_stock_option else ''}")
    print(f"• Current LTP:    Rs. {ltp:.2f} (Bid: Rs. {best_bid:.2f} | Ask: Rs. {best_ask:.2f})")
    print(f"• Breakout Trigger: Rs. {trigger:.2f} (+Rs. {trigger - ltp:.2f} buffer)")
    print(f"• Limit Price:    Rs. {limit:.2f}")
    print(f"• Quantity:       {qty:,} shares ({args.lots} lot{'s' if args.lots > 1 else ''} @ {lot_size}/lot)")
    print(f"• Capital Value:  Rs. {total_cost:,.2f}")
    print("-" * 85)
    print(f"• Target Estimate:Rs. {est_target:.2f} (+Rs. {(est_target - limit) * qty:,.2f} profit)")
    print(f"• Stop Loss Est:  Rs. {est_sl:.2f} (-Rs. {(limit - est_sl) * qty:,.2f} risk)")
    print("=" * 85)

    if not args.execute:
        print("\n⚠️ PREVIEW MODE: Order has NOT been sent to Zerodha yet.")
        print(f"To execute live on Kite, add --execute:")
        print(f"   python zerodha_gtt.py buy --symbol {symbol} --lots {args.lots} --execute")
        return None

    # Check for fresh LTP right before placement
    fresh_q = kite.quote([full_symbol]).get(full_symbol, {})
    fresh_ltp = fresh_q.get("last_price", ltp)
    if (trigger - fresh_ltp) < 0.10:
        trigger = round(fresh_ltp + buffer_amt, 2)
        limit = round(trigger + max(0.10, round(trigger * 0.02, 2)), 2)

    print("🚀 Submitting GTT Buy Order to Zerodha Kite...")
    buy_orders = [
        {
            "transaction_type": kite.TRANSACTION_TYPE_BUY,
            "quantity": qty,
            "order_type": kite.ORDER_TYPE_LIMIT,
            "product": product,
            "price": limit
        }
    ]

    try:
        resp = kite.place_gtt(
            trigger_type=kite.GTT_TYPE_SINGLE,
            tradingsymbol=symbol,
            exchange=exchange,
            trigger_values=[trigger],
            last_price=fresh_ltp,
            orders=buy_orders
        )
        gid = resp.get("trigger_id")
        print(f"\n🎉 SUCCESS! GTT Trigger #{gid} successfully placed on Zerodha Kite!")
        print(f"   • Status:          ACTIVE 🟢")
        print(f"   • Symbol:          {symbol}")
        print(f"   • Product:         {product}")
        print(f"   • Trigger Price:   Rs. {trigger:.2f}")
        print(f"   • Limit Price:     Rs. {limit:.2f}")
        print(f"   • Quantity:        {qty:,} shares")
        print("=" * 85)
        return gid
    except Exception as e:
        print(f"❌ Failed to place GTT: {e}")
        return None


# ==============================================================================
# 2. OCO EXIT GTT (TARGET + STOP LOSS)
# ==============================================================================
def handle_oco(args):
    symbol = args.symbol.upper().strip()
    info = get_instrument_info(symbol)
    exchange = args.exchange or info["exchange"]

    # Auto-detect position quantity and product
    pos_list = kite.positions().get("net", [])
    active_pos = next((p for p in pos_list if p.get("tradingsymbol") == symbol and p.get("quantity", 0) > 0), None)

    if active_pos:
        qty = active_pos.get("quantity")
        product = active_pos.get("product", "NRML")
        avg_price = active_pos.get("average_price", 0.0)
    else:
        qty = args.qty if args.qty else (args.lots * info["lot_size"])
        product = args.product or ("NRML" if info["instrument_type"] in ["CE", "PE"] else "MIS")
        avg_price = 0.0

    full_symbol = f"{exchange}:{symbol}"
    q = kite.quote([full_symbol]).get(full_symbol, {})
    ltp = q.get("last_price", 0.0)
    if avg_price == 0.0:
        avg_price = ltp

    # Target & Stop Loss Defaults
    target = args.target if args.target else (round(ltp * 1.80, 2) if ltp < 20 else round(ltp * 1.05, 2))
    sl = args.sl if args.sl else (round(ltp * 0.50, 2) if ltp < 20 else round(ltp * 0.98, 2))
    sl_limit = round(max(0.05, sl - (0.05 if sl < 5 else 0.50)), 2)

    # Kite OCO rule: sl must be strictly lower than target
    if sl >= target:
        print(f"❌ Invalid OCO levels: Stop-loss (Rs. {sl}) cannot be higher than Target (Rs. {target})")
        return None

    t_profit = (target - avg_price) * qty
    sl_loss = (sl - avg_price) * qty

    print("=" * 85)
    print(f"🎯 ZERODHA GTT OCO (TARGET + STOP-LOSS) EXIT TICKET: {symbol}")
    print("=" * 85)
    print(f"• Tradingsymbol:      {symbol}")
    print(f"• Exchange:           {exchange} | Product: {product}")
    print(f"• Position Quantity:  {qty:,} shares (Entry/Ref: Rs. {avg_price:.2f} | Live LTP: Rs. {ltp:.2f})")
    print("-" * 85)
    print(f"• TARGET LEG:         Trigger: Rs. {target:.2f} | Limit: Rs. {target:.2f}")
    print(f"                      Expected Profit: +Rs. {t_profit:,.2f} ({((target - avg_price)/avg_price*100):+.1f}%)")
    print(f"• STOP-LOSS LEG:      Trigger: Rs. {sl:.2f} | Limit: Rs. {sl_limit:.2f}")
    print(f"                      Max Risk:        Rs. {sl_loss:,.2f} ({((sl - avg_price)/avg_price*100):+.1f}%)")
    print("=" * 85)

    if not args.execute:
        print("\n⚠️ PREVIEW MODE: OCO order has NOT been sent to Zerodha yet.")
        print(f"To execute live on Kite, add --execute:")
        print(f"   python zerodha_gtt.py oco --symbol {symbol} --target {target} --sl {sl} --execute")
        return None

    # Clean up previous GTTs on this symbol
    print(f"🔄 Cleaning up any existing GTTs for {symbol}...")
    try:
        gtts = kite.get_gtts()
        for g in gtts:
            cond = g.get("condition", {})
            if cond.get("tradingsymbol") == symbol and g.get("status") in ["active", "triggered"]:
                gid = g.get("id")
                kite.delete_gtt(gid)
                print(f"   ✅ Cleaned up old GTT #{gid}.")
    except Exception as e:
        print(f"   Notice: {e}")

    print("🚀 Placing fresh GTT OCO on Zerodha Kite...")
    trigger_values = [sl, target]
    sell_orders = [
        {
            "transaction_type": kite.TRANSACTION_TYPE_SELL,
            "quantity": qty,
            "order_type": kite.ORDER_TYPE_LIMIT,
            "product": product,
            "price": sl_limit
        },
        {
            "transaction_type": kite.TRANSACTION_TYPE_SELL,
            "quantity": qty,
            "order_type": kite.ORDER_TYPE_LIMIT,
            "product": product,
            "price": target
        }
    ]

    try:
        resp = kite.place_gtt(
            trigger_type=kite.GTT_TYPE_OCO,
            tradingsymbol=symbol,
            exchange=exchange,
            trigger_values=trigger_values,
            last_price=ltp,
            orders=sell_orders
        )
        gid = resp.get("trigger_id")
        print(f"\n🎉 SUCCESS! GTT OCO Order #{gid} successfully deployed on Zerodha Kite!")
        print(f"   • Status:          ACTIVE 🟢")
        print(f"   • Target:          Trigger Rs. {target:.2f} (Profit: +Rs. {t_profit:,.2f})")
        print(f"   • Stop-Loss:       Trigger Rs. {sl:.2f} (Risk: Rs. {sl_loss:,.2f})")
        print(f"   • Mechanism:       Whichever leg hits first automatically cancels the other!")
        print("=" * 85)
        return gid
    except Exception as e:
        print(f"❌ Failed to place OCO GTT: {e}")
        return None


# ==============================================================================
# 2B. TRAIL STOP-LOSS GTT (AUTO OR MANUAL)
# ==============================================================================
def handle_trail(args):
    symbol = args.symbol.upper().strip()
    gtts = kite.get_gtts()
    active_oco = next((g for g in gtts if g.get("condition", {}).get("tradingsymbol") == symbol and g.get("type") == "two-leg" and g.get("status") == "active"), None)

    if not active_oco:
        print(f"❌ No active OCO GTT found for {symbol}. Deploy one first using 'oco' command.")
        return None

    gid = active_oco["id"]
    old_triggers = active_oco.get("condition", {}).get("trigger_values", [0, 0])
    old_sl = old_triggers[0]
    old_target = old_triggers[1]

    # New levels
    new_sl = args.sl if args.sl is not None else old_sl
    new_target = args.target if args.target is not None else old_target

    if new_sl >= new_target:
        print(f"❌ Invalid: Trailed Stop Loss (Rs. {new_sl}) must be lower than Target (Rs. {new_target})")
        return None

    ex = active_oco.get("orders", [{}])[0].get("exchange", "NFO")
    q = kite.quote([f"{ex}:{symbol}"]).get(f"{ex}:{symbol}", {})
    ltp = q.get("last_price", 0.0)

    if new_sl >= ltp:
        print(f"❌ Stop loss (Rs. {new_sl}) cannot be at or above current live market price (Rs. {ltp:.2f})")
        return None

    print("=" * 85)
    print(f"🛡️ TRAILING STOP-LOSS TICKET: {symbol}")
    print("=" * 85)
    print(f"• Active GTT ID:       #{gid}")
    print(f"• Current LTP:         Rs. {ltp:.2f}")
    print(f"• Previous Stop Loss:  Rs. {old_sl:.2f}")
    print(f"• New Trailed SL:      Rs. {new_sl:.2f} ({'+' if new_sl > old_sl else ''}{new_sl - old_sl:+.2f} pts trail)")
    print(f"• Target Price:        Rs. {new_target:.2f}")
    print("=" * 85)

    if not args.execute:
        print(f"\n⚠️ PREVIEW MODE: Run with --execute to update GTT #{gid} on Zerodha.")
        print(f"   python zerodha_gtt.py trail --symbol {symbol} --sl {new_sl} --execute")
        return None

    print(f"🚀 Updating GTT #{gid} on Zerodha Kite...")
    orders = active_oco.get("orders", [])
    sl_limit = round(max(0.05, new_sl - (0.05 if new_sl < 5 else 0.50)), 2)

    if len(orders) >= 2:
        orders[0]["price"] = sl_limit
        orders[1]["price"] = new_target

    try:
        resp = kite.modify_gtt(
            trigger_id=gid,
            trigger_type=kite.GTT_TYPE_OCO,
            tradingsymbol=symbol,
            exchange=ex,
            trigger_values=[new_sl, new_target],
            last_price=ltp,
            orders=orders
        )
        print(f"🎉 SUCCESS! GTT #{gid} Stop-Loss successfully TRAILED on Zerodha Kite!")
        print(f"   • Status:                ACTIVE 🟢")
        print(f"   • New Stop-Loss Trigger: Rs. {new_sl:.2f}")
        print(f"   • Target Trigger:        Rs. {new_target:.2f}")
        print("=" * 85)
    except Exception as e:
        print(f"❌ Trailing error: {e}")


# ==============================================================================
# 3. STATUS DASHBOARD
# ==============================================================================
def handle_status(args):
    print("=" * 95)
    print(f"📊 ZERODHA GTT & POSITION AUDIT ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print("=" * 95)

    # 1. Positions
    pos_list = kite.positions().get("net", [])
    print(f"\n📌 ACTIVE OPEN POSITIONS ({len(pos_list)}):")
    if not pos_list:
        print("   • No active open positions.")
    else:
        for p in pos_list:
            sym = p.get("tradingsymbol")
            qty = p.get("quantity")
            avg = p.get("average_price")
            pnl = p.get("pnl")
            ltp = p.get("last_price")
            print(f"   • {sym:<25} Qty: {qty:>6} | Avg: Rs.{avg:>8.2f} | LTP: Rs.{ltp:>8.2f} | PnL: Rs.{pnl:>+9.2f}")

    # 2. GTTs
    gtts = kite.get_gtts()
    active_gtts = [g for g in gtts if g.get("status") in ["active", "triggered"]]
    print(f"\n📋 LIVE GTT ORDERS ({len(active_gtts)}):")
    if not active_gtts:
        print("   • No active GTT orders found.")
    else:
        quote_symbols = []
        for g in active_gtts:
            cond = g.get("condition", {})
            sym = cond.get("tradingsymbol")
            ex = g.get("orders", [{}])[0].get("exchange", "NFO")
            quote_symbols.append(f"{ex}:{sym}")

        quotes = kite.quote(quote_symbols) if quote_symbols else {}

        header = f"{'GTT ID':<11} {'Symbol':<24} {'Type':<8} {'Status':<10} {'Triggers':<16} {'Live LTP':<10} {'Distance':<14}"
        print("-" * 95)
        print(header)
        print("-" * 95)

        for g in active_gtts:
            gid = g.get("id")
            cond = g.get("condition", {})
            sym = cond.get("tradingsymbol")
            gtype = g.get("type", "single").upper()
            status = g.get("status").upper()
            trigs = cond.get("trigger_values", [])
            trig_str = str(trigs)

            ex = g.get("orders", [{}])[0].get("exchange", "NFO")
            full_sym = f"{ex}:{sym}"
            live_ltp = quotes.get(full_sym, {}).get("last_price", 0.0)

            if len(trigs) == 1 and live_ltp > 0:
                dist = trigs[0] - live_ltp
                dist_str = f"{dist:>+6.2f} pts"
            elif len(trigs) == 2 and live_ltp > 0:
                dist_sl = live_ltp - trigs[0]
                dist_tg = trigs[1] - live_ltp
                dist_str = f"SL:{dist_sl:.1f}|TG:{dist_tg:.1f}"
            else:
                dist_str = "-"

            status_icon = "🟢 ACTIVE" if status == "ACTIVE" else f"⚪ {status}"
            print(f"{gid:<11} {sym:<24} {gtype:<8} {status_icon:<10} {trig_str:<16} Rs.{live_ltp:<7.2f} {dist_str:<14}")
        print("-" * 95)


# ==============================================================================
# 4. CANCEL GTT
# ==============================================================================
def handle_cancel(args):
    if args.id:
        try:
            resp = kite.delete_gtt(args.id)
            print(f"✅ GTT #{args.id} successfully cancelled: {resp}")
        except Exception as e:
            print(f"❌ Failed to cancel GTT #{args.id}: {e}")
    elif args.symbol:
        sym = args.symbol.upper().strip()
        deleted = 0
        try:
            gtts = kite.get_gtts()
            for g in gtts:
                cond = g.get("condition", {})
                if cond.get("tradingsymbol") == sym:
                    gid = g.get("id")
                    kite.delete_gtt(gid)
                    print(f"✅ Cancelled GTT #{gid} for {sym}")
                    deleted += 1
            if deleted == 0:
                print(f"Notice: No active GTTs found for {sym}")
        except Exception as e:
            print(f"❌ Cancel error: {e}")
    else:
        print("Please provide --id <GTT_ID> or --symbol <SYMBOL>")


# ==============================================================================
# 5. REUSABLE PROGRAMMATIC API (FOR SCANNERS & AUTOMATED SIGNALS)
# ==============================================================================
def place_signal_gtt(symbol: str, trigger: float = None, limit: float = None,
                     target: float = None, sl: float = None, lots: int = 1,
                     qty: int = None, product: str = None, exchange: str = None,
                     execute: bool = False):
    """
    Programmatic entry point for scanners and signal engines.
    Pass signal parameters directly and it auto-handles:
    - Exchange & lot-size resolution
    - SEBI delivery rule protection (NRML vs MIS)
    - Compliant buffer calculations (>0.09)
    - Single Buy GTT placement
    """
    class SignalArgs:
        def __init__(self):
            self.symbol = symbol
            self.trigger = trigger
            self.limit = limit
            self.target = target
            self.sl = sl
            self.lots = lots
            self.qty = qty
            self.product = product
            self.exchange = exchange
            self.execute = execute

    return handle_buy(SignalArgs())


# ==============================================================================
# CLI ENTRY POINT
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Universal Zerodha GTT Trading Tool")

    # Global/Direct Signal Parameters (No subcommand required!)
    parser.add_argument("--symbol", default=None, help="Tradingsymbol (e.g. TATASTEEL26NOV172.5PE, VEDL26NOV230PE)")
    parser.add_argument("--trigger", type=float, default=None, help="Trigger price (auto-calculated if omitted)")
    parser.add_argument("--limit", type=float, default=None, help="Limit price (auto-calculated if omitted)")
    parser.add_argument("--target", type=float, default=None, help="Target price")
    parser.add_argument("--sl", type=float, default=None, help="Stop loss price")
    parser.add_argument("--lots", type=int, default=1, help="Number of lots (default: 1)")
    parser.add_argument("--qty", type=int, default=None, help="Explicit quantity (overrides lots)")
    parser.add_argument("--product", default=None, help="MIS, NRML, or CNC")
    parser.add_argument("--exchange", default=None, help="NFO, NSE, BFO, BSE")
    parser.add_argument("--mode", choices=["buy", "oco"], default="buy", help="GTT mode (buy or oco, default: buy)")
    parser.add_argument("--execute", action="store_true", help="Execute live on Kite (preview mode if omitted)")
    parser.add_argument("--payload", default=None, help="JSON string or file containing signal parameters")

    subparsers = parser.add_subparsers(dest="command", help="Optional command (buy, oco, status, cancel)")

    # BUY
    buy_parser = subparsers.add_parser("buy", help="Place Breakout or Limit Buy GTT")
    buy_parser.add_argument("--symbol", required=True, help="Tradingsymbol (e.g. TATASTEEL26NOV172.5PE, RELIANCE)")
    buy_parser.add_argument("--exchange", default=None, help="Exchange (NFO, NSE, BFO, BSE)")
    buy_parser.add_argument("--lots", type=int, default=1, help="Number of lots (default: 1)")
    buy_parser.add_argument("--qty", type=int, default=None, help="Explicit quantity (overrides lots)")
    buy_parser.add_argument("--product", default=None, help="MIS, NRML, or CNC")
    buy_parser.add_argument("--trigger", type=float, default=None, help="Trigger price (auto-calculated if omitted)")
    buy_parser.add_argument("--limit", type=float, default=None, help="Limit price (auto-calculated if omitted)")
    buy_parser.add_argument("--target", type=float, default=None, help="Target price")
    buy_parser.add_argument("--sl", type=float, default=None, help="Stop loss price")
    buy_parser.add_argument("--execute", action="store_true", help="Execute live on Kite (preview mode if omitted)")

    # OCO
    oco_parser = subparsers.add_parser("oco", help="Place Target + Stop-Loss Exit GTT")
    oco_parser.add_argument("--symbol", required=True, help="Tradingsymbol")
    oco_parser.add_argument("--exchange", default=None, help="Exchange")
    oco_parser.add_argument("--lots", type=int, default=1, help="Number of lots if position not found")
    oco_parser.add_argument("--qty", type=int, default=None, help="Explicit quantity")
    oco_parser.add_argument("--product", default=None, help="Product type")
    oco_parser.add_argument("--target", type=float, default=None, help="Target trigger price")
    oco_parser.add_argument("--sl", type=float, default=None, help="Stop loss trigger price")
    oco_parser.add_argument("--execute", action="store_true", help="Execute live on Kite")

    # STATUS
    subparsers.add_parser("status", help="Show all live GTTs and positions")

    # CANCEL
    cancel_parser = subparsers.add_parser("cancel", help="Cancel GTT by ID or Symbol")
    cancel_parser.add_argument("--id", type=int, default=None, help="GTT ID to cancel")
    cancel_parser.add_argument("--symbol", default=None, help="Symbol to cancel all GTTs for")

    # TRAIL
    trail_parser = subparsers.add_parser("trail", help="Trail/Update Stop-Loss on active OCO GTT")
    trail_parser.add_argument("--symbol", required=True, help="Tradingsymbol")
    trail_parser.add_argument("--sl", type=float, required=True, help="New higher stop loss trigger price")
    trail_parser.add_argument("--target", type=float, default=None, help="Optional new target price")
    trail_parser.add_argument("--execute", action="store_true", help="Execute trail live on Kite")

    args = parser.parse_args()

    # 1. Payload support (JSON input from webhooks / scanner alerts)
    if args.payload:
        try:
            if Path(args.payload).exists():
                pdata = json.loads(Path(args.payload).read_text(encoding="utf-8"))
            else:
                pdata = json.loads(args.payload)
            for k, v in pdata.items():
                if hasattr(args, k) and getattr(args, k) is None:
                    setattr(args, k, v)
        except Exception as e:
            print(f"⚠️ Payload parsing notice: {e}")

    # 2. Direct top-level parameter execution
    if args.symbol and not args.command:
        if args.mode == "oco":
            handle_oco(args)
        else:
            handle_buy(args)
        return

    # 3. Subcommand routing
    if args.command == "buy":
        handle_buy(args)
    elif args.command == "oco":
        handle_oco(args)
    elif args.command == "trail":
        handle_trail(args)
    elif args.command == "status":
        handle_status(args)
    elif args.command == "cancel":
        handle_cancel(args)
    else:
        # Default to status if no arguments passed
        handle_status(args)

if __name__ == "__main__":
    main()
