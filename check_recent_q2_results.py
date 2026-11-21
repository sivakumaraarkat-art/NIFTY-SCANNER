import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.parse
import xml.etree.ElementTree as ET
import requests
from datetime import datetime

portfolio_stocks = [
    # Key user holdings
    "COALINDIA", "COCHINSHIP", "SUZLON", "PCBL", "LODHA", "BAJAJHFL",
    "ASHOKLEY", "IOC", "IEX", "IRB", "EPACK", "ELECTCAST", "HAPPSTMNDS",
    "DREAMFOLKS", "ALOKINDS", "NTPCGREEN", "SALASAR",
    # Watchlist / Monday candidates
    "RVNL", "IRFC", "APOLLO", "TITAGARH", "KAYNES", "RAILTEL"
]

company_names = {
    "COALINDIA": "Coal India",
    "COCHINSHIP": "Cochin Shipyard",
    "SUZLON": "Suzlon Energy",
    "PCBL": "PCBL",
    "LODHA": "Macrotech Developers Lodha",
    "BAJAJHFL": "Bajaj Housing Finance",
    "ASHOKLEY": "Ashok Leyland",
    "IOC": "Indian Oil Corporation",
    "IEX": "Indian Energy Exchange",
    "IRB": "IRB Infrastructure",
    "EPACK": "EPACK Durable",
    "ELECTCAST": "Electrosteel Castings",
    "HAPPSTMNDS": "Happiest Minds",
    "DREAMFOLKS": "Dreamfolks Services",
    "ALOKINDS": "Alok Industries",
    "NTPCGREEN": "NTPC Green",
    "SALASAR": "Salasar Techno",
    "RVNL": "RVNL",
    "IRFC": "IRFC",
    "APOLLO": "Apollo Micro Systems",
    "TITAGARH": "Titagarh Rail",
    "KAYNES": "Kaynes Technology",
    "RAILTEL": "Railtel"
}

print("=" * 80)
print(f"🔍 SCANNING Q2 RESULTS (YESTERDAY & TODAY / LATEST) FOR YOUR PORTFOLIO")
print("=" * 80)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

results_found = []

for sym in portfolio_stocks:
    cname = company_names.get(sym, sym)
    query = f"{cname} (Q2 OR results OR profit OR dividend)"
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"

    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            items = root.findall(".//item")
            for item in items[:4]:
                title = item.findtext("title", "")
                pub_date = item.findtext("pubDate", "")
                title_lower = title.lower()
                if any(w in title_lower for w in ["q2", "results", "profit", "quarter", "pat", "dividend"]):
                    results_found.append({
                        "symbol": sym,
                        "title": title,
                        "pub_date": pub_date
                    })
    except Exception as e:
        pass

print(f"Total matching Q2 / financial news items found: {len(results_found)}\n")

grouped = {}
for r in results_found:
    grouped.setdefault(r["symbol"], []).append(r)

for sym, items in grouped.items():
    print(f"📌 {sym} ({company_names.get(sym, sym)}):")
    for it in items[:3]:
        print(f"   • [{it['pub_date'][:16]}] {it['title']}")
    print()

