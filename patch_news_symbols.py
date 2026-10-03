import re
from pathlib import Path

NEWS_FUNC = '''
def get_latest_news_symbols(log_dir: Path) -> list:
    """Fetch symbols dynamically from the most recent morning News Scanner JSON."""
    import json
    if not log_dir.exists():
        return []
    news_files = list(log_dir.glob("news_scan_*.json"))
    if not news_files:
        return []
    latest_file = max(news_files, key=lambda f: f.stat().st_mtime)
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    symbols = []
    if "data" in data:
        # Sort by avg_score
        scored = [(sym, d.get("avg_score", 0)) for sym, d in data["data"].items() if d.get("sentiment") == "BULLISH ⬆️"]
        scored.sort(key=lambda x: x[1], reverse=True)
        symbols = [s[0] for s in scored]
    return symbols

'''

def patch_file(filepath):
    content = Path(filepath).read_text(encoding='utf-8')
    
    # Insert helper before main()
    if "def get_latest_news_symbols" not in content:
        content = content.replace("def main():", NEWS_FUNC + "def main():")
        
    # Replace logic in main
    main_pattern = r"(args = parse_args\(\))"
    replacement = r"""\1

    if getattr(args, 'use_news_candidates', False):
        news_syms = get_latest_news_symbols(Path("logs"))
        if news_syms:
            print(f"\n📰 [NEWS INTEGRATION] Fetched {len(news_syms)} BULLISH symbols from latest news scan: {', '.join(news_syms)}")
            args.symbols = ",".join(news_syms)
        else:
            print("\n⚠️  [NEWS INTEGRATION] No recent bullish news symbols found. Falling back to default symbols.")"""
            
    content = re.sub(main_pattern, replacement, content, count=1)
    Path(filepath).write_text(content, encoding='utf-8')
    print(f"Patched {filepath}")

patch_file("src/scanners/run_options_intraday_scan_powerful_sl.py")
patch_file("src/scanners/run_btst_options_scan_powerful_sl.py")
