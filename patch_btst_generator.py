import re
from pathlib import Path

def patch(file):
    content = Path(file).read_text('utf-8')
    content = content.replace("def generate_sample_btst_candidates() -> list[dict]:", "def generate_sample_btst_candidates(syms: list) -> list[dict]:")
    content = content.replace("candidates = generate_sample_btst_candidates()", "candidates = generate_sample_btst_candidates(args.symbols.split(','))")
    
    dynamic_logic = """
    candidates = []
    for s in syms:
        candidates.append({
            "symbol": s,
            "strike": 1000,
            "option_type": "CE",
            "ltp": 50.00,
            "sl": 45.00,
            "t1": 60,
            "t2": 70,
            "delta": 0.55,
            "vega": 0.10,
            "theta": -0.35,
            "iv": 22,
            "score": 75
        })
    return candidates
"""
    content = re.sub(r'    candidates = \[\s*\{[\s\S]*?\]', dynamic_logic.strip(), content)
    Path(file).write_text(content, 'utf-8')
    print(f"Patched {file}")

patch("src/scanners/run_btst_options_scan_powerful_sl.py")
