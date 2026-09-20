import re
html = open('process_guide_interactive.html', 'r', encoding='utf-8').read()
for match in re.findall(r'<div class="nav-item[^>]*>(.*?)</div>', html, re.IGNORECASE|re.DOTALL):
    print(match.strip())
