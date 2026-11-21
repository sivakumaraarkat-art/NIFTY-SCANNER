import sys
import os
from pathlib import Path

# UTF-8 fix for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scanners.options_data_provider import get_kite_client

def cancel_gtt_order(trigger_id=343152346):
    print("=" * 75)
    print("🗑️  CANCELLING ZERODHA GTT ORDER")
    print("=" * 75)

    kite = get_kite_client()
    if not kite:
        print("❌ Kite client initialization failed. Check credentials.")
        return

    try:
        # Check active GTTs
        all_gtts = kite.get_gtts()
        cochin_gtts = [
            g for g in all_gtts
            if g.get("condition", {}).get("tradingsymbol") == "COCHINSHIP"
            and g.get("status") == "active"
        ]

        if not cochin_gtts and not trigger_id:
            print("ℹ️ No active GTT orders found for COCHINSHIP.")
            return

        # Target trigger id or all active COCHINSHIP GTTs
        target_ids = [trigger_id] if trigger_id else []
        for g in cochin_gtts:
            tid = g.get("id")
            if tid and tid not in target_ids:
                target_ids.append(tid)

        print(f"Found {len(target_ids)} GTT order(s) to cancel: {target_ids}")
        for tid in target_ids:
            try:
                res = kite.delete_gtt(tid)
                print(f"✅ GTT Order ID {tid} successfully CANCELLED! (Response: {res})")
            except Exception as e:
                print(f"⚠️ Could not cancel ID {tid}: {e}")

        print("\n🎉 All requested GTT orders have been cancelled.")
        print("   Your Kite account is clean. No active orders pending.")
        print("=" * 75)

    except Exception as e:
        print(f"❌ Error during GTT cancellation: {e}")

if __name__ == "__main__":
    cancel_gtt_order(343152346)
