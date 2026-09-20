# STOCK SWING V1 - Complete Process Guide

This folder contains the working swing-trading screening and signal pipeline for the NSE market. The project is built to scan the market, filter candidates, download historical data, calculate technical signals, rank trade setups, and optionally send Telegram alerts. It is designed for signal generation only and does not place broker orders automatically.

Important:
- Do not run scripts with the system Python if the project virtual environment is available.
- Use the workspace venv for all execution.
- The scripts use live Zerodha market data and require valid credentials and a working KITE connection.

## 1. Project Setup

From the project root:

```powershell
cd "D:\Sivakumar\GCP\PRACTICE\AUTOMATION\NiftyScanner\STOCK_SWING_V1_updated"
.\.venv\Scripts\Activate.ps1
```

Or run directly with the venv Python:

```powershell
cd "D:\Sivakumar\GCP\PRACTICE\AUTOMATION\NiftyScanner\STOCK_SWING_V1_updated"
.\.venv\Scripts\python.exe <script_name>.py
```

Required packages are already listed in `requirements.txt` and include `pandas`, `numpy`, `kiteconnect`, `openpyxl`, `pyarrow`, and others.

## 2. Main Execution Flow

The main pipeline is launched by:

```powershell
.\.venv\Scripts\python.exe run_swing_trade_system.py
```

This master driver performs the full screening workflow:

1. Load project settings
2. Verify Zerodha connectivity
3. Load full NSE equity universe
4. Filter by quote liquidity
5. Download historical OHLCV data with cache support
6. Validate historical liquidity
7. Calculate technical indicators
8. Generate swing setup candidates
9. Rank candidates by quality and risk/reward
10. Enrich with company news and sentiment
11. Send Telegram alerts

This is the primary end-to-end process for trade idea generation.

## 3. Process Order by Script

### A. Run the master pipeline
File: run_swing_trade_system.py

Purpose:
- Full market scan workflow
- Technical and liquidity screening
- Candidate generation and ranking
- News enrichment
- Telegram alerting

Command:

```powershell
.\.venv\Scripts\python.exe run_swing_trade_system.py
```

### B. Rebound candidate screening
File: screen_rebound_candidates.py

Purpose:
- Checks large, mid, and small-cap symbols for rebound behavior from 52-week lows/support zones
- Writes output to rebound_stock_candidates.csv

Command:

```powershell
.\.venv\Scripts\python.exe screen_rebound_candidates.py
```

### C. Fundamental support stock screening
File: screen_fundamental_support_stocks.py

Purpose:
- Finds stocks near support with strong fundamentals
- Reads fundamental_snapshot.csv
- Exports results to fundamental_support_candidates.xlsx

Command:

```powershell
.\.venv\Scripts\python.exe screen_fundamental_support_stocks.py
```

Notes:
- If `fundamental_snapshot.csv` is missing, the script creates it from the template automatically.
- You must populate the CSV with trusted data before using it for real screening.

### D. Portfolio recovery workbook
File: generate_portfolio_recovery_plan.py

Purpose:
- Builds the weekly portfolio review and recovery workbook
- Helps classify holdings by trend, action, and average-cost recovery planning
- Saves portfolio_recovery_plan.xlsx

Command:

```powershell
.\.venv\Scripts\python.exe generate_portfolio_recovery_plan.py
```

## 4. Data and Output Files

This folder contains the project data and generated outputs:

- `data/nse_cap_segments/` - NSE cap segment CSV files
- `fundamental_snapshot_template.csv` - template for fundamental inputs
- `fundamental_snapshot.csv` - real fundamental screening input
- `rebound_stock_candidates.csv` - rebound scan results
- `fundamental_support_candidates.xlsx` - fundamental support results
- `portfolio_recovery_plan.xlsx` - weekly portfolio review workbook
- `portfolio_history/` - archived weekly portfolio plans
- `logs/` - logging output

## 5. Folder Responsibilities

### configuration/
Contains settings for the project, connection config, and market parameters.

### zerodha_market_data/
Handles Zerodha connectivity, market data downloads, historical cache storage, and quote checks.

### stock_universe/
Loads NSE universe data and classifies stocks by market cap.

### historical_market_data/
Stores technical indicator logic and calculation transforms.

### swing_strategies/
Contains strategy setups and candidate generation logic.

### trade_selection/
Ranks candidate setups by risk/reward and quality.

### news_analysis/
Adds company news and sentiment context to candidates.

### telegram_alerts/
Formats and sends Telegram alerts for signal generation.

### database/
Stores persistent data structures and cache/backing store logic.

### institutional_data/
Handles FII/DII style institutional data if configured.

### backtesting/
Contains backtesting and historical simulation modules.

## 6. Typical Daily Workflow

1. Activate environment.
2. Run `run_swing_trade_system.py` for the main full scan.
3. Review generated candidates and supporting outputs.
4. Run `screen_rebound_candidates.py` when you want a focused rebound watchlist.
5. Run `screen_fundamental_support_stocks.py` if you need fundamental support screening.
6. Run `generate_portfolio_recovery_plan.py` to review your current portfolio plan.
7. Check Telegram alerts and generated Excel/CSV outputs.

## 7. Important Notes

- This is a signal generation system, not an auto-trading bot.
- No direct broker order placement is implemented in the package.
- A valid Zerodha login and connection must exist.
- Some scripts require market data availability and trusted source inputs.
- If you see a missing package error like `ModuleNotFoundError`, make sure you are using the project venv and not the system `python`.

## 8. Troubleshooting

### Module not found
Use:

```powershell
.\.venv\Scripts\python.exe
```

instead of:

```powershell
python
```

### Missing data file
For fundamentals, copy the template file to `fundamental_snapshot.csv` and populate it with trusted values.

### Parquet cache warning
The project tries to use Parquet cache files. If the engine is missing, the app falls back to CSV storage automatically in the downloader.

## 9. Recommended First Run

Run these in order:

```powershell
.\.venv\Scripts\python.exe screen_rebound_candidates.py
.\.venv\Scripts\python.exe screen_fundamental_support_stocks.py
.\.venv\Scripts\python.exe generate_portfolio_recovery_plan.py
.\.venv\Scripts\python.exe run_swing_trade_system.py
```

This gives a complete signal review workflow across rebound scanning, fundamental screening, portfolio review, and master pipeline execution.

## 10. Summary

This folder is organized as a full market scanning and trade idea pipeline. The master script is the core driver, while the support scripts provide focused analysis for rebound stocks, fundamentals, and portfolio recovery planning.
