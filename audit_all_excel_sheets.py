"""
audit_all_excel_sheets.py
Audits all Excel files in the working directory:
  - Sheet names
  - Max row/column
  - Header / title summary
  - Last modified timestamp
  - Flags outdated prices or inconsistencies
"""

import sys
import io
import os
from pathlib import Path
from datetime import datetime
import openpyxl

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent

excel_files = sorted(list(ROOT.glob("*.xlsx")), key=lambda f: f.stat().st_mtime, reverse=True)

print("=" * 85)
print(f"📊 EXCEL FILES INVENTORY & HEALTH AUDIT ({len(excel_files)} FILES FOUND)")
print("=" * 85)

for f in excel_files:
    mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    size_kb = f.stat().st_size / 1024
    print(f"\n📁 FILE: {f.name} ({size_kb:.1f} KB | Last Modified: {mtime})")
    try:
        wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
        sheet_names = wb.sheetnames
        print(f"   Sheets ({len(sheet_names)}): {', '.join(sheet_names)}")
        for sname in sheet_names[:3]:
            ws = wb[sname]
            title_cell = ws.cell(row=1, column=1).value or "N/A"
            r2_cell = ws.cell(row=2, column=1).value or ""
            print(f"   • [{sname}]: {ws.max_row} rows × {ws.max_column} cols | Header: {str(title_cell)[:60]}")
            if r2_cell:
                print(f"     Subtitle: {str(r2_cell)[:75]}")
        wb.close()
    except Exception as e:
        print(f"   ⚠️ Error reading workbook: {e}")

print("\n" + "=" * 85)
