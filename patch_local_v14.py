import os
import shutil
from datetime import datetime
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIR = ROOT.parent / "VM" / "nifty_v14_7" / "scripts"
stage9_file = DIR / "index_oi_scanner_stage9.py"
v14_file = DIR / "NIFTY_V14_9_PAPER_FINAL_DB_SNAPSHOT.py"

ts = datetime.now().strftime("%Y%m%d_%H%M%S")

# 1. CREATE BACKUPS
shutil.copy2(stage9_file, f"{stage9_file}.bak_{ts}")
shutil.copy2(stage9_file, f"{stage9_file}.bak")
shutil.copy2(v14_file, f"{v14_file}.bak_{ts}")
shutil.copy2(v14_file, f"{v14_file}.bak")
print(f"[OK] Local backups created for Stage 9 and V14_9 with timestamp {ts}")

# 2. PATCH index_oi_scanner_stage9.py
with open(stage9_file, "r", encoding="utf-8") as f:
    s9_code = f.read()

old_s9_conflict = """        # conflict when PCR actively contradicts aggregated bias (and aggregated not NEUTRAL)
        if confirmed_bias == 'BULLISH' and pcr_bias == 'BEARISH':
            conflict = True
        elif confirmed_bias == 'BEARISH' and pcr_bias == 'BULLISH':
            conflict = True"""

new_s9_conflict = """        # conflict when PCR actively contradicts aggregated bias (and aggregated not NEUTRAL)
        # SHORT-SQUEEZE / MOMENTUM OVERRIDE (Indian Market Dynamic):
        # In Indian markets, when Technical Bias is strongly BULLISH with NORMAL/HIGH volume,
        # low PCR (0.65-0.90) represents call-writer short-squeeze, NOT a bearish conflict.
        tech_b = str(last_stage8.get('technical_bias', '')).upper() if last_stage8 else ''
        vol_s = str(last_stage8.get('volume_status', '')).upper() if last_stage8 else ''
        if confirmed_bias == 'BULLISH' and pcr_bias == 'BEARISH':
            if tech_b == 'BULLISH' and vol_s in ('NORMAL', 'HIGH', 'STRONG') and pcr >= 0.60:
                conflict = False  # Short-squeeze momentum breakout; allow trade
            else:
                conflict = True
        elif confirmed_bias == 'BEARISH' and pcr_bias == 'BULLISH':
            if tech_b == 'BEARISH' and vol_s in ('NORMAL', 'HIGH', 'STRONG') and pcr <= 1.40:
                conflict = False  # Long-liquidation breakdown; allow trade
            else:
                conflict = True"""

if old_s9_conflict in s9_code:
    s9_code = s9_code.replace(old_s9_conflict, new_s9_conflict)
    with open(stage9_file, "w", encoding="utf-8") as f:
        f.write(s9_code)
    print("[OK] Successfully patched local index_oi_scanner_stage9.py")
elif "SHORT-SQUEEZE" in s9_code:
    print("[INFO] local index_oi_scanner_stage9.py already patched")

# 3. PATCH NIFTY_V14_9_PAPER_FINAL_DB_SNAPSHOT.py
with open(v14_file, "r", encoding="utf-8") as f:
    v14_code = f.read()

old_pcr_eval = (
    '    if bias == "BULLISH":\n'
    '        if pcr_value < 0.95:\n'
    '            return False, f"PCR={pcr_value:.2f} is too weak for bullish entry"\n'
    '        return True, f"PCR={pcr_value:.2f} supports bullish entry"\n\n'
    '    if pcr_value > 1.05:\n'
    '        return False, f"PCR={pcr_value:.2f} is too strong for bearish entry"\n'
    '    return True, f"PCR={pcr_value:.2f} supports bearish entry"'
)

new_pcr_eval = (
    '    # Expanded dynamic PCR thresholds for Indian Index Options:\n'
    '    # 0.65+ allows Short-Covering Bullish Squeezes\n'
    '    # Up to 1.35 allows Long-Unwinding Bearish Cascades\n'
    '    if bias == "BULLISH":\n'
    '        if pcr_value < 0.65:\n'
    '            return False, f"PCR={pcr_value:.2f} is below 0.65 threshold (extreme call resistance)"\n'
    '        return True, f"PCR={pcr_value:.2f} supports bullish entry (momentum/squeeze zone)"\n\n'
    '    if pcr_value > 1.35:\n'
    '        return False, f"PCR={pcr_value:.2f} is above 1.35 threshold (extreme put support)"\n'
    '    return True, f"PCR={pcr_value:.2f} supports bearish entry (unwinding zone)"'
)

if old_pcr_eval in v14_code:
    v14_code = v14_code.replace(old_pcr_eval, new_pcr_eval)
    print("[OK] Replaced local evaluate_pcr_support thresholds")
elif "0.65 threshold" in v14_code:
    print("[INFO] local evaluate_pcr_support already patched")

old_final_gate = (
    '    raw_final_bias = normalize_label(report.get("final_bias"))\n'
    '    if raw_final_bias and any(bad in raw_final_bias for bad in ("CAUTION", "NEUTRAL", "CLIMAX", "TRAP", "REJECTION", "UNCONFIRMED")):\n'
    '        return (False, "FINAL_BIAS_CAUTION")'
)

new_final_gate = (
    '    raw_final_bias = normalize_label(report.get("final_bias"))\n'
    '    # If final bias is CAUTION solely due to PCR in a squeeze, but technical is strong, allow entry\n'
    '    if raw_final_bias:\n'
    '        if any(bad in raw_final_bias for bad in ("NEUTRAL", "CLIMAX", "TRAP", "REJECTION", "UNCONFIRMED")):\n'
    '            return (False, "FINAL_BIAS_CAUTION")\n'
    '        if "CAUTION" in raw_final_bias:\n'
    '            tech_ok = normalize_bias(report.get("technical_bias")) == bias\n'
    '            vol_ok = normalize_label(report.get("volume_status")) in ("NORMAL", "HIGH", "STRONG")\n'
    '            if not (tech_ok and vol_ok):\n'
    '                return (False, "FINAL_BIAS_CAUTION")'
)

if old_final_gate in v14_code:
    v14_code = v14_code.replace(old_final_gate, new_final_gate)
    print("[OK] Replaced local evaluate_entry_gate FINAL_BIAS_CAUTION")
elif "tech_ok and vol_ok" in v14_code:
    print("[INFO] local evaluate_entry_gate already patched")

with open(v14_file, "w", encoding="utf-8") as f:
    f.write(v14_code)

try:
    py_compile.compile(str(stage9_file), doraise=True)
    print("[VERIFIED] Local Stage 9 compiles with ZERO errors")
except Exception as e:
    print(f"[FAIL] Local Stage 9 syntax error: {e}")

try:
    py_compile.compile(str(v14_file), doraise=True)
    print("[VERIFIED] Local V14_9 compiles with ZERO errors")
except Exception as e:
    print(f"[FAIL] Local V14_9 syntax error: {e}")
