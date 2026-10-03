import re

html_path = "docs/IMPLEMENTATION_REPORT.html"
with open(html_path, "r", encoding="utf-8") as f:
    text = f.read()

old_text = """                    <div class="timeline-item" style="border-left-color: #8b5cf6;">
                        <div class="timeline-time">NEXT DAY: 9:15 AM - 9:45 AM</div>
                        <div class="timeline-action">🌅 BTST EXIT WINDOW</div>
                        <div class="timeline-details">
                            <strong>Market Opens - Fresh Sentiment</strong><br>
                            <strong>BTST Exit Strategy:</strong>
                            <ul style="margin-left: 20px;">
                                <li>Exit at 9:15 AM (best liquidity)</li>
                                <li>Or wait until 9:25-9:45 AM for clearer direction</li>
                                <li>Use limit orders, not market orders</li>
                                <li>Capture overnight gap move (2-5% moves common)</li>
                            </ul>
                            <strong>Example BTST P&L (Next Day):</strong>"""

new_text = """                    <div class="timeline-item" style="border-left-color: #8b5cf6;">
                        <div class="timeline-time">NEXT DAY: 9:15 AM</div>
                        <div class="timeline-action">🌅 BTST SMART EXIT DECISION</div>
                        <div class="timeline-details">
                            <strong>Run the Smart Exit Decision Engine:</strong><br>
                            <div class="code-block" style="margin: 10px 0;">python "D:/NiftyScanner/STOCK_SWING_V1_updated/src/scanners/btst_smart_exit_strategy.py"</div>
                            <strong>What It Does:</strong>
                            <ul style="margin-left: 20px; margin-top: 10px;">
                                <li>Tells you exactly <b>what % to sell</b> based on Gap Up/Flat/Down/Crash.</li>
                                <li>Calculates your <b>"Roll" entry prices</b> if you opened with a Gap Down loss.</li>
                                <li>Saves a checklist guide inside <code>logs/</code> for immediate review.</li>
                                <li>Protects capital via predefined math instead of emotion.</li>
                            </ul>
                            <strong>Next Actions:</strong>
                            <ul style="margin-left: 20px; margin-top: 10px;">
                                <li>Execute the exact recommended % quantities in Zerodha at 9:15-9:20 AM.</li>
                            </ul>
                            <strong>Example BTST P&L (Next Day):</strong>"""

text = text.replace(old_text, new_text)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(text)
print("Updated Next Day Exit Window in IMPLEMENTATION_REPORT.html")
