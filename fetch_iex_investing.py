import requests
import re

url = 'https://news.google.com/rss/articles/CBMizwFBVV95cUxPOEd6NjZBS2VwOGRjX01FcHlBTDNSZ1dXS0VfMVNaZlFEVUNxT1FqVEpHeXhmS2FLODFOeVJCQ2lzMTZ1RGtwUG1nUXQtT2hTdDVnYVlxY3ZndDZ2WGNYSTI5N1VFRC1KRGl5Sm9QN2hIOWZud2tyN0czOF9YLTd2Y0x5LUE0VTJNbktaVHlRT1cwNDZoTXFKZXFscEFWeTUzcmdidDBITEh5NEhEc1o5bFlkSDhrQkJMMWFkT0ZmQVdMRVZRY2U4a0lsdmtYdjg?oc=5'
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
r = s.get(url, allow_redirects=True)
match = re.search(r'href="(https://in\.investing\.com/[^"]+)"', r.text)
if match:
    investing_url = match.group(1)
    print('Found investing URL:', investing_url)
    r2 = s.get(investing_url)
    lines = [l.strip() for l in re.sub('<[^<]+?>', '', r2.text).split('\n') if len(l.strip()) > 50]
    for l in lines[:25]:
        print('•', l)
else:
    urls = re.findall(r'https?://[^\s"\'<>]+', r.text)
    print('Discovered URLs:', [u for u in urls if 'investing' in u or 'iex' in u])
