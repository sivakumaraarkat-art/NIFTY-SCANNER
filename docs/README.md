# Nifty Options Intraday & News Sentiment Scanner

An automated algorithmic trading system that combines **macro news sentiment analysis** with **options chain scoring** to identify high-probability intraday F&O setups on NSE options.

## 📊 System Overview

```
News Sentiment Engine          Options Intraday Scoring Engine
       ↓                                    ↓
Scrapes 11 RSS Feeds      →    Analyzes 100-point scoring
Ranks Top 10 Stocks       →    (OI, Volume, Price, Greeks)
(Bullish/Bearish)         →    Outputs qualified trades
                                Sends Telegram alerts
```

## ⚙️ Requirements

### Python & Packages
```bash
pip install requests beautifulsoup4 pandas python-docx openpyxl kiteconnect
```

### Zerodha API Setup
- Active Zerodha KiteConnect account with API credentials
- Valid access token (refreshed daily)
- Telegram Bot Token and Chat ID configured

### Platform
- **Windows:** PowerShell 5.0+
- **Linux/Mac:** Bash 4.0+
- Python 3.8+

**Note:** Windows users must prefix all commands with `PYTHONIOENCODING=utf-8` to avoid emoji encoding errors.

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Run News Scanner (Pre-market)
```bash
PYTHONIOENCODING=utf-8 python news_based_scanner.py
```
**Output:** Top 10 macro-impacted stocks with sentiment scores

### Step 2: Copy Symbol List
```
RELIANCE,MARUTI,BPCL,KOTAKBANK,ONGC,GAIL,ICICIBANK,SBIN,BAJAJFINSV,AXISBANK
```

### Step 3: Run Options Intraday Scanner (9:45–10:30 AM)
```bash
PYTHONIOENCODING=utf-8 python run_options_intraday_scan.py \
  --symbols RELIANCE,MARUTI,BPCL,KOTAKBANK,ONGC \
  --min-score 35
```

**Result:** Telegram alerts with scored option trades ready to execute

---

## 📖 Detailed Workflow

See **[EXECUTION_GUIDE.md](EXECUTION_GUIDE.md)** for:
- Step-by-step instructions with real examples
- 100-point scoring engine breakdown
- Greeks filtering explained
- Complete RELIANCE & MARUTI case studies
- Optimal market timing windows
- Troubleshooting & FAQ

---

## 🎯 The 100-Point Scoring Engine

Each option contract is scored across 4 independent dimensions:

| Metric | Points | What It Measures |
|--------|--------|------------------|
| **Open Interest** | 30 | Institutional participation & liquidity depth |
| **Volume Surge** | 25 | Abnormal buying/selling pressure today |
| **Price Action** | 25 | Technical breakout/breakdown signals |
| **Greeks Edge** | 20 | Delta probability band + Theta/Vega optimization |
| **TOTAL** | **100** | Overall trade conviction |

### Score Interpretation

- **95–100 pts:** ✅ High Conviction → Execute full size
- **80–94 pts:** ✅ Strong Buy → 80% size with moderate stops
- **65–79 pts:** 🟡 Moderate → 50% size with tight stops
- **35–64 pts:** ⚠️ Speculative → 25% size (news-driven only)
- **< 35 pts:** ❌ Skip → Do not trade

### Example: RELIANCE 2350 CE

```
Open Interest Score:  27/30  (90% of chain max — Institutional heavy)
Volume Surge Score:   25/25  (2.33x average — Strong buying)
Price Action Score:   24/25  (Above 50-day SMA, RSI 64)
Greeks Edge Score:    19/20  (Delta +0.58 — Optimal probability)
─────────────────────────────────────────────────────
TOTAL SCORE:          95/100  ✅ STRONG BUY
```

---

## 📈 Greeks Filtering Explained

The algorithm prioritizes options with **Delta +0.35 to +0.75** (for calls) or **-0.35 to -0.75** (for puts):

- **Delta ≈ Probability of expiry ITM**
- **+0.5 Delta:** 50% probability (fair bet)
- **+0.35–+0.75 range:** Asymmetric risk/reward
- **> +0.85:** ITM, high gamma risk (avoid)
- **< +0.25:** OTM, lottery ticket (avoid)

Additional checks:
- **Theta:** Bonus if time decay favors your direction
- **Vega:** Penalty if IV is elevated (>75th percentile)
- **Gamma:** Penalize if too high (fast Delta acceleration)

---

## ⏰ Optimal Market Windows

| Time | Recommendation | Why |
|------|-----------------|-----|
| 09:15–09:45 AM | ❌ Avoid | Market opening; high volatility; low liquidity |
| **09:45–10:30 AM** | ✅ **OPTIMAL** | Market settled; volume building; clear trends |
| 10:30 AM–1:30 PM | ✅ Good | Established ranges; moderate activity |
| **1:30–2:45 PM** | ✅ **OPTIMAL** | Afternoon reversal; fresh momentum; peak OI |
| 2:45–3:30 PM | ⚠️ Caution | Approaching close; lower liquidity |

Running the scanner at wrong times = fewer qualified signals (by design, to protect capital).

---

## 📋 Command Parameters

```bash
python run_options_intraday_scan.py \
  --symbols RELIANCE,MARUTI,BPCL        # Required: NSE symbols (comma-separated)
  --min-score 35                         # Default: 35 (score threshold 0–100)
  --option-type BOTH                     # Default: BOTH ("CALL", "PUT", or "BOTH")
  --max-strikes 8                        # Default: 8 (±N strikes around ATM)
```

---

## 📱 Example Output

```
========================================
OPTIONS INTRADAY SCAN | 10:15 AM IST
Symbols: RELIANCE, MARUTI, BPCL
Min Score: 35
========================================

RELIANCE 2350 CE | CALL
  ├─ OI Score: 27/30 | Volume: 25/25 | Price: 24/25 | Greeks: 19/20
  └─ TOTAL: 95/100 ✅ STRONG BUY
  Entry: ₹46.30 | Stop: ₹38.50 | T1: ₹54.80 | T2: ₹65.10
  Delta: +0.58 | Theta: -0.21 | IV: 18.3%

MARUTI 7850 PE | PUT
  ├─ OI Score: 28/30 | Volume: 25/25 | Price: 18/25 | Greeks: 18/20
  └─ TOTAL: 89/100 ✅ STRONG BUY
  Entry: ₹63.50 | Stop: ₹54.20 | T1: ₹72.80 | T2: ₹85.60
  Delta: -0.55 | Theta: +0.18 | IV: 20.5%

BPCL 280 CE | CALL
  ├─ OI Score: 15/30 | Volume: 12/25 | Price: 18/25 | Greeks: 14/20
  └─ TOTAL: 59/100 🟡 MODERATE
  Entry: ₹18.40 | Stop: ₹12.10 | T1: ₹24.60 | T2: ₹32.80

========================================
✅ Telegram alerts sent for 2 trades (95 & 89 scores)
========================================
```

---

## ❓ Common Questions

**Q: I'm getting 0 results. What's wrong?**  
A: This is normal during 9:15–9:45 AM. Market needs time to settle. Retry at 10:15 AM or 1:45 PM.

**Q: Why am I seeing different scores for the same contract at different times?**  
A: Volume, OI, and price action change throughout the day. Morning = low volume (low scores). Mid-morning = volume builds (high scores).

**Q: Should I trade all 10 symbols from the news scanner?**  
A: No. Start with Top 3–5 bullish symbols. Master the system before scaling.

**Q: What if Telegram alerts don't send?**  
A: Check `telegram_bot_token` and `telegram_chat_id` in `swing_trade_settings.py`. Verify connectivity.

**Q: Can I use this for weekly expiries?**  
A: Yes, but reduce position size by 50% (higher Theta decay). Tighten stops.

---

## 📚 Full Documentation

- **[EXECUTION_GUIDE.md](EXECUTION_GUIDE.md)** — Step-by-step workflow with real examples
- **Intraday_Options_Scanner_Strategy_Documentation.docx** — Complete mathematical models & formulas
- **options_intraday_guide.html** — Interactive visual guide (side-by-side nav)

---

## 🔧 Configuration

Edit `configuration/swing_trade_settings.py` to customize:

```python
initial_capital = 500000.0          # Your account capital
risk_per_trade = 0.01               # 1.0% max risk per trade (standard)
telegram_bot_token = "YOUR_TOKEN"   # Get from Telegram BotFather
telegram_chat_id = "YOUR_CHAT_ID"   # Your chat ID
zerodha_api_key = "YOUR_KEY"        # From Zerodha console
minimum_score_threshold = 35        # Default filter level
```

---

## 🚨 Important Notes

1. **This is a signal generation system, not an auto-trading bot.**  
   No broker orders are placed automatically. You execute trades manually.

2. **Timing is critical.**  
   Run during 9:45–10:30 AM or 1:30–2:45 PM IST for best signal quality.

3. **Risk management is essential.**  
   Always use stop losses. Never risk more than 1% per trade.

4. **News matters.**  
   The system works best when macro catalysts are fresh (< 24 hours old).

5. **Market conditions vary.**  
   Flat markets = fewer signals (by design). High-volatility markets = more signals.

---

## 📊 Next Steps

1. Verify Zerodha API credentials are active
2. Configure Telegram bot in `swing_trade_settings.py`
3. Run `python news_based_scanner.py` at 8:30 AM
4. Copy Top 10 symbols
5. Run `python run_options_intraday_scan.py --symbols <list> --min-score 35` at 9:45 AM
6. Monitor Telegram for alerts
7. Execute trades based on conviction scores (95+ only to start)

---

## 📞 Support

For issues with:
- **Zerodha connection:** Verify access token refresh, check market hours
- **Telegram alerts:** Validate bot token and chat ID
- **Scoring logic:** Review `Intraday_Options_Scanner_Strategy_Documentation.docx`
- **Execution questions:** See `EXECUTION_GUIDE.md` for detailed walkthrough
