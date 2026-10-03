from pathlib import Path

def fix(file):
    lines = Path(file).read_text('utf-8').splitlines()
    for i in range(len(lines)):
        if 'print(f"' in lines[i] and '📰' not in lines[i]:
            if i+1 < len(lines) and '📰' in lines[i+1]:
                lines[i] = '            print(f"\n📰 [NEWS INTEGRATION] Fetched {len(news_syms)} BULLISH symbols from latest news scan: {\', \'.join(news_syms)}")'
                lines[i+1] = "DELETE_ME"
        if 'print("' in lines[i] and '⚠️' not in lines[i]:
            if i+1 < len(lines) and '⚠️' in lines[i+1]:
                lines[i] = '            print("\n⚠️  [NEWS INTEGRATION] No recent bullish news symbols found. Falling back to default symbols.")'
                lines[i+1] = "DELETE_ME"
    
    clean_lines = [l for l in lines if l != "DELETE_ME"]
    Path(file).write_text("\n".join(clean_lines), 'utf-8')

fix("src/scanners/run_options_intraday_scan_powerful_sl.py")
fix("src/scanners/run_btst_options_scan_powerful_sl.py")
