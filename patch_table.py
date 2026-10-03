import re

html_path = "docs/IMPLEMENTATION_REPORT.html"
with open(html_path, "r", encoding="utf-8") as f:
    text = f.read()

target = """                        <tr>
                            <td>8:00-9:00 AM</td>
                            <td>📰 News Scanner</td>
                            <td>✅ YES</td>
                            <td>Identify macro catalysts</td>
                            <td><code>news_scanner_with_twitter.py --hours 48</code></td>
                        </tr>"""

replacement = """                        <tr>
                            <td>8:00-9:00 AM</td>
                            <td>📰 News Scanner</td>
                            <td>✅ YES</td>
                            <td>Identify macro catalysts</td>
                            <td><code>news_scanner_with_twitter.py --hours 48</code></td>
                        </tr>
                        <tr style="background: #e0e7ff; border-left: 4px solid #6366f1;">
                            <td>9:15-9:20 AM</td>
                            <td>🌅 BTST Exit Engine</td>
                            <td>✅ CRITICAL</td>
                            <td>Calculate BTST exit/roll percentages based on gap</td>
                            <td><code>btst_smart_exit_strategy.py</code></td>
                        </tr>"""

text = text.replace(target, replacement)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(text)
print("Updated Workflow Summary Table")
