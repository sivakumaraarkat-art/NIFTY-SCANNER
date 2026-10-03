from pathlib import Path
import json

def get_latest_news_symbols():
    log_dir = Path("logs")
    if not log_dir.exists():
        return []
    
    # Check both formats just in case
    news_files = list(log_dir.glob("news_scan_*.json"))
    if not news_files:
        return []
        
    latest_file = max(news_files, key=lambda f: f.stat().st_mtime)
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    symbols = []
    if "results" in data:
        for sym, d in data["results"].items():
            if d.get("sentiment") == "BULLISH":
                symbols.append(sym)
    return symbols

print(get_latest_news_symbols())
