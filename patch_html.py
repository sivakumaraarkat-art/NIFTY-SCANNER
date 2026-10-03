import re
with open('docs/IMPLEMENTATION_REPORT.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Update the Intraday 9:45 block
html = html.replace('''<div class="code-block">python "D:/NiftyScanner/STOCK_SWING_V1_updated/src/scanners/run_options_intraday_scan_powerful_sl.py" \
  --symbols RELIANCE,MARUTI,BPCL,KOTAKBANK,ONGC \
  --min-score 50</div>''', '''<div class="code-block">python "D:/NiftyScanner/STOCK_SWING_V1_updated/src/scanners/run_options_intraday_scan_powerful_sl.py" \
  --use-news-candidates \
  --min-score 50</div>''')

# Update the BTST 2:30 block
html = html.replace('''<div class="code-block">python "D:/NiftyScanner/STOCK_SWING_V1_updated/src/scanners/run_btst_options_scan_powerful_sl.py" \
  --symbols RELIANCE,MARUTI,BPCL,HDFCBANK,INFY \
  --min-score 50</div>''', '''<div class="code-block">python "D:/NiftyScanner/STOCK_SWING_V1_updated/src/scanners/run_btst_options_scan_powerful_sl.py" \
  --use-news-candidates \
  --min-score 50</div>''')

# Update the Workflow block logic
html = html.replace(
'''9:50 AM  ├─ Run: python "D:/NiftyScanner/STOCK_SWING_V1_updated/src/scanners/run_options_intraday_scan_powerful_sl.py" \
         │        --symbols RELIANCE,MARUTI,BPCL,KOTAKBANK,ONGC \
         │        --min-score 50''',
'''9:50 AM  ├─ Run: python "D:/NiftyScanner/STOCK_SWING_V1_updated/src/scanners/run_options_intraday_scan_powerful_sl.py" \
         │        --use-news-candidates \
         │        --min-score 50'''
)

html = html.replace(
'''3:10 PM  ├─ Run: python "D:/NiftyScanner/STOCK_SWING_V1_updated/src/scanners/run_btst_options_scan_powerful_sl.py" \
         │        --symbols RELIANCE,MARUTI,BPCL,HDFCBANK,INFY \
         │        --min-score 50''',
'''3:10 PM  ├─ Run: python "D:/NiftyScanner/STOCK_SWING_V1_updated/src/scanners/run_btst_options_scan_powerful_sl.py" \
         │        --use-news-candidates \
         │        --min-score 50'''
)

# And add the VM Cloud Automation Section right after Checklist
vm_section = '''
                <h3 style="margin-top: 40px; color: #667eea;">☁️ Cloud Infrastructure & Oracle VM Automation</h3>
                <div class="improvement-card" style="background: #f8fafc; border-left: 4px solid #3b82f6;">
                    <h4>Fully Automated Trading Pipeline (Crontab based)</h4>
                    <p style="margin-top: 10px;">The entire ecosystem is deployed to an Oracle Linux VM running on <code>140.245.195.112</code>. It utilizes <code>crontab</code> to automatically handle execution precisely on time. The workflow seamlessly relays 'BULLISH' news symbols straight into the Options engines using the new <code>--use-news-candidates</code> flag.</p>
                    
                    <h5 style="margin-top:15px">Active Crontab Schedule (Weekdays only: 1-5):</h5>
                    <div class="code-block" style="margin-top: 5px;">
# 1. MORNING (08:30 AM): Pre-Market News Catalyst Scanner
30 08 * * 1-5 cd /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated && /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/venv/bin/python3 src/scanners/news_scanner_with_twitter.py --hours 48 >> logs/cron_news.log 2>&1

# 2. MORNING (09:12 AM): BTST Smart Exit Monitor
12 09 * * 1-5 cd /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated && /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/venv/bin/python3 src/scanners/run_btst_exit_monitor.py >> logs/cron_btst_exit.log 2>&1

# 3. MID-MORNING (09:50 AM): Intraday Options Engine
50 09 * * 1-5 cd /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated && /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/venv/bin/python3 src/scanners/run_options_intraday_scan_powerful_sl.py --use-news-candidates --min-score 50 >> logs/cron_intraday.log 2>&1

# 4. AFTERNOON (03:00 PM): BTST Overnight Engine
00 15 * * 1-5 cd /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated && /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/venv/bin/python3 src/scanners/run_btst_options_scan_powerful_sl.py --use-news-candidates --min-score 50 >> logs/cron_btst.log 2>&1

# 5. WEEKEND (Saturday 10:00 AM): Weekly Audit Sync to Google Drive
0 10 * * 6 cd /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated && /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/venv/bin/python3 src/scanners/generate_weekly_audit.py >> logs/cron_audit.log 2>&1</div>
                </div>
'''

html = html.replace('</ul>\n            </div>\n            <div id="news" class="tab-content">', '</ul>\n' + vm_section + '\n            </div>\n            <div id="news" class="tab-content">')

# Modify the timeline-details to reflect --use-news-candidates
html = html.replace('<li>Fetches live option chains (±8 strikes ATM)</li>', '<li>Reads 08:30 AM <strong>news predictions JSON</strong> output</li>\n                                <li>Only fetches live option chains for Top Bullish Symbols</li>')

with open('docs/IMPLEMENTATION_REPORT.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Done patching.")
