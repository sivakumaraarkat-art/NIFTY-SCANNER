import openpyxl
from kiteconnect import KiteConnect
from pathlib import Path
import json

ROOT = Path(".")
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

# 1. Fetch live Zerodha holdings
holdings = kite.holdings()
holdings_dict = {}
for h in holdings:
    sym = h.get("tradingsymbol")
    qty = h.get("quantity", 0) + h.get("t1_quantity", 0)
    avg = h.get("average_price", 0.0)
    ltp = h.get("last_price", 0.0)
    pnl = h.get("pnl", 0.0)
    holdings_dict[sym] = {
        "qty": qty,
        "avg": avg,
        "ltp": ltp,
        "pnl": pnl,
        "inv": qty * avg,
        "cur": qty * ltp
    }

# 2. Read Master Excel Plan
wb = openpyxl.load_workbook("Portfolio_Master_Exit_and_Target_Plan_2026_2027.xlsx", data_only=True)
ws = wb["Master Portfolio Exit Matrix"]

excel_rows = []
for r in range(9, ws.max_row + 1):
    category = ws.cell(r, 1).value
    sym = ws.cell(r, 2).value
    if not sym:
        continue
    plan_qty = ws.cell(r, 3).value
    plan_avg = ws.cell(r, 4).value
    plan_ltp = ws.cell(r, 5).value
    target1 = ws.cell(r, 9).value
    target2 = ws.cell(r, 12).value
    action = ws.cell(r, 14).value

    excel_rows.append({
        "category": category,
        "sym": sym,
        "plan_qty": plan_qty,
        "plan_avg": plan_avg,
        "plan_ltp": plan_ltp,
        "target1": target1,
        "target2": target2,
        "action": action
    })

# Compare
comparison = []
total_live_inv = sum(h["inv"] for h in holdings_dict.values())
total_live_cur = sum(h["cur"] for h in holdings_dict.values())
total_live_pnl = sum(h["pnl"] for h in holdings_dict.values())

for row in excel_rows:
    sym = row["sym"]
    live = holdings_dict.get(sym)

    if live:
        live_qty = live["qty"]
        live_avg = live["avg"]
        live_ltp = live["ltp"]
        live_pnl = live["pnl"]
        live_pnl_pct = (live_pnl / live["inv"] * 100) if live["inv"] else 0

        t1 = row["target1"]
        t2 = row["target2"]
        dist_t1_pct = ((t1 - live_ltp) / live_ltp * 100) if (t1 and live_ltp) else None
        dist_t2_pct = ((t2 - live_ltp) / live_ltp * 100) if (t2 and live_ltp) else None

        comparison.append({
            "category": row["category"],
            "sym": sym,
            "plan_qty": row["plan_qty"],
            "live_qty": live_qty,
            "qty_match": (row["plan_qty"] == live_qty),
            "plan_avg": row["plan_avg"],
            "live_avg": live_avg,
            "plan_ltp": row["plan_ltp"],
            "live_ltp": live_ltp,
            "live_pnl": live_pnl,
            "live_pnl_pct": live_pnl_pct,
            "target1": t1,
            "dist_t1_pct": dist_t1_pct,
            "target2": t2,
            "dist_t2_pct": dist_t2_pct,
            "action": row["action"]
        })
    else:
        comparison.append({
            "category": row["category"],
            "sym": sym,
            "plan_qty": row["plan_qty"],
            "live_qty": 0,
            "qty_match": False,
            "plan_avg": row["plan_avg"],
            "live_avg": 0,
            "plan_ltp": row["plan_ltp"],
            "live_ltp": 0,
            "live_pnl": 0,
            "live_pnl_pct": 0,
            "target1": row["target1"],
            "dist_t1_pct": 0,
            "target2": row["target2"],
            "dist_t2_pct": 0,
            "action": "NOT FOUND IN CURRENT LIVE DEMAT"
        })

# Check if there are live holdings not in the Excel plan
not_in_plan = [sym for sym in holdings_dict if sym not in [r["sym"] for r in excel_rows]]

with open("portfolio_comparison_result.json", "w", encoding="utf-8") as f:
    json.dump({
        "totals": {
            "total_live_inv": total_live_inv,
            "total_live_cur": total_live_cur,
            "total_live_pnl": total_live_pnl,
            "total_live_pnl_pct": (total_live_pnl / total_live_inv * 100) if total_live_inv else 0
        },
        "comparison": comparison,
        "not_in_plan": not_in_plan
    }, f, indent=2)

print(f"Comparison complete! Total Holdings: {len(holdings_dict)}, Excel Holdings: {len(excel_rows)}")
print(f"Total Invested: Rs.{total_live_inv:,.2f} | Current: Rs.{total_live_cur:,.2f} | Net P&L: Rs.{total_live_pnl:,.2f} ({(total_live_pnl/total_live_inv*100):.2f}%)")
if not_in_plan:
    print(f"Holdings in Demat but not in Excel: {not_in_plan}")
