import re

html_path = "docs/IMPLEMENTATION_REPORT.html"
with open(html_path, "r", encoding="utf-8") as f:
    text = f.read()

old_list = """                        <li>✅ <strong>src/scanners/btst_smart_exit_strategy.py</strong> - The internal engine for the morning gap-down protection logic.</li>
                    </ul>"""

new_list = """                        <li>✅ <strong>src/scanners/btst_smart_exit_strategy.py</strong> - The internal engine for the morning gap-down protection logic.</li>
                    </ul>

                    <h3 style="color: #ef4444; margin-top: 25px; margin-bottom: 15px;">3. Cleaned Up / Deprecated Scripts (.trash)</h3>
                    <ul style="list-style-type: none; padding-left: 20px; line-height: 2;">
                        <li>🗑️ <strong>.trash/news_based_scanner_improved.py</strong> - Deprecated (Replaced by Twitter scanner)</li>
                        <li>🗑️ <strong>.trash/run_btst_options_scan_improved.py</strong> - Deprecated (Replaced by powerful_sl)</li>
                        <li>🗑️ <strong>.trash/run_btst_options_scan_with_nifty.py</strong> - Deprecated (Replaced by powerful_sl)</li>
                        <li>🗑️ <strong>.trash/run_options_intraday_scan_improved.py</strong> - Deprecated (Replaced by powerful_sl)</li>
                    </ul>"""
                    
text = text.replace(old_list, new_list)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(text)
print("Updated Project Files Map perfectly.")
