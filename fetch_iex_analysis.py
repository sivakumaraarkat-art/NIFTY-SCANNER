import requests
import re

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
google_url = 'https://news.google.com/rss/articles/CBMi1gFBVV95cUxQcFQ5cENQbmV0UTBBTTNrQjZzbWJqSUlpaHBWbDVSbl8yWHRfdkQ3bDhmd0JWMzJLeVBpZVdOeHYwYVVwTE16cmRhM3ZRZHhwWmxnQVAzeGQ1VFhSZGV1bUd6Q3F6d1RlUENBV1ZtMlBsUzZlaGNDcGlvTXJaWGtGWGdmeW9lTjNzWXd6NUpZcTJEM0syYllFQ25JTWxBSjUtRERRNk43emJqWVByMXhTajRYVzg4M1hvWG1GTXNvLUJjdl80LVZaUzBaVVNKUjlOUnoyRkRR0gHbAUFVX3lxTE4zN3I0bkV0QkxaR3lwek9yN2tyQzRMaHF3dVJMN2J3YUVTN2tGNlhKUEpsSFQ5b05jXzJfdHdMQktqQ0VpRFEzaHVEdEtlVjF0V3lsNnpHcGxneDR1UUt4cElWdjhSU1N1OE9adldJRTJmelNrZHgyaGhLaGFqb1FSbkhHbkRxVVFvbWJPeGZLUDlxTFNndjBuMkliUzhnTExiQmM0NHBDQmtRd1lfR1d6NzVEY2tfYktFbTRSTE1McU9ZYlp3VW1FbExpNERzRkh4SlhCbzc0U2w4MA?oc=5'

r = s.get(google_url)
urls = re.findall(r'(https://www\.businesstoday\.in/[^\s\"\'<>]+)', r.text)
if urls:
    final_url = urls[0]
    print('Target article URL:', final_url)
    r2 = s.get(final_url)
    lines = [l.strip() for l in re.sub('<[^<]+?>', '', r2.text).split('\n') if len(l.strip()) > 40]
    print(f'Total lines extracted: {len(lines)}')
    for l in lines:
        if any(w in l.lower() for w in ['profit', 'pat', 'target', 'brokerage', 'ambit', 'axis', 'jm financial', 'market coupling', 'cerc', 'volume', 'margin']):
            print('•', l)
else:
    print('URL not matched in redirect.')
