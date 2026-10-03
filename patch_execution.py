import re

html_path = "docs/IMPLEMENTATION_REPORT.html"
with open(html_path, "r", encoding="utf-8") as f:
    text = f.read()

injection = """                <h2>📅 Complete Step-by-Step Execution Guide with Timing</h2>
                
                <div class="test-card" style="margin-top: 20px; background: #f0fdf4; border-left: 4px solid #16a34a; padding: 20px;">
                    <h3 style="color: #166534; font-size: 1.1em; display: flex; align-items: center;">💡 Built-in Enterprise Guards (October 2026)</h3>
                    <p style="margin-top: 10px; color: #166534;">When you run <b>any</b> of the scanners below, the following guards execute <i>automatically</i> in the background:</p>
                    <ul style="margin-top: 10px; margin-left: 20px; color: #15803d; line-height: 1.6;">
                        <li><b>Weekend & Holiday Guard:</b> Gracefully exits if attempted on a Saturday, Sunday, or any of the 15 NSE yearly holidays.</li>
                        <li><b>Silent Log Rotation:</b> Automatically clears out any JSON logs in the <code>logs/</code> folder older than 30 days to prevent bloat.</li>
                        <li><b>Paper Trading Safe:</b> Defaults to paper-trading mode; live Zerodha execution requires manual CLI flags (infrastructure is ready but safely off).</li>
                    </ul>
                </div>"""

text = text.replace("                <h2>📅 Complete Step-by-Step Execution Guide with Timing</h2>", injection)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(text)
print("Updated Step-by-Step execution in IMPLEMENTATION_REPORT.html")
