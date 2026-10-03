import re

html_path = "docs/IMPLEMENTATION_REPORT.html"
with open(html_path, "r", encoding="utf-8") as f:
    text = f.read()

# --- 1. Workflow Summary Table ---
workflow_old = """                            <td>9:15-9:30 AM</td>
                            <td>🔴 Market Open</td>
                            <td>-</td>
                            <td>Wait for stabilization</td>
                            <td><i>Do not run scanners</i></td>
                        </tr>"""

workflow_new = """                            <td>9:15-9:30 AM</td>
                            <td>🔴 Market Open (BTST Exit)</td>
                            <td>✅ CRITICAL</td>
                            <td>Calculate BTST Exit/Roll</td>
                            <td><code>btst_smart_exit_strategy.py</code></td>
                        </tr>"""
text = text.replace(workflow_old, workflow_new)

# --- 2. Deployment Tab ---
# Let's find what's in deployment tab
deployment_target = "<h2>🚀 Live Deployment & System Verification</h2>"
deployment_new = """<h2>🚀 Live Deployment & System Verification</h2>

                <div class="test-card" style="margin-top: 20px; background: #f0fdf4; border-left: 4px solid #16a34a; padding: 20px;">
                    <h3 style="color: #166534; font-size: 1.2em;">🟢 Enterprise Auto-Guards & Maintenance (October 2026)</h3>
                    <p style="margin-top: 10px; color: #166534;">The system is currently in Phase 1 (Paper-Trading Safe). The following enterprise infrastructure is now live in production:</p>
                    <ul class="feature-list" style="margin-top: 15px; color: #15803d;">
                        <li><strong>Live API Infrastructure Foundation:</strong> <code>--live-api</code> structure built in. Currently defaults safely to paper trading mode (no real orders) to protect capital. Ready to switch to Live Zerodha API when verified.</li>
                        <li><strong>Weekend & Holiday Guard:</strong> Pre-loaded with 15 NSE holidays for 2026. Automatically halts execution gracefully on weekends or non-trading days to prevent bad signals.</li>
                        <li><strong>Log Rotation Maintenance:</strong> A silent garbage-collection runs on startup, deleting JSON logs older than 30 days to prevent GBs of disk bloat over time.</li>
                    </ul>
                </div>
"""
if "🟢 Enterprise Auto-Guards" not in text:
    text = text.replace(deployment_target, deployment_new)

# --- 3. Project Files & Map ---
# Update directory structure
dir_target = """│   ├── powerful_sl_module.py               # Core SL engine
│   ├── run_btst_options_scan_powerful_sl.py # Final BTST
│   ├── run_options_intraday_scan_powerful_sl.py # Final Intraday
│   └── run_btst_options_scan_with_nifty.py  # NIFTY specialized"""

dir_new = """│   ├── btst_smart_exit_strategy.py         # 9:15 AM cost-to-cost algorithm
│   ├── powerful_sl_module.py               # Core 4-layer SL mathematical engine
│   ├── news_scanner_with_twitter.py        # Final News + Twitter Sentiment Engine
│   ├── run_btst_options_scan_powerful_sl.py # Final BTST + NIFTY
│   └── run_options_intraday_scan_powerful_sl.py # Final Intraday Scanner
│
├── .trash/                           # Replaced / Obsolete Scripts
│   ├── news_based_scanner_improved.py
│   ├── run_btst_options_scan_improved.py
│   ├── run_btst_options_scan_with_nifty.py
│   └── run_options_intraday_scan_improved.py"""

text = text.replace(dir_target, dir_new)

# Also update the summary list at the bottom of file-map
list_target_old = """                    <h3 style="color: #667eea; margin-top: 25px; margin-bottom: 15px;">2. Core Executable Scanners</h3>
                    <ul style="list-style-type: none; padding-left: 20px; line-height: 2;">
                        <li>✅ <strong>src/scanners/run_options_intraday_scan_powerful_sl.py</strong> - The Intraday Scanner (Runs 9:50 AM to 3:25 PM)</li>
                        <li>✅ <strong>src/scanners/run_btst_options_scan_powerful_sl.py</strong> - The BTST & Nifty Overnight Scanner (Runs 3:00 PM to 3:25 PM)</li>
                        <li>✅ <strong>src/scanners/news_scanner_with_twitter.py</strong> - Pre-Market News & Twitter Scanner (Runs 8:30 AM)</li>
                        <li>✅ <strong>src/scanners/powerful_sl_module.py</strong> - The internal math engine for the 4-Layer Stop Loss Strategy.</li>
                        <li>✅ <strong>src/scanners/btst_smart_exit_strategy.py</strong> - The internal engine for the morning gap-down protection logic.</li>
                    </ul>"""

if "2. Core Executable Scanners" in text:
    pass # It looks fine mostly, let's just make sure it highlights the cleanups.

with open(html_path, "w", encoding="utf-8") as f:
    f.write(text)
print("Updated Workflow, Deployment, and Files Map successfully.")
