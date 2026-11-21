"""
check_zerodha_muhurat_bulletin.py
Fetches latest circulars / bulletins from Zerodha and NSE
regarding Muhurat trading and market holiday timings.
"""

import sys
import io
import json
import urllib.request
import re

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 70)
print("🔍 CHECKING ZERODHA BULLETIN & NSE CIRCULARS FOR MARKET TIMINGS")
print("=" * 70)

# 1. Check Zerodha Bulletin
urls_to_try = [
    ("Zerodha Bulletin", "https://zerodha.com/marketintel/bulletin/"),
    ("Zerodha Support Muhurat", "https://support.zerodha.com/category/trading-and-markets/trading-faqs/articles/muhurat-trading"),
    ("NSE Holiday List", "https://www.nseindia.com/api/holiday-master?type=trading")
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

for name, url in urls_to_try:
    print(f"\n--- Checking {name}: {url} ---")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            print(f"Successfully fetched {len(content)} chars.")
            # Search for Muhurat or trading timings
            matches = re.findall(r'(?i)(.{0,80}(?:muhurat|trading session|market timings|pre-open|06:15|18:15|18:00|diwali).{0,80})', content)
            if matches:
                print(f"Found {len(matches)} relevant mentions:")
                for m in matches[:10]:
                    clean = re.sub(r'<[^>]+>', ' ', m).strip()
                    clean = re.sub(r'\s+', ' ', clean)
                    if clean:
                        print(f"  • {clean}")
            else:
                print("No direct keywords matched in content snippet.")
    except Exception as e:
        print(f"Error fetching {name}: {e}")

print("\n" + "=" * 70)
