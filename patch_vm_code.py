import os
import shutil
from datetime import datetime
import py_compile

DIR = "/home/ubuntu/NiftyScanner/nifty_v14_7/scripts"
stage9_file = os.path.join(DIR, "index_oi_scanner_stage9.py")
v14_file = os.path.join(DIR, "NIFTY_V14_9_PAPER_FINAL_DB_SNAPSHOT.py")
v14_bak = os.path.join(DIR, "NIFTY_V14_9_PAPER_FINAL_DB_SNAPSHOT.py.bak")

# 1. RESTORE PRISTINE V14 FROM BACKUP FIRST
if os.path.exists(v14_bak):
    shutil.copy2(v14_bak, v14_file)
    print("[OK] Restored pristine NIFTY_V14_9_PAPER_FINAL_DB_SNAPSHOT.py from backup")

# 2. PATCH index_oi_scanner_stage9.py (SHORT-SQUEEZE OVERRIDE)
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
    print("[OK] Patched index_oi_scanner_stage9.py with Short-Squeeze override")
else:
    print("[INFO] index_oi_scanner_stage9.py Short-Squeeze override already active")

# 3. PATCH NIFTY_V14_9_PAPER_FINAL_DB_SNAPSHOT.py (EVALUATE_PCR_SUPPORT ONLY)
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
    with open(v14_file, "w", encoding="utf-8") as f:
        f.write(v14_code)
    print("[OK] Replaced evaluate_pcr_support with dynamic range 0.65 - 1.35")
elif "0.65 threshold" in v14_code:
    print("[INFO] evaluate_pcr_support dynamic range 0.65 - 1.35 is active")
else:
    print("[WARN] Could not find evaluate_pcr_support in restored v14 code")

# 4. VERIFY COMPILATION
py_compile.compile(stage9_file, doraise=True)
py_compile.compile(v14_file, doraise=True)
print("[VERIFIED] Both Stage 9 and V14_9 compiled with ZERO errors.")
