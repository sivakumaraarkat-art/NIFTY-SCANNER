import re
from pathlib import Path

def patch(file):
    content = Path(file).read_text('utf-8')
    content = content.replace("def generate_sample_intraday_candidates() -> list[dict]:", "def generate_sample_intraday_candidates(syms: list) -> list[dict]:")
    content = content.replace("candidates = generate_sample_intraday_candidates()", "candidates = generate_sample_intraday_candidates(args.symbols.split(','))")
    
    # replace the hardcoded candidates with dynamic generator
    target_block = """    candidates = ["""
    if "def generate_sample_intraday_candidates(syms: list)" in content:
        # Just inject dynamic logic
        dynamic_logic = """
    candidates = []
    for s in syms:
        candidates.append({
            "symbol": s,
            "strike": 1000,
            "option_type": "CE",
            "ltp": 50.00,
            "delta": 0.55,
            "theta": -0.35,
            "vega": 0.10,
            "iv": 22,
            "score": 70,
        })
    return candidates
"""
        # regex replace the entire mock array
        content = re.sub(r'    candidates = \[\s*\{[\s\S]*?\]', dynamic_logic.strip(), content)
        Path(file).write_text(content, 'utf-8')
        print(f"Patched {file}")

patch("src/scanners/run_options_intraday_scan_powerful_sl.py")
