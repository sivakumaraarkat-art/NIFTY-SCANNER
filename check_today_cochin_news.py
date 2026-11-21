import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
from datetime import datetime

queries = [
    'Cochin Shipyard',
    'Cochin Shipyard order',
    'Cochin Shipyard contract',
    'Cochin Shipyard MoD',
    'Cochin Shipyard dividend',
    'COCHINSHIP'
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

all_news = {}
for q in queries:
    url = f'https://news.google.com/rss/search?q={urllib.parse.quote(q)}&hl=en-IN&gl=IN&ceid=IN:en'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            root = ET.fromstring(resp.read())
            for item in root.findall('.//item')[:10]:
                title = item.findtext('title')
                pub_date = item.findtext('pubDate')
                link = item.findtext('link')
                desc = item.findtext('description')
                if title and title not in all_news:
                    all_news[title] = {'date': pub_date, 'link': link, 'desc': desc}
    except Exception as e:
        print(f'Error fetching {q}:', e)

print(f"Total unique news items: {len(all_news)}")
print("=" * 80)
for title, data in sorted(all_news.items(), key=lambda x: x[1]['date'], reverse=True)[:15]:
    dt = data['date']
    print(f"[{dt}]")
    print(f"TITLE: {title}")
    # print description snippet
    desc = data['desc']
    if desc:
        import re
        clean_desc = re.sub('<[^<]+?>', '', desc)
        print(f"SNIP : {clean_desc[:200]}")
    print("-" * 80)
