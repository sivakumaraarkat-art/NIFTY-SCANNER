# ⏱️ MASTER OPERATIONAL TIMELINE & VM SCHEDULE
### Unified Trading Engines, Options Scanners & Portfolio Sentinel
**Timezone:** Indian Standard Time (`IST` / `UTC+05:30`)  
**Server:** Oracle Cloud VM (`140.245.195.112` / `ubuntu`)  
**Last Updated:** 05-Oct-2026

---

## 🕒 Visual Daily Operational Flow (Monday – Friday)

```
06:00 AM ── [1] Pre-Market Maintenance & Log Cleanup
07:00 AM ── [2] Automated Zerodha Kite Access Token Auth
08:30 AM ── [3] 18-Feed News & Regulatory Catalyst Scan (Intraday Pre-Market)
09:00 AM ── [4] NIFTY V14.9 Paper Trading Engine Launch (Runs All Day)
09:12 AM ── [5] BTST Smart Exit Strategy Check
09:15 AM ── [6] 🛡️ PORTFOLIO CONTINUOUS SENTINEL (Polls Every 15 Mins: 9:15 AM – 3:30 PM)
09:50 AM ── [7] Intraday Options Scan (CE / PE Dynamic Strike Engine)
02:30 PM ── [8] Fresh Afternoon News Catalyst Scan (For BTST)
03:00 PM ── [9] BTST Options Scan (CE / PE Afternoon Setups)
03:15 PM ── 🛡️ Portfolio Guard Daily Wrap-up Summary (Sent by Sentinel)
03:35 PM ── [10] Weekly Audit Report (Dispatches Excel to Telegram & Drive — Fridays Only)
```

---

## 📋 Comprehensive Execution Schedule

| Time (IST) | Days | Engine / Script Path | Target Telegram Bot | Recipient List | Purpose & Scope |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **06:00 AM** | Mon–Fri | `/home/ubuntu/NiftyScanner/daily_system_maintenance.sh` | *Internal VM* | System | Cleans memory caches, trims old log files, and performs disk checks. |
| **07:00 AM** | Mon–Fri | `/home/ubuntu/NiftyScanner/nifty_v14_7/scripts/auto_kite_auth.py` | *Internal VM* | System | Generates fresh daily Zerodha Kite Connect access token via TOTP. |
| **08:30 AM** | Mon–Fri | `STOCK_SWING_V1_updated/src/scanners/news_scanner_with_twitter.py` (`--hours 48`) | **`@Swingtradeniftybot`** | **1 User** *(Siva Kumar)* | Scans 18 RSS media feeds and BSE/NSE filings for morning catalysts. |
| **09:00 AM** | Mon–Fri | `nifty_v14_7/run_NIFTY_V14_9_PAPER.sh` | **`@Jinna_Nifty_BOT`** | **2 Users** *(Siva Kumar + Sravan Reddy)* | Launches the NIFTY V14.9 paper trading engine for market hours. |
| **09:12 AM** | Mon–Fri | `STOCK_SWING_V1_updated/src/scanners/btst_smart_exit_strategy.py` (`--cron`) | **`@Swingtradeniftybot`** | **1 User** *(Siva Kumar)* | Evaluates pre-market opening gaps and triggers profit locking / trailing stops for BTST. |
| **09:15 AM – 03:30 PM** *(Every 15m)* | Mon–Fri | `PORTFOLIO_PEAK_EXIT_GUARD/run_continuous_monitor.sh` | **`@Zerodhaportfoliopro_bot`** | **1 User** *(Siva Kumar)* | **Portfolio Continuous Sentinel:** Monitors 22 Demat holdings silently via state ledger; alerts instantly on state transitions or breaking filings; sends **03:15 PM** daily closing audit. |
| **09:50 AM** | Mon–Fri | `STOCK_SWING_V1_updated/src/scanners/run_options_intraday_scan_powerful_sl.py` | **`@Swingtradeniftybot`** | **1 User** *(Siva Kumar)* | Dynamic ATM/OTM CE/PE options scan with analytical Greeks and 4-layer SL. |
| **02:30 PM** | Mon–Fri | `STOCK_SWING_V1_updated/src/scanners/news_scanner_with_twitter.py` (`--hours 8`) | **`@Swingtradeniftybot`** | **1 User** *(Siva Kumar)* | Scans fresh afternoon news (last 8 hrs) to find breaking catalysts for BTST candidates. |
| **03:00 PM** | Mon–Fri | `STOCK_SWING_V1_updated/src/scanners/run_btst_options_scan_powerful_sl.py` | **`@Swingtradeniftybot`** | **1 User** *(Siva Kumar)* | Dispatches high-probability overnight BTST options trade setups (CE/PE). |
| **03:35 PM** | Fridays Only | `STOCK_SWING_V1_updated/src/scanners/generate_weekly_audit.py` | **`@Swingtradeniftybot`** | **1 User** *(Siva Kumar)* | Compiles the weekly audit spreadsheet and uploads to Telegram & Google Drive. |

---

## 🤖 Dedicated Telegram Bot Routing & Channel Architecture

```
                                    ┌──────────────────────────────────────────────────────────┐
                                    │               NIFTY SCANNER TELEGRAM ROUTING             │
                                    └────────────────────────────┬─────────────────────────────┘
                                                                 │
                 ┌───────────────────────────────────────────────┼───────────────────────────────────────────────┐
                 │                                               │                                               │
                 ▼                                               ▼                                               ▼
   ┌───────────────────────────┐                   ┌───────────────────────────┐                   ┌───────────────────────────┐
   │ 🛡️ PORTFOLIO PEAK GUARD    │                   │ ⚡ SWING & OPTIONS SYSTEM  │                   │ 📈 NIFTY V14.7 ENGINE     │
   │ @Zerodhaportfoliopro_bot  │                   │ @Swingtradeniftybot       │                   │ @Jinna_Nifty_BOT          │
   ├───────────────────────────┤                   ├───────────────────────────┤                   ├───────────────────────────┤
   │ 👤 Recipient: 1 User      │                   │ 👤 Recipient: 1 User      │                   │ 👥 Recipients: 2 Users    │
   │   - Siva Kumar            │                   │   - Siva Kumar            │                   │   - Siva Kumar            │
   │                           │                   │                           │                   │   - Sravan Reddy          │
   │ 📦 Content:               │                   │ 📦 Content:               │                   │ 📦 Content:               │
   │   - 22 Demat Holdings     │                   │   - Intraday Options      │                   │   - NIFTY V14.9 Paper     │
   │   - 20-EMA & Peak Defense │                   │   - BTST Overnight Setups │                   │   - Real-time Signals     │
   │   - 1-Day Pre-Earnings    │                   │   - 18 News Media Scans   │                   │   - Execution Tracking    │
   │   - BSE/NSE Filings (MoU) │                   │   - Weekly Audit Excel    │                   │                           │
   └───────────────────────────┘                   └───────────────────────────┘                   └───────────────────────────┘
```

---

## 🛠️ Linux Crontab Configuration on Cloud VM

```bash
# ==============================================================================
# UNIFIED TRADING ENGINE & SCANNER SCHEDULE (ORACLE VM) - IST Timezone
# ==============================================================================

# 1. 06:00 AM (Mon-Fri): Pre-Market Maintenance & Log Cleanup
00 06 * * 1-5 /home/ubuntu/NiftyScanner/daily_system_maintenance.sh >> /home/ubuntu/NiftyScanner/daily_maintenance.log 2>&1

# 2. 07:00 AM (Mon-Fri): Automated Zerodha Kite Connect Token Generation
00 07 * * 1-5 /home/ubuntu/NiftyScanner/nifty_v14_7/.venv/bin/python /home/ubuntu/NiftyScanner/nifty_v14_7/scripts/auto_kite_auth.py >> /home/ubuntu/NiftyScanner/nifty_v14_7/logs/auto_auth_cron.log 2>&1

# 3. 08:30 AM (Mon-Fri): Pre-Market News Catalyst Scanner (For Intraday Options)
30 08 * * 1-5 cd /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated && /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/venv/bin/python3 src/scanners/news_scanner_with_twitter.py --hours 48 >> logs/cron_news_am.log 2>&1

# 4. 09:00 AM (Mon-Fri): NIFTY V14.9 Paper Trading Engine
00 09 * * 1-5 cd /home/ubuntu/NiftyScanner/nifty_v14_7 && ./run_NIFTY_V14_9_PAPER.sh >> /home/ubuntu/NiftyScanner/nifty_v14_7/logs/cron_v14_9_$(date +\%Y\%m\%d).log 2>&1

# 5. 09:12 AM (Mon-Fri): BTST Smart Exit Monitor
12 09 * * 1-5 cd /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated && /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/venv/bin/python3 src/scanners/btst_smart_exit_strategy.py --cron >> logs/cron_btst_exit.log 2>&1

# 6. 09:15 AM (Mon-Fri): 🛡️ PORTFOLIO CONTINUOUS SENTINEL (09:15 AM - 03:30 PM, Polls Every 15m)
15 09 * * 1-5 /home/ubuntu/NiftyScanner/PORTFOLIO_PEAK_EXIT_GUARD/run_continuous_monitor.sh >> /home/ubuntu/NiftyScanner/PORTFOLIO_PEAK_EXIT_GUARD/logs/cron_sentinel.log 2>&1

# 7. 09:50 AM (Mon-Fri): Options Intraday Scan (CE / PE)
50 09 * * 1-5 cd /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated && /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/venv/bin/python3 src/scanners/run_options_intraday_scan_powerful_sl.py --use-news-candidates --min-score 50 >> logs/cron_intraday.log 2>&1

# 8. 02:30 PM (Mon-Fri): Fresh Afternoon News Catalyst Scanner (For BTST)
30 14 * * 1-5 cd /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated && /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/venv/bin/python3 src/scanners/news_scanner_with_twitter.py --hours 8 >> logs/cron_news_pm.log 2>&1

# 9. 03:00 PM (Mon-Fri): BTST Options Scan (CE / PE)
00 15 * * 1-5 cd /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated && /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/venv/bin/python3 src/scanners/run_btst_options_scan_powerful_sl.py --use-news-candidates --include-nifty --min-score 50 >> logs/cron_btst.log 2>&1

# 10. 03:35 PM (Fridays only): Weekly Trading Audit Generation
35 15 * * 5 cd /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated && /home/ubuntu/NiftyScanner/STOCK_SWING_V1_updated/venv/bin/python3 src/scanners/generate_weekly_audit.py >> logs/cron_audit.log 2>&1
```
