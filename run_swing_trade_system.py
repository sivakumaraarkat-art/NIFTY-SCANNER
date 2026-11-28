"""
STOCK SWING V1 - MASTER DRIVER

Executes the complete swing trade screening pipeline:
1. Load configuration
2. Verify Zerodha connection
3. Load full NSE equity universe
4. Stage 1: Fast quote-based liquidity prefilter across full universe
5. Download historical data with caching for top liquid candidates
6. Stage 2: Historical liquidity validation
7. Calculate technical indicators (SMA, EMA, RSI, ATR, Volume)
8. Generate swing trade setup candidates
9. Rank candidates and calculate risk/reward targets
10. Enrich candidates with Live Company News & Sentiment
11. Send Telegram alerts with FII/DII flow & News (signal-only mode)
"""

import os

from configuration.swing_trade_settings import load_settings
from zerodha_market_data.zerodha_connection import (
    create_zerodha_client,
    verify_connection,
)
from stock_universe.nse_stock_universe import load_nse_equity_universe
from stock_universe.liquidity_ranker import (
    prefilter_by_quote_liquidity,
    rank_liquid_stocks,
)
from zerodha_market_data.market_data_downloader import HistoricalMarketDataDownloader
from historical_market_data.technical_indicator_calculator import (
    add_technical_indicators,
)
from swing_strategies.swing_setup_engine import generate_setup_candidates
from trade_selection.swing_candidate_ranker import rank_trade_candidates
from news_analysis.company_news_analyzer import enrich_candidates_with_news
from telegram_alerts.swing_trade_alert_sender import send_swing_alerts
from trade_selection.active_swing_trade_registry import register_swing_candidates
from stock_universe.controlled_stock_universe import (
    parse_controlled_symbols,
    select_controlled_universe,
)
from stock_universe.cap_classification import (
    classify_symbol_by_cap_segment,
    load_nse_cap_snapshot,
)


def build_controlled_candidate_universe(
    stock_candidates: list[dict],
    controlled_symbols: list[str],
    maximum_size: int,
) -> list[dict]:
    """Validate and return an explicit controlled universe in the source order."""
    requested_symbols = parse_controlled_symbols(",".join(controlled_symbols))
    return select_controlled_universe(
        stock_candidates=stock_candidates,
        controlled_symbols=requested_symbols,
        maximum_size=maximum_size,
    )


def main():
    settings = load_settings()
    print("STOCK SWING V1 - MASTER DRIVER\n")

    # ------------------------------------------------------------------
    # STAGE 1: CONFIGURATION
    # ------------------------------------------------------------------
    print("[1/9] Configuration loaded.")

    # ------------------------------------------------------------------
    # STAGE 2: ZERODHA CONNECTION
    # ------------------------------------------------------------------
    client = create_zerodha_client(settings)
    verify_connection(client)
    print("[2/9] Zerodha connection verified.")

    # ------------------------------------------------------------------
    # STAGE 2.5: MARKET REGIME AUDIT (P1: NIFTY 50 Trend Alignment)
    # ------------------------------------------------------------------
    try:
        nifty_quote = client.quote(["NSE:NIFTY 50"]).get("NSE:NIFTY 50", {})
        n_ltp = float(nifty_quote.get("last_price", 0.0))
        n_pc = float(nifty_quote.get("ohlc", {}).get("close", 0.0))
        n_open = float(nifty_quote.get("ohlc", {}).get("open", 0.0))
        if n_pc > 0:
            n_pct = ((n_ltp - n_pc) / n_pc) * 100
            regime = "BULLISH 🚀" if (n_pct >= 0.25 and n_ltp >= n_open) else ("BEARISH ⚠️" if (n_pct <= -0.40 or n_ltp < n_open) else "CHOPPY / NEUTRAL ⚖️")
            print(f"[2.5/9] Market Regime: NIFTY 50 is {regime} ({n_pct:+.2f}%).")
            if "BEARISH" in regime:
                orig_score = settings.minimum_candidate_score
                settings.minimum_candidate_score = max(orig_score, 88)
                print(f"       🛡️ Regime Guard: NIFTY in correction. Tightening swing qualification score ({orig_score} ➔ {settings.minimum_candidate_score}) to filter out correlated drawdowns.")
    except Exception as exc:
        print(f"[2.5/9] Market regime check notice: {exc}")

    # ------------------------------------------------------------------
    # STAGE 3: UNIVERSE DISCOVERY (Full NSE Equity)
    # ------------------------------------------------------------------
    universe = load_nse_equity_universe(client, settings)
    controlled_symbol_source = os.getenv("CONTROLLED_SYMBOLS", "").strip()
    controlled_symbols = parse_controlled_symbols(controlled_symbol_source)

    if controlled_symbols:
        historical_pool = build_controlled_candidate_universe(
            stock_candidates=universe,
            controlled_symbols=controlled_symbols,
            maximum_size=max(1, settings.controlled_universe_size),
        )
        print(
            f"[3/9] Controlled universe selected: {len(historical_pool)} explicit "
            f"symbols from the validated NSE list."
        )
    else:
        historical_pool = universe
        print(f"[3/9] Stock candidates loaded: {len(universe)} symbols.")

    cap_snapshot = load_nse_cap_snapshot()
    cap_by_symbol = {}
    for candidate in historical_pool:
        symbol = str(candidate.get("tradingsymbol", "")).strip().upper()
        if symbol:
            cap_segment = classify_symbol_by_cap_segment(symbol, cap_snapshot)
            candidate["cap_segment"] = cap_segment
            cap_by_symbol[symbol] = cap_segment

    print(
        "[3/9] NSE cap segments: "
        + ", ".join(
            f"{segment}={sum(value == segment for value in cap_by_symbol.values())}"
            for segment in ("LARGE", "MID", "SMALL", "UNKNOWN")
        )
    )

    # ------------------------------------------------------------------
    # STAGE 4: STAGE 1 LIQUIDITY PREFILTER (Quote-based across full market)
    # ------------------------------------------------------------------
    # Prefilter the universe by current traded value using fast batched quote
    # requests. When a controlled symbol list is configured, the wholesale
    # selection is explicit and ordered; no arbitrary slice fallback is allowed.
    try:
        quote_liquid_candidates = prefilter_by_quote_liquidity(
            kite=client,
            stock_candidates=historical_pool,
            maximum_stocks=settings.max_historical_download_symbols,
            request_delay_seconds=1.10,
            minimum_price=settings.minimum_stock_price,
            maximum_price=settings.maximum_stock_price,
        )
        candidate_map = {c["tradingsymbol"]: c for c in historical_pool}
        historical_candidates = []
        for item in quote_liquid_candidates:
            sym = item.get("symbol") or item.get("tradingsymbol")
            if sym and sym in candidate_map:
                historical_candidates.append(candidate_map[sym])

        print(
            f"[4/9] Quote liquidity prefilter: selected {len(historical_candidates)} "
            f"top liquid stocks for historical download."
        )
    except Exception as exc:
        scope = "controlled" if controlled_symbols else "full-universe"
        raise RuntimeError(
            f"Quote prefilter failed for the {scope} scan: {exc}"
        ) from exc

    # ------------------------------------------------------------------
    # STAGE 5: HISTORICAL MARKET DATA DOWNLOAD (with caching)
    # ------------------------------------------------------------------
    downloader = HistoricalMarketDataDownloader(client, settings)
    data = downloader.download_universe(historical_candidates)
    print(f"[5/9] Historical market data ready: {len(data)} symbols.")

    # ------------------------------------------------------------------
    # STAGE 6: STAGE 2 HISTORICAL LIQUIDITY VALIDATION
    # ------------------------------------------------------------------
    liquid_stocks = rank_liquid_stocks(
        market_data=data,
        minimum_average_traded_value=10_000_000,  # 1 Crore daily avg turnover
        maximum_stocks=100,
        minimum_price=settings.minimum_stock_price,
        maximum_price=settings.maximum_stock_price,
    )
    liquid_symbols = {item["symbol"] for item in liquid_stocks}
    data = {symbol: df for symbol, df in data.items() if symbol in liquid_symbols}
    print(f"[6/9] Historical liquidity validated: {len(data)} stocks qualify.")

    # ------------------------------------------------------------------
    # STAGE 7: TECHNICAL INDICATORS
    # ------------------------------------------------------------------
    frames = {}
    for symbol, dataframe in data.items():
        try:
            frames[symbol] = add_technical_indicators(dataframe)
        except Exception as exc:
            print(f"WARNING: Indicator calculation failed for {symbol}: {exc}")

    print(f"[7/9] Technical indicators calculated for {len(frames)} symbols.")

    # ------------------------------------------------------------------
    # STAGE 8: STRATEGY SETUP GENERATION & RANKING
    # ------------------------------------------------------------------
    candidates = generate_setup_candidates(frames, settings)
    print(f"[8/9] Initial setup candidates: {len(candidates)}")

    ranked = rank_trade_candidates(candidates, settings)
    for candidate in ranked:
        symbol = str(candidate.get("symbol", "")).strip().upper()
        candidate["cap_segment"] = cap_by_symbol.get(symbol, "UNKNOWN")
    print(f"      Ranked high-conviction candidates: {len(ranked)}")

    # ------------------------------------------------------------------
    # STAGE 8.5: LIVE NEWS, PREDICTIVE CATALYSTS & CRASH RISK SHIELD
    # ------------------------------------------------------------------
    if ranked:
        print(f"      Fetching news & predictive sentiment for top {len(ranked)} candidates...")
        ranked = enrich_candidates_with_news(ranked)

        # Apply Future Predictive Crash Shield (Disqualify SEBI/Fraud/Earnings Blackout)
        safe_ranked = []
        rejected_risks = []
        for cand in ranked:
            if cand.get("is_crash_risk", False):
                rejected_risks.append((cand["symbol"], cand.get("crash_reason", "Critical Red Flag")))
            elif cand.get("earnings_risk", False):
                rejected_risks.append((cand["symbol"], "Upcoming Earnings Blackout in 10-day window"))
            else:
                safe_ranked.append(cand)

        if rejected_risks:
            print(f"      🛡️ Crash Shield Alert: Filtered out {len(rejected_risks)} stock(s) with crash hazards:")
            for sym, rsn in rejected_risks:
                print(f"         - ❌ {sym}: {rsn}")

        # P1: Sector Concentration Cap (Max 2 stocks per sector group)
        from src.scanners.run_options_intraday_scan_powerful_sl import get_stock_sector
        sector_counts = {}
        diversified_ranked = []
        for cand in safe_ranked:
            sym = cand.get("symbol", "")
            sec = get_stock_sector(sym)
            if sec and sector_counts.get(sec, 0) >= 2:
                print(f"      🛡️ Sector Concentration Cap: Skipping {sym} (Sector '{sec}' already has 2 candidates in this batch).")
                continue
            diversified_ranked.append(cand)
            if sec:
                sector_counts[sec] = sector_counts.get(sec, 0) + 1

        if len(diversified_ranked) < len(safe_ranked):
            print(f"      🛡️ Sector Cap: Filtered from {len(safe_ranked)} down to {len(diversified_ranked)} well-diversified candidates.")
        ranked = diversified_ranked

    # ------------------------------------------------------------------
    # STAGE 9: NOTIFICATIONS & ACTIVE 10-DAY SWING REGISTRY
    # ------------------------------------------------------------------
    send_swing_alerts(ranked, settings)
    if ranked:
        registered = register_swing_candidates(ranked, max_holding_days=10)
        print(f"      Registered {len(registered)} trade(s) for 7-10 day lifecycle tracking.")
    print("[9/9] Telegram stage completed & active registry updated.\n")

    print("SCAN COMPLETE - SIGNAL ONLY / NO AUTOMATIC ORDERS")
    return ranked


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Stock Swing V1 Master Engine")
    parser.add_argument("--monitor-exits", action="store_true", help="Monitor active trades for targets, stop-loss, and 10-day time exit")
    parser.add_argument("--audit", action="store_true", help="Generate weekly swing trade performance audit and upload to Telegram")
    parser.add_argument("--close-and-audit", action="store_true", help="Evaluate exits for active batch and dispatch weekly Telegram performance report + Excel")
    args = parser.parse_args()

    if args.close_and_audit:
        from src.scanners.swing_trade_exit_monitor import monitor_active_swing_trades
        from src.scanners.generate_swing_audit import generate_swing_trade_audit
        print("Running Weekly Swing Exit Evaluation & Report Generation...")
        monitor_active_swing_trades()
        generate_swing_trade_audit()
    elif args.monitor_exits:
        from src.scanners.swing_trade_exit_monitor import monitor_active_swing_trades
        monitor_active_swing_trades()
    elif args.audit:
        from src.scanners.generate_swing_audit import generate_swing_trade_audit
        generate_swing_trade_audit()
    else:
        main()
