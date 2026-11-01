import sys
import os
import time
from datetime import datetime

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.scanners.options_data_provider import get_kite_client

def track_live_crude():
    kite = get_kite_client()
    if not kite:
        print("Error connecting to Kite.")
        return

    token = 145894407  # CRUDEOIL26OCTFUT
    sym = "MCX:CRUDEOIL26OCTFUT"

    print("==================================================================")
    print(" LIVE MCX CRUDE OIL TRADE TRACKER & TARGET MONITOR")
    print("==================================================================")
    print("Press Ctrl+C to stop tracking.\n")

    entry_price = 9073.0
    stop_loss = 9033.0
    target_1 = 9120.0
    target_2 = 9150.0
    target_3 = 9200.0

    print(f"Entry Benchmark: {entry_price}")
    print(f"Stop-Loss: {stop_loss} (-40 pts)")
    print(f"Target 1: {target_1} (+47 pts)")
    print(f"Target 2: {target_2} (+77 pts)")
    print(f"Target 3: {target_3} (+127 pts)\n")

    try:
        for i in range(5):  # Live snapshot ticks
            q = kite.quote([token])
            if str(token) in q or sym in q:
                data = q.get(str(token)) or q.get(sym, {})
                ltp = data.get("last_price", 0.0)
                change = data.get("net_change", 0.0)
                ts = datetime.now().strftime("%H:%M:%S")

                print(f"[{ts}] Live LTP: {ltp} | Change: {change}")
                if ltp >= target_3:
                    print("🎉 TARGET 3 REACHED! Book full profits!")
                elif ltp >= target_2:
                    print("🎯 TARGET 2 REACHED! Trail stop-loss to entry.")
                elif ltp >= target_1:
                    print("✅ TARGET 1 REACHED! Secure partial profits.")
                elif ltp <= stop_loss:
                    print("🛑 STOP-LOSS HIT! Exit trade immediately to protect capital.")
                else:
                    print("⏳ HOLDING... Price moving within acceptable risk band.")
            else:
                print("Could not fetch price quote.")

            if i < 4:
                time.sleep(5)
    except KeyboardInterrupt:
        print("\nStopped tracking.")

if __name__ == "__main__":
    track_live_crude()
