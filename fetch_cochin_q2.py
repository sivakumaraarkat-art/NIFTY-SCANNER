import sys
import os
import urllib.parse
import xml.etree.ElementTree as ET
import urllib.request
import json
import re

# UTF-8 fix for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def fetch_cochin_news():
    print("=" * 80)
    print("🔍 CHECKING COCHIN SHIPYARD Q2 RESULTS, BOARD MEETING & EARNINGS METRICS")
    print("=" * 80)

    queries = [
        "Cochin Shipyard Q2 results",
        "Cochin Shipyard board meeting Q2 results date",
        "Cochin Shipyard Q2 net profit revenue"
    ]

    all_items = []
    for q in queries:
        encoded = urllib.parse.quote(q)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                xml_data = resp.read()
                root = ET.fromstring(xml_data)
                items = root.findall(".//item")
                for it in items[:6]:
                    title = it.findtext("title", "")
                    pub_date = it.findtext("pubDate", "")
                    link = it.findtext("link", "")
                    if title and title not in [x['title'] for x in all_items]:
                        all_items.append({"title": title, "date": pub_date, "link": link})
        except Exception as e:
            print(f"Error fetching '{q}': {e}")

    print(f"Found {len(all_items)} relevant news items / earnings reports:\n")
    for idx, item in enumerate(all_items[:10], start=1):
        print(f"{idx}. [{item['date'][:16]}]")
        print(f"   {item['title']}")
        print("-" * 80)

if __name__ == "__main__":
    fetch_cochin_news()
