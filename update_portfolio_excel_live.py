"""
update_portfolio_excel_live.py
Updates Portfolio_Master_Exit_and_Target_Plan_2026_2027.xlsx with real-time Zerodha Kite data.
"""

import datetime
from pathlib import Path
import openpyxl
from kiteconnect import KiteConnect

ROOT = Path(__file__).resolve().parent
api_key = open(ROOT / ".kite_api_key", "r", encoding="utf-8").read().strip()
token = open(ROOT / ".kite_access_token", "r", encoding="utf-8").read().strip()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token)

print("=" * 85)
print("📊 SYNCHRONIZING EXCEL MASTER PLAN WITH LIVE ZERODHA HOLDINGS")
print("=" * 85)

# 1. Fetch live holdings & cash from Zerodha
holdings = kite.holdings()
kite_holdings = {}
for h in holdings:
    sym = h["tradingsymbol"].strip()
    qty = h["quantity"] + h["t1_quantity"]
    buy_avg = h["average_price"]
    ltp = h["last_price"]
    pnl = h["pnl"]
    kite_holdings[sym] = {
        "qty": qty,
        "buy_avg": buy_avg,
        "ltp": ltp,
        "pnl": pnl,
        "invested": qty * buy_avg,
        "live_val": qty * ltp
    }

margins = kite.margins(segment="equity")
available_cash = margins.get("available", {}).get("live_balance", 0.0)

print(f"Fetched {len(kite_holdings)} holdings from Zerodha.")
print(f"Available Zerodha Free Cash: ₹{available_cash:,.2f}")

# 2. Open workbook
wb_path = ROOT / "Portfolio_Master_Exit_and_Target_Plan_2026_2027.xlsx"
wb = openpyxl.load_workbook(wb_path)

now_str = datetime.datetime.now().strftime("%d-%b-%Y %H:%M")

# 3. Update 'Master Portfolio Exit Matrix'
ws_matrix = wb["Master Portfolio Exit Matrix"]
ws_matrix.cell(2, 1).value = f"Account: Siva Kumar Aarkat (FH7698) | Live Zerodha Scanned Feed ({now_str}) | Pre-Budget 2027"

tot_invested = 0.0
tot_live_val = 0.0
tot_live_pnl = 0.0

for r in range(9, ws_matrix.max_row + 1):
    sym = ws_matrix.cell(r, 2).value
    if not sym or str(sym).strip() == "TOTAL PORTFOLIO":
        continue
    sym = str(sym).strip()
    if sym in kite_holdings:
        kh = kite_holdings[sym]
        ws_matrix.cell(r, 3).value = kh["qty"]
        ws_matrix.cell(r, 4).value = kh["buy_avg"]
        ws_matrix.cell(r, 5).value = kh["ltp"]

        tot_invested += kh["invested"]
        tot_live_val += kh["live_val"]
        tot_live_pnl += kh["pnl"]

# Update KPI Cards
ws_matrix.cell(5, 1).value = f"₹{int(round(tot_invested)):,}"
ws_matrix.cell(5, 4).value = f"₹{int(round(tot_live_val)):,}"
ws_matrix.cell(6, 4).value = f"P&L: ₹{int(round(tot_live_pnl)):,}"
ws_matrix.cell(5, 13).value = f"₹{int(round(available_cash)):,}"

print("\n✅ Updated 'Master Portfolio Exit Matrix':")
print(f"    • Total Invested Cost:  ₹{tot_invested:,.2f}")
print(f"    • Live Current Value:   ₹{tot_live_val:,.2f}")
print(f"    • Live Current P&L:     ₹{tot_live_pnl:,.2f} ({(tot_live_pnl / tot_invested * 100):+.2f}%)")
print(f"    • Available Cash:       ₹{available_cash:,.2f}")

# 4. Update 'Live vs Previous Plan Audit'
if "Live vs Previous Plan Audit" in wb.sheetnames:
    ws_audit = wb["Live vs Previous Plan Audit"]
    ws_audit.cell(2, 1).value = f"Real-Time Movement Audit | Comparison against previous plan updated on {now_str}"

    for r in range(5, ws_audit.max_row + 1):
        sym = ws_audit.cell(r, 1).value
        if not sym:
            continue
        sym = str(sym).strip()
        if sym in kite_holdings:
            kh = kite_holdings[sym]
            prev_ltp = ws_audit.cell(r, 5).value or ws_audit.cell(r, 4).value or kh["ltp"]
            live_ltp = kh["ltp"]

            # Previous LTP moves to Col 4 (D)
            ws_audit.cell(r, 4).value = prev_ltp
            # Live LTP goes to Col 5 (E)
            ws_audit.cell(r, 5).value = live_ltp
            # Update Qty and Buy Avg
            ws_audit.cell(r, 2).value = kh["qty"]
            ws_audit.cell(r, 3).value = kh["buy_avg"]

            # Update Movement Status (Col 9 / I)
            if live_ltp > prev_ltp:
                ws_audit.cell(r, 9).value = "🟢 GAINED"
            elif live_ltp < prev_ltp:
                ws_audit.cell(r, 9).value = "🔴 DIPPED"
            else:
                ws_audit.cell(r, 9).value = "⚪ UNCHANGED"

    print("✅ Updated 'Live vs Previous Plan Audit' with previous vs live price comparison.")

# 5. Save workbook
wb.save(wb_path)
print(f"\n🎉 Successfully saved updated workbook to: {wb_path.name}")
print("=" * 85)
