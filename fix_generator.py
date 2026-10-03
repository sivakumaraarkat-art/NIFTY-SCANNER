from pathlib import Path
content = Path("src/scanners/run_options_intraday_scan_powerful_sl.py").read_text('utf-8')
# Find the start and end of the broken block
start_str = 'def generate_sample_intraday_candidates(syms: list) -> list[dict]:\n    """Generate sample intraday candidates with Greeks."""\n'
replacement = '''def generate_sample_intraday_candidates(syms: list) -> list[dict]:
    """Generate sample intraday candidates with Greeks."""
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
'''

import re
# regex replace from start_str to the end of the return
content = re.sub(r'def generate_sample_intraday_candidates\(syms: list\) -> list\[dict\]:[\s\S]*?return candidates\n\n' , replacement + '\n', content)
content = content.replace("return candidates\n\nreturn candidates", "return candidates\n\n")
Path("src/scanners/run_options_intraday_scan_powerful_sl.py").write_text(content, 'utf-8')
