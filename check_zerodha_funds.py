"""
Check Zerodha funds/margins and compare against Cochin Shipyard trade requirements.
"""
import sys
import os
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scanners.options_data_provider import get_kite_client

def sync_from_vm_if_needed():
    key_path = Path(r"D:\NiftyScanner\oracle\nifty-v15.key")
    if not key_path.exists():
        return
    host = "ubuntu@140.245.195.112"
    remote_token = "/home/ubuntu/NiftyScanner/.kite_access_token"
    remote_key = "/home/ubuntu/NiftyScanner/.kite_api_key"
    try:
        res = subprocess.run(
            ["ssh", "-i", str(key_path), "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=3", host, f"cat {remote_token} 2>/dev/null"],
            capture_output=True, text=True, timeout=5
        )
        if res.returncode == 0 and res.stdout.strip():
            vm_token = res.stdout.strip()
            local_token_file = ROOT / ".kite_access_token"
            if local_token_file.read_text(encoding="utf-8").strip() != vm_token:
                local_token_file.write_text(vm_token, encoding="utf-8")
                print("🔄 Updated local access token from Oracle VM.")
    except Exception as e:
        pass

def check_funds():
    print("=" * 80)
    print("💰 ZERODHA ACCOUNT FUND & MARGIN AUDIT FOR COCHIN SHIPYARD")
    print("=" * 80)

    sync_from_vm_if_needed()
    kite = get_kite_client()
    if not kite:
        print("❌ Kite client authentication failed (Token expired or invalid).")
        return

    try:
        profile = kite.profile()
        user_name = profile.get("user_name", "N/A")
        user_id = profile.get("user_id", "N/A")
        print(f"👤 Account: {user_name} ({user_id})")

        margins = kite.margins()
        equity_margins = margins.get("equity", {})

        avail_cash = equity_margins.get("available", {}).get("cash", 0.0)
        net = equity_margins.get("net", 0.0)
        collateral = equity_margins.get("available", {}).get("collateral", 0.0)
        opening_balance = equity_margins.get("available", {}).get("opening_balance", 0.0)
        intraday_payin = equity_margins.get("available", {}).get("intraday_payin", 0.0)
        live_balance = equity_margins.get("available", {}).get("live_balance", 0.0)
        utilised_debits = equity_margins.get("utilised", {}).get("debits", 0.0)

        print("-" * 80)
        print(f"💵 Available Net Equity Margin:   ₹{net:,.2f}")
        print(f"💵 Available Clean Cash:          ₹{avail_cash:,.2f}")
        print(f"📊 Collateral Margin (Pledged):   ₹{collateral:,.2f}")
        print(f"💳 Utilised Debits (Positions):   ₹{utilised_debits:,.2f}")
        print("-" * 80)

        # Cochin Shipyard requirements
        cochin_quote = kite.quote(["NSE:COCHINSHIP"]).get("NSE:COCHINSHIP", {})
        ltp = cochin_quote.get("last_price", 1237.5)
        print(f"🚢 COCHIN SHIPYARD (NSE:COCHINSHIP) Live Price: ₹{ltp:.2f}")

        # Requirement 1: MIS 400 shares (5x leverage)
        # Zerodha MIS margin on equity stocks is typically 20% (5x)
        mis_exposure = 400 * ltp
        mis_req_margin = mis_exposure * 0.20

        # Requirement 2: CNC 30 shares
        cnc_req_margin = 30 * ltp

        print("\n📋 TRADE MARGIN REQUIREMENTS:")
        print(f"1. MIS Trade (400 Shares @ 5x Margin):")
        print(f"   • Total Value:   ₹{mis_exposure:,.2f}")
        print(f"   • Margin Needed: ₹{mis_req_margin:,.2f} (~20%)")
        mis_status = "✅ SUFFICIENT FUNDS" if net >= mis_req_margin else f"❌ SHORT BY ₹{mis_req_margin - net:,.2f}"
        print(f"   • Status:        {mis_status}")

        print(f"\n2. CNC Averaging (30 Shares Delivery 1x):")
        print(f"   • Margin Needed: ₹{cnc_req_margin:,.2f} (100% Cash)")
        cnc_status = "✅ SUFFICIENT FUNDS" if net >= cnc_req_margin else f"❌ SHORT BY ₹{cnc_req_margin - net:,.2f}"
        print(f"   • Status:        {cnc_status}")

        print(f"\n3. BOTH Simultaneously (400 MIS + 30 CNC):")
        total_req = mis_req_margin + cnc_req_margin
        both_status = "✅ SUFFICIENT FUNDS FOR BOTH" if net >= total_req else f"⚠️ SHORT BY ₹{total_req - net:,.2f}"
        print(f"   • Total Needed:  ₹{total_req:,.2f}")
        print(f"   • Status:        {both_status}")

        # If MIS 400 shares is too high for available funds, calculate max affordable MIS shares
        if net < mis_req_margin and net > 0:
            max_mis_shares = int(net // (ltp * 0.20))
            print(f"\n💡 Max affordable MIS shares with current ₹{net:,.2f}: {max_mis_shares} Shares")

        print("=" * 80)

    except Exception as e:
        print(f"❌ Error querying margins from Zerodha: {e}")

if __name__ == "__main__":
    check_funds()
