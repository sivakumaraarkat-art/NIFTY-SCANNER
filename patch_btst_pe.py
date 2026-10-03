import re

with open('src/scanners/run_btst_options_scan_powerful_sl.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update get_latest_news_symbols to fetch both
old_news_func = '''def get_latest_news_symbols(log_dir: Path) -> list:
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
    return symbols'''

new_news_func = '''def get_latest_news_symbols(log_dir: Path) -> list:
    """Fetch BOTH Bullish and Bearish symbols dynamically from the morning News."""
    import json
    if not log_dir.exists():
        return []
    news_files = list(log_dir.glob("news_scan_*.json"))
    if not news_files:
        return []
    latest_file = max(news_files, key=lambda f: f.stat().st_mtime)
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    symbols_with_sentiment = []
    if "data" in data:
        # We extract BOTH Bullish and Bearish and pass their sentiment as a tuple
        for sym, d in data["data"].items():
            sent = d.get("sentiment", "")
            if "BULLISH" in sent or "BEARISH" in sent:
                symbols_with_sentiment.append((sym, sent, d.get("avg_score", 0)))
        
        # Sort entirely by the absolute intensity score 
        symbols_with_sentiment.sort(key=lambda x: abs(x[2]), reverse=True)
        
        # Only extract the symbol and the raw sentiment string
        symbols_with_sentiment = [(item[0], item[1]) for item in symbols_with_sentiment]
    return symbols_with_sentiment'''

content = content.replace(old_news_func, new_news_func)


# 2. Update generate_sample_btst_candidates
old_gen = '''def generate_sample_btst_candidates(syms: list) -> list[dict]:
    """Generate sample BTST candidates with Greeks."""
    candidates = []
    for s in syms:
        candidates.append({
            "symbol": s,
            "strike": 1000,
            "option_type": "CE",
            "ltp": 50.00,
            "delta": 0.60,
            "theta": -0.25,
            "vega": 0.15,
            "iv": 18,
            "score": 75,
        })
    return candidates'''

new_gen = '''def generate_sample_btst_candidates(syms: list) -> list[dict]:
    """Generate sample BTST candidates with Greeks mapped to CE/PE."""
    candidates = []
    for item in syms:
        # Backwards compatibility check
        if isinstance(item, tuple):
            symbol, sentiment = item
        else:
            symbol, sentiment = item, "BULLISH"
            
        opt_type = "PE" if "BEARISH" in sentiment else "CE"
        delta_val = -0.60 if opt_type == "PE" else 0.60
        
        candidates.append({
            "symbol": symbol,
            "strike": 1000,
            "option_type": opt_type,
            "ltp": 65.00 if opt_type == "PE" else 50.00,
            "delta": delta_val,
            "theta": -0.25,
            "vega": 0.15,
            "iv": 22 if opt_type == "PE" else 18,
            "score": 80 if opt_type == "PE" else 75,
            "sentiment_catalyst": sentiment,
        })
    return candidates'''
    
content = content.replace(old_gen, new_gen)


# 3. Update main integration block
old_main = '''    if getattr(args, 'use_news_candidates', False):
        news_syms = get_latest_news_symbols(Path("logs"))
        if news_syms:
            print(f"\n📰 [NEWS INTEGRATION] Fetched {len(news_syms)} BULLISH symbols from latest news scan: {', '.join(news_syms)}")
            args.symbols = ",".join(news_syms)
        else:
            print("\n⚠️  [NEWS INTEGRATION] No recent bullish news symbols found. Falling back to default symbols.")

    # Get candidates
    candidates = generate_sample_btst_candidates(args.symbols.split(','))'''

new_main = '''    if getattr(args, 'use_news_candidates', False):
        news_data = get_latest_news_symbols(Path("logs"))
        if news_data:
            # Separate them for reporting
            bullish = [s[0] for s in news_data if "BULLISH" in s[1]]
            bearish = [s[0] for s in news_data if "BEARISH" in s[1]]
            
            print(f"\n📰 [NEWS INTEGRATION] Dynamic fetch complete from latest morning scan!")
            if bullish:
                print(f"   🟢 BULLISH (Targeting CE): {', '.join(bullish)}")
            if bearish:
                print(f"   🔴 BEARISH (Targeting PE): {', '.join(bearish)}")
            
            # Pass the tuple list directly to generator instead of joining a string
            candidates = generate_sample_btst_candidates(news_data)
            
            # Reconstruct string for logging 
            args.symbols = ",".join([s[0] for s in news_data])
        else:
            print("\n⚠️  [NEWS INTEGRATION] No recent news symbols found. Falling back to default symbols.")
            candidates = generate_sample_btst_candidates(args.symbols.split(','))
    else:
        candidates = generate_sample_btst_candidates(args.symbols.split(','))'''

content = content.replace(old_main, new_main)

with open('src/scanners/run_btst_options_scan_powerful_sl.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("BTST PE patched.")
