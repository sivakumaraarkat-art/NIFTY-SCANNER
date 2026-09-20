# STOCK SWING V1 - Implementation Roadmap

**Project Status as of 2026-09-14**

## Executive Summary

- **Total Modules**: 45 Python files
- **Implemented**: 16 files (35.6%) - Core pipeline functional
- **Staged/Placeholder**: 26 files (57.8%) - Future enhancements
- **Tests**: 4 files (6 tests passing)
- **Current State**: Signal-only system with basic technical analysis

---

## ✅ Phase 0: COMPLETED (Current Working System)

### What Works Now

The system can run end-to-end and produce swing trade signals:

#### 1. Market Data Pipeline ✅
- Zerodha API connection with shared token
- NSE equity universe loader (filters ETFs, bonds, SGBs)
- Two-stage liquidity filtering:
  - Stage 1: Quote-based prefilter (top 300)
  - Stage 2: Historical validation (top 100, min 10M traded value)
- Historical OHLCV downloader with caching (24h cache)
- Technical indicator calculator (SMA, EMA, RSI, ATR, volume)

#### 2. Strategy Engine ✅
- Basic "TECHNICAL SWING WATCH" strategy
- Score-based system (0-100):
  - Trend alignment (25 pts)
  - RSI health (20 pts)
  - Volume expansion (20 pts)
  - Momentum (20 pts)
  - Breakout proximity (15 pts)
- ATR-based stop loss (1.5× ATR)

#### 3. Trade Selection ✅
- Position size calculator (capital × risk ÷ per-share risk)
- Simple ranking by score
- Fixed 2:1 risk/reward ratio

#### 4. Alerts ✅
- Telegram integration (top 5 signals)
- Safety enforcement (SIGNAL_ONLY=true)
- Console fallback if Telegram not configured

#### 5. Testing ✅
- 6 passing tests covering core modules
- Unit tests for universe selection, liquidity, indicators, position sizing

---

## 🎯 Phase 1: Foundation (Week 1-2)

**Priority: HIGH | Effort: Low | Impact: Quality**

### Goals
- Make the codebase maintainable
- Follow Python best practices
- Improve code readability

### Tasks

#### 1.1 Project Structure
- [ ] Add `__init__.py` to all module directories (13 files)
  - backtesting/
  - configuration/
  - database/
  - fundamental_analysis/
  - historical_market_data/
  - market_analysis/
  - news_analysis/
  - stock_universe/
  - swing_strategies/
  - telegram_alerts/
  - tests/
  - trade_selection/
  - zerodha_market_data/

#### 1.2 Code Quality
- [ ] Refactor `technical_indicator_calculator.py` (currently 10 compressed lines)
  - Break into separate functions with docstrings
  - Add input validation
  - Improve variable naming
  - Add type hints
- [ ] Add docstrings to compressed functions in:
  - `swing_setup_engine.py`
  - `swing_candidate_ranker.py`
  - `telegram_alerts/swing_trade_alert_sender.py`

#### 1.3 Documentation
- [ ] Create `.env.example` template
- [ ] Update PROJECT_FILE_MAP.md with current status
- [ ] Add inline comments to strategy scoring logic
- [ ] Document liquidity filter thresholds and rationale

#### 1.4 Git Management
- [ ] Remove `.venv-1/` directory (duplicate virtual environment)
- [ ] Update `.gitignore` for logs and reports directories

**Deliverable**: Clean, maintainable codebase following Python standards

---

## 🔧 Phase 2: Core Enhancements (Week 3-6)

**Priority: HIGH | Effort: Medium | Impact: Functionality**

### Goals
- Track signal history
- Add more strategy detectors
- Improve risk management

### 2.1 Signal Lifecycle Management

#### Implement `database/swing_signal_database.py`
- [ ] Design signal schema:
  ```python
  {
    "signal_id": "uuid",
    "symbol": "RELIANCE",
    "strategy": "TECHNICAL SWING WATCH",
    "generated_at": "2026-09-14 10:00:00",
    "entry": 2500.00,
    "stop_loss": 2450.00,
    "target": 2600.00,
    "score": 85,
    "status": "NEW|ACTIVE|HIT_TARGET|HIT_STOP|EXPIRED",
    "outcome_date": null,
    "outcome_pnl": null
  }
  ```
- [ ] Implement SQLite storage (use `database/` directory)
- [ ] Add signal deduplication (don't re-alert same setup)
- [ ] Track signal performance (for future backtesting)

#### Signal Tracking Features
- [ ] Store all generated signals
- [ ] Mark signals as active/closed
- [ ] Calculate actual vs expected outcomes
- [ ] Generate weekly performance reports

**Estimated Effort**: 2-3 days

### 2.2 Additional Strategy Detectors

#### Implement `swing_strategies/breakout_setup_detector.py`
- [ ] 20-day high breakout with volume confirmation
- [ ] Consolidation period detection (ATR compression)
- [ ] Volume surge validation (2× average)
- [ ] Integration with swing_setup_engine.py

#### Implement `swing_strategies/trend_pullback_detector.py`
- [ ] Identify strong uptrends (price > SMA50 > SMA200)
- [ ] Detect pullbacks to support (SMA20 or Fibonacci levels)
- [ ] RSI oversold bounce (RSI dips below 40, recovers above)
- [ ] Volume contraction during pullback, expansion on bounce

#### Strategy Integration
- [ ] Modify `swing_setup_engine.py` to call all detectors
- [ ] Each detector returns standardized signal format
- [ ] Combine scores from multiple strategies
- [ ] Add strategy diversity bonus (multi-strategy confirmation)

**Estimated Effort**: 4-5 days

### 2.3 Dynamic Risk Management

#### Implement `trade_selection/stop_loss_calculator.py`
- [ ] ATR-based stops (1.5× to 2.5× ATR based on volatility)
- [ ] Support-level stops (recent swing low)
- [ ] Percentage stops (2-3% for aggressive, 5% for conservative)
- [ ] Choose tightest valid stop

#### Implement `trade_selection/profit_target_calculator.py`
- [ ] Multi-target system:
  - Target 1: 1.5× risk (book 50% position)
  - Target 2: 2.5× risk (book 30% position)
  - Target 3: Trail remaining 20%
- [ ] Resistance-based targets
- [ ] ATR-based targets (3× to 5× ATR)

#### Implement `trade_selection/risk_reward_calculator.py`
- [ ] Calculate actual R:R for each target
- [ ] Validate minimum R:R threshold (default: 2.0)
- [ ] Adjust position size based on R:R quality
- [ ] Filter out poor R:R setups

#### Implement `trade_selection/entry_price_calculator.py`
- [ ] Limit order pricing (avoid market orders)
- [ ] Entry above breakout level with buffer
- [ ] Entry at pullback support levels
- [ ] Current price validation (don't chase)

**Estimated Effort**: 3-4 days

### 2.4 Enhanced Position Sizing

#### Upgrade `trade_selection/position_size_calculator.py`
- [ ] Kelly Criterion option (based on win rate)
- [ ] Volatility-adjusted sizing (reduce size in high ATR)
- [ ] Maximum position size limits (% of capital)
- [ ] Minimum lot size validation
- [ ] Account for brokerage charges

**Estimated Effort**: 1-2 days

**Phase 2 Deliverable**: Robust signal generation with multiple strategies and smart risk management

---

## 📊 Phase 3: Market Context & Filtering (Week 7-10)

**Priority: MEDIUM | Effort: Medium-High | Impact: Win Rate**

### Goals
- Trade only in favorable market conditions
- Filter stocks by fundamental quality
- Avoid earnings surprises

### 3.1 Market Regime Detection

#### Implement `market_analysis/nifty_market_regime.py`
- [ ] Download NIFTY 50 daily data
- [ ] Calculate trend indicators:
  - Price vs SMA50/SMA200 (bull/bear)
  - ADX for trend strength
  - Market breadth (% stocks above SMA50)
- [ ] Classify regime: BULL | CONSOLIDATION | BEAR
- [ ] Generate market regime score (0-100)

#### Implement `market_analysis/sector_strength_analyzer.py`
- [ ] Group NSE stocks by sector
- [ ] Calculate relative strength vs NIFTY
- [ ] Identify leading sectors (buy stocks in these)
- [ ] Identify lagging sectors (avoid these)
- [ ] Sector rotation detection

#### Implement `market_analysis/market_panic_detector.py`
- [ ] VIX India equivalent (if available)
- [ ] Sharp decline detection (NIFTY down >2% in day)
- [ ] Breadth indicators (advancing/declining ratio)
- [ ] Fear gauge: HIGH | MODERATE | LOW

**Estimated Effort**: 4-5 days

### 3.2 Fundamental Filters

#### Implement `fundamental_analysis/quarterly_results_loader.py`
- [ ] Integrate with screener.in API or manual CSV upload
- [ ] Load quarterly results data (revenue, profit, margins)
- [ ] Cache fundamental data (refresh quarterly)
- [ ] Validate data quality

#### Implement `fundamental_analysis/eight_quarter_performance.py`
- [ ] Check last 8 quarters revenue growth
- [ ] Check last 8 quarters profit growth
- [ ] Calculate consistency score
- [ ] Detect earnings deterioration

#### Implement `fundamental_analysis/fundamental_quality_score.py`
- [ ] Scoring system (0-100):
  - Revenue growth trend (25 pts)
  - Profit margin improvement (20 pts)
  - Debt/equity ratio (15 pts)
  - ROE trend (20 pts)
  - Promoter holding stability (20 pts)
- [ ] Filter: only trade stocks scoring >60

**Estimated Effort**: 5-6 days

### 3.3 News & Event Awareness

#### Implement `news_analysis/earnings_event_analyzer.py`
- [ ] Download earnings calendar (NSE or BSE)
- [ ] Flag stocks with earnings in next 5 days
- [ ] Option 1: Avoid these stocks (reduce event risk)
- [ ] Option 2: Create dedicated earnings strategies

#### Implement `news_analysis/negative_event_detector.py`
- [ ] Integrate with NewsAPI or web scraping
- [ ] Detect negative keywords (fraud, regulatory, lawsuit)
- [ ] Block trades in stocks with recent negative news
- [ ] Alert on negative news for held positions

#### Implement `news_analysis/company_news_analyzer.py`
- [ ] Positive catalyst detection (new order, acquisition)
- [ ] Sentiment scoring (positive/negative/neutral)
- [ ] Boost signal score for positive catalysts

**Estimated Effort**: 4-5 days

### 3.4 Strategy Integration with Context

#### Implement `swing_strategies/earnings_reaction_detector.py`
- [ ] Detect post-earnings gaps (>3% move)
- [ ] Volume confirmation after gap
- [ ] Follow-through setup (continuation pattern)
- [ ] Only if earnings beat expectations

#### Implement `swing_strategies/market_panic_discount_detector.py`
- [ ] Detect quality stocks down >10% with market
- [ ] Fundamentals remain strong
- [ ] RSI oversold + market panic
- [ ] Buy the dip in bull market corrections

**Estimated Effort**: 3-4 days

**Phase 3 Deliverable**: Context-aware system that trades only in favorable conditions

---

## 🔬 Phase 4: Backtesting & Validation (Week 11-14)

**Priority: MEDIUM | Effort: High | Impact: Strategy Confidence**

### Goals
- Validate strategies historically
- Optimize parameters
- Understand expected performance

### 4.1 Backtesting Framework

#### Implement `database/market_data_database.py`
- [ ] SQLite database for historical OHLCV
- [ ] Efficient storage (1+ years of daily data)
- [ ] Fast query interface
- [ ] Bulk data loader

#### Implement `backtesting/swing_strategy_backtester.py`
- [ ] Replay historical data day-by-day
- [ ] Generate signals using current strategies
- [ ] Simulate trade execution:
  - Entry at next day open (or limit order)
  - Exit at stop loss or target
  - Track all trades
- [ ] Calculate metrics:
  - Win rate
  - Average R:R
  - Max drawdown
  - Sharpe ratio
  - Total return vs NIFTY

#### Implement `backtesting/historical_trade_simulator.py`
- [ ] Position management rules
- [ ] Slippage and commission modeling
- [ ] Concurrent position limits
- [ ] Portfolio-level tracking

#### Implement `backtesting/backtest_performance_report.py`
- [ ] Generate HTML reports
- [ ] Equity curve charts
- [ ] Trade distribution analysis
- [ ] Strategy comparison tables
- [ ] Parameter sensitivity analysis

**Estimated Effort**: 7-10 days

### 4.2 Strategy Optimization
- [ ] Run backtests for each strategy separately
- [ ] Test parameter variations:
  - ATR multiplier for stops (1.5× vs 2× vs 2.5×)
  - Minimum score threshold (50 vs 60 vs 70)
  - Lookback periods (20 vs 30 vs 50 days)
- [ ] Identify optimal parameter sets
- [ ] Test combined strategy portfolio

**Estimated Effort**: 3-4 days

**Phase 4 Deliverable**: Validated strategies with historical performance data

---

## 🚀 Phase 5: Production Readiness (Week 15-18)

**Priority: LOW | Effort: Medium | Impact: Automation**

### Goals
- Automate daily scanning
- Monitor system health
- Generate reports

### 5.1 Logging & Monitoring

#### Upgrade Logging
- [ ] Implement structured logging (Python `logging` module)
- [ ] Log levels: DEBUG, INFO, WARNING, ERROR
- [ ] Daily log rotation
- [ ] Store logs in `logs/` directory
- [ ] Error alerting via Telegram

#### Health Monitoring
- [ ] Zerodha API health check
- [ ] Cache freshness monitoring
- [ ] Signal generation rate tracking
- [ ] Alert on anomalies (zero signals, API failures)

**Estimated Effort**: 2-3 days

### 5.2 Reporting

#### Daily Reports
- [ ] Generate `reports/daily_scan_YYYY-MM-DD.html`
- [ ] Include:
  - Market regime summary
  - Top liquid stocks scanned
  - Signals generated by strategy
  - Position sizing recommendations
- [ ] Email or Telegram summary

#### Weekly Reports
- [ ] Past week signal performance
- [ ] Win rate, average R:R
- [ ] Best/worst performers
- [ ] Strategy effectiveness breakdown

**Estimated Effort**: 3-4 days

### 5.3 Automation

#### Scheduler Setup
- [ ] Windows Task Scheduler or systemd timer
- [ ] Run daily at market close (3:30 PM IST)
- [ ] Download latest data
- [ ] Generate signals
- [ ] Send alerts
- [ ] Generate reports

#### Graceful Error Handling
- [ ] Retry logic for API failures
- [ ] Fallback to cached data if API down
- [ ] Continue scanning even if some stocks fail
- [ ] Alert on critical failures

**Estimated Effort**: 2-3 days

### 5.4 Configuration Management

#### Environment Profiles
- [ ] Development vs Production configs
- [ ] Separate Telegram channels for testing
- [ ] Risk parameters per environment
- [ ] Feature flags for new strategies

**Estimated Effort**: 1-2 days

**Phase 5 Deliverable**: Fully automated, production-ready system

---

## 🔮 Phase 6: Advanced Features (Future)

**Priority: LOW | Effort: High | Impact: Advanced Users**

### Potential Enhancements

#### 6.1 Machine Learning Integration
- [ ] Train ML models on historical patterns
- [ ] Feature engineering from technical indicators
- [ ] Predict next-day move probability
- [ ] ML-based signal scoring

#### 6.2 Options Strategies
- [ ] Detect high-probability option plays
- [ ] Credit spreads in strong trends
- [ ] Iron condors in consolidations
- [ ] Options chain analysis

#### 6.3 Intraday Signals
- [ ] 5-minute or 15-minute timeframe
- [ ] Intraday breakout detection
- [ ] VWAP-based strategies
- [ ] Real-time alerting

#### 6.4 Portfolio Management
- [ ] Track live positions
- [ ] Automated position sizing across multiple signals
- [ ] Portfolio heat map (sector, strategy diversification)
- [ ] Rebalancing recommendations

#### 6.5 Web Dashboard
- [ ] Flask or FastAPI web interface
- [ ] Real-time signal feed
- [ ] Interactive charts
- [ ] Backtest results visualization
- [ ] Trade journal integration

---

## 📋 Implementation Checklist

### Immediate Actions (This Week)
- [ ] Add all `__init__.py` files
- [ ] Refactor `technical_indicator_calculator.py`
- [ ] Create `.env.example`
- [ ] Remove duplicate `.venv-1/`

### Short Term (Next Month)
- [ ] Implement signal database
- [ ] Add 2 more strategy detectors
- [ ] Dynamic profit targets
- [ ] Market regime detection

### Medium Term (Next 3 Months)
- [ ] Fundamental filters
- [ ] News integration
- [ ] Complete backtesting framework
- [ ] Optimize strategies

### Long Term (Next 6 Months)
- [ ] Production automation
- [ ] Comprehensive monitoring
- [ ] Advanced reporting
- [ ] Web dashboard

---

## 📊 Success Metrics

### Code Quality Metrics
- Test coverage: Target >70%
- Linting score: 9.0+/10 (pylint)
- Documentation: All functions documented
- Type hints: 100% coverage

### System Performance Metrics
- Signal generation time: <5 minutes for 100 stocks
- Cache hit rate: >80%
- API error rate: <5%
- Uptime: >99%

### Trading Performance Metrics (Backtest)
- Win rate: Target >50%
- Average R:R: Target >2.0
- Max drawdown: Target <20%
- Sharpe ratio: Target >1.5
- Annual return: Target >NIFTY + 10%

---

## 🛠️ Technology Stack

### Current
- Python 3.14.5
- kiteconnect (Zerodha API)
- pandas, numpy (data processing)
- pyarrow (parquet caching)
- python-dotenv (configuration)
- requests (Telegram)
- pytest (testing)

### Planned Additions
- SQLite (signal and historical data storage)
- matplotlib/plotly (charting for backtests)
- jinja2 (HTML report templates)
- schedule (task automation)
- logging (structured logging)

---

## 📚 Resources & References

### Documentation to Create
1. API_INTEGRATION.md - Zerodha API usage guide
2. STRATEGY_GUIDE.md - Detailed strategy logic documentation
3. DEPLOYMENT.md - Production deployment instructions
4. TROUBLESHOOTING.md - Common issues and fixes

### External Resources
- Zerodha Kite Connect API: https://kite.trade/docs/connect/v3/
- NSE Stock Data: https://www.nseindia.com/
- Telegram Bot API: https://core.telegram.org/bots/api

---

## 🎯 Risk Disclaimer

**IMPORTANT**: This system generates signals for educational and informational purposes only.

- Past performance does not guarantee future results
- All trading involves risk of loss
- User is responsible for all trading decisions
- SIGNAL_ONLY mode must remain enabled until full system validation
- Backtesting results may not reflect real-world trading
- Market conditions change; strategies may become ineffective

---

## 📝 Version History

- **v1.0** (Current) - Basic technical swing scanner
  - Single strategy (technical swing watch)
  - Two-stage liquidity filtering
  - Simple position sizing
  - Telegram alerts

- **v1.1** (Planned - Phase 1-2) - Enhanced strategies
  - Multiple strategy detectors
  - Signal database
  - Dynamic risk management

- **v2.0** (Planned - Phase 3-4) - Context-aware system
  - Market regime detection
  - Fundamental filters
  - Backtesting framework

- **v3.0** (Planned - Phase 5-6) - Production system
  - Full automation
  - Web dashboard
  - Advanced analytics

---

**Last Updated**: 2026-09-14
**Next Review**: End of Phase 1 (Week 2)
