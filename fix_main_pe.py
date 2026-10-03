import re

for filename in ['src/scanners/run_options_intraday_scan_powerful_sl.py', 'src/scanners/run_btst_options_scan_powerful_sl.py']:
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
        
    pattern = r"if getattr\(args, 'use_news_candidates', False\):.*?# Get candidates\n.*?candidates = generate_sample_[a-zA-Z_]+\(args\.symbols\.split\([\'\"]\,[\'\"]\)\)"
    
    new_main = '''if getattr(args, 'use_news_candidates', False):
        news_data = get_latest_news_symbols(Path("logs"))
        if news_data:
            bullish = [s[0] for s in news_data if "BULLISH" in s[1]]
            bearish = [s[0] for s in news_data if "BEARISH" in s[1]]
            
            print(f"\n📰 [NEWS INTEGRATION] Dynamic fetch complete from latest morning scan!")
            if bullish:
                print(f"   🟢 BULLISH (Targeting CE): {', '.join(bullish)}")
            if bearish:
                print(f"   🔴 BEARISH (Targeting PE): {', '.join(bearish)}")
            
            # Pass tuple list directly
            candidates = generate_sample_REPLACEME_candidates(news_data)
            args.symbols = ",".join([s[0] for s in news_data])
        else:
            print("\n⚠️  [NEWS INTEGRATION] No recent news symbols found. Falling back to default.")
            candidates = generate_sample_REPLACEME_candidates(args.symbols.split(','))
    else:
        candidates = generate_sample_REPLACEME_candidates(args.symbols.split(','))'''

    if 'intraday' in filename:
        replacement = new_main.replace('REPLACEME', 'intraday')
    else:
        replacement = new_main.replace('REPLACEME', 'btst')
        
    # use re.sub with dotall
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
print("Fixed main blocks.")
