"""
get_live_zerodha_funds.py
Directly queries Zerodha Kite API for live account margins, cash balance,
collateral, utilized debits, and fund availability.
"""

import sys
import io
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent

try:
    from kiteconnect import KiteConnect
    token_file = ROOT / ".kite_access_token"
    key_file = ROOT / ".kite_api_key"

    if not token_file.exists() or not key_file.exists():
        print("❌ Token or API key file missing in project root.")
        sys.exit(1)

    access_token = token_file.read_text(encoding="utf-8").strip()
    api_key = key_file.read_text(encoding="utf-8").strip()

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

    profile = kite.profile()
    user_name = profile.get("user_name", "N/A")
    user_id = profile.get("user_id", "N/A")

    margins = kite.margins()
    eq = margins.get("equity", {})
    avail = eq.get("available", {})
    util = eq.get("utilised", {})

    net = eq.get("net", 0.0)
    cash = avail.get("cash", 0.0)
    collateral = avail.get("collateral", 0.0)
    opening_balance = avail.get("opening_balance", 0.0)
    live_balance = avail.get("live_balance", 0.0)

    debits = util.get("debits", 0.0)
    exposure = util.get("exposure", 0.0)
    m2m_unrealised = util.get("m2m_unrealised", 0.0)
    m2m_realised = util.get("m2m_realised", 0.0)

    print("=" * 65)
    print("💼 ZERODHA KITE ACCOUNT FUND & MARGIN AUDIT")
    print("=" * 65)
    print(f"👤 Account Holder  : {user_name} ({user_id})")
    print(f"💰 Net Margin Avail : ₹{net:,.2f}")
    print(f"💵 Available Cash   : ₹{cash:,.2f}")
    print(f"📊 Collateral (MF)  : ₹{collateral:,.2f}")
    print(f"🏦 Opening Balance  : ₹{opening_balance:,.2f}")
    print(f"💳 Utilised Debits  : ₹{debits:,.2f}")
    print(f"📈 Realised M2M     : ₹{m2m_realised:,.2f}")
    print(f"📉 Unrealised M2M   : ₹{m2m_unrealised:,.2f}")
    print("=" * 65)

    # Commodity margin if any
    comm = margins.get("commodity", {})
    if comm and comm.get("net", 0) > 0:
        print(f"🛢️ Commodity Margin : ₹{comm.get('net', 0.0):,.2f}")
        print("=" * 65)

except Exception as e:
    print(f"❌ Error fetching Zerodha margins: {e}")
